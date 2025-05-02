import ctypes

from . import jsobject, base

class JSString(jsobject.JSObject, base.ValueObject):
    _fields_ = (
        ('length', ctypes.c_uint32),
        ('value', ctypes.c_char_p)
    )

    def __repr__(self):
        return self.value[:self.length].decode()

