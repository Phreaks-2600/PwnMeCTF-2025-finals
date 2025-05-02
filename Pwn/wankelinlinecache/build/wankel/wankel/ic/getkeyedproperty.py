import ctypes

from .. import globals
from ..interpreter import bytecode_node
from .. import objects
from . import ic, feedback

from .. import runtime


class GetKeyedProperty_FeedbackData(ctypes.Structure):
    pass

GetKeyedProperty_FeedbackData._fields_ = (
        ('map', objects.TaggedPointer),
        ('key', objects.TaggedPointer),
        ('property_descriptor', objects.TaggedPointer),

        # Null if end of prototype walk
        ('proto_feedback_data', ctypes.POINTER(GetKeyedProperty_FeedbackData)),
    )


class GetKeyedProperty_IC(ic.IC):
    node_type = bytecode_node.GetKeyedProperty

    def save_feedback(self, prototype_walk):
        self.slot.n_entries += 1

        if self.slot.n_entries >= 5:
            # Megamorphic => Fallback to generic
            return

        feedback_data = None
        prev_feedback_data = None

        key = prototype_walk.pop(0)

        while prototype_walk:
            tmp = globals.BROKER.alloc(GetKeyedProperty_FeedbackData)
            tmp.key = key
            tmp.map = prototype_walk.pop(0)
            tmp.property_descriptor = prototype_walk.pop(0)

            if feedback_data is None:
                feedback_data = tmp

            if prev_feedback_data is not None:
                prev_feedback_data.proto_feedback_data = ctypes.pointer(tmp)

            prev_feedback_data = tmp

        prev_feedback_data.proto_feedback_data.value = 0


        if self.slot.n_entries == 1:
            self.slot.data = ctypes.addressof(feedback_data)
        else:
            ctypes.cast(self.slot.data, ctypes.POINTER(GetKeyedProperty_FeedbackData))[
                    self.slot.n_entries - 1] = feedback_data



    def miss(self):
        frame = globals.INTERPRETER_DATA.current_frame[0]
        receiver_ptr = frame.registers[self.node.receiver_register.value]

        if receiver_ptr.is_smi():
            runtime.ThrowException.call(ctypes.c_char_p(
                f'{receiver} has no properties.\n\0'.encode()))

        property_key_ptr = globals.INTERPRETER_DATA.accumulator
        property_key = property_key_ptr.value_deref

        if isinstance(property_key, int) or \
                isinstance(property_key, objects.HeapNumber) and property_key.value.is_integer():
            if isinstance(property_key, objects.HeapNumber):
                property_key = int(property_key.value)
            x = runtime.LoadElement.call(receiver_ptr, ctypes.c_uint32(property_key))
            globals.INTERPRETER_DATA.accumulator = x
            return

        value_descriptor = None

        prototype_walk = [objects.TaggedPointer(property_key_ptr.raw_value), receiver_ptr.value_deref.map]

        while value_descriptor is None or value_descriptor.tagged_value == 1:
            value_descriptor = runtime.GetOwnPropertyDescriptor.call(receiver_ptr,
                                                      property_key_ptr)
            if value_descriptor.tagged_value == 1:
                proto_descriptor = runtime.GetOwnPropertyDescriptor.call(
                        receiver_ptr, globals.BROKER.proto_string)
                if proto_descriptor.tagged_value == 1:
                    globals.INTERPRETER_DATA.accumulator.tagged_ptr = \
                            globals.BROKER.undefined_oddball

                    return

                prototype_walk.append(proto_descriptor)

                # Get prototype value and use it as the new receiver
                receiver_ptr = runtime.GetValueFromPropertyDescriptor.call(
                        receiver_ptr, proto_descriptor)

                prototype_walk.append(receiver_ptr.value_deref.map)

        prototype_walk.append(value_descriptor)

        x = runtime.GetValueFromPropertyDescriptor.call(
                receiver_ptr, value_descriptor)

        globals.INTERPRETER_DATA.accumulator = x

        self.save_feedback(prototype_walk)
        return


    def try_fast(self):
        frame = globals.INTERPRETER_DATA.current_frame[0]
        receiver_ptr = frame.registers[self.node.receiver_register.value]

        if receiver_ptr.is_smi():
            runtime.ThrowException.call(ctypes.c_char_p(
                f'{receiver} has no properties.\n\0'.encode()))


        property_key_ptr = globals.INTERPRETER_DATA.accumulator
        property_key = property_key_ptr.value_deref

        if isinstance(property_key, int) or \
                isinstance(property_key, objects.HeapNumber) and property_key.value.is_integer():
            if isinstance(property_key, objects.HeapNumber):
                property_key = int(property_key.value)
            x = runtime.LoadElement.call(receiver_ptr, ctypes.c_uint32(property_key))
            globals.INTERPRETER_DATA.accumulator = x
            return

        matching_entry = None

        if self.slot.n_entries == 1:
            data = GetKeyedProperty_FeedbackData.from_address(self.slot.data)
            if data.map == receiver_ptr.value_deref.map and \
                    data.key.value_deref == property_key:
                matching_entry = data
        else:
            datas = ctypes.cast(self.slot.data, ctypes.POINTER(GetKeyedProperty_FeedbackData))
            for i in range(self.slot.n_entries):
                data = datas[i]
                if data.map == receiver_ptr.value_deref.map and \
                    data.key.value_deref == property_key:
                    matching_entry = data
        if matching_entry is None:
            return self.miss()

        while matching_entry:
            if matching_entry.map != receiver_ptr.value_deref.map:
                return slow()

            receiver_ptr = runtime.GetValueFromPropertyDescriptor.call(
                        receiver_ptr, matching_entry.property_descriptor)

            matching_entry = matching_entry.proto_feedback_data
            if matching_entry:
                matching_entry = matching_entry[0]


        globals.INTERPRETER_DATA.accumulator = receiver_ptr

