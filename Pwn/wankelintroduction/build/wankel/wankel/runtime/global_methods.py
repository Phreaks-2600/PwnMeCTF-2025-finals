import ctypes
import time

from ..asm import *

from . import base
from .. import objects
from .. import globals

class GlobalPrint(base.RuntimeOp):
    _argtypes_ = (ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8)

    def __python_impl__(a, b, first_argument_register, last_argument_register):
        outer_frame = globals.INTERPRETER_DATA.current_frame[0]

        print(*[outer_frame.registers[i].value_deref for i in
                range(first_argument_register, last_argument_register + 1)])


class GlobalExit(base.RuntimeOp):
    _argtypes_ = (ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8)

    __asm_impl__ = [
        # sys_exit
        mov(rax, 60),
        mov(rdi, 0),
        syscall(),
    ]


class GlobalSleep(base.RuntimeOp):
    _argtypes_ = (ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8)

    def __python_impl__(a, b, first_argument_register, last_argument_register):
        outer_frame = globals.INTERPRETER_DATA.current_frame[0]

        arg = outer_frame.registers[first_argument_register].value_deref

        if isinstance(arg, int):
            time.sleep(arg)
        elif isinstance(arg, objects.HeapNumber):
            time.sleep(arg.value)

