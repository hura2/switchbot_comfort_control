import dataclasses
from typing import Optional

# 定数を管理するファイル
import common.constants as constants


@dataclasses.dataclass
class PMVCalculation:
    """
    PMV（Predicted Mean Vote）計算結果を表すデータクラス。

    Attributes:
        pmv (float): PMV値（快適度指数）。
        ppd (float): PPD値（不快指数）。
        clo (float): 衣服の断熱性。
        air (float): 空気の速度。
        met (float): MET値（代謝当量）。
        wall (float): 壁表面温度。
        ceiling (float): 天井表面温度。
        floor (float): 床表面温度。
        mean_radiant_temperature (float): 平均放射温度。
        dry_bulb_temperature (float): 乾球温度。
        relative_air_speed (float): 相対風速。
        dynamic_clothing_insulation (float): 動的な衣服の断熱性。
    """

    pmv: float
    ppd: float
    clo: float
    air: float
    met: float
    wall: float
    ceiling: float
    floor: float
    mean_radiant_temperature: float
    dry_bulb_temperature: float
    relative_air_speed: float
    dynamic_clothing_insulation: float


@dataclasses.dataclass
class AirconSetting:
    """
    エアコンの設定を表すデータクラス。

    Attributes:
        temp_setting (str): 温度設定。
        mode_setting (constants.AirconMode): 動作モード設定（エアコンモード）。
        fan_speed_setting (constants.AirconFanSpeed): 風速設定。
        power_setting (constants.AirconPower): 電源設定。
        force_fan_below_dew_point (Optional[bool]): 露点温度を下回った場合に強制的に送風にするかどうかの設定。
    """

    temp_setting: str
    mode_setting: constants.AirconMode
    fan_speed_setting: constants.AirconFanSpeed
    power_setting: constants.AirconPower
    force_fan_below_dew_point: Optional[bool] = False  # デフォルトはFalse

    def __eq__(self, other):
        """
        他のAirconSettingオブジェクトと比較して、等しいかどうかを判定するメソッド。

        Args:
            other: 比較対象のオブジェクト。

        Returns:
            bool: オブジェクトが等しい場合はTrue、そうでない場合はFalse。
        """
        if isinstance(other, AirconSetting):
            return (
                self.temp_setting == other.temp_setting
                and self.mode_setting == other.mode_setting
                and self.fan_speed_setting == other.fan_speed_setting
                and self.power_setting == other.power_setting
            )
        return False


@dataclasses.dataclass
class TemperatureHumidity:
    """
    温度と湿度のデータを表すデータクラス。

    Attributes:
        temperature (float): 温度値。
        humidity (float): 湿度値。
    """

    temperature: float
    humidity: float


@dataclasses.dataclass
class CO2SensorData:
    """
    CO2センサーのデータを表すデータクラス。

    Attributes:
        temperature_humidity (TemperatureHumidity): 温度と湿度のデータ。
        co2 (int): CO2濃度値。
    """
    temperature_humidity: TemperatureHumidity
    co2: int