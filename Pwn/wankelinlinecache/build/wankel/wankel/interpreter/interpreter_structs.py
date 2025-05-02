from ..objects import jsvalue, bytecode_array
import ctypes

class PC(ctypes.Union):
    _fields_ = (
        ('as_ptr', ctypes.POINTER(ctypes.c_uint8)),
        ('as_int', ctypes.c_uint64),
    )


class Frame(ctypes.Structure):
    pass

Frame._fields_ = (
        ('previous', ctypes.POINTER(Frame)),
        ('bytecode', ctypes.POINTER(bytecode_array.BytecodeArray)),
        ('registers', ctypes.POINTER(jsvalue.JSValue)),
        ('this', jsvalue.JSValue),
        ('pc', PC),
    )


class InterpreterData(ctypes.Structure):
    _fields_ = (
        ('last_alloc_offset', ctypes.c_uint32),
        ('accumulator', jsvalue.JSValue),
        ('global_object', jsvalue.TaggedPointer),
        ('current_frame', ctypes.POINTER(Frame)),
    )
