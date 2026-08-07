# helios interp
import tokenizer
import sys
import codecs
from dataclasses import dataclass, field
from typing import List, Any, Optional
from pprint import pprint
strace = False
# Mock tokenizer import as per your existing code

tokenizer.KEYWORDS.update(
    {
        "repeat",
        "begin",
        "end",
        "pop",
        "return",
        "break",
        "continue",
        "done",
        "TOGGLE_DEBUG_OUTPUT",
        "DEBUG_ACTIVE",
        "while",
        "do",
        "if",
        "else",
        "top",
    })

MAX_F = 100

# --- 1. AST Definition (The Structure) ---

## @NODES ##


class ASTNode:
    def __str__(self):
        return f"{self.__class__.__name__}"


@dataclass
class Block(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class If(ASTNode):
    body: Block
    else_block: Optional[Block]


@dataclass
class FunctionDef(ASTNode):
    name: str
    args: List[str]
    body: Block


@dataclass
class Repeat(ASTNode):
    body: Block


@dataclass
class While(ASTNode):
    body: Block


@dataclass
class Literal(ASTNode):
    value: Any  # int, float, str

    def __str__(self):
        return f'"{self.value}"' if isinstance(self.value, str) else str(self.value)


@dataclass
class Identifier(ASTNode):
    name: str
    token: Any  # Keep token for error reporting

    def __str__(self):
        return self.name


@dataclass
class Attribute(ASTNode):
    name: str  # e.g. "str", "int"

    def __str__(self):
        return f"@{self.name}"


@dataclass
class Op(ASTNode):
    symbol: str

    def __str__(self):
        return self.symbol


@dataclass
class Intrinsic(ASTNode):
    name: str  # "pop", "return", "break", "continue", "done"

    def __str__(self):
        return self.name


@dataclass
class MultiSet(ASTNode):
    """Handles the [ a, b ] syntax"""
    names: List[str]

    def __str__(self):
        return f"[{', '.join(self.names)}]"

# --- 2. The Parser (Building the AST) ---


class Parser:
    def __init__(self, tokens):
        self.tokens = self.expand_includes(tokens)
        self.pos = 0

    def expand_includes(self, tokens):
        """Pre-processor: Handles 'use' directives before parsing"""
        out = []
        i = 0
        while i < len(tokens):
            tk = tokens[i]
            if tk.type == "PP_DIRECTIVE":
                # Assuming simple format: #use "file"
                # Parse the directive content (removing '#')
                tt = tokenizer.tokenize(tk.value[1:], tk.file)
                if tt[0].value == "use":
                    filename = tt[1].value
                    with open(filename, "r") as f:
                        imported = tokenizer.tokenize(f.read(), filename)
                    out.extend(imported)
                else:
                    # Handle other directives or error
                    pass
            else:
                out.append(tk)
            i += 1
        return out

    def peek(self, offset=0):
        if self.pos + offset >= len(self.tokens):
            return None
        return self.tokens[self.pos + offset]

    def advance(self):
        if self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            self.pos += 1
            return t
        return None

    def match(self, type_name=None, value=None):
        t = self.peek()
        if not t:
            return False
        if type_name and t.type != type_name:
            return False
        if value and t.value != value:
            return False
        self.advance()
        return True

    def expect(self, type_name=None, value=None):
        t = self.peek()
        if not t:
            raise ValueError("Unexpected EOF")
        if type_name and t.type != type_name:
            raise ValueError(f"{t.file}:{t.line} Expected type {
                             type_name}, got {t.type}")
        if value and t.value != value:
            raise ValueError(f"{t.file}:{t.line} Expected value '{
                             value}', got '{t.value}'")
        return self.advance()

    def parse_body(self, stop_at="end") -> Block:
        """
        Parses a sequence of statements until a specific keyword (usually 'end') is met.
        Consumes the stop token.
        """
        block = self._parse_until({stop_at})
        # Consume the stop token
        self.expect(value=stop_at)
        return block

    def _parse_until(self, stop_set: set) -> Block:
        """
        Parse statements until the current token's type is in stop_set.
        Does NOT consume the stop token.
        """
        stmts = []
        while self.peek() is not None:
            if self.peek().type in stop_set:
                break
            # Handle nested structures (they may consume their own 'end')
            if self.peek().type == "repeat":
                stmts.append(self.parse_repeat())
            elif self.peek().type == "do":
                stmts.append(self.parse_while())
            elif self.peek().type == "if":
                stmts.append(self.parse_if())
            else:
                stmt = self.parse_statement()
                if stmt:
                    stmts.append(stmt)
        return Block(stmts)

    def parse_if(self):
        self.expect(value="if")
        # Parse the 'then' part until we see 'else' or 'end'
        then_block = self._parse_until({"else", "end"})
        else_block = None
        if self.match(value="else"):
            # Parse the 'else' part until we see 'end'
            else_block = self._parse_until({"end"})
            self.expect(value="end")   # consume the final 'end'
        else:
            # No else, just consume the 'end' that terminated the if
            self.expect(value="end")
        return If(then_block, else_block)

    def parse_repeat(self):
        self.expect(value="repeat")
        body = self._parse_until({"end"})
        self.expect(value="end")
        return Repeat(body)

    def parse_while(self):
        self.expect(value="do")
        body = self._parse_until({"while"})
        self.expect(value="while")
        return While(body)

    def parse_statement(self):
        t = self.peek()

        # 1. Literals
        if t.type == "NUMBER":
            self.advance()
            val = float(t.value) if "." in t.value else int(t.value)
            return Literal(val)

        elif t.type == "STRING":
            self.advance()
            val = codecs.decode(t.value, "unicode-escape")
            return Literal(val)

        # 2. Variable packing: [ a, b ]
        elif t.type == "OP" and t.value == "[":
            return self.parse_multiset()

        # 3. Operations
        elif t.type == "OP":
            self.advance()
            return Op(t.value)

        # 4. Attributes
        elif t.type == "ATTR":
            self.advance()
            return Attribute(t.value[1:])  # strip @

        # 5. Keywords / Intrinsics
        elif t.type in ["pop", "DEBUG_ACTIVE", "top", "return", "break", "continue", "done"]:
            self.advance()
            return Intrinsic(t.value)

        # 6. Identifiers (Function calls or Variable gets)
        elif t.type == "ID":
            self.advance()
            return Identifier(t.value, t)

        else:
            raise ValueError(f"{t.file}:{t.line} Unexpected token {t.value}")

    def parse_multiset(self):
        """Parses [ a, b ]"""
        self.expect(value="[")
        names = []
        while not self.match(value="]"):
            if self.match(value=","):
                continue

            t = self.expect(type_name="ID")
            names.append(t.value)
        return MultiSet(names)

    def parse_function(self):
        """Parses: name : arg1 arg2 begin ... end"""
        name_token = self.expect(type_name="ID")
        self.expect(value=":")

        args = []
        while self.peek().type != "begin":
            arg = self.expect(type_name="ID")
            args.append(arg.value)

        self.expect(type_name="begin")
        body = self.parse_body(stop_at="end")

        return FunctionDef(name_token.value, args, body)

    def parse_program(self):
        functions = {}
        while self.peek() is not None:
            # We expect top-level definitions to be functions in the format: NAME :
            if self.peek().type == "ID" and self.peek(1) and self.peek(1).value == ":":
                fn = self.parse_function()
                functions[fn.name] = fn
            elif self.peek().type == "TOGGLE_DEBUG_OUTPUT":
                self.expect(value="TOGGLE_DEBUG_OUTPUT")
                global strace
                strace = not strace
            else:
                # Skip unknown tokens or raise error?
                # For now, let's assume everything top level is a function
                raise ValueError(
                    f"Expected function definition at {self.peek()}")
        return functions

# --- 3. Errors that we use for control --- ###


class Return(Exception):
    pass


class Break(Exception):
    pass


class Continue(Exception):
    pass
