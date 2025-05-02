# Make sure globals.broker is initialized
from .. import broker

from .. import globals
from . import bytecode_meta
from . import interpreter_structs
from ..objects import bytecode_array, jsvalue, jsobject
from ..factory import Factory

from .. import asm

import mmap
import ctypes

class Interpreter:
    def __init__(self):

        self.interpreter_heap_size = 0x10000
        self.interpreter_heap = mmap.mmap(-1, self.interpreter_heap_size)
        self.interpreter_heap_base: ctypes.c_void_p = ctypes.cast(
                ctypes.POINTER(ctypes.c_uint32)(
                    ctypes.c_uint32.from_buffer(self.interpreter_heap)
                ), ctypes.c_void_p)

        self.interpreter_data = interpreter_structs.InterpreterData.from_buffer(self.interpreter_heap)

        self.interpreter_data.last_alloc_offset = \
                ctypes.sizeof(self.interpreter_data)

        self.interpreter_data.accumulator.tagged_ptr = globals.BROKER.undefined_oddball
        self.interpreter_data.current_frame = None

        self.bytecode_handlers = {}
        self.bytecode_sizes = {}

    def compute_bytecode_handler_and_size(self, pc_value):
        bytecode_id = ctypes.c_uint8.from_address(pc_value).value
        bytecode_node_cls = bytecode_meta.BytecodeMeta.get_bytecode(bytecode_id)
        node = bytecode_node_cls.from_address(pc_value)

        self.bytecode_handlers[pc_value] = node.get_cfunc()
        self.bytecode_sizes[pc_value] = ctypes.sizeof(node)

    def get_bytecode_handler(self, pc_value):
        if pc_value not in self.bytecode_handlers:
            self.compute_bytecode_handler_and_size(pc_value)
        return self.bytecode_handlers[pc_value]

    def get_bytecode_size(self, pc_value):
        if pc_value not in self.bytecode_handlers:
            self.compute_bytecode_handler_and_size(pc_value)
        return self.bytecode_sizes[pc_value]

    def run(self):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        while ctypes.cast(globals.INTERPRETER_DATA.current_frame,
                          ctypes.c_void_p).value == ctypes.addressof(frame):
            pc_value = frame.pc.as_int

            self.get_bytecode_handler(pc_value)()

            if frame.pc.as_int == pc_value:
                # Avoid interfering with Jmps
                frame.pc.as_int += self.get_bytecode_size(pc_value)


    def alloc_frame(self, bc_arr: ctypes.POINTER(bytecode_array.BytecodeArray)):
        off = self.interpreter_data.last_alloc_offset
        regs_off = off + ctypes.sizeof(interpreter_structs.Frame)

        if regs_off + ctypes.sizeof(jsvalue.JSValue) * bc_arr[0].n_regs >= self.interpreter_heap_size:
            print("OOM")
            asm.mkfunction([asm.int3()])()

        frame = interpreter_structs.Frame.from_buffer(self.interpreter_heap, off)
        frame.previous = self.interpreter_data.current_frame
        self.interpreter_data.current_frame = ctypes.pointer(frame)

        frame.bytecode = bc_arr

        regs = (jsvalue.JSValue * bc_arr[0].n_regs).from_buffer(
                self.interpreter_heap, regs_off)
        frame.registers = regs

        self.interpreter_data.last_alloc_offset = regs_off + ctypes.sizeof(regs)

        frame.this.tagged_pointer = globals.BROKER.undefined_oddball

        frame.pc.as_ptr = bc_arr[0].bytecode_array


globals.INTERPRETER = Interpreter()
globals.INTERPRETER_DATA = globals.INTERPRETER.interpreter_data
globals.INTERPRETER_DATA_PTR = globals.INTERPRETER.interpreter_heap_base.value

