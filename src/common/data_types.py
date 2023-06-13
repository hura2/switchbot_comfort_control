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