import ctypes

from . import jsvalue, base


class Map(base.AbstractObject):
    def __repr__(self):
        return "#Map"

class PropertyDescriptor(base.AbstractObject):
    _fields_ = (
        ('key', jsvalue.JSValue), # TODO: Change this to correct type
        ('writable', ctypes.c_bool),
        ('index', ctypes.c_uint16),
        ('value', jsvalue.JSValue), # Can point to either the value, or a prop
                                    # accessor
        ('enumerable', ctypes.c_bool),
        ('configurable', ctypes.c_bool),
        ('is_simple', ctypes.c_bool), # False if `value` can be a prop accessor
    )

    def __repr__(self):
        return "#PropertyDescriptor"

class PropertyAccessor(base.AbstractObject):
    _fields_ = (
        ('get', ctypes.c_void_p),
        ('set', ctypes.c_void_p),
    )

    def __repr__(self):
        return "#PropertyAccessor"

class TransitionDescriptor(base.AbstractObject):
    _fields_ = (
        ('property', jsvalue.TaggedPointer),
        ('target_map', jsvalue.TaggedPointer),
    )

    def __repr__(self):
        return "#TransitionDescriptor"


class ReceiverMap(Map):
    _fields_ = (
        ("descriptors_count", ctypes.c_uint32),
        ("descriptors", ctypes.POINTER(jsvalue.TaggedPointer)),
        ("transitions_count", ctypes.c_uint32),
        ("transitions", ctypes.POINTER(jsvalue.TaggedPointer)),
    )

    def __repr__(self):
        return "#ReceiverMap"

