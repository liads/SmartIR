from .ir_generator import IrGenerator
from .climate_device_data import ClimateDeviceState, ClimateDeviceData
from enum import Enum
import ctypes
c_uint64 = ctypes.c_uint64

class _Jt03Bits(ctypes.LittleEndianStructure):
    _fields_ = [
        # Byte 0
        ('timer_duration',  c_uint64, 5 ),
        ('timer_switch',    c_uint64, 3 ),
        # Byte 1
        ('lamp',            c_uint64, 1 ),
        ('na1',             c_uint64, 1 ),
        ('hold',            c_uint64, 1 ),
        ('turbo',           c_uint64, 1 ),
        ('na2',             c_uint64, 4 ),
        # Byte 2
        ('command',         c_uint64, 4 ),
        ('na3',             c_uint64, 4 ),
        # Byte 3
        ('sleep',           c_uint64, 1 ),
        ('power',           c_uint64, 1 ),
        ('swing',           c_uint64, 2 ),
        ('airflow',         c_uint64, 1 ),
        ('fan',             c_uint64, 2 ),
        ('na4',             c_uint64, 1 ),
        # Byte 4
        ('temperature',     c_uint64, 4 ),
        ('na5',             c_uint64, 1 ),
        ('mode',            c_uint64, 3 ),
        # Byte 5
        ('end_frame',       c_uint64, 8 ),
        ]
        
class _Jt03Code(ctypes.Union):
    _anonymous_ = ("bits",)
    _fields_ = [
        ("bits", _Jt03Bits),
        ("num",  c_uint64),
        ]

class _Jt03Mode(Enum):
    auto        = 0x00
    cool        = 0x01
    dry         = 0x02
    fan_only    = 0x03
    heat        = 0x04

class _Jt03Cmd(Enum):
    onOff       = 0x00
    mode        = 0x01
    tempUp      = 0x02
    tempDown    = 0x03
    swing       = 0x04
    fan         = 0x05
    timer       = 0x06
    airFlow     = 0x07
    hold        = 0x08
    sleep       = 0x09
    turbo       = 0x0A
    lamp        = 0x0B

class _Jt03Fan(Enum):
    auto        = 0x00
    high        = 0x01
    mid         = 0x02
    low         = 0x03

class _Jt03Swing(Enum):
    fast        = 0x00
    slow        = 0x01
    off         = 0x12

class _Jt03AirFlow(Enum):
    inverter    = 0x0
    continous   = 0x1

class _Jt03Timer(Enum):
    ignore      = 0x00
    on          = 0x01
    off         = 0x05

class _Jt03Power(Enum):
    off         = 0x00
    on          = 0x01

_jt03_tick = 620
_jt03_bit_mark = _jt03_tick
_jt03_one_space = -1 * _jt03_tick
_jt03_zero_space = -1 * _jt03_tick * 3
_jt03_header_mark = _jt03_tick * 11
_jt03_header_space = -1 * _jt03_tick * 11
_jt03_bits = 48

class ZhJt03DeviceData(ClimateDeviceData):
    def __init__(self, device_code):
        super().__init__(
            manufacturer = 'Chigo',
            supported_models = 'ZH-JT-03',
            supported_controller = 'MQTT',
            commands_encoding = 'Raw',
            min_temperature = 16,
            max_temperature = 32,
            precision = 1,
            operation_modes = ['off', 'auto', 'cool', 'heat', 'fan_only', 'dry'],
            fan_modes = ['auto', 'low', 'mid', 'high'],
            swing_modes = ['off', 'fast', 'slow'])

    def get_command(self, target_state : ClimateDeviceState, current_state : ClimateDeviceState):
        code = _Jt03Code()
        code.num = 0
        code.end_frame = 0xD5
        code.temperature = int(target_state.target_temperature) - self.min_temperature

        if target_state.fan_mode is not None:
            code.fan = _Jt03Fan[target_state.fan_mode].value

        if target_state.swing_mode is not None:
            code.swing = _Jt03Swing[target_state.swing_mode].value
        
        if target_state.operation_mode is None or target_state.operation_mode == 'off':
            code.power = _Jt03Power.off.value
        else:
            code.power = _Jt03Power.on.value
            code.mode = _Jt03Mode[target_state.operation_mode].value

        encoded = []

        # Header
        encoded.append(_jt03_header_mark)
        encoded.append(_jt03_header_space)

        # Go through the bytes of the code, encoding each byte and then its bitwise inversion
        for i in range(0, _jt03_bits, 8):
            chunk: c_uint64 = (code.num >> i) & 0xFF
            encoded.extend(IrGenerator.gen_raw_ir_data(_jt03_bit_mark, _jt03_one_space, _jt03_bit_mark, _jt03_zero_space, chunk, 8, False))
            encoded.extend(IrGenerator.gen_raw_ir_data(_jt03_bit_mark, _jt03_one_space, _jt03_bit_mark, _jt03_zero_space, ~chunk, 8, False))

        encoded.append(_jt03_bit_mark)
        encoded.append(_jt03_header_space)
        encoded.append(_jt03_bit_mark)

        return str(encoded)
