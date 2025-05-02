import ctypes

from . import feedback

class ICMeta(type):
    node_type_to_ic = {}
    def __new__(cls, name, bases, attrs):
        new_cls = super().__new__(cls, name, bases, attrs)

        if 'node_type' in attrs:
            cls.node_type_to_ic[new_cls.node_type] = new_cls

        return new_cls

class IC(metaclass=ICMeta):
    ic_handlers = {}        # Get handler from PC value

    def __init__(self, node, slot):
        self.node = node
        self.slot = slot

        self.ic_handlers[ctypes.addressof(node)] = ctypes.CFUNCTYPE(None)(
                lambda: self.entry())


    # TODO: Rewrite this in asm and support asm implementation for `miss`,
    #       `try_fast` and `slow` methods.
    def entry(self):
        if self.slot.n_entries == 0:     # No feedback
            # Try to compute feedback for next time
            return self.miss()

        if self.slot.n_entries <= 5:     # Monomorphic / Polymorphic
            # Try to use existing feedback
            return self.try_fast()

        return self.slow()                  # Megamorphic => Fallback to generic


    def slow(self):
        globals.INTERPRETER.get_bytecode_handler(ctypes.addressof(self.node))()
