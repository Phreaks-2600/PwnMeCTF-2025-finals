import ctypes

from . import base

class HeapNumber(base.ValueObject):
    _fields_ = (
        ('value', ctypes.c_double),
    )

    def __repr__(self):
        return f"{self.value}"


