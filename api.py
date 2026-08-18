import sys


class API:
    _builtins = []
    _onsetup = []

    @classmethod
    def add(cls, fn=None, *, name=None):
        def register(fn):
            cls._builtins.append((name or fn.__name__, fn))
            return fn

        if fn is not None:
            return register(fn)

        return register

    @classmethod
    def onsetup(cls, fn):
        cls._onsetup.append(fn)
        return fn

    def __init__(self, vm):
        self.vm = vm

        vm.frames[0].set("stdin", sys.stdin)
        vm.frames[0].set("argv", sys.argv)
        vm.frames[0].set("stdout", sys.stdout)
        vm.frames[0].set("stderr", sys.stderr)

        for i in self._onsetup:
            i(self, vm)

        for i, (name, fn) in enumerate(self._builtins, start=1):
            vm.funcs[name] = fn


@API.add(name="io:open")
def OpenFile(f):
    path = f.pop()
    mode = f.pop()
    f.push(open(path, mode))


@API.add(name="io:write")
def Write(f):
    where: IO = f.pop()
    text = f.pop()
    where.write(text)


@API.add(name="io:read")
def Read(f):
    where: IO = f.pop()
    bcount = f.pop()
    f.push(where.read(bcount))


@API.add(name="io:flush")
def Flush(f):
    f.pop().flush()


@API.add
def Head(f):
    v = f.pop()[0]
    # print(v)
    f.push(v)


@API.add
def Reverse(f):
    f.top().reverse()


@API.add
def Length(f):
    v = f.pop()
    # print(v)
    f.push(len(v))


@API.add
def Tail(f):
    f.push(f.pop()[-1])


@API.add(name="array:new")
def EmptyArray(f):
    f.push(list())


@API.add(name="array:push")
def Push(f):
    t = f.pop()
    t.append(f.pop())
    f.push(t)


@API.add(name="str:join")
def Join(f):
    how = f.pop()
    data = f.pop()
    f.push(how.join(data))


def buildBuiltins(interp: Vm):
    API(interp)
