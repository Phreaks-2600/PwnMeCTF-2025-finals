import ctypes
from . import base

from ..asm import *

class ThrowException(base.RuntimeOp):
    _argtypes_ = (ctypes.c_char_p,)

    __asm_impl__ = [
        # strlen exception message in rdi
        mov(rcx, -1),
        label('strlen_start'),
        inc(rcx),
        cmp([rdi + rcx], 0),
        jne('strlen_start'),
        # Length in rcx

        # sys_write
        mov(rax, 1),
        mov(rdx, rcx),
        mov(rsi, rdi),
        mov(rdi, 2),
        syscall(),

        # sys_exit
        mov(rax, 60),
        mov(rdi, 1),
        syscall(),
    ]
