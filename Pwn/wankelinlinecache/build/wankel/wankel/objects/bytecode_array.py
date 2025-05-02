import ctypes

from . import base, jsvalue
from ..interpreter import bytecode_meta

from ..ic import feedback


class BytecodeArray(ctypes.Structure):
    _fields_ = (
        ('bytecode_size', ctypes.c_uint16),
        ('bytecode_array', ctypes.POINTER(ctypes.c_uint8)),
        ('n_consts', ctypes.c_uint8),
        ('const_array', ctypes.POINTER(jsvalue.JSValue)),
        ('n_regs', ctypes.c_uint8),
        ('n_fb_slots', ctypes.c_uint8),
        ('feedback_vector', ctypes.POINTER(feedback.FeedbackSlot)),
    )

    def __repr__(self):
        ret = "Bytecode Array"  "\n" \
              "=============="  "\n" \
              ""                "\n"

        ptr = ctypes.cast(self.bytecode_array, ctypes.c_void_p).value
        offset = 0

        while offset < self.bytecode_size:
            bytecode_id = self.bytecode_array[offset]
            bytecode_node_cls = bytecode_meta.BytecodeMeta.get_bytecode(bytecode_id)
            node = bytecode_node_cls.from_address(ptr + offset)
            ret += f"{ptr + offset:#18x}  -  {bytes(node).hex(' '):16s}  - {node}\n"
            offset += ctypes.sizeof(node)

        ret += ""               "\n" \
               "Constant Array:""\n"
        ret += "\n".join(
        f"{i}: {str(base.AbstractObjectMeta.from_tagged_pointer(self.const_array[i].value))}" \
                           for i in range(self.n_consts))

        return ret

