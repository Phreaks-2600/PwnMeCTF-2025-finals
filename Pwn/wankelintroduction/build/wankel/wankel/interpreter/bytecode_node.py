import ctypes
import time

from ..asm import *

from . import interpreter_structs, bytecode_meta, operand_types
from ..objects import base as base_obj
from .. import objects

from .. import globals

from .. import exceptions

from .. import runtime

from .. import baseline
# from .. import compiler


class BytecodeNode(ctypes.Structure, metaclass=bytecode_meta.BytecodeMeta):
    def __init__(self, *operands):
        super()
        self.id = self._id

    @classmethod
    def from_operands(cls, *operands):
        if len(operands) != len(cls._operands_):
            raise ValueError(f"Expected {len(cls._operands_)} operands, "
                             f"got {len(operands)}")

        res = cls()

        for key_type, value in zip(cls._operands_, operands):
            key, t = key_type
            setattr(res, key, value)

        return res


    def get_cfunc(self):
        if hasattr(self, 'get_assembly'):
            assembly = self.get_assembly() + [ret()]
            f = mkfunction(assembly)
        else:
            args = [getattr(self, k) for k, t in self._operands_]
            args = [x.value if isinstance(x, operand_types.RegisterOperand) \
                    else x for x in args]
            handler = self.__python_handler__

            @ctypes.CFUNCTYPE(None)
            def f():
                handler(*args)

        globals.PY_STRONG_REFERENCES.append(f)

        return f


    def __str__(self):
        return f"{type(self).__name__} " + \
               f"{', '.join(str(getattr(self, x)) for x, y in self._operands_)}"


class Ldar(BytecodeNode):
    _operands_ = (('register', operand_types.RegisterOperand),)

    def get_assembly(self):
        return [
            mov(rax, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.current_frame.offset),
            mov(rax, qword([rax])),
            *([add(rax, interpreter_structs.Frame.registers.offset)] \
                    if interpreter_structs.Frame.registers.offset else []),
            mov(rax, qword([rax])),
            mov(eax, dword([rax + ctypes.sizeof(objects.JSValue) *
                            self.register.value])),
            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(dword([rbx]), eax),
        ]


class LdaConstant(BytecodeNode):
    _operands_ = (('constant_idx', ctypes.c_uint8),)

    def get_assembly(self):
        return [
            mov(rax, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.current_frame.offset),
            mov(rax, qword([rax])),
            *([add(rax, interpreter_structs.Frame.bytecode.offset)] \
                    if interpreter_structs.Frame.bytecode.offset else []),
            mov(rax, qword([rax])),
            *([add(rax, objects.BytecodeArray.const_array.offset)] \
                    if objects.BytecodeArray.const_array.offset else []),
            mov(rax, qword([rax])),
            mov(eax, dword([rax + ctypes.sizeof(objects.JSValue) *
                            self.constant_idx])),
            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(dword([rbx]), eax),
        ]



class LdaSmi(BytecodeNode):
    _operands_ = (('value', ctypes.c_uint32),)

    def get_assembly(self):
        return [
            mov(eax, self.value),
            shl(eax, 1),
            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(dword([rbx]), eax),
        ]


class LdaUndefined(BytecodeNode):
    def get_assembly(self):
        return [
            mov(eax, globals.BROKER.undefined_oddball.tagged_value),
            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(dword([rbx]), eax),
        ]


class LdaTrue(BytecodeNode):
    def get_assembly(self):
        return [
            mov(eax, globals.BROKER.true_oddball.tagged_value),
            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(dword([rbx]), eax),
        ]


class LdaFalse(BytecodeNode):
    def get_assembly(self):
        return [
            mov(eax, globals.BROKER.false_oddball.tagged_value),
            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(dword([rbx]), eax),
        ]

class LdaNull(BytecodeNode):
    def get_assembly(self):
        return [
            mov(eax, globals.BROKER.null_oddball.tagged_value),
            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(dword([rbx]), eax),
        ]

