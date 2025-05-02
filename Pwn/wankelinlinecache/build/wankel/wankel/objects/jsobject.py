import ctypes

from . import base, jsvalue


class JSObject(base.AbstractObject):
    _fields_ = (
        ('properties', ctypes.POINTER(jsvalue.JSValue)),
        ("elements_kind", ctypes.c_uint8),  # 0: SMI_ELEMENTS
                                            # 1: DOUBLE_ELEMENTS
                                            # 2: OBJECTS_ELEMENTS
        ('elements_count', ctypes.c_uint16),
        ('elements', ctypes.POINTER(jsvalue.JSValue)),
    )

    def __repr__(self):
        return "#<JSObject>"


