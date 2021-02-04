from .climate_device_data import ClimateDeviceState, ClimateDeviceData
from enum import Enum
import ctypes
c_uint64 = ctypes.c_uint64

_electra_time_unit = 1000

class _ElectraMode(Enum):
    cool        = 0b001
    heat        = 0b010
    auto        = 0b011
    dry         = 0b100
    fan_only    = 0b101
    off         = 0b111

class _ElectraFan(Enum):
    low     = 0b00
    mid     = 0b01
    high    = 0b10
    auto    = 0b11

class _ElectraBits(ctypes.LittleEndianStructure):
    _fields_ = [
        ('zeros1',      c_uint64, 1 ),
        ('ones1',       c_uint64, 1 ),
        ('zeros2',      c_uint64, 16 ),
        ('sleep',       c_uint64, 1 ),
        ('temperature', c_uint64, 4 ),
        ('zeros3',      c_uint64, 1 ),
        ('ifeel',       c_uint64, 1 ),
        ('auto_swing',  c_uint64, 1 ),
        ('mini_swing',  c_uint64, 1 ),
        ('zeros4',      c_uint64, 1 ),
        ('fan',         c_uint64, 2 ),
        ('mode',        c_uint64, 3 ),
        ('power',       c_uint64, 1 ),
        ]

class _ElectraCode(ctypes.Union):
    _anonymous_ = ("bits",)
    _fields_ = [
        ("bits", _ElectraBits),
        ("num",  c_uint64),
        ]

class ElectraRC3DeviceData(ClimateDeviceData):
    def __init__(self, device_code):
        super().__init__(
            manufacturer = 'Electra',
            supported_models = 'RC-3',
            supported_controller = 'MQTT',
            commands_encoding = 'Raw',
            min_temperature = 16,
            max_temperature = 30,
            precision = 1,
            operation_modes = ['off', 'auto', 'cool', 'heat', 'fan_only', 'dry'],
            fan_modes = ['auto', 'low', 'mid', 'high'],
            swing_modes = ['off','on'])

    def get_command(self, target_state : ClimateDeviceState, current_state : ClimateDeviceState):
        mark = _electra_time_unit
        space = -1 * _electra_time_unit

        code = _ElectraCode()
        code.num = 0
        code.ones1 = 1
        code.temperature = int(target_state.target_temperature) - 15
        code.fan = _ElectraFan[target_state.fan_mode].value
        code.mode = _ElectraMode[target_state.operation_mode].value

        if target_state.swing_mode == 'on':
            code.auto_swing = 1

        # If changing from off to on, set the power bit so that the AC toggles its power
        if current_state != None and current_state.operation_mode == 'off' and target_state.operation_mode != 'off':
            code.power = 1

        encoded = []

        # Add 3 units mark
        encoded.append(3 * mark)

        # Add 3 units space
        encoded.append(3 * space)

        # Go through the 34 bits of the code, left to right
        for j in range(33, -1, -1):
            bit = (code.num >> j) & 1
            is_last_element_space = encoded[len(encoded) - 1] < 0

            # A one bit translates to one unit low then one unit high (01)
            if bit == 1:
                # Need to add space and mark
                # If last element was space, we need to add time to the last element
                if is_last_element_space:
                    encoded[len(encoded) - 1] += space
                    encoded.append(mark)
                else:
                    encoded.append(space)
                    encoded.append(mark)

            # A zero bit translates to one unit high then one unit low (10)
            else:
                # Need to add mark and space
                # If last element was mark, we need to add time to the last element
                if not is_last_element_space:
                    encoded[len(encoded) - 1] += mark
                    encoded.append(space)
                else:
                    encoded.append(mark)
                    encoded.append(space)

        # Code repeats 3 time followed by 4 units mark
        result = encoded + encoded + encoded + [4 * mark]

        return str(result)
