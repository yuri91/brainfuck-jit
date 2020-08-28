import sys
from collections import namedtuple

import llvmlite.ir as ir
import llvmlite.binding as llvm

from ctypes import CFUNCTYPE

# main (and only) module
module = ir.Module()

# main (and only) function
func_t = ir.FunctionType(ir.VoidType(), [])
func = ir.Function(module, func_t, "func")

# entry point of func
bb_entry = func.append_basic_block('entry')
irbuilder = ir.IRBuilder(bb_entry)

# memory size
NUM_CELLS = 30000

# Types
cell_t = ir.IntType(8)
pcell_t = cell_t.as_pointer()
memory_t = ir.ArrayType(cell_t, NUM_CELLS)
int32_t = ir.IntType(32)

# Constants
zero = cell_t(0)
one = cell_t(1)
minus_one = cell_t(-1)

# Globals
memory = ir.GlobalVariable(module, memory_t, "memory")
memory.initializer = memory_t([0]*NUM_CELLS)

ptr = irbuilder.gep(memory, [zero, zero], "ptr")

# Function declarations
putchar_t = ir.FunctionType(int32_t, [int32_t])
putchar = ir.Function(module, putchar_t, 'putchar')

getchar_t = ir.FunctionType(int32_t, [])
getchar = ir.Function(module, getchar_t, 'getchar')

# for loops
stack = []
class Loop:
    pass


if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        while True:
            c = f.read(1)
            if not c:
                break
            c = c[0]
            if c == '>':
                ptr = irbuilder.gep(ptr, [one])
            elif c == '<':
                ptr = irbuilder.gep(ptr, [minus_one])
            elif c == '+':
                value = irbuilder.load(ptr)
                value = irbuilder.add(value, one)
                irbuilder.store(value, ptr)
            elif c == '-':
                value = irbuilder.load(ptr)
                value = irbuilder.sub(value, one)
                irbuilder.store(value, ptr)
            elif c == '.':
                value = irbuilder.load(ptr)
                value = irbuilder.zext(value, int32_t)
                irbuilder.call(putchar, [value])
            elif c == ',':
                value = irbuilder.call(getchar,[])
                value = irbuilder.trunc(value, cell_t)
                irbuilder.store(value, ptr)
            elif c == '[':
                # prepare data for the stack
                loop = Loop()
                loop.entry = irbuilder.block
                loop.body = irbuilder.append_basic_block("body")
                loop.exit = irbuilder.append_basic_block("exit")

                # emit [ conditional branch
                value = irbuilder.load(ptr)
                cond = irbuilder.icmp_unsigned("!=",value,zero)
                irbuilder.cbranch(cond, loop.body, loop.exit)

                # define the pointer after the loop
                with irbuilder.goto_block(loop.exit):
                    loop.ptr_exit = irbuilder.phi(pcell_t, "ptr")
                    loop.ptr_exit.add_incoming(ptr, loop.entry)

                # define the pointer whitin the loop
                with irbuilder.goto_block(loop.body):
                    loop.ptr_body = irbuilder.phi(pcell_t, "ptr")
                    loop.ptr_body.add_incoming(ptr, loop.entry)

                # continue generating code within the loop
                irbuilder.position_at_end(loop.body)
                ptr = loop.ptr_body
                stack.append(loop)

            elif c == ']':
                if len(stack)==0:
                    print("error: ] requires matching [")
                    exit(1)

                loop = stack.pop()

                #finish the phi nodes
                loop.ptr_body.add_incoming(ptr, irbuilder.block)
                loop.ptr_exit.add_incoming(ptr, irbuilder.block)

                # emit ] conditional branch
                value = irbuilder.load(ptr)
                cond = irbuilder.icmp_unsigned("!=",value, zero)
                irbuilder.cbranch(cond, loop.body, loop.exit)

                # move insertion after the loop
                ptr = loop.ptr_exit
                irbuilder.position_at_end(loop.exit)

            else:
                pass
    irbuilder.ret_void()

    print("=== LLVM IR (Unoptimized)")
    print(module)

    # binding
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    # convert to in-memory representation
    llvm_module = llvm.parse_assembly(str(module))

    # optimization
    pmb = llvm.create_pass_manager_builder()
    pmb.opt_level = 2
    pm = llvm.create_module_pass_manager()
    pmb.populate(pm)
    pm.run(llvm_module)

    print("=== LLVM IR (Optimized)")
    print(str(llvm_module))

    tm = llvm.Target.from_default_triple().create_target_machine()

    print("=== ASM")
    print(tm.emit_assembly(llvm_module))

    with llvm.create_mcjit_compiler(llvm_module, tm) as ee:
        ee.finalize_object()

        cfptr = ee.get_function_address("func")
        cfunc = CFUNCTYPE(None)(cfptr)

        print("=== START")

        cfunc()

        print("=== END")



