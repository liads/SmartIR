from ctypes import c_uint64

class IrGenerator():
    @staticmethod
    def gen_raw_ir_data(one_mark: int, one_space: int, zero_mark: int, zero_space: int, data: c_uint64, nbits: int, is_msb_first: bool):
        if (nbits == 0):
            return

        if (is_msb_first):
            bit_range = range(nbits - 1, -1, -1)
        else:
            bit_range = range(0, nbits, 1)

        for i in bit_range:
            bit = (data >> i) & 1
            if (bit == 1):
                yield one_mark
                yield one_space
            else:
                yield zero_mark
                yield zero_space
