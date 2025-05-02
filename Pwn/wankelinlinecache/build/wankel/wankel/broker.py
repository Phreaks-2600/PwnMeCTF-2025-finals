import ctypes
import mmap
from time import sleep

from typing import Any

from .objects import base as base_obj
from . import objects

from . import globals
from .ic import feedback


class Broker:
    def __init__(self):
        self.heap_size = 0x1000000
        self.heap = mmap.mmap(-1, self.heap_size)
        self.heap_base: ctypes.c_void_p = ctypes.cast(
                ctypes.POINTER(ctypes.c_uint32)(
                    ctypes.c_uint32.from_buffer(self.heap)
                ), ctypes.c_void_p)
        self.last_heap_alloc_offset = ctypes.c_uint64.from_buffer(self.heap, 0)
        self.last_heap_alloc_offset.value = 8

        self.builtin_maps: dict[Any, objects.TaggedPointer] = {}
        self.builtin_maps_reverse: dict[objects.TaggedPointer] = {}
        self.map_map_to_orig_type: dict[objects.TaggedPointer, objects.TaggedPointer] = {}

        self.builtins_primitives: dict[str, ctypes.pointer] = {}

    def init(self):
        self.init_builtin_maps()

        self.alloc_builtins_primitives()

        self.proto_string = self.alloc_literal('__proto__', 'String')




    def alloc_builtins_primitives(self):
        undefined = self.alloc(objects.JSUndefined)
        undefined.map = self.builtin_maps[objects.JSUndefined]
        undefined_ptr = ctypes.pointer(undefined)
        self.builtins_primitives['undefined'] = objects.TaggedPointer(
                ctypes.cast(undefined_ptr, ctypes.c_void_p).value)

        null = self.alloc(objects.JSNull)
        null.map = self.builtin_maps[objects.JSNull]
        null_ptr = ctypes.pointer(null)
        self.builtins_primitives['null'] = objects.TaggedPointer(
                ctypes.cast(null_ptr, ctypes.c_void_p).value)

        nan = self.alloc(objects.HeapNumber)
        nan.map.value = self.builtin_maps[objects.HeapNumber]
        nan.value = float('nan')
        nan_ptr = ctypes.pointer(nan)
        self.builtins_primitives['nan'] = objects.TaggedPointer(
                ctypes.cast(nan_ptr, ctypes.c_void_p).value)

        true = self.alloc(objects.Boolean)
        true.value = True
        true.map = self.builtin_maps[objects.Boolean]
        true_ptr = ctypes.pointer(true)
        self.builtins_primitives['true'] = objects.TaggedPointer(
                ctypes.cast(true_ptr, ctypes.c_void_p).value)

        false = self.alloc(objects.Boolean)
        false.value = False
        false.map = self.builtin_maps[objects.Boolean]
        false_ptr = ctypes.pointer(false)
        self.builtins_primitives['false'] = objects.TaggedPointer(
                ctypes.cast(false_ptr, ctypes.c_void_p).value)


    @property
    def undefined_oddball(self):
        return self.builtins_primitives['undefined']

    @property
    def null_oddball(self):
        return self.builtins_primitives['null']

    @property
    def nan_number(self):
        return self.builtins_primitives['nan']

    @property
    def true_oddball(self):
        return self.builtins_primitives['true']

    @property
    def false_oddball(self):
        return self.builtins_primitives['false']


    def init_builtin_maps(self):
        map_p = ctypes.POINTER(objects.Map)

        for obj_t in base_obj.AbstractObjectMeta.get_object_types():
            if issubclass(obj_t, objects.JSObject):
                m = self.alloc(objects.ReceiverMap)
                m.descriptors_count = 0
                m.descriptors.value = 0
                m.transitions_count = 0
                m.transitions.value = 0
            else:
                m = self.alloc(objects.Map)

            ptr = objects.TaggedPointer(ctypes.cast(map_p(m), ctypes.c_void_p).value)
            self.builtin_maps[obj_t] = ptr
            self.builtin_maps_reverse[ptr] = obj_t

            m2 = self.alloc(objects.Map)
            ptr2 = objects.TaggedPointer(ctypes.addressof(m2))
            m.map = ptr2

            if issubclass(obj_t, objects.JSObject):
                self.builtin_maps_reverse[ptr2] = objects.ReceiverMap
            else:
                self.builtin_maps_reverse[ptr2] = objects.Map

            self.map_map_to_orig_type[ptr2] = obj_t


        base_obj.AbstractObjectMeta.builtin_maps = self.builtin_maps
        base_obj.AbstractObjectMeta.builtin_maps_reverse = self.builtin_maps_reverse
        base_obj.AbstractObjectMeta.map_map_to_orig_type = self.map_map_to_orig_type


    def alloc_literal(self, value, literal_type):
        # TODO: Rename this function as it is used for other things than just
        #       literals
        assert literal_type in ['Null', 'String', 'Boolean', 'Number'] # We don't
                                                  # allocate anything for SMIs

        match literal_type:
            case 'String':
                assert isinstance(value, str)
                value = value.encode()
                length = len(value)
                value_field = self.alloc(ctypes.c_char * (length + 1))
                for i, x in enumerate(value):
                    value_field[i] = x
                value_field[-1] = 0
                ret = self.alloc(objects.JSString)
                ret.map = self.builtin_maps[objects.JSString]
                ret.length = length
                ret.value = ctypes.cast(value_field, ctypes.c_char_p)
                ret_ptr = ctypes.pointer(ret)
                return objects.TaggedPointer(
                        ctypes.cast(ret_ptr, ctypes.c_void_p).value)
            case 'Boolean':
                assert isinstance(value, bool)
                return self.true_oddball if value else self.false_oddball
            case 'Number':
                ret = self.alloc(objects.HeapNumber)
                ret.map = self.builtin_maps[objects.HeapNumber]
                ret.value = value
                ret_ptr = ctypes.pointer(ret)
                return objects.TaggedPointer(
                        ctypes.cast(ret_ptr, ctypes.c_void_p).value)
            case 'Null':
                return self.null_oddball


    def alloc_bytecode_array(self, bc_arr: 'bytecode_array.BytecodeArray'):
        # Compute length
        length = 0
        for bc in bc_arr._bytecode_array:
            length += ctypes.sizeof(bc)

        # Alloc
        array = self.alloc(ctypes.c_uint8 * length)

        # Write to memory
        offset = 0
        for bc in bc_arr._bytecode_array:
            for i, data in enumerate(bytes(bc)):
                array[offset + i] = data

            offset += ctypes.sizeof(bc)

        bc_arr_alloc = self.alloc(objects.BytecodeArray)
        bc_arr_alloc.bytecode_size = length
        bc_arr_alloc.bytecode_array = array

        n_consts = len(bc_arr.constant_array.constants)
        const_array = self.alloc(objects.JSValue * n_consts)

        for i, const in enumerate(bc_arr.constant_array.constants):
            const_array[i].tagged_ptr = const

        bc_arr_alloc.n_consts = n_consts
        bc_arr_alloc.const_array = const_array

        bc_arr_alloc.n_regs = bc_arr.n_regs

        bc_arr_alloc.n_fb_slots = bc_arr.n_fb_slots

        feedback_vector = self.alloc(feedback.FeedbackSlot * bc_arr.n_fb_slots)

        for slot in feedback_vector:
            slot.n_entries = 0

        bc_arr_alloc.feedback_vector = feedback_vector

        return bc_arr_alloc



    def alloc(self, obj_type) -> ctypes.Structure:
        new_offset = self.last_heap_alloc_offset.value + (ctypes.sizeof(obj_type) + 8) & (~7)

        if new_offset > self.heap_size:
            print("OOM: Maybe implementing a real GC would be a good idea :(")
            return None

        obj = obj_type.from_buffer(self.heap, self.last_heap_alloc_offset.value)
        self.last_heap_alloc_offset.value = new_offset
        return obj

    def gc(self):
        # Running our "stop the world" gc algorithm can take some times ... :D
        sleep(1)


globals.BROKER = Broker()
globals.BROKER.init()