class LdaGlobal(BytecodeNode):
    _operands_ = (('name_idx', ctypes.c_uint8),)

    def get_assembly(self):
        return [
            push(rbp),
            mov(rbp, rsp),
            mov(rax, 0xf),
            not_(rax),
            and_(rsp, rax),
            mov(rax, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.current_frame.offset),
            mov(rax, qword([rax])),
            *([add(rax, interpreter_structs.Frame.bytecode.offset)] \
                    if interpreter_structs.Frame.bytecode.offset else []),
            mov(rax, qword([rax])),
            *([add(rax, objects.BytecodeArray.const_array.offset)] \
                    if objects.BytecodeArray.const_array.offset else []),
            mov(rax, qword([rax])),
            mov(eax, dword([rax + ctypes.sizeof(objects.JSValue) *
                            self.name_idx])),

            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.global_object.offset),
            mov(ebx, dword([rbx])),

            mov(rsi, rax),
            mov(rdi, rbx),

            mov(rax, ctypes.cast(runtime.LoadProperty.__impl__,
                                                 ctypes.c_void_p).value),

            call(rax),

            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(dword([rbx]), eax),
            mov(rsp, rbp),
            pop(rbp),
        ]


class Star(BytecodeNode):
    _operands_ = (('register', operand_types.RegisterOperand),)

    def get_assembly(self):
        return [
            mov(rax, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.current_frame.offset),
            mov(rax, qword([rax])),
            *([add(rax, interpreter_structs.Frame.registers.offset)] \
                    if interpreter_structs.Frame.registers.offset else []),
            mov(rax, qword([rax])),
            *([add(rax, ctypes.sizeof(objects.JSValue) * self.register.value)] \
                    if self.register.value else []),
            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(ebx, dword(rbx)),
            mov(dword([rax]), ebx),
        ]


class StaGlobal(BytecodeNode):
    _operands_ = (('name_idx', ctypes.c_uint8),)

    def get_assembly(self):
        return [
            push(rbp),
            mov(rbp, rsp),
            mov(rax, 0xf),
            not_(rax),
            and_(rsp, rax),
            mov(rax, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.current_frame.offset),
            mov(rax, qword([rax])),
            *([add(rax, interpreter_structs.Frame.bytecode.offset)] \
                    if interpreter_structs.Frame.bytecode.offset else []),
            mov(rax, qword([rax])),
            *([add(rax, objects.BytecodeArray.const_array.offset)] \
                    if objects.BytecodeArray.const_array.offset else []),
            mov(rax, qword([rax])),
            mov(eax, dword([rax + ctypes.sizeof(objects.JSValue) *
                            self.name_idx])),

            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.global_object.offset),
            mov(ebx, dword([rbx])),

            mov(rsi, rax),
            mov(rdi, rbx),

            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(ebx, dword([rbx])),

            mov(rdx, rbx),

            mov(rax, ctypes.cast(runtime.StoreProperty.__impl__,
                                                 ctypes.c_void_p).value),

            call(rax),

            mov(rsp, rbp),
            pop(rbp),
        ]


class DeclareGlobal(BytecodeNode):
    _operands_ = (
        ('name_idx', ctypes.c_uint8),
        ('kind', ctypes.c_uint8), # {'const': 0, 'let': 1, 'var': 2}
                                  # TODO: Declare enum
    )

    def get_assembly(self):
        if self.kind != 2:
            # TODO:
            runtime.ThrowException.call(ctypes.c_char_p(
               b'Only `var` statements allowed in global scope for now...\n\0'))

        return [
            push(rbp),
            mov(rbp, rsp),
            mov(rax, 0xf),
            not_(rax),
            and_(rsp, rax),
            mov(rax, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.current_frame.offset),
            mov(rax, qword([rax])),
            *([add(rax, interpreter_structs.Frame.bytecode.offset)] \
                    if interpreter_structs.Frame.bytecode.offset else []),
            mov(rax, qword([rax])),
            *([add(rax, objects.BytecodeArray.const_array.offset)] \
                    if objects.BytecodeArray.const_array.offset else []),
            mov(rax, qword([rax])),
            mov(eax, dword([rax + ctypes.sizeof(objects.JSValue) *
                            self.name_idx])),

            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.global_object.offset),
            mov(ebx, dword([rbx])),

            mov(rsi, rax),
            mov(rdi, rbx),

            mov(rbx, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(ebx, dword([rbx])),

            mov(rdx, rbx),

            mov(rax, ctypes.cast(runtime.StoreProperty.__impl__,
                                                 ctypes.c_void_p).value),

            call(rax),

            mov(rsp, rbp),
            pop(rbp),
        ]


