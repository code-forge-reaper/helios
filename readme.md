# Helios
[Small](#Keywords) Forth-like language made in Python
It does the bare-minimum to get you a working runtime, and that's it

## Syntax choices

### Vars/MultiSet
[...] is used to bind variables instead of `<val> <name> =`
because it lets you convey that you want to make more than one variable
`52 12 [x, y]` => x = 52; y = 12

[x y] and [x, y] are the same, a MultiSet node.


### Functions/Procedures
to make a proc you have to do `<id>: [names to bind] begin [body] end`
```txt
dup: x
begin
  x x
end

```

### API-defined functions
the vm has a internal function map which you can define when embedding it,
simply call `@API.add` and define a function
```python
@API.add
def length(f: Frame):
    v = f.pop()
    # print(v)
    f.push(len(v))
```

you have to do `@<name>` to call them
```txt
print:
begin
  @str stdout @write
  "\n" stdout @write
  stdout @flush
end
```

these are defined in [Defaults](#Defaults)
and on procs.txt


## Other stuff

Sample program:
```txt
#use "procs.txt"
fibonacci:n
begin
  // Step 1: Initialize the stack with the first two numbers
  1
  0

  // Step 2: Loop N times
  n repeat
    // Print the current value without destroying it
    dup
    print
    
    // The Stack Math: Transform [A, B] into [B, A+B]
    over        // Stack becomes: [A, B, A]
    +         // Pops B and A, pushes (B+A). Stack becomes: [A, B+A]
    swap        // Stack becomes: [B+A, A] (Rotates the pair for the next loop)
  end

  // Step 3: Clean up the remaining 2 numbers left on the stack
  pop
  pop
end

main:
begin
  "hello, world\n" stdout write
  argv @head print
  argv @length
  2 < if
    30 fibonacci
  else
    argv @head @int fibonacci
  end
end
```

by default we pop the python script from argv, because of this:
```python
import sys
print(sys.argv)
```
> python main.py main.txt 24
>> ['main.py', 'main.txt', '24']


## Defaults
Helios doesn't define much, just these in 24 lines

```python
@API.add
def Open(f):
    path = f.pop()
    mode = f.pop()
    f.push(open(path, mode))


@API.add
def write(f):
    where: IO = f.pop()
    text = f.pop()
    where.write(text)


@API.add
def read(f):
    where: IO = f.pop()
    bcount = f.pop()
    f.push(where.read(bcount))


@API.add
def flush(f):
    f.pop().flush()


@API.add
def head(f):
    v = f.pop()[0]
    # print(v)
    f.push(v)


@API.add
def reverse(f):
    f.top().reverse()


@API.add
def length(f: Frame):
    v = f.pop()
    # print(v)
    f.push(len(v))


@API.add
def tail(f):
    f.push(f.pop()[-1])


def buildBuiltins(interp: Vm):
    API(interp)

```


## Keywords
When I said small, I meant it
15 total lines on the tokenizer are just for these strings
```python
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
        "top"
    })
```

`TOGGLE_DEBUG_OUTPUT` toggles some more nerdy stuff
`DEBUG_ACTIVE` just returns if you have enabled debug

## Nerdy stuff
```txt
╰─>$ scc --by-file *.py helios
───────────────────────────────────────────────────────────────────────────────
Language            Files       Lines    Blanks  Comments       Code Complexity
───────────────────────────────────────────────────────────────────────────────
Python                  3         890       128        31        731        164
───────────────────────────────────────────────────────────────────────────────
nodes.py                          342        50        14        278         19
tokenizer.py                      287        31         6        250         82
helios                            261        47        11        203         63
───────────────────────────────────────────────────────────────────────────────
Total                   3         890       128        31        731        164
───────────────────────────────────────────────────────────────────────────────
```

## License details
Made by cross-sniper/code-forge-reaper
licensed under GPLV3
