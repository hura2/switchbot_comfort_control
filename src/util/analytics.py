from typing import Optional, Tuple
import datetime
from common.data_types import AirconSetting, TemperatureHumidity
import common.constants as constants
from util.supabase_client import SupabaseClient
from util.time import TimeUtil

# 温度情報をデータベースに挿入
def insert_temperature(location_id: int, temperature: float, created_at: datetime):
    """
    温度情報をデータベースに挿入します。

    Args:
        location_id (int): 温度情報の位置ID。
        temperature (float): 温度情報。
        created_at (datetime): 温度情報の作成日時。

    Returns:
        APIResponse: 挿入結果の情報が含まれる。
    """
    result = (
        SupabaseClient.get_supabase()
        .from_("temperatures")
        .insert([{"location_id": location_id, "temperature": temperature, "created_at": created_at.isoformat()}])
        .execute()
    )
    return result


# 湿度情報をデータベースに挿入
def insert_humidity(location_id: int, humidity: float, created_at: datetime):
    """
    湿度情報をデータベースに挿入します。

    Args:
        location_id (int): 湿度情報の位置ID。
        humidity (float): 湿度情報。
        created_at (datetime): 湿度情報の作成日時。

    Returns:
        APIResponse: 挿入結果の情報が含まれる。
    """
    result = (
        SupabaseClient.get_supabase()
        .from_("humidities")
        .insert([{"location_id": location_id, "humidity": humidity, "created_at": created_at.isoformat()}])
        .execute()
    )
    return result


# 表面温度情報をデータベースに挿入
def insert_surface_temperature(wall_temp: float, ceiling_temp: float, floor_temp: float):
    """
    表面温度情報をデータベースに挿入します。

    Args:
        wall_temp (float): 壁の表面温度情報。
        ceiling_temp (float): 天井の表面温度情報。
        floor_temp (float): 床の表面温度情報。

    Returns:
        APIResponse: 挿入結果の情報が含まれる。
    """
    result = (
        SupabaseClient.get_supabase()
        .from_("surface_temperatures")
        .insert(
            [{"wall": wall_temp, "ceiling": ceiling_temp, "floor": floor_temp, "created_at": TimeUtil.get_current_time().isoformat()}]
        )
        .execute()
    )
    return result


# PMV情報をデータベースに挿入
def insert_pmv(pmv: float, met: float, clo: float, air: float):
    """
    PMV情報をデータベースに挿入します。

    Args:
        pmv (float): PMV値。
        met (float): MET値。
        clo (float): CLO値。
        air (float): 空気速度値。

    Returns:
        APIResponse: 挿入結果の情報が含まれる。
    """
    result = (
        SupabaseClient.get_supabase()
        .from_("pmvs")
        .insert([{"pmv": pmv, "met": met, "clo": clo, "air": air, "created_at": TimeUtil.get_current_time().isoformat()}])
        .execute()
    )
    return result


# エアコン設定情報をデータベースに挿入
def insert_aircon_setting(aircon_setting: AirconSetting, current_time: Optional[datetime.datetime] = None):
    """
    エアコン設定をデータベースに挿入します。

    Args:
        aircon_setting (AirconSetting): エアコンの設定情報。

    Returns:
        APIResponse: 挿入結果の情報が含まれる。
    """
    supabase = SupabaseClient.get_supabase()
    #current_timeの設定がNoneの場合は現在の日時を設定
    if current_time is None:
        current_time = TimeUtil.get_current_time().isoformat()
    
    data = {
        "temperature": aircon_setting.temp_setting,
        "mode": aircon_setting.mode_setting.id,
        "fan_speed": aircon_setting.fan_speed_setting.id,
        "power": aircon_setting.power_setting.id,
        "created_at": current_time,
    }
    
    return supabase.from_("aircon_settings").insert([data]).execute()


# 最新のエアコン設定情報を取得
def get_latest_aircon_setting() -> Tuple[AirconSetting, datetime.datetime]:
    """
    最新のエアコン設定情報を取得します。

    Returns:
        Tuple[AirconSetting, datetime.datetime]: 最新のエアコン設定情報と作成日時のタプル。
    """
    data = (
        SupabaseClient.get_supabase()
        .table("aircon_settings")
        .select("*")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    latest_setting = data.data[0]
    aircon_setting = AirconSetting(
        temp_setting=str(latest_setting["temperature"]),
        mode_setting=constants.AirconMode.get_by_id(latest_setting["mode"]),
        fan_speed_setting=constants.AirconFanSpeed.get_by_id(str((latest_setting["fan_speed"]))),
        power_setting=constants.AirconPower.get_by_id(latest_setting["power"]),
    )
    created_at = latest_setting["created_at"]
    return aircon_setting, created_at


def insert_temperature_humidity(
    ceiling: TemperatureHumidity,
    floor: TemperatureHumidity,
    outdoor: TemperatureHumidity
):
    """
    天井、床、外部の温度と湿度データをデータベースに挿入します。

    Args:
        ceiling (TemperatureHumidity): 天井の温度と湿度データ
        floor (TemperatureHumidity): 床の温度と湿度データ
        outdoor (TemperatureHumidity): 外部の温度と湿度データ
    """
    now = TimeUtil.get_current_time()
    insert_temperature(constants.Location.FLOOR.id, floor.temperature, now)
    insert_temperature(constants.Location.CEILING.id, ceiling.temperature, now)
    insert_temperature(constants.Location.OUTDOOR.id, outdoor.temperature, now)
    insert_humidity(constants.Location.FLOOR.id, floor.humidity, now)
    insert_humidity(constants.Location.CEILING.id, ceiling.humidity, now)
    insert_humidity(constants.Location.OUTDOOR.id, outdoor.humidity, now)


# サーキュレーター設定情報をデータベースに挿入
def insert_circulator_setting(fan_speed: str, power: str):
    """
    サーキュレーターの風速と電源設定をデータベースに挿入します。

    Args:
        fan_speed (str): サーキュレーターの風速設定
        power (str): サーキュレーターの電源設定

    Returns:
        APIResponse: 挿入結果の情報が含まれる。
    """
    result = (
        SupabaseClient.get_supabase()
        .from_("circulator_settings")
        .insert([{"fan_speed": fan_speed, "power": power, "created_at": TimeUtil.get_current_time().isoformat()}])
        .execute()
    )
    return result


# 最新のサーキュレーター設定情報を取得
def get_latest_circulator_setting() -> Tuple[str, str]:
    """
    最新のサーキュレーターの風速と電源設定を取得します。

    Returns:
        Tuple[str, str]: 最新の風速設定と電源設定
    """
    data = (
        SupabaseClient.get_supabase()
        .table("circulator_settings")
        .select("power, fan_speed")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return data.data[0]["power"], data.data[0]["fan_speed"]
