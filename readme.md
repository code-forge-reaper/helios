# Helios
Small Assembly-like language made in Python
It does the bare-minimum to get you a working runtime, and that's it


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
    @str print
    
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
  30 fibonacci
end

```

## Defaults
Helios doesn't define much, just these in 27 lines

```python
def buildBuiltins(interp: Vm):
    interp.frames[0].set("stdin", sys.stdin)
    interp.frames[0].set("stdout", sys.stdout)
    interp.frames[0].set("stderr", sys.stderr)
    fid = 0
    def add(fn):
        nonlocal fid
        interp.funcs[fid + 1] = fn
        fid += 1
    def write(f):
        where: IO = f.pop()
        text = f.pop()
        where.write(text)
    def read(f):
        where: IO = f.pop()
        bcount = f.pop()
        char = where.read(bcount)
        f.push(char)
    def Open(f):
        path = f.pop()
        mode = f.pop()
        f.push(open(path, mode))

    add(Open) # 1
    add(write) # 2
    add(read) #...
    add(lambda t: t.pop().flush())
```
