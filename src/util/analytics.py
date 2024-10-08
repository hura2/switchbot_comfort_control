from typing import Optional, Tuple
import datetime
from api.jma_forecast import WeatherData
from common.data_types import AirconSetting, TemperatureHumidity
import common.constants as constants
from util.aircon_intensity_calculator import AirconIntensityCalculator
from util.supabase_client import SupabaseClient
from util.time import TimeUtil
from collections import defaultdict


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
            [
                {
                    "wall": wall_temp,
                    "ceiling": ceiling_temp,
                    "floor": floor_temp,
                    "created_at": TimeUtil.get_current_time().isoformat(),
                }
            ]
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
        .insert(
            [{"pmv": pmv, "met": met, "clo": clo, "air": air, "created_at": TimeUtil.get_current_time().isoformat()}]
        )
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
    # current_timeの設定がNoneの場合は現在の日時を設定
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


def insert_temperature_humidity(ceiling: TemperatureHumidity, floor: TemperatureHumidity, outdoor: TemperatureHumidity):
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


# 日毎の最高気温をデータベースに挿入
def insert_max_temperature(max_temperature: float):
    """
    日毎の最高気温をデータベースに挿入します。

    Args:
        recorded_date (str): 温度が記録された日付（YYYY-MM-DD形式）
        max_temperature (float): 最高気温（摂氏度）

    Returns:
        APIResponse: 挿入結果の情報が含まれる。
    """
    result = (
        SupabaseClient.get_supabase()
        .from_("daily_max_temperatures")
        .insert(
            [
                {
                    "recorded_date": TimeUtil.get_current_time().date().isoformat(),
                    "max_temperature": max_temperature,
                    "created_at": TimeUtil.get_current_time().isoformat(),
                }
            ]
        )
        .execute()
    )
    return result


# 指定した日付の最高気温を取得
def get_max_temperature_by_date(recorded_date: str) -> Optional[Tuple[str, float]]:
    """
    指定した日付の最高気温を取得します。

    Args:
        recorded_date (str): 温度を取得したい日付（YYYY-MM-DD形式）

    Returns:
        Optional[Tuple[str, float]]: 記録日付と最高気温。データがない場合は None。
    """
    data = (
        SupabaseClient.get_supabase()
        .table("daily_max_temperatures")
        .select("recorded_date, max_temperature")
        .eq("recorded_date", recorded_date)
        .execute()
    )

    if data.data:
        return data.data[0]["recorded_date"], data.data[0]["max_temperature"]
    return None


def get_or_insert_max_temperature() -> float:
    """
    現在の日付の最高気温を取得し、存在しない場合は新たに挿入します。

    Returns:
        float: 最高気温の値
    """
    # 現在の日付を取得
    recorded_date = TimeUtil.get_current_time().date().isoformat()

    # 現在の日付の最高気温を取得
    result = get_max_temperature_by_date(recorded_date)

    # 取得できなかった場合は挿入
    if result is None:
        max_temperature = WeatherData.get_max_temperature_by_date(recorded_date)
        insert_max_temperature(max_temperature)
        return max_temperature

    # 取得できた場合は、その値を返す
    return result[1]  # 最高気温の値を返す

# 指定した日付のエアコン設定の強度を取得
def get_daily_aircon_intensity(date: str) -> int:
    """
    指定した日付のエアコン設定の強度を計算します。

    Args:
        date (str): YYYY-MM-DD形式の日付。

    Returns:
        int: 指定日付の強度スコア。
    """
    data = (
        SupabaseClient.get_supabase()
        .table("aircon_settings")
        .select("*")
        .filter("created_at", "gte", f"{date} 00:00:00")
        .filter("created_at", "lt", f"{date} 23:59:59")
        .execute()
    )

    intensity_by_mode = defaultdict(float)  # 各モードの強度スコアを格納
    last_setting = None

    # 最初の設定の持続時間を計算するためのフラグ
    first_setting_time = None

    # タイムゾーンの定義（日本時間の例）
    JST = TimeUtil.timezone()

    for setting in data.data:
        aircon_setting = AirconSetting(
            temp_setting=str(setting["temperature"]),
            mode_setting=constants.AirconMode.get_by_id(setting["mode"]),
            fan_speed_setting=constants.AirconFanSpeed.get_by_id(str(setting["fan_speed"])),
            power_setting=constants.AirconPower.get_by_id(setting["power"]),
        )
        
        created_at_str = setting["created_at"]
        created_at_str = created_at_str.split('.')[0] + created_at_str[-6:]  # 秒以下の部分を切り捨て
        current_time = datetime.datetime.fromisoformat(created_at_str)

        # 最初の設定の場合、持続時間を計算
        if first_setting_time is None:
            first_setting_time = current_time

        if last_setting is not None:
            # 前の設定の持続時間を計算
            time_difference = (current_time - last_setting["created_at"]).total_seconds()
            intensity_score = AirconIntensityCalculator.calculate_intensity(
                temperature=float(last_setting["temperature"]),
                mode=last_setting["mode"],
                fan_speed=last_setting["fan_speed"],
                power=last_setting["power"],
            )
            intensity_by_mode[last_setting["mode"]] += intensity_score * time_difference

        # 新しい設定を記録
        last_setting = {
            "mode": aircon_setting.mode_setting.id,
            "created_at": current_time,
            "temperature": aircon_setting.temp_setting,
            "fan_speed": aircon_setting.fan_speed_setting.id,
            "power": aircon_setting.power_setting.id,
        }

    # 最初の設定の持続時間を計算
    if first_setting_time is not None:
        start_of_day = datetime.datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST)
        time_difference = (first_setting_time - start_of_day).total_seconds()
        intensity_score = AirconIntensityCalculator.calculate_intensity(
            temperature=float(last_setting["temperature"]),
            mode=last_setting["mode"],
            fan_speed=last_setting["fan_speed"],
            power=last_setting["power"],
        )
        intensity_by_mode[last_setting["mode"]] += intensity_score * time_difference

    # 最後の設定の持続時間を計算
    if last_setting is not None:
        end_of_day = datetime.datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST)
        time_difference = (end_of_day - last_setting["created_at"]).total_seconds()
        intensity_score = AirconIntensityCalculator.calculate_intensity(
            temperature=float(last_setting["temperature"]),
            mode=last_setting["mode"],
            fan_speed=last_setting["fan_speed"],
            power=last_setting["power"],
        )
        intensity_by_mode[last_setting["mode"]] += intensity_score * time_difference

    # 全てのモードの強度スコアを合計
    total_intensity = sum(intensity_by_mode.values())

    return total_intensity

