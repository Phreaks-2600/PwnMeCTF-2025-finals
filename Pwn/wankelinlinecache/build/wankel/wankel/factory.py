import ctypes

from . import objects
from . import globals

class Factory:
    @staticmethod
    def create_map_for_js_object():
        map = globals.BROKER.alloc(objects.ReceiverMap)
        map.descriptors_count = 0
        map.descriptors.value = 0
        map.transitions_count = 0
        map.transitions.value = 0

        jsobject_map = globals.BROKER.builtin_maps[objects.JSObject]
        map.map = jsobject_map.value_deref.map
        return map


    @staticmethod
    def create_property_descriptor(key: str, index: int, value: objects.JSValue):
        descriptor = globals.BROKER.alloc(objects.PropertyDescriptor)
        descriptor.map = globals.BROKER.builtin_maps[objects.PropertyDescriptor]

        descriptor.key.tagged_ptr = globals.BROKER.alloc_literal(key, 'String')
        descriptor.writable = True
        descriptor.index = index
        descriptor.value = value
        descriptor.enumerable = True
        descriptor.configurable = True
        assert not isinstance(value, objects.PropertyAccessor)
        descriptor.is_simple = True # We don't use accessors for now

        return descriptor

    @staticmethod
    def create_js_builtin_function(entry, arity, name):
        function = globals.BROKER.alloc(objects.JSFunction)
        function.map = globals.BROKER.builtin_maps[objects.JSFunction]

        function.entry = ctypes.cast(entry, type(function.entry))
        function.name = name
        function.arity = arity
        function.exec_type = -1         # Builtin => never compile

        value = objects.JSValue()
        value.tagged_ptr = objects.TaggedPointer(ctypes.addressof(function))

        return value


    @staticmethod
    def create_js_object(properties: dict[str, objects.JSValue]):
        # TODO: Support keys that are not strings

        n = len(properties)
        if properties:
            map = Factory.create_map_for_js_object()
            map.transitions_count = 0
            map.transitions.value = 0

            descriptors = globals.BROKER.alloc(objects.TaggedPointer * n)

            i = 0
            for prop, value in properties.items():
                descriptor = Factory.create_property_descriptor(prop, i, value)
                descriptors[i] = objects.TaggedPointer(
                        ctypes.addressof(descriptor))
                i += 1

            map.descriptors_count = n
            map.descriptors = descriptors

            map = objects.TaggedPointer(ctypes.addressof(map))
        else:
            map = globals.BROKER.builtin_maps[objects.JSObject]

        obj = globals.BROKER.alloc(objects.JSObject)
        obj.map = map
        obj.properties = globals.BROKER.alloc(objects.JSValue * n) if n else \
                ctypes.cast(0, ctypes.POINTER(objects.JSValue))
        for i in range(n):
            obj.properties[i].tagged_ptr = objects.TaggedPointer(0)

        obj.elements_count = 0
        obj.elements_kind = 0
        obj.elements = ctypes.cast(0, ctypes.POINTER(objects.JSValue))

        return obj

