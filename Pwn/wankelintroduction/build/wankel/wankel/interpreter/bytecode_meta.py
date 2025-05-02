import ctypes
from ..asm import *

class BytecodeMeta(type(ctypes.Structure)):
    _next_id = 0
    _bytecodes: list['BytecodeNode'] = []

    def __new__(cls, name, bases, attrs):
        id = len(cls._bytecodes)
        operands = attrs.get('_operands_', ())

        attrs['_operands_'] = operands
        attrs['_id'] = ctypes.c_uint8(id)

        python_handler = attrs.get('__python_handler__', BytecodeMeta._get_default_py_handler())
        attrs['__python_handler__'] = python_handler

        if id: # Skip `BytecodeNode` parent class
            attrs['_pack_'] = True
            attrs['_fields_'] = (('id', ctypes.c_uint8), *operands)

        new_cls = super().__new__(cls, name, bases, attrs)

        cls._bytecodes.append(new_cls)

        return new_cls


    @classmethod
    def _get_default_py_handler(cls):
        def f(self, *args, **kwargs):
            print(f"UNREACHABLE: {self}")
            mkfunction([int3()])()
        return f


    @classmethod
    def get_bytecode(cls, bytecode_id: int) -> 'BytecodeNode':
        return cls._bytecodes[bytecode_id]

    @classmethod
    def get_bytecodes(cls) -> list['BytecodeNode']:
        return cls._bytecodes
