from . import operand_types, bytecode_meta
from . import constant_array_builder


class BytecodeArrayMeta(type):
    def __new__(cls, name, bases, attrs):
        supported_bytecodes = attrs['supported_bytecodes']

        for bytecode in supported_bytecodes:
            attrs[bytecode.__name__.lower()] = cls._get_method(bytecode)

        new_cls = super().__new__(cls, name, bases, attrs)
        return new_cls


    @classmethod
    def _get_method(cls, bytecode: 'bytecode_node.BytecodeNode'):
        def f(self, *args):
            args = [*args]
            for op_name, op_type in bytecode._operands_:
                if op_type is operand_types.FeedbackOperand:
                    args.append(self.n_fb_slots)
                    self.n_fb_slots += 1

            bc = bytecode.from_operands(*args)
            for op_name, op_type in bytecode._operands_:
                if op_type is operand_types.RegisterOperand and \
                        getattr(bc, op_name).value >= self.n_regs:
                    self.n_regs = getattr(bc, op_name).value + 1
            self._bytecode_array.append(bc)
            return bc

        return f



class BytecodeArray(metaclass=BytecodeArrayMeta):
    supported_bytecodes = bytecode_meta.BytecodeMeta.get_bytecodes()

    def __init__(self):
        self._bytecode_array: list[BytecodeNode] = []
        self.constant_array  = constant_array_builder.ConstantArrayBuilder()
        self.n_regs = 0
        self.n_fb_slots = 0

