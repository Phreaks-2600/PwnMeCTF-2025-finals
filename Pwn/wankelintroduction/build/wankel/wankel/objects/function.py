import ctypes

from . import jsobject, jsvalue, bytecode_array, base

class JSFunction(jsobject.JSObject, base.AbstractObject):
    _fields_ = (
        ('bytecode', ctypes.POINTER(bytecode_array.BytecodeArray)),
        ('entry', ctypes.CFUNCTYPE(
            None, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8)),
        ('arity', ctypes.c_uint8),
        ('name', jsvalue.TaggedPointer),
        ('total_time', ctypes.c_uint32), # 1000000 ns => Baseline compiler
                                         # 10000000 ns => Speculative JIT
        ('exec_type', ctypes.c_uint8), # If native => never compile
    )

    def __repr__(self):
        return f"JSFunction `{self.name}`"
