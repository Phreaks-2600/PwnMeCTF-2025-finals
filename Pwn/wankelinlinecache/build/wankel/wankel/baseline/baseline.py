import ctypes


from .. import globals
from ..interpreter import bytecode_meta, interpreter_structs
from .. import objects

from ..ic import ic

from ..asm import *

class Baseline:
    def __init__(self, function):
        self.function = function
        self.asm = [
            push(rbp),
            mov(rbp, rsp),
            mov(rax, 0xf),
            not_(rax),
            and_(rsp, rax),
        ]

    def compile(self):
        bytecode = self.function.bytecode[0]

        # Allocate frame


        self.asm += [
            mov(rax, globals.INTERPRETER_DATA_PTR + \
                    interpreter_structs.InterpreterData.last_alloc_offset.offset),
            mov(ebx, dword([rax])),
            add(ebx, ctypes.sizeof(interpreter_structs.Frame) +
                ctypes.sizeof(objects.JSValue) * bytecode.n_regs),
            mov(rax, globals.INTERPRETER.interpreter_heap_size),
            cmp(rax, rbx),
            jg('alloc_frame'),

            mov(rax, 1),
            mov(rdi, 2),
            mov(rsi, ctypes.cast(ctypes.c_char_p(b"OOM\n\0"),
                                 ctypes.c_void_p).value),
            mov(rdx, 4),
            syscall(),

            int3(),

            label('alloc_frame'),

            # rcx = last_argument_register
            # rdx = first_argument_register
            # rdi = target_register
            # rsi = receiver_register
            mov(rax, globals.INTERPRETER_DATA_PTR + \
                    interpreter_structs.InterpreterData.last_alloc_offset.offset),
            mov(eax, dword([rax])),
            mov(rbx, globals.INTERPRETER_DATA_PTR),
            add(rax, rbx),

            # rax = frame ptr
            # rcx = last_argument_register
            # rdx = first_argument_register
            # rdi = target_register
            # rsi = receiver_register

            mov(rbx, rax),
            *([add(rbx, interpreter_structs.Frame.previous.offset)] \
                    if interpreter_structs.Frame.previous.offset else []),
            mov(r8, globals.INTERPRETER_DATA_PTR + \
                    interpreter_structs.InterpreterData.current_frame.offset),
            mov(r9, qword([r8])),
            mov(qword([rbx]), r9),
            mov(qword([r8]), rax),

            # rax = frame ptr
            # rcx = last_argument_register
            # rdx = first_argument_register
            # rdi = target_register
            # rsi = receiver_register
            # r9  = outer frame ptr

            mov(rbx, rax),
            *([add(rbx, interpreter_structs.Frame.bytecode.offset)] \
                    if interpreter_structs.Frame.bytecode.offset else []),
            mov(r10, ctypes.cast(self.function.bytecode, ctypes.c_void_p).value),
            mov(qword([rbx]), r10),



            # rax = frame ptr
            # rcx = last_argument_register
            # rdx = first_argument_register
            # rdi = target_register
            # rsi = receiver_register
            # r9  = outer frame ptr

            mov(rbx, rax),
            *([add(rbx, interpreter_structs.Frame.registers.offset)] \
                    if interpreter_structs.Frame.registers.offset else []),
            mov(r8, rax),
            add(r8, ctypes.sizeof(interpreter_structs.Frame)),
            mov(qword([rbx]), r8),

            mov(r8, r9),
            *([add(r8, interpreter_structs.Frame.registers.offset)] \
                    if interpreter_structs.Frame.registers.offset else []),
            mov(r8, qword([r8])),

            # rax = frame ptr
            # rcx = last_argument_register
            # rdx = first_argument_register
            # rdi = target_register
            # rsi = receiver_register
            # r8  = outer frame registers
            # r9  = outer frame ptr

            mov(rbx, rax),
            *([add(rbx, interpreter_structs.Frame.this.offset)] \
                    if interpreter_structs.Frame.this.offset else []),
            mov(r10d, dword([r8 + ctypes.sizeof(objects.JSValue) * rsi])),
            mov(dword([rbx]), r10d),

            mov(r10, rax),
            *([add(r10, interpreter_structs.Frame.registers.offset)] \
                    if interpreter_structs.Frame.registers.offset else []),
            mov(r10, qword([r10])),

            # rax = frame ptr
            # rcx = last_argument_register
            # rdx = first_argument_register
            # rdi = target_register
            # rsi = receiver_register
            # r8  = outer frame registers
            # r9  = outer frame ptr
            # r10  = current frame registers

            mov(rbx, 0),

            label('first_loop_start'),

            cmp(rdx, rcx),
            jg('first_loop_exit'),

            cmp(rbx, min(bytecode.n_regs, self.function.arity)),
            jge('first_loop_exit'),

            mov(r11d, dword([r8 + ctypes.sizeof(objects.JSValue) * rdx])),
            mov(dword([r10 + ctypes.sizeof(objects.JSValue) * rbx]), r11d),

            inc(rbx),
            inc(rdx),

            jmp('first_loop_start'),
            label('first_loop_exit'),

            label('second_loop_start'),

            cmp(rbx, min(bytecode.n_regs, self.function.arity)),
            jge('second_loop_exit'),

            mov(dword([r10 + ctypes.sizeof(objects.JSValue) * rbx]),
                globals.BROKER.undefined_oddball.tagged_value),

            inc(rbx),

            jmp('second_loop_start'),
            label('second_loop_exit'),

            mov(rax, globals.INTERPRETER_DATA_PTR + \
                    interpreter_structs.InterpreterData.last_alloc_offset.offset),
            mov(ebx, dword([rax])),
            add(ebx, ctypes.sizeof(interpreter_structs.Frame) +
                ctypes.sizeof(objects.JSValue) * bytecode.n_regs),
            mov(dword([rax]), ebx),
        ]


        ptr = ctypes.cast(bytecode.bytecode_array, ctypes.c_void_p).value
        offset = 0

        while offset < bytecode.bytecode_size:
            bytecode_id = bytecode.bytecode_array[offset]
            bytecode_node_cls = bytecode_meta.BytecodeMeta.get_bytecode(bytecode_id)
            node = bytecode_node_cls.from_address(ptr + offset)

            self.asm += [label(f"__{offset}__")]
            getattr(self, f"visit_{type(node).__name__}")(node, offset)

            offset += ctypes.sizeof(node)

        f = mkfunction(self.asm)
        f.argtypes = (ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8)
        f.restype = None

        globals.PY_STRONG_REFERENCES.append(f)

        return f


    @classmethod
    def init(cls):
        bytecodes = bytecode_meta.BytecodeMeta.get_bytecodes()
        for bc in bytecodes:
            visitor_name = f"visit_{bc.__name__}"
            if not hasattr(cls, visitor_name):
                def f(self, bytecode_node, offset):
                    if type(bytecode_node) in ic.ICMeta.node_type_to_ic:
                        ic_cls = ic.ICMeta.node_type_to_ic[type(bytecode_node)]
                        bytecode_arr = self.function.bytecode[0]
                        slot = bytecode_arr.feedback_vector[bytecode_node.feedback_slot.value]
                        ic_cls(bytecode_node, slot)
                        asm = [
                            mov(rax,
                                ctypes.cast(ic.IC.ic_handlers[ctypes.addressof(bytecode_node)],
                                            ctypes.c_void_p).value),
                            call(rax),
                        ]

                    elif hasattr(bytecode_node, 'get_assembly'):
                        asm = bytecode_node.get_assembly()
                    else:
                        asm = [
                            mov(rax,
                                ctypes.cast(globals.INTERPRETER.get_bytecode_handler(ctypes.addressof(bytecode_node)),
                                                 ctypes.c_void_p).value),
                            call(rax),
                        ]

                    self.asm += asm

                setattr(cls, visitor_name, f)


    def visit_JmpIf(self, node, offset):
        self.asm += [
            # We know that this is always emitted after a conversion to boolean
            mov(rax, globals.INTERPRETER_DATA_PTR +
                interpreter_structs.InterpreterData.accumulator.offset),
            mov(eax, dword(rax)),
            and_(eax, ~1),
            mov(rbx, globals.BROKER.heap_base.value),
            add(rax, rbx),
            mov(rax, [rax + objects.Boolean.value.offset]),
            test(rax, rax),
            jnz(f"__{offset + node.dest_offset}__"),
        ]


    def visit_Jmp(self, node, offset):
        self.asm += [
            jmp(f"__{offset + node.dest_offset}__"),
        ]


    def visit_Ret(self, node, offset):
        self.asm += [
            mov(rax, ctypes.cast(node.get_cfunc(),
                                 ctypes.c_void_p).value),
            call(rax),
            mov(rsp, rbp),
            pop(rbp),
            ret(),
        ]


