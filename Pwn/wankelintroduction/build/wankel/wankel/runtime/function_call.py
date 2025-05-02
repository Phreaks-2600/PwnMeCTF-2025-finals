import ctypes
from . import base
from .. import globals

class InterpreterTrampoline(base.RuntimeOp):
    _argtypes_ = (ctypes.c_uint8, ctypes.c_uint8,
                  ctypes.c_uint8, ctypes.c_uint8)

    @staticmethod
    def __python_impl__(target_register: int,
                        receiver_register: int,
                        first_argument_register: int,
                        last_argument_register: int):
        outer_frame = globals.INTERPRETER_DATA.current_frame[0]
        target = outer_frame.registers[target_register].value_deref


        globals.INTERPRETER.alloc_frame(target.bytecode)

        frame = globals.INTERPRETER_DATA.current_frame[0]
        frame.this = outer_frame.registers[receiver_register]

        j = -1

        for i in range(first_argument_register, last_argument_register+1):
            j = i - first_argument_register
            if j >= target.bytecode[0].n_regs or j >= target.arity:
                # Stop filling if those registers are not used :)
                break
            frame.registers[j] = outer_frame.registers[i]

        for i in range(j + 1, min(target.arity, target.bytecode[0].n_regs)):
            frame.registers[i].tagged_ptr = globals.BROKER.undefined_oddball

        globals.INTERPRETER.run()

