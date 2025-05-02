from ..asm import mkfunction
import ctypes

class RuntimeMeta(type):
    def __new__(cls, name, bases, attrs):
        restype  = attrs.get('_restype_', None)
        argtypes = attrs.get('_argtypes_', ())

        ints = {
            1: ctypes.c_uint8,
            2: ctypes.c_uint16,
            4: ctypes.c_uint32,
            8: ctypes.c_uint64,
        }

        fake_restype  = ints[ctypes.sizeof(restype)] if restype else None
        fake_argtypes = tuple(ints[ctypes.sizeof(x)] for x in argtypes)

        if '__asm_impl__' in attrs:
            f = mkfunction(attrs['__asm_impl__'])
            f.restype  = fake_restype
            f.argtypes = fake_argtypes
            attrs['__impl__'] = f
        elif '__python_impl__' in attrs:
            f = ctypes.CFUNCTYPE(fake_restype, *fake_argtypes)(attrs['__python_impl__'])
            attrs['__impl__'] = f


        def wrapper(*args):
            correct_args = [
                ctypes.cast(ctypes.pointer(x), ctypes.POINTER(t))[0]
                for x, t in zip(args, fake_argtypes)
            ]

            ret = attrs['__impl__'](*correct_args)
            return None if restype is None else restype(ret)

        attrs['call'] = wrapper
        new_cls = super().__new__(cls, name, bases, attrs)
        return new_cls


class RuntimeOp(metaclass=RuntimeMeta):
    pass


