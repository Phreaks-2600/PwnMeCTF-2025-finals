from . import base


class JSUndefined(base.AbstractObject):
    def __repr__(self):
        return "undefined"

class JSNull(base.AbstractObject):
    def __repr__(self):
        return "null"