class GetNamedProperty(BytecodeNode):
    _operands_ = (
        ('receiver_register', operand_types.RegisterOperand),
        ('property_name_idx', ctypes.c_uint8),
        ('feedback_slot', operand_types.FeedbackOperand),
    )

    @staticmethod
    def __python_handler__(receiver_register, property_name_idx, fb_slot):
        frame = globals.INTERPRETER_DATA.current_frame[0]
        receiver = frame.registers[receiver_register]

        if receiver.is_smi():
            runtime.ThrowException.call(ctypes.c_char_p(
                f'{receiver} has no properties.\n\0'.encode()))

        key = frame.bytecode[0].const_array[property_name_idx]

        res = runtime.LoadProperty.call(receiver.tagged_ptr, key.tagged_ptr)
        globals.INTERPRETER_DATA.accumulator = res



class SetNamedProperty(BytecodeNode):
    _operands_ = (
        ('receiver_register', operand_types.RegisterOperand),
        ('property_name_idx', ctypes.c_uint8),
        ('feedback_slot', operand_types.FeedbackOperand),
    )

    @staticmethod
    def __python_handler__(receiver_register, property_name_idx, feedback_slo):
        frame = globals.INTERPRETER_DATA.current_frame[0]
        receiver = frame.registers[receiver_register]

        if receiver.is_smi():
            runtime.ThrowException.call(ctypes.c_char_p(
                f'{receiver} has no properties.\n\0'.encode()))

        key = frame.bytecode[0].const_array[property_name_idx]
        value = globals.INTERPRETER_DATA.accumulator

        runtime.StoreProperty.call(receiver.tagged_ptr, key, value)


class GetKeyedProperty(BytecodeNode):
    _operands_ = (
        ('receiver_register', operand_types.RegisterOperand),
        ('feedback_slot', operand_types.FeedbackOperand),
    )

    @staticmethod
    def __python_handler__(receiver_register, fb_slot):
        frame = globals.INTERPRETER_DATA.current_frame[0]
        receiver = frame.registers[receiver_register]

        if receiver.is_smi():
            runtime.ThrowException.call(ctypes.c_char_p(
                f'{receiver} has no properties.\n\0'.encode()))

        key = globals.INTERPRETER_DATA.accumulator

        res = runtime.LoadPropertyOrElement.call(receiver.tagged_ptr, key)
        globals.INTERPRETER_DATA.accumulator = res


class SetKeyedProperty(BytecodeNode):
    _operands_ = (
        ('receiver_register', operand_types.RegisterOperand),
        ('key_register', operand_types.RegisterOperand),
        ('feedback_slot', operand_types.FeedbackOperand),
    )

    @staticmethod
    def __python_handler__(receiver_register, key_register, feedback_slot):
        frame = globals.INTERPRETER_DATA.current_frame[0]
        receiver = frame.registers[receiver_register]

        if receiver.is_smi():
            runtime.ThrowException.call(ctypes.c_char_p(
                f'{receiver} has no properties.\n\0'.encode()))

        key = frame.registers[key_register]
        value = globals.INTERPRETER_DATA.accumulator

        runtime.StorePropertyOrElement.call(receiver.tagged_ptr, key, value)



class SetGetter(BytecodeNode):
    _operands_ = (
        ('receiver_register', operand_types.RegisterOperand),
        ('property_name_idx', ctypes.c_uint8),
    )

    # TODO: Handling of this


class SetSetter(BytecodeNode):
    _operands_ = (
        ('receiver_register', operand_types.RegisterOperand),
        ('property_name_idx', ctypes.c_uint8),
    )

    # TODO: Handling of this


