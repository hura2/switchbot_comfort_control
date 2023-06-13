from enum import Enum

class AirconMode(Enum):
    AUTO = ("1", "自動モード")
    COOLING = ("2", "冷房モード")
    DRY = ("3", "除湿モード")
    FAN = ("4", "送風モード")
    HEATING = ("5", "暖房モード")
    POWERFUL_COOLING = ("101", "パワフル冷房")
    POWERFUL_HEATING = ("102", "パワフル暖房")

    def __init__(self, id, description):
        self.id = id
        self.description = description

    @classmethod
    def get_description(cls, id):
        return next((mode.description for mode in cls if mode.id == id), None)


class AirconFanSpeed(Enum):
    AUTO = ("1", "自動")
    LOW = ("2", "弱")
    MEDIUM = ("3", "中")
    HIGH = ("4", "強")

    def __init__(self, id, description):
        self.id = id
        self.description = description

    @classmethod
    def get_description(cls, id):
        return next((speed.description for speed in cls if speed.id == id), None)


class AirconPower(Enum):
    ON = ("on", "ON")
    OFF = ("off", "OFF")

    def __init__(self, id, description):
        self.id = id
        self.description = description

    @classmethod
    def get_description(cls, id):
        return next((state.description for state in cls if state.id == id), None)


class CirculatorFanSpeed(Enum):
    UP = "風力プラス"
    DOWN = "風力マイナス"
    
class CirculatorPower(Enum):
    ON = ("電源", "on")
    OFF = ("電源", "off")

    def __init__(self, id, description):
        self.id = id
        self.description = description

    @classmethod
    def get_description(cls, id):
        return next((state.description for state in cls if state.id == id), None)
