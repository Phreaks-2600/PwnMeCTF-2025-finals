import ctypes
import struct

from . import base
from .. import objects
from .. import globals

class HackersFtoi(base.RuntimeOp):
    _argtypes_ = (ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8)

    def __python_impl__(a, b, first_argument_register, last_argument_register):
        outer_frame = globals.INTERPRETER_DATA.current_frame[0]
        arg = outer_frame.registers[first_argument_register]

        arg = arg.value_deref

        acc = globals.INTERPRETER_DATA.accumulator

        if isinstance(arg, int):
            val = arg
        elif isinstance(arg, objects.HeapNumber):
            val = arg.value
        else:
            acc.tagged_value = \
                    globals.BROKER.undefined_oddball
            return

        result = struct.unpack('<q', struct.pack('<d', val))[0]

        if objects.SMI(result).value == result:
            acc.smi.value = int(result)
        else:
            acc.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class HackersItof(base.RuntimeOp):
    _argtypes_ = (ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8)

    def __python_impl__(a, b, first_argument_register, last_argument_register):
        outer_frame = globals.INTERPRETER_DATA.current_frame[0]
        arg = outer_frame.registers[first_argument_register]

        arg = arg.value_deref

        acc = globals.INTERPRETER_DATA.accumulator

        if isinstance(arg, int):
            val = arg
        elif isinstance(arg, objects.HeapNumber):
            val = int(arg.value)
        else:
            acc.tagged_value = \
                    globals.BROKER.undefined_oddball
            return

        result = struct.unpack('<d', struct.pack('<q', val))[0]

        acc.tagged_ptr = \
            globals.BROKER.alloc_literal(result, 'Number')


class HackersAddrOf(base.RuntimeOp):
    _argtypes_ = (ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8)

    def __python_impl__(a, b, first_argument_register, last_argument_register):
        outer_frame = globals.INTERPRETER_DATA.current_frame[0]
        arg = outer_frame.registers[first_argument_register]
        result = arg.tagged_ptr.value

        # convert to double so that we have enough bytes :)
        result = struct.unpack('<d', struct.pack('<q', result))[0]

        acc = globals.INTERPRETER_DATA.accumulator

        if (isinstance(result, int) or result.is_integer()) and (
                objects.SMI(int(result)).value == int(result) and \
                        int(result) # Avoid storing zeros as SMI to keep the sign
                        ):
            acc.smi.value = int(result)
        else:
            acc.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')

class HackersFakeObj(base.RuntimeOp):
    _argtypes_ = (ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8)

    def __python_impl__(a, b, first_argument_register, last_argument_register):
        outer_frame = globals.INTERPRETER_DATA.current_frame[0]
        arg = outer_frame.registers[first_argument_register]
        arg = arg.value_deref

        acc = globals.INTERPRETER_DATA.accumulator

        if isinstance(arg, int):
            val = arg
        elif isinstance(arg, objects.HeapNumber):
            val = int(arg.value)
        else:
            acc.tagged_value = \
                    globals.BROKER.undefined_oddball
            return

        acc.tagged_ptr.tagged_value = val

