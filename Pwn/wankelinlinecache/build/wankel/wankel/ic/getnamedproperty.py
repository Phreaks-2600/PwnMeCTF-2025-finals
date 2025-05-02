import ctypes

from .. import globals
from ..interpreter import bytecode_node
from .. import objects
from . import ic, feedback

from .. import runtime


class GetNamedProperty_FeedbackData(ctypes.Structure):
    pass

GetNamedProperty_FeedbackData._fields_ = (
        ('map', objects.TaggedPointer),
        ('property_descriptor', objects.TaggedPointer),

        # Null if end of prototype walk
        ('proto_feedback_data', ctypes.POINTER(GetNamedProperty_FeedbackData)),
    )


class GetNamedProperty_IC(ic.IC):
    node_type = bytecode_node.GetNamedProperty

    def save_feedback(self, prototype_walk):
        self.slot.n_entries += 1

        if self.slot.n_entries >= 5:
            # Megamorphic => Fallback to generic
            return

        feedback_data = None
        prev_feedback_data = None

        while prototype_walk:
            tmp = globals.BROKER.alloc(GetNamedProperty_FeedbackData)
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
            return

        if self.slot.n_entries == 2:
            # Alloc array of 4 ptrs
            array = globals.BROKER.alloc(4 * GetNamedProperty_FeedbackData)
            array[0] = ctypes.cast(self.slot.data, ctypes.POINTER(GetNamedProperty_FeedbackData))[0]
            self.slot.data = ctypes.addressof(array)

        ctypes.cast(self.slot.data, ctypes.POINTER(GetNamedProperty_FeedbackData))[
                self.slot.n_entries - 1] = feedback_data



    def miss(self):
        frame = globals.INTERPRETER_DATA.current_frame[0]
        receiver_ptr = frame.registers[self.node.receiver_register.value]

        if receiver_ptr.is_smi():
            runtime.ThrowException.call(ctypes.c_char_p(
                f'{receiver} has no properties.\n\0'.encode()))

        property_key_ptr = frame.bytecode[0].const_array[self.node.property_name_idx]

        value_descriptor = None

        prototype_walk = [receiver_ptr.value_deref.map]

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


        matching_entry = None

        if self.slot.n_entries == 1:
            data = GetNamedProperty_FeedbackData.from_address(self.slot.data)
            if data.map == receiver_ptr.value_deref.map:
                matching_entry = data
        else:
            datas = ctypes.cast(self.slot.data, ctypes.POINTER(GetNamedProperty_FeedbackData))
            for i in range(self.slot.n_entries):
                data = datas[i]
                if data.map == receiver_ptr.value_deref.map:
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