def _save_intensity_score(date: str, score: int) -> None:
    """
    指定した日付とスコアをDBに保存します。

    Args:
        date (str): YYYY-MM-DD形式の日付。
        score (int): エアコン設定の強度スコア。
    """
    SupabaseClient.get_supabase().table("aircon_intensity_scores").insert(
        {"record_date": date, "intensity_score": score}
    ).execute()


def register_yesterday_intensity_score() -> None:
    """
    昨日のエアコン強度スコアを計算し、DBに保存します。
    """
    yesterday = (TimeUtil.get_current_time() - datetime.timedelta(days=1)).date()
    date_str = yesterday.strftime("%Y-%m-%d")

    # 昨日のスコアをDBで確認
    existing_score = (
        SupabaseClient.get_supabase()
        .table("aircon_intensity_scores")
        .select("*")
        .filter("record_date", "eq", date_str)
        .execute()
    )

    # スコアが既に登録されている場合、計算をスキップ
    if existing_score.data:
        print(f"{date_str} のスコアは既に登録されています。")
        return

    # 昨日のスコアを取得
    intensity_score = get_daily_aircon_intensity(date_str)

    # スコアをDBに保存
    _save_intensity_score(date_str, intensity_score)

    # エアコンの強度スコアを取得する関数


def get_aircon_intensity_scores(today: datetime.date) -> Tuple[int, int, int, int]:
    """
    先々週、先週、昨日、今日のエアコンの強度スコアを取得します。

    Args:
        today (datetime.date): 今日の日付。

    Returns:
        Tuple[int, int, int, int]: 先々週、先週、昨日、今日のスコア。
    """

    # 今日の日付を基に他の日付を計算
    yesterday = today - datetime.timedelta(days=1)
    last_week = today - datetime.timedelta(weeks=1)
    two_weeks_ago = today - datetime.timedelta(weeks=2)

    # スコアを格納するための変数
    last_two_weeks_score = 0
    last_week_score = 0
    yesterday_score = 0

    # 先々週のスコアをDBから取得
    two_weeks_ago_score = (
        SupabaseClient.get_supabase()
        .table("aircon_intensity_scores")
        .select("intensity_score")
        .filter("record_date", "eq", str(two_weeks_ago))
        .execute()
    )

    if two_weeks_ago_score.data:
        last_two_weeks_score = two_weeks_ago_score.data[0]["intensity_score"]

    # 先週のスコアをDBから取得
    last_week_data = (
        SupabaseClient.get_supabase()
        .table("aircon_intensity_scores")
        .select("intensity_score")
        .filter("record_date", "eq", str(last_week))
        .execute()
    )

    if last_week_data.data:
        last_week_score = last_week_data.data[0]["intensity_score"]

    # 昨日のスコアをDBから取得
    yesterday_data = (
        SupabaseClient.get_supabase()
        .table("aircon_intensity_scores")
        .select("intensity_score")
        .filter("record_date", "eq", str(yesterday))
        .execute()
    )

    if yesterday_data.data:
        yesterday_score = yesterday_data.data[0]["intensity_score"]

    # 今日のスコアを計算
    today_score = get_daily_aircon_intensity(today.strftime("%Y-%m-%d"))

    return last_two_weeks_score, last_week_score, yesterday_score, today_score


def register_last_month_intensity_scores() -> None:
    """
    過去1ヶ月の各日付のエアコン強度スコアを計算し、DBに保存します。
    """
    current_date = TimeUtil.get_current_time().date()
    start_date = current_date - datetime.timedelta(days=30)

    for i in range(30):
        target_date = start_date + datetime.timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")

        # 指定日付のスコアをDBで確認
        existing_score = (
            SupabaseClient.get_supabase()
            .table("aircon_intensity_scores")
            .select("*")
            .filter("record_date", "eq", date_str)
            .execute()
        )

        # スコアが既に登録されている場合、計算をスキップ
        if existing_score.data:
            print(f"{date_str} のスコアは既に登録されています。")
            continue

        # aircon_settingsから指定日付のデータを取得
        intensity_score = get_daily_aircon_intensity(date_str)

        # スコアをDBに保存
        _save_intensity_score(date_str, intensity_score)
        print(f"{date_str} のスコア {intensity_score} を登録しました。")
