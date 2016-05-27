# brainfuck-jit
a brainfuck just-in-time compiler written in python with llvmlite

## About

This simple program does the following:

* parse a brainfuck source file
* build an llvm ir representation of the program and prints it
* optimize said llvm ir and prints it
* runs it as machine code

## Dependencies

* python
* [llvmlite](http://llvmlite.pydata.org/en/latest/)

## Test

```
python bf.py mandelbrot.bf
```

## Credits

very helpful resources:

* [Building and using llvmlite - a basic example](http://eli.thegreenplace.net/2015/building-and-using-llvmlite-a-basic-example/)
* [llvm-brainfuck] (https://github.com/jeremyroman/llvm-brainfuck) (c++ implementation)
* [pykaleidoscope](https://github.com/eliben/pykaleidoscope) (official tutorial rewritten with llvmlite)
