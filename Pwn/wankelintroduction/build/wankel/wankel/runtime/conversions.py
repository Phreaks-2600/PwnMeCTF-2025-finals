from .. import globals
from .. import objects
from ..objects import base as base_obj
from ..asm import *

from . import base

import ctypes


# https://tc39.es/ecma262/#sec-toboolean
class ToBoolean(base.RuntimeOp):
    __asm_impl__ = [
        mov(rax, globals.INTERPRETER_DATA_PTR),
        mov(eax, dword([rax + type(globals.INTERPRETER_DATA).accumulator.offset])),

        # eax = accumulator
        test(eax, 1),
        jz('handle_smi'),

        # tagged_ptr case
        and_(rax, ~1),

        mov(rbx, globals.BROKER.heap_base.value),

        # rax = ptr to object
        add(rax, rbx),

        # 1. If argument is a Boolean, return argument.
        cmp(dword([rax]), globals.BROKER.builtin_maps[objects.Boolean].tagged_value),
        je('ret'),

        cmp(dword([rax]), globals.BROKER.builtin_maps[objects.JSUndefined].tagged_value),
        je('false'),

        cmp(dword([rax]), globals.BROKER.builtin_maps[objects.JSNull].tagged_value),
        je('false'),

        cmp(dword([rax]), globals.BROKER.builtin_maps[objects.HeapNumber].tagged_value),
        jne('check_string'),

        # Check for NaN
        mov(rbx, qword([rax + objects.HeapNumber.value.offset])),
        mov(rcx, 0x7ff0000000000000),
        and_(rbx, rcx),
        cmp(rbx, rcx),
        jne('check_zeros'),

        mov(rbx, qword([rax + objects.HeapNumber.value.offset])),
        mov(rcx, 0x000fffffffffffff),
        test(rbx, rcx),
        jnz('false'), # NaN if ZF is not set

        label('check_zeros'),

        # Check for zeros
        mov(rbx, qword([rax + objects.HeapNumber.value.offset])),
        mov(rcx, 0x7ff0000000000000),
        and_(rbx, rcx),
        cmp(rbx, rcx),
        je('check_string'), #infty case

        mov(rbx, qword([rax + objects.HeapNumber.value.offset])),
        mov(rcx, 0x000fffffffffffff),
        test(rbx, rcx),
        jz('false'), # 0 if ZF is not set

        label('check_string'),
        cmp(dword([rax]), globals.BROKER.builtin_maps[objects.JSString].tagged_value),
        jne('true'),

        cmp(dword([rax + objects.JSString.length.offset]), 0),
        je('false'),
        jmp('true'),

        label('handle_smi'),

        test(eax, eax),
        jz('false'),

        label('true'),
        mov(rax, globals.INTERPRETER_DATA_PTR),
        mov(dword([rax + type(globals.INTERPRETER_DATA).accumulator.offset]),
            globals.BROKER.true_oddball.tagged_value),
        jmp('ret'),

        label('false'),
        mov(rax, globals.INTERPRETER_DATA_PTR),
        mov(dword([rax + type(globals.INTERPRETER_DATA).accumulator.offset]),
            globals.BROKER.false_oddball.tagged_value),

        label('ret'),
        ret(),
    ]


class ToString(base.RuntimeOp):
    @staticmethod
    def __python_impl__():
        acc = globals.INTERPRETER_DATA.accumulator.value_deref
        globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(str(acc), 'String')

class ToNumber(base.RuntimeOp):
    @staticmethod
    def __python_impl__():
        acc = globals.INTERPRETER_DATA.accumulator.value

        if isinstance(acc, objects.SMI):
            return

        acc_obj = base_obj.AbstractObjectMeta.from_tagged_pointer(acc)

        if isinstance(acc_obj, objects.HeapNumber):
            return


        if isinstance(acc_obj, objects.Boolean):
            globals.INTERPRETER_DATA.accumulator.smi.value = int(acc_obj.value)
            return

        if isinstance(acc_obj, objects.JSUndefined):
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.nan_number
            return

        if isinstance(acc_obj, objects.JSNull):
            globals.INTERPRETER_DATA.accumulator.smi.value = 0
            return

        if isinstance(acc_obj, objects.JSArray):
            # TODO: This is not spec compliant, do we care about this?
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.nan_number
            return

        if isinstance(acc_obj, objects.JSString):
            if acc_obj.length == 0:
                globals.INTERPRETER_DATA.accumulator.smi.value = 0
                return

            try:
                x = float(acc_obj.value)
                if x.is_integer() and objects.SMI(int(x)) == int(x) and int(x):
                    globals.INTERPRETER_DATA.accumulator.smi.value = int(x)
                else:
                    globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                            globals.BROKER.alloc_literal(x, 'Number')
            except ValueError:
                globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.nan_number
            return

        if isinstance(acc_obj, objects.JSFunction):
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.nan_number
            return

        if isinstance(acc_obj, objects.JSObject):
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.nan_number
            return

        raise Exception("UNREACHABLE")
