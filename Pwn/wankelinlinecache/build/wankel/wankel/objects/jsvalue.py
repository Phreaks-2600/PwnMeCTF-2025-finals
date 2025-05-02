import ctypes

from .. import globals


class TaggedPointer(ctypes.Structure):
    _fields_ = (
        ('tagged_value', ctypes.c_uint32),
    )

    def __init__(self, v = None):
        if v is not None:
            self.value = v

    @property
    def value(self):
        return globals.BROKER.heap_base.value + (self.tagged_value & ~1)


    @value.setter
    def value(self, value: int):
        if isinstance(value, TaggedPointer):
            value = value.value
        # Directly setting super().value does not work for some reasons...
        if value > globals.BROKER.heap_base.value:
            self.tagged_value = (value - globals.BROKER.heap_base.value) | 1
        else:
            self.tagged_value = value | 1


    @property
    def value_deref(self):
        return TaggedPointer.obj_from_tagged_pointer(self)


    def __eq__(self, o):
        val = self.value
        if isinstance(o, int):
            if val == o or val | 1 == o:
                return True

            if (val - globals.BROKER.heap_base.value) == o or (val - globals.BROKER.heap_base.value) | 1 == o:
                return True

        if not isinstance(o, type(self)):
            return False

        if val == o.value:
            return True

        obj_self = self.obj_from_tagged_pointer(self)
        obj_o    = self.obj_from_tagged_pointer(o)

        return obj_self == obj_o


    def __hash__(self):
        return hash(self.value)


    def __repr__(self):
        obj = self.obj_from_tagged_pointer(self)
        return f"#TaggedPtr to {obj}"


class SMI(ctypes.Structure):
    _fields_ = (
        ('shifted_value', ctypes.c_int32),
    )

    def __init__(self, v = None):
        if v is not None:
            self.value = v

    @property
    def value(self):
        return self.shifted_value >> 1

    @value.setter
    def value(self, value):
        self.shifted_value = (value if isinstance(value, int) else value.value) << 1


    def __repr__(self):
        return str(self.value)


class JSValue(ctypes.Union):
    _fields_ = (
        ('raw_value', ctypes.c_uint32),
        ('tagged_ptr', TaggedPointer),
        ('smi', SMI),
    )

    def __init__(self, v = None):
        if v is not None:
            self.raw_value = v

    @property
    def value(self):
        if self.raw_value & 1:
            # Tagged:
            return self.tagged_ptr
        return self.smi

    @value.setter
    def value(self, value):
        self.raw_value = value


    @property
    def value_deref(self):
        val = self.value
        if isinstance(val, SMI):
            return val.value
        return TaggedPointer.obj_from_tagged_pointer(val)


    def is_smi(self):
        return not bool(self.raw_value & 1)


    def __repr__(self):
        return str(self.value)


