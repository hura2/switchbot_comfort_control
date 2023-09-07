from enum import Enum


class AirconMode(Enum):
    """
    エアコンの動作モードを表すEnumクラス。
    """

    AUTO = ("1", "自動モード")  # 自動モード: エアコンが自動的に動作モードを選択します
    COOLING = ("2", "冷房モード")  # 冷房モード: エアコンが冷房モードで動作します
    DRY = ("3", "除湿モード")  # 除湿モード: エアコンが除湿モードで動作します
    FAN = ("4", "送風モード")  # 送風モード: エアコンが送風モードで動作します
    HEATING = ("5", "暖房モード")  # 暖房モード: エアコンが暖房モードで動作します
    POWERFUL_COOLING = ("101", "パワフル冷房")  # パワフル冷房: 強力な冷房モード
    POWERFUL_HEATING = ("102", "パワフル暖房")  # パワフル暖房: 強力な暖房モード

    def __init__(self, id, description):
        self.id = id
        self.description = description

    @classmethod
    def get_description(cls, id):
        """
        指定されたIDに対応する動作モードの説明を取得します。

        Args:
            id (str): 動作モードのID。

        Returns:
            str: 動作モードの説明。
        """
        return next((mode.description for mode in cls if mode.id == id), None)

    @classmethod
    def get_by_id(cls, id):
        """
        指定されたIDに対応する AirconMode の要素を取得します。

        Args:
            id (str): 動作モードのID。

        Returns:
            AirconMode: 対応する AirconMode の要素。見つからない場合は None。
        """
        for mode in cls:
            if mode.id == id:
                return mode
        return None

class AirconFanSpeed(Enum):
    """
    エアコンの風速を表すEnumクラス。
    """

    AUTO = ("1", "自動")  # 自動: エアコンが風速を自動で調整します
    LOW = ("2", "弱")  # 弱: 低い風速
    MEDIUM = ("3", "中")  # 中: 中程度の風速
    HIGH = ("4", "強")  # 強: 高い風速

    def __init__(self, id, description):
        self.id = id
        self.description = description

    @classmethod
    def get_description(cls, id):
        """
        指定されたIDに対応する風速の説明を取得します。

        Args:
            id (str): 風速のID。

        Returns:
            str: 風速の説明。
        """
        return next((speed.description for speed in cls if speed.id == id), None)

    @classmethod
    def get_by_id(cls, id):
        """
        指定されたIDに対応する AirconFanSpeed の要素を取得します。

        Args:
            id (str): 動作モードのID。

        Returns:
            AirconFanSpeed: 対応する AirconFanSpeed の要素。見つからない場合は None。
        """
        for mode in cls:
            if mode.id == id:
                return mode
        return None
    

class AirconPower(Enum):
    """
    エアコンの電源状態を表すEnumクラス。
    """

    ON = ("on", "ON")  # ON: 電源がオンの状態
    OFF = ("off", "OFF")  # OFF: 電源がオフの状態

    def __init__(self, id, description):
        self.id = id
        self.description = description

    @classmethod
    def get_description(cls, id):
        """
        指定されたIDに対応する電源状態の説明を取得します。

        Args:
            id (str): 電源状態のID。

        Returns:
            str: 電源状態の説明。
        """
        return next((state.description for state in cls if state.id == id), None)

    @classmethod
    def get_by_id(cls, id):
        """
        指定されたIDに対応する AirconPower の要素を取得します。

        Args:
            id (str): 動作モードのID。

        Returns:
            AirconPower: 対応する AirconPower の要素。見つからない場合は None。
        """
        for mode in cls:
            if mode.id == id:
                return mode
        return None

class CirculatorFanSpeed(Enum):
    """
    サーキュレーターの風速を表すEnumクラス。
    """

    UP = "風力プラス"  # 風力プラス: 風速を増加させる
    DOWN = "風力マイナス"  # 風力マイナス: 風速を減少させる


class CirculatorPower(Enum):
    """
    サーキュレーターの電源状態を表すEnumクラス。
    """

    ON = ("電源", "on")  # ON: 電源がオンの状態
    OFF = ("電源", "off")  # OFF: 電源がオフの状態

    def __init__(self, id, description):
        self.id = id
        self.description = description

    @classmethod
    def get_description(cls, id):
        """
        指定されたIDに対応する電源状態の説明を取得します。

        Args:
            id (str): 電源状態のID。

        Returns:
            str: 電源状態の説明。
        """
        return next((state.description for state in cls if state.id == id), None)


class Location(Enum):
    """
    温度・湿度の計測場所を表すEnumクラス。
    """

    FLOOR = (1, "床")  # 床: 床近くの場所で温度と湿度を計測
    CEILING = (2, "天井")  # 天井: 天井近くの場所で温度と湿度を計測
    OUTDOOR = (3, "外")  # 外: 屋外の場所で温度と湿度を計測

    def __init__(self, id, description):
        self.id = id
        self.description = description

    @classmethod
    def get_description(cls, id):
        """
        指定されたIDに対応する場所の説明を取得します。

        Args:
            id (int): 場所のID。

        Returns:
            str: 場所の説明。
        """
        return next((location.description for location in cls if location.id == id), None)
