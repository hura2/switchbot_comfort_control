import dataclasses
# 定数を管理するファイル
import common.constants as constants

@dataclasses.dataclass
class PMVResult:
    pmv: float
    clo: float
    air: float
    met: float
    wall: float
    ceiling: float
    floor: float

@dataclasses.dataclass
class AirconSetting:
    temp_setting: str
    mode_setting: constants.AirconMode
    fan_speed_setting: constants.AirconFanSpeed
    power_setting: constants.AirconPower

    def __eq__(self, other):
        if isinstance(other, AirconSetting):
            return (
                self.temp_setting == other.temp_setting and
                self.mode_setting == other.mode_setting and
                self.fan_speed_setting == other.fan_speed_setting and
                self.power_setting == other.power_setting
            )
        return False