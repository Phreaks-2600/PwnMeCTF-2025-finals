import ctypes

from . import base

class Boolean(base.ValueObject):
    _fields_ = (
        ('value', ctypes.c_bool),
    )

    def __repr__(self):
        return str(self.value).lower()

