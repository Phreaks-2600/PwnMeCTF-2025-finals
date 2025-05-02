import ctypes

from . import jsvalue


class AbstractObjectMeta(type(ctypes.Structure)):
    _object_types: list['AbstractObject'] = []
    _jsobject: 'AbstractObject'

    def __new__(cls, name, bases, attrs):
        new_cls = super().__new__(cls, name, bases, attrs)
        if name not in ['AbstractObject', 'ValueObject']:
            cls._object_types.append(new_cls)
        if name == 'JSObject':
            cls._jsobject = new_cls
        return new_cls

    @classmethod
    def get_object_types(cls):
        return cls._object_types

    @classmethod
    def from_tagged_pointer(cls, tagged_pointer: jsvalue.TaggedPointer):
        untagged = tagged_pointer.value
        tmp = ctypes.c_uint32.from_address(untagged)
        tp = jsvalue.TaggedPointer(tmp.value)

        if tp in cls.builtin_maps_reverse:
            return cls.builtin_maps_reverse[tp].from_address(untagged)

        ut = tp.value
        tmp = ctypes.c_uint32.from_address(ut)
        tp = jsvalue.TaggedPointer(tmp.value)
        return cls.map_map_to_orig_type[tp].from_address(untagged)


class AbstractObject(ctypes.Structure, metaclass=AbstractObjectMeta):
    _fields_ = (
        ('map', jsvalue.TaggedPointer),
    )


class ValueObject(AbstractObject):
    def __eq__(self, other):
        if type(other) != type(self):
            return False

        return self.value == other.value

# Avoid circular import
jsvalue.TaggedPointer.obj_from_tagged_pointer = AbstractObjectMeta.from_tagged_pointer

