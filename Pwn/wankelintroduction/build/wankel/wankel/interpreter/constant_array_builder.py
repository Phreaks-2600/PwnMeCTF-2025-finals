from ..objects import jsvalue

class ConstantArrayBuilder:
    def __init__(self):
        self.constants = []

    def get_constant_id(self, constant: jsvalue.TaggedPointer):
        # TODO: Now that `constant` is a TaggedPointer, this does not work
        #       anymore
        if constant in self.constants:
            return self.constants.index(constant)

        self.constants.append(constant)
        return len(self.constants)-1
