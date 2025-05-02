import ctypes

from . import base
from .. import globals
from .. import objects
from . import exceptions


class GetOwnPropertyDescriptor(base.RuntimeOp):
    _restype_ = objects.TaggedPointer
    _argtypes_ = (objects.TaggedPointer, objects.JSValue)

    @staticmethod
    def __python_impl__(receiver_ptr: int, property_key_ptr: int):
        receiver_ptr = objects.TaggedPointer(receiver_ptr)
        property_key_ptr = objects.TaggedPointer(property_key_ptr)

        frame = globals.INTERPRETER_DATA.current_frame[0]

        receiver = receiver_ptr.value_deref
        receiver_map = receiver.map.value_deref

        if not isinstance(receiver_map, objects.ReceiverMap):
            exceptions.ThrowException.call(ctypes.c_char_p(
                f'TypeError: {receiver} has no properties\n\0'.encode()))

        for i in range(receiver_map.descriptors_count):
            descriptor = receiver_map.descriptors[i]
            if descriptor.value_deref.key.value_deref == property_key_ptr.value_deref:
                return descriptor.tagged_value

        return objects.TaggedPointer(0).tagged_value


class GetValueFromPropertyDescriptor(base.RuntimeOp):
    _restype_  = objects.JSValue
    _argtypes_ = (objects.TaggedPointer, objects.TaggedPointer)

    @staticmethod
    def __python_impl__(receiver_ptr: int, property_descriptor: int):
        receiver_ptr = objects.TaggedPointer(receiver_ptr)
        property_descriptor = objects.TaggedPointer(property_descriptor)

        receiver = receiver_ptr.value_deref
        descriptor = property_descriptor.value_deref

        value = None

        # First, check if it is present *in* the object
        inobj = receiver.properties[descriptor.index]

        if inobj.tagged_ptr.tagged_value != 1:
            value = inobj
        else: # Fallback to map's one
            value = descriptor.value

        v = value.value_deref

        if isinstance(v, objects.PropertyAccessor):
            # TODO:
            exceptions.ThrowException.call(ctypes.c_char_p(
                b"Property accessors are not implemented yet\n\0"))

        return value.raw_value


class LoadProperty(base.RuntimeOp):
    _restype_ = objects.JSValue
    _argtypes_ = (objects.TaggedPointer, objects.TaggedPointer)

    @staticmethod
    def __python_impl__(receiver_ptr: int, property_key_ptr: int):
        receiver_ptr = objects.TaggedPointer(receiver_ptr)
        property_key_ptr = objects.TaggedPointer(property_key_ptr)

        value_descriptor = None

        proto_key_ptr = globals.BROKER.proto_string

        while value_descriptor is None or value_descriptor.tagged_value == 1:
            value_descriptor = GetOwnPropertyDescriptor.call(receiver_ptr,
                                                      property_key_ptr)
            if value_descriptor.tagged_value == 1:
                proto_descriptor = GetOwnPropertyDescriptor.call(
                        receiver_ptr, proto_key_ptr)
                if proto_descriptor.tagged_value == 1:
                    return globals.BROKER.undefined_oddball.tagged_value

                # Get prototype value and use it as the new receiver
                receiver_ptr = GetValueFromPropertyDescriptor.call(
                        receiver_ptr, proto_descriptor)


        x = GetValueFromPropertyDescriptor.call(
                receiver_ptr, value_descriptor)
        return x.raw_value


class GetMapTransitionForValueProperty(base.RuntimeOp):
    _restype_ = objects.TaggedPointer
    _argtypes_ = (objects.TaggedPointer, objects.JSValue)

    @staticmethod
    def __python_impl__(receiver_ptr: int, property_key_ptr: int):
        receiver_ptr = objects.TaggedPointer(receiver_ptr)
        property_key_ptr = objects.TaggedPointer(property_key_ptr)

        frame = globals.INTERPRETER_DATA.current_frame[0]

        receiver = receiver_ptr.value_deref
        receiver_map = receiver.map.value_deref

        if not isinstance(receiver_map, objects.ReceiverMap):
            exceptions.ThrowException.call(ctypes.c_char_p(
                f'TypeError: {receiver} has no properties\n\0'.encode()))

        for i in range(receiver_map.transitions_count):
            transition = receiver_map.transitions[i]
            if transition.value_deref.property.value_deref.key.value_deref == property_key_ptr.value_deref:
                return transition.tagged_value

        return objects.TaggedPointer(0).tagged_value


