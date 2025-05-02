import ctypes

class FeedbackSlot(ctypes.Structure):
    _fields_ = (
        ('n_entries', ctypes.c_uint8),  # 0    ==> No feedback
                                        # 1    ==> Monomorphic
                                        # 2->4 ==> Polymorphic
                                        # 5->. ==> Megamorphic
        ('data', ctypes.c_void_p),  # Handlers use this the way they want :)
    )
