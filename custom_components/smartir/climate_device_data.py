from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

import json
import logging
import os.path
from . import COMPONENT_ABS_DIR, Helper
from homeassistant.const import STATE_OFF

_LOGGER = logging.getLogger(__name__)

@dataclass
class ClimateDeviceState:
    operation_mode: str
    fan_mode: str = None
    target_temperature: float = None

@dataclass
class ClimateDeviceData(ABC):
    manufacturer: str
    supported_models: str
    supported_controller: str
    commands_encoding: str
    min_temperature: float = 16
    max_temperature: float = 30
    precision: float = 1.0
    operation_modes: List[str] = field(default_factory=list)
    fan_modes: List[str] = field(default_factory=list)

    @abstractmethod
    def get_command(self, target_state : ClimateDeviceState, current_state : ClimateDeviceState):
        pass


class FileClimateDeviceData(ClimateDeviceData):
    def __init__(self, device_code):

        self._commands = None

        device_files_subdir = os.path.join('codes', 'climate')
        device_files_absdir = os.path.join(COMPONENT_ABS_DIR, device_files_subdir)

        if not os.path.isdir(device_files_absdir):
            os.makedirs(device_files_absdir)

        device_json_filename = str(device_code) + '.json'
        device_json_path = os.path.join(device_files_absdir, device_json_filename)
        print(device_json_path)
        if not os.path.exists(device_json_path):
            _LOGGER.warning("Couldn't find the device Json file. The component will " \
                            "try to download it from the GitHub repo.")

            try:
                codes_source = ("https://raw.githubusercontent.com/"
                                "smartHomeHub/SmartIR/master/"
                                "codes/climate/{}.json")

                Helper.downloader(codes_source.format(device_code), device_json_path)
            except:
                _LOGGER.error("There was an error while downloading the device Json file. " \
                              "Please check your internet connection or the device code " \
                              "exists on GitHub. If the problem still exists please " \
                              "place the file manually in the proper location.")
                raise
     
        # Read file
        with open(device_json_path) as j:
            try:
                device_data = json.load(j)
            except:
                _LOGGER.error("The device Json file is invalid")
                raise

        super().__init__(manufacturer = device_data['manufacturer'],
              supported_models = device_data['supportedModels'],
              supported_controller = device_data['supportedController'],
              commands_encoding = device_data['commandsEncoding'],
              min_temperature = device_data['minTemperature'],
              max_temperature = device_data['maxTemperature'],
              precision = device_data['precision'],
              operation_modes = [STATE_OFF] + device_data['operationModes'],
              fan_modes = device_data['fanModes'])

        self._commands = device_data['commands']
 
    def get_command(self, target_state : ClimateDeviceState, current_state : ClimateDeviceState):
        if (self._commands == None):
            return None

        operation_mode = target_state.operation_mode
        fan_mode = target_state.fan_mode
        target_temperature = '{0:g}'.format(target_state.target_temperature)

        if operation_mode.lower() == STATE_OFF:
            return self._commands['off']
        else:
            return self._commands[operation_mode][fan_mode][target_temperature]