class StoreProperty(base.RuntimeOp):
    _restype_ = None
    _argtypes_ = (objects.TaggedPointer, objects.TaggedPointer, objects.JSValue)

    @staticmethod
    def __python_impl__(receiver_ptr: int, property_key_ptr: int, value: int):
        receiver_ptr = objects.TaggedPointer(receiver_ptr)
        property_key_ptr = objects.TaggedPointer(property_key_ptr)
        value = objects.JSValue(value)

        receiver = receiver_ptr.value_deref

        value_descriptor = GetOwnPropertyDescriptor.call(receiver_ptr,
                                                  property_key_ptr)

        if value_descriptor.tagged_value == 1:
            # Map transition

            # First, check if the correct map transition already exists:
            transition_ptr = GetMapTransitionForValueProperty.call(receiver_ptr,
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

            receiver.map = transition.target_map
            receiver.properties = new_props

            new_props[transition.property.value_deref.index] = value
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

        return


class LoadPropertyOrElement(base.RuntimeOp):
    _restype_ = objects.JSValue
    _argtypes_ = (objects.TaggedPointer, objects.JSValue)

    @staticmethod
    def __python_impl__(receiver_ptr: int, property_key_ptr: int):
        receiver_ptr = objects.TaggedPointer(receiver_ptr)
        property_key_ptr = objects.JSValue(property_key_ptr)
        property_key = property_key_ptr.value_deref

        if isinstance(property_key, int) or \
                isinstance(property_key, objects.HeapNumber) and property_key.value.is_integer():
            if isinstance(property_key, objects.HeapNumber):
                property_key = int(property_key.value)
            x = LoadElement.call(receiver_ptr, ctypes.c_uint32(property_key))

        else:
            x = LoadProperty.call(receiver_ptr, property_key_ptr)
        return x.raw_value


class LoadElement(base.RuntimeOp):
    _restype_ = objects.JSValue
    _argtypes_ = (objects.TaggedPointer, ctypes.c_uint32)

    @staticmethod
    def __python_impl__(receiver_ptr: int, index: int):
        receiver_ptr = objects.TaggedPointer(receiver_ptr)
        receiver = receiver_ptr.value_deref
        receiver_map = receiver.map.value_deref

        # TODO: Implement this correctly:
        #           - Holes
        #           - Prototype chain
        #           - Use property descriptors (for read only / accessors / etc.)

        if not isinstance(receiver_map, objects.ReceiverMap):
            exceptions.ThrowException.call(ctypes.c_char_p(
                f'TypeError: {receiver} has no properties\n\0'.encode()))

        if index < 0 or index >= receiver.elements_count:
            return globals.BROKER.undefined_oddball.tagged_value

        elements = receiver.elements
        if receiver.elements_kind == 1:
            elements = ctypes.cast(elements, ctypes.POINTER(ctypes.c_double))

        val = elements[index]

        if receiver.elements_kind == 1:
            return globals.BROKER.alloc_literal(val, 'Number').tagged_value

        return val.raw_value



class StorePropertyOrElement(base.RuntimeOp):
    _restype_ = None
    _argtypes_ = (objects.TaggedPointer, objects.JSValue, objects.JSValue)

    @staticmethod
    def __python_impl__(receiver_ptr: int, property_key_ptr: int, value: int):
        receiver_ptr = objects.TaggedPointer(receiver_ptr)
        property_key_ptr = objects.JSValue(property_key_ptr)
        value = objects.JSValue(value)

        property_key = property_key_ptr.value_deref

        if isinstance(property_key, int) or \
                isinstance(property_key, objects.HeapNumber) and property_key.value.is_integer():
            if isinstance(property_key, objects.HeapNumber):
                property_key = int(property_key.value)
            StoreElement.call(receiver_ptr, ctypes.c_uint32(property_key), value)

        else:
            StoreProperty.call(receiver_ptr, property_key_ptr, value)


class StoreElement(base.RuntimeOp):
    _restype_ = None
    _argtypes_ = (objects.TaggedPointer, ctypes.c_uint32, objects.JSValue)

    @staticmethod
    def __python_impl__(receiver_ptr: int, index: int, value: int):
        receiver_ptr = objects.TaggedPointer(receiver_ptr)
        receiver = receiver_ptr.value_deref
        receiver_map = receiver.map.value_deref

        value = objects.JSValue(value)

        if not isinstance(receiver_map, objects.ReceiverMap):
            exceptions.ThrowException.call(ctypes.c_char_p(
                f'TypeError: {receiver} has no properties\n\0'.encode()))

        value_kind = 0 if value.is_smi() else 1 if isinstance(
                value.value_deref, objects.HeapNumber) else 2

        current_kind = receiver.elements_kind
        create_holes = index > receiver.elements_count
        new_kind = 2 if create_holes else max(value_kind, current_kind)
        new_count = max(index + 1, receiver.elements_count)

        needs_realloc = current_kind < new_kind and (
                current_kind != 0 or value_kind != 2
            ) or index >= receiver.elements_count

        elements = receiver.elements
        if current_kind == 1:
            elements = ctypes.cast(elements, ctypes.POINTER(ctypes.c_double))

        if needs_realloc:
            new_elements = globals.BROKER.alloc(
                    (ctypes.c_double if new_kind == 1 else objects.JSValue) *
                    new_count
                )

            for i in range(receiver.elements_count):
                elmt = elements[i]
                if current_kind == 0 and new_kind == 1:
                    elmt = float(elmt.value_deref)
                    new_elements[i] = elmt
                elif current_kind == 1 and new_kind == 2:
                    elmt = globals.BROKER.alloc_literal(elmt, 'Number')
                    new_elements[i].tagged_ptr = elmt
                else:
                    new_elements[i] = elmt


            for i in range(receiver.elements_count, new_count):
                if i != index:
                    new_elements[i].tagged_ptr = globals.BROKER.undefined_oddball


            receiver.elements = ctypes.cast(new_elements, ctypes.POINTER(objects.JSValue))
            elements = new_elements

        receiver.elements_kind = new_kind
        receiver.elements_count = new_count

        if new_kind == 1:
            elements[index] = float(value.value_deref if value.is_smi() \
                    else value.value_deref.value)
        else:
            elements[index] = value

