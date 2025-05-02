import ctypes

from . import ic, feedback
from ..interpreter import bytecode_node
from .. import objects
from .. import globals
from .. import runtime

class SetNamedProperty_FeedbackData(ctypes.Structure):
    _fields_ = (
        ('map', objects.TaggedPointer),
        ('dest_map', objects.TaggedPointer),
        ('prop_index', ctypes.c_uint8),
    )


class SetNamedProperty_IC(ic.IC):
    node_type = bytecode_node.SetNamedProperty

    def save_feedback(self, feedback):
        source_map, dest_map, index = feedback

        self.slot.n_entries += 1

        if self.slot.n_entries >= 5:
            # Megamorphic => Fallback to generic
            return

        feedback_data = globals.BROKER.alloc(SetNamedProperty_FeedbackData)
        feedback_data.map = source_map
        feedback_data.dest_map = dest_map
        feedback_data.prop_index = index

        if self.slot.n_entries == 1:
            self.slot.data = ctypes.addressof(feedback_data)
            return

        if self.slot.n_entries == 2:
            # Alloc array of 4 ptrs
            array = globals.BROKER.alloc(4 * ctypes.c_void_p)
            array[0] = self.slot.data
            self.slot.data = ctypes.addressof(array)

        ctypes.cast(self.slot.data, ctypes.POINTER(ctypes.c_void_p))[
                self.slot.n_entries - 1] = ctypes.addressof(feedback_data)


    def miss(self):
        frame = globals.INTERPRETER_DATA.current_frame[0]

        receiver_ptr = frame.registers[self.node.receiver_register.value]

        if receiver_ptr.is_smi():
            runtime.ThrowException.call(ctypes.c_char_p(
                f'{receiver} has no properties.\n\0'.encode()))


        property_key_ptr = frame.bytecode[0].const_array[self.node.property_name_idx]

        value = globals.INTERPRETER_DATA.accumulator

        receiver = receiver_ptr.value_deref

        value_descriptor = runtime.GetOwnPropertyDescriptor.call(receiver_ptr,
                                                  property_key_ptr)

        if value_descriptor.tagged_value == 1:
            # Map transition

            # First, check if the correct map transition already exists:
            transition_ptr = runtime.GetMapTransitionForValueProperty.call(receiver_ptr,
                                                  property_key_ptr)


            if transition_ptr.tagged_value == 1:
                # Create new map
                new_map = globals.BROKER.alloc(objects.ReceiverMap)
                new_map.map = receiver.map.value_deref.map

                new_map.descriptors_count = receiver.map.value_deref.descriptors_count + 1

                new_descriptor_array = globals.BROKER.alloc(
                        objects.TaggedPointer * new_map.descriptors_count)

                new_map.descriptors = new_descriptor_array

                new_descriptor = globals.BROKER.alloc(objects.PropertyDescriptor)
                new_descriptor.map = globals.BROKER.builtin_maps[objects.PropertyDescriptor]
                new_descriptor.key.tagged_ptr = property_key_ptr
                new_descriptor.writable = True
                new_descriptor.index = len(new_descriptor_array) - 1
                new_descriptor.value.tagged_ptr = objects.TaggedPointer(0)
                new_descriptor.enumerable = True
                new_descriptor.configurable = True
                new_descriptor.is_simple = True

                for i in range(receiver.map.value_deref.descriptors_count):
                    new_map.descriptors[i] = receiver.map.value_deref.descriptors[i]

                new_descriptor_array[-1] = objects.TaggedPointer(
                        ctypes.addressof(new_descriptor))

                new_map.transitions_count = 0
                new_map.transitions.value = 0

                new_transition = globals.BROKER.alloc(objects.TransitionDescriptor)
                # Somehow fixes a mysterious bug...
                new_transition = objects.TransitionDescriptor.from_address(ctypes.addressof(new_transition))
                new_transition.map = globals.BROKER.builtin_maps[objects.TransitionDescriptor]
                new_transition.property = objects.TaggedPointer(
                        ctypes.addressof(new_descriptor))
                new_transition.target_map = objects.TaggedPointer(
                        ctypes.addressof(new_map))

                new_transition_array = globals.BROKER.alloc(
                        objects.TaggedPointer *
                        (receiver.map.value_deref.transitions_count + 1))

                for i in range(receiver.map.value_deref.transitions_count):
                    new_transition_array[i] = receiver.map.value_deref.transitions[i]
                new_transition_array[-1] = objects.TaggedPointer(
                        ctypes.addressof(new_transition))

                receiver.map.value_deref.transitions = new_transition_array
                receiver.map.value_deref.transitions_count += 1

                transition = new_transition

            else:
                transition = transition_ptr.value_deref

            # Transition the map, realloc props and we're good :D
            new_props = globals.BROKER.alloc(objects.JSValue *
                                transition.target_map.value_deref.descriptors_count)

            for i in range(receiver.map.value_deref.descriptors_count):
                new_props[i] = receiver.properties[i]

            source_map = receiver.map
            receiver.map = transition.target_map
            receiver.properties = new_props

            new_props[transition.property.value_deref.index] = value

            self.save_feedback((source_map,
                                transition.target_map,
                                transition.property.value_deref.index))

            return

        descriptor = value_descriptor.value_deref

        # First, check if it is present *in* the object
        inobj = receiver.properties[descriptor.index]
        if inobj.tagged_ptr.tagged_value != 1:
            v = inobj
        else: # Fallback to map's one
            v = descriptor.value

        v = v.value_deref

        if isinstance(v, objects.PropertyAccessor):
            # TODO:
            exceptions.ThrowException.call(ctypes.c_char_p(
                b"Property accessors are not implemented yet\n\0"))

        receiver.properties[descriptor.index] = value

        self.save_feedback((receiver.map,
                            receiver.map,
                            descriptor.index))

        return


    def try_fast(self):
        frame = globals.INTERPRETER_DATA.current_frame[0]
        receiver_ptr = frame.registers[self.node.receiver_register.value]

        if receiver_ptr.is_smi():
            runtime.ThrowException.call(ctypes.c_char_p(
                f'{receiver} has no properties.\n\0'.encode()))

        receiver = receiver_ptr.value_deref

        matching_entry = None

        if self.slot.n_entries == 1:
            data = SetNamedProperty_FeedbackData.from_address(self.slot.data)
            if data.map == receiver_ptr.value_deref.map:
                matching_entry = data
        else:
            datas = ctypes.cast(self.slot.data, ctypes.POINTER(ctypes.c_void_p))
            for i in range(self.slot.n_entries):
                data = SetNamedProperty_FeedbackData.from_address(datas[i])
                if data.map == receiver_ptr.value_deref.map:
                    matching_entry = data
        if matching_entry is None:
            return self.miss()


        receiver.map = matching_entry.dest_map
        receiver.properties[matching_entry.prop_index] = globals.INTERPRETER_DATA.accumulator