class Call(BytecodeNode):
    _operands_ = (
        ('target_register', operand_types.RegisterOperand),
        ('receiver_register', operand_types.RegisterOperand),
        ('first_argument_register', operand_types.RegisterOperand),
        ('last_argument_register', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(
            target_register, receiver_register,
            first_argument_register, last_argument_register):
        target = globals.INTERPRETER_DATA.current_frame[0].registers[
                target_register].value_deref

        if not isinstance(target, objects.JSFunction):
            runtime.ThrowException.call(ctypes.c_char_p(
               f'{target} is not callable\n\0'.encode()))

        if target.exec_type == 0 and target.total_time > 5000000:
            cplr = baseline.Baseline(target)
            new_f_entry = cplr.compile()
            if new_f_entry:
                target.entry = ctypes.cast(new_f_entry, type(target.entry))
            target.exec_type = 1    # If we failed compiling, we don't want
                                    # to try again each time we hit this

        # if target.exec_type == 1 and target.total_time > 20000000:
        #     cplr = compiler.Compiler(target)
        #     new_f_entry = cplr.compile()
        #     if new_f_entry:
        #         target.entry = ctypes.cast(new_f_entry, type(target.entry))
        #     target.exec_type = 2    # If we failed compiling, we don't want
                                    # to try again each time we hit this

        start = time.perf_counter_ns()
        target.entry(
            target_register,
            receiver_register,
            first_argument_register,
            last_argument_register,
        )
        stop = time.perf_counter_ns()

        target.total_time += int(stop - start)

        return


class CreateObject(BytecodeNode):
    @staticmethod
    def __python_handler__():
        obj = globals.BROKER.alloc(objects.JSObject)
        obj.map = globals.BROKER.builtin_maps[objects.JSObject]
        obj.properties = ctypes.cast(0, ctypes.POINTER(objects.JSValue))
        obj.elements = ctypes.cast(0, ctypes.POINTER(objects.JSValue))
        obj.elements_count = 0
        obj.elements_kind = 0
        obj_ptr = ctypes.pointer(obj)
        obj_ptr_val = ctypes.cast(obj_ptr, ctypes.c_void_p).value

        globals.INTERPRETER_DATA.accumulator.tagged_ptr.value = obj_ptr_val



class CreateArray(BytecodeNode):
    _operands_ = (
        ('length', ctypes.c_int16),
    )

    @staticmethod
    def __python_handler__(length):
        arr = globals.BROKER.alloc(objects.JSArray)
        arr.map = globals.BROKER.builtin_maps[objects.JSArray]
        arr.properties = ctypes.cast(0, ctypes.POINTER(objects.JSValue))
        arr.elements_count = length
        arr.elements_kind = 0
        if length:
            arr.elements = globals.BROKER.alloc(objects.JSValue * length)
        else:
            arr.elements = ctypes.cast(0, ctypes.POINTER(objects.JSValue))

        arr_ptr = ctypes.pointer(arr)
        arr_ptr_val = ctypes.cast(arr_ptr, ctypes.c_void_p).value

        globals.INTERPRETER_DATA.accumulator.tagged_ptr.value = arr_ptr_val



class JmpIf(BytecodeNode):
    _operands_ = (
        ('dest_offset', ctypes.c_int16),
    )

    @staticmethod
    def __python_handler__(dest_offset):
        frame = globals.INTERPRETER_DATA.current_frame.contents

        # We know that this is always emitted after a conversion to boolean
        acc = globals.INTERPRETER_DATA.accumulator.tagged_ptr
        obj = base_obj.AbstractObjectMeta.from_tagged_pointer(acc)
        if obj.value:
            frame.pc.as_int += dest_offset


class Jmp(BytecodeNode):
    _operands_ = (
        ('dest_offset', ctypes.c_int16),
    )

    @staticmethod
    def __python_handler__(dest_offset):
        frame = globals.INTERPRETER_DATA.current_frame.contents
        frame.pc.as_int += dest_offset


class Inc(BytecodeNode):
    @staticmethod
    def __python_handler__():
        # We know that this is always emitted after a conversion to number
        # We can have both SMI or HeapNumber
        acc = globals.INTERPRETER_DATA.accumulator

        if isinstance(acc.value, objects.SMI):
            result = acc.value.value + 1
        else:
            result = acc.value_deref.value + 1


        if (isinstance(result, int) or result.is_integer()) and (
                objects.SMI(int(result)).value == int(result) and \
                        int(result) # Avoid storing zeros as SMI to keep the sign
                        ):
            acc.smi.value = int(result)
        else:
            acc.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class Dec(BytecodeNode):
    @staticmethod
    def __python_handler__():
        # We know that this is always emitted after a conversion to number
        # We can have both SMI or HeapNumber
        acc = globals.INTERPRETER_DATA.accumulator

        if isinstance(acc.value, objects.SMI):
            result = acc.value.value - 1
        else:
            result = acc.value_deref.value - 1


        if (isinstance(result, int) or result.is_integer()) and (
                objects.SMI(int(result)).value == int(result) and \
                        int(result) # Avoid storing zeros as SMI to keep the sign
                        ):
            acc.smi.value = int(result)
        else:
            acc.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class ToNumber(BytecodeNode):
    @staticmethod
    def __python_handler__():
        runtime.ToNumber.call()

class Negate(BytecodeNode):
    @staticmethod
    def __python_handler__():
        # We know that this is always emitted after a conversion to number
        # We can have both SMI or HeapNumber
        acc = globals.INTERPRETER_DATA.accumulator

        if isinstance(acc.value, objects.SMI):
            result = -acc.value.value
        else:
            result = -acc.value_deref.value


        if (isinstance(result, int) or result.is_integer()) and (
                objects.SMI(int(result)).value == int(result) and \
                        int(result) # Avoid storing zeros as SMI to keep the sign
                        ):
            acc.smi.value = int(result)
        else:
            acc.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')

class BitwiseNot(BytecodeNode):
    @staticmethod
    def __python_handler__():
        # We know that this is always emitted after a conversion to number
        # We can have both SMI or HeapNumber
        acc = globals.INTERPRETER_DATA.accumulator

        if isinstance(acc.value, objects.SMI):
            val = acc.value.value
        else:
            val = int(base_obj.AbstractObjectMeta.from_tagged_pointer(acc.value).value)

        res = ~1

        if objects.SMI(res).value == res and res:
            acc.smi.value = res
        else:
            acc.tagged_ptr = globals.BROKER.alloc_literal(res, 'Number')

class ToBooleanLogicalNot(BytecodeNode):
    @staticmethod
    def __python_handler__():
        runtime.ToBoolean.call()
        acc = globals.INTERPRETER_DATA.accumulator.tagged_ptr
        obj = base_obj.AbstractObjectMeta.from_tagged_pointer(acc)
        acc.value = globals.BROKER.false_oddball if obj.value else \
                globals.BROKER.true_oddball


class LogicalOr(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to bool:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToBoolean.call()
        left_ptr = globals.INTERPRETER_DATA.accumulator.tagged_ptr
        left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(left_ptr)

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToBoolean.call()
        right_ptr = globals.INTERPRETER_DATA.accumulator.tagged_ptr
        right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(right_ptr)

        if left_val.value or right_val.value:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.true_oddball
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.false_oddball


class Mul(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        result = left_val * right_val

        if (isinstance(result, int) or result.is_integer()) and (
                objects.SMI(int(result)).value == int(result) and \
                        int(result) # Avoid storing zeros as SMI to keep the sign
                        ):
            globals.INTERPRETER_DATA.accumulator.smi.value = int(result)
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')



class Div(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        if right_val == 0:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.nan_number
            return

        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value


        result = left_val / right_val

        if (isinstance(result, int) or result.is_integer()) and (
                objects.SMI(int(result)).value == int(result) and \
                        int(result) # Avoid storing zeros as SMI to keep the sign
                        ):
            globals.INTERPRETER_DATA.accumulator.smi.value = int(result)
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')



class Mod(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        if right_val == 0:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.nan_number
            return

        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value


        result = left_val % right_val

        if (isinstance(result, int) or result.is_integer()) and (
                objects.SMI(int(result)).value == int(result) and \
                        int(result) # Avoid storing zeros as SMI to keep the sign
                        ):
            globals.INTERPRETER_DATA.accumulator.smi.value = int(result)
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class Add(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        left = frame.registers[left_reg]
        right = frame.registers[right_reg]

        concatenation = False

        if isinstance(left.value_deref, objects.JSString):
            left = left.value_deref
            concatenation = True
            if not isinstance(right.value_deref, objects.JSString):
                globals.INTERPRETER_DATA.accumulator = right
                runtime.ToString.call()
                right = globals.INTERPRETER_DATA.accumulator
            right = right.value_deref

        elif isinstance(right.value_deref, objects.JSString):
            right = right.value_deref
            concatenation = True
            if not isinstance(left.value_deref, objects.JSString):
                globals.INTERPRETER_DATA.accumulator = left
                runtime.ToString.call()
                left = globals.INTERPRETER_DATA.accumulator
            left = left.value_deref


        if concatenation:
            result = left.value[:left.length] + right.value[:right.length]
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.alloc_literal(
                    result.decode(), 'String')
            return


        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        result = left_val + right_val

        if (isinstance(result, int) or result.is_integer()) and (
                objects.SMI(int(result)).value == int(result) and \
                        int(result) # Avoid storing zeros as SMI to keep the sign
                        ):
            globals.INTERPRETER_DATA.accumulator.smi.value = int(result)
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')



class Sub(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        result = left_val - right_val

        if (isinstance(result, int) or result.is_integer()) and (
                objects.SMI(int(result)).value == int(result) and \
                        int(result) # Avoid storing zeros as SMI to keep the sign
                        ):
            globals.INTERPRETER_DATA.accumulator.smi.value = int(result)
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class LShift(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        result = int(left_val) << int(right_val)

        if objects.SMI(result).value == result:
            globals.INTERPRETER_DATA.accumulator.smi.value = result
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class RShift(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        result = int(left_val) >> int(right_val)

        if objects.SMI(result).value == result:
            globals.INTERPRETER_DATA.accumulator.smi.value = result
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class URShift(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        result = ctypes.c_uint32(int(left_val)).value >> \
                ctypes.c_uint32(int(right_val)).value

        if objects.SMI(result).value == result:
            globals.INTERPRETER_DATA.accumulator.smi.value = result
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class LessThan(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        if left_val < right_val:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.true_oddball
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.false_oddball




class LessThanOrEq(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        if left_val <= right_val:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.true_oddball
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.false_oddball


class GreaterThan(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        if left_val > right_val:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.true_oddball
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.false_oddball

class GreaterThanOrEq(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        if left_val >= right_val:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.true_oddball
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.false_oddball

class InstanceOf(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

class InOp(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

class LooseEq(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

class LooseNEq(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

class StrictEq(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        left = frame.registers[left_reg].value_deref
        right = frame.registers[right_reg].value_deref

        if left == right:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.true_oddball
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.false_oddball


class StrictNEq(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        left = frame.registers[left_reg].value_deref
        right = frame.registers[right_reg].value_deref

        if left != right:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.true_oddball
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = globals.BROKER.false_oddball


class BitwiseOr(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        result = int(left_val) | int(right_val)

        if objects.SMI(result).value == result:
            globals.INTERPRETER_DATA.accumulator.smi.value = result
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class BitwiseAnd(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        result = int(left_val) & int(right_val)

        if objects.SMI(result).value == result:
            globals.INTERPRETER_DATA.accumulator.smi.value = result
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class BitwiseXor(BytecodeNode):
    _operands_ = (
        ('left_reg', operand_types.RegisterOperand),
        ('right_reg', operand_types.RegisterOperand),
    )

    @staticmethod
    def __python_handler__(left_reg, right_reg):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        # Convert both values to number:
        globals.INTERPRETER_DATA.accumulator = frame.registers[left_reg]
        runtime.ToNumber.call()
        left_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(left_val, objects.TaggedPointer):
            left_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    left_val).value
        else:
            left_val = left_val.value

        globals.INTERPRETER_DATA.accumulator = frame.registers[right_reg]
        runtime.ToNumber.call()
        right_val = globals.INTERPRETER_DATA.accumulator.value
        if isinstance(right_val, objects.TaggedPointer):
            right_val = base_obj.AbstractObjectMeta.from_tagged_pointer(
                    right_val).value
        else:
            right_val = right_val.value

        result = int(left_val) ^ int(right_val)

        if objects.SMI(result).value == result:
            globals.INTERPRETER_DATA.accumulator.smi.value = result
        else:
            globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                globals.BROKER.alloc_literal(result, 'Number')


class Ret(BytecodeNode):
    @staticmethod
    def __python_handler__():
        globals.INTERPRETER_DATA.current_frame = globals.INTERPRETER_DATA.current_frame.contents.previous
