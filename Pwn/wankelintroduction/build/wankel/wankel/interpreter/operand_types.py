import ctypes

class RegisterOperand(ctypes.c_uint8):
    def __repr__(self):
        return f"r{self.value}"

class FeedbackOperand(ctypes.c_uint8):
    def __repr__(self):
        return f"[{self.value}]"


