import dataclasses

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
    mode_setting: str
    fan_speed_setting: str
    power_setting: str