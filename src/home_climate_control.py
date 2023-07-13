# 必要なライブラリをインポートします
import common.constants as constants
import common.data_types as data_types
from common.logger import logger
import os
import datetime
import pytz
from collections import namedtuple
import util.analytics as analytics
import util.heat_comfort_calculator as heat_comfort_calculator
from dotenv import load_dotenv
from supabase import create_client, Client
import api.switchbot_api as switchbot_api

# 環境変数を読み込みます
load_dotenv(".env")

# 必要な環境変数を設定します
PROJECT_URL = os.environ["SUPABASE_PROJECT_URL"]
API_KEY = os.environ["SUPABASE_API_KEY"]


def adjust_fan_speed(current_fan_speed, target_fan_speed):
    adjusted_fan_speed = current_fan_speed
    while adjusted_fan_speed != target_fan_speed:
        if target_fan_speed > adjusted_fan_speed:
            switchbot_api.increase_air_volume()
            adjusted_fan_speed += 1
        else:
            switchbot_api.decrease_air_volume()
            adjusted_fan_speed -= 1
    return adjusted_fan_speed

def set_circulator(current_power, current_fan_speed, target_fan_speed):
    power = current_power
    if target_fan_speed == 0:
        if current_power == constants.CirculatorPower.ON.description:
            adjust_fan_speed(current_fan_speed, target_fan_speed)
            switchbot_api.power_on_off()
            power = constants.CirculatorPower.OFF.description
    else:
        if current_power == constants.CirculatorPower.OFF.description:
            switchbot_api.power_on_off()
            power = constants.CirculatorPower.ON.description
        adjust_fan_speed(current_fan_speed, target_fan_speed)
    
    return power


# エアコンの動作を設定する関数
def set_aircon(
    pmv: int,
    outdoor_temperature: float,
    absolute_humidity: float,
    humidity: float
):
    # Define aircon settings
    setting = data_types.AirconSetting("","","","")

    if pmv <= -3:
        # pmvが-3以下の場合の処理
        setting.temp_setting = "25"
        setting.mode_setting = constants.AirconMode.POWERFUL_HEATING
        setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
        setting.power_setting = constants.AirconPower.ON
    elif pmv <= -2.5:
        # pmvが-2.5以下の場合の処理
        setting.temp_setting = "25"
        setting.mode_setting = constants.AirconMode.POWERFUL_HEATING
        setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
        setting.power_setting = constants.AirconPower.ON
    elif pmv <= -2:
        # pmvが-2以下の場合の処理
        setting.temp_setting = "25"
        setting.mode_setting = constants.AirconMode.HEATING
        setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
        setting.power_setting = constants.AirconPower.ON
    elif pmv <= -1.5:
        # pmvが-1.5以下の場合の処理
        setting.temp_setting = "25"
        setting.mode_setting = constants.AirconMode.HEATING
        setting.fan_speed_setting = constants.AirconFanSpeed.MEDIUM
        setting.power_setting = constants.AirconPower.ON
    elif pmv <= -1:
        # pmvが-1以下の場合の処理
        setting.temp_setting = "25"
        setting.mode_setting = constants.AirconMode.HEATING
        setting.fan_speed_setting = constants.AirconFanSpeed.LOW
        setting.power_setting = constants.AirconPower.ON
    elif pmv <= -0.3:
        # pmvが-0.3以下の場合の処理
        if outdoor_temperature >= 25:
            setting.temp_setting = "25"
            setting.mode_setting = constants.AirconMode.FAN
            setting.fan_speed_setting = constants.AirconFanSpeed.LOW
            setting.power_setting = constants.AirconPower.ON
        else:
            setting.temp_setting = "25"
            setting.mode_setting = constants.AirconMode.HEATING
            setting.fan_speed_setting = constants.AirconFanSpeed.LOW
            setting.power_setting = constants.AirconPower.ON

    elif pmv <= 0:
        # pmvが0以下の場合の処理
        setting.temp_setting = "25"
        setting.mode_setting = constants.AirconMode.FAN
        setting.fan_speed_setting = constants.AirconFanSpeed.LOW
        setting.power_setting = constants.AirconPower.ON
    elif pmv <= 0.3:
        # pmvが0.5以下の場合の処理
        setting.temp_setting = "25"
        setting.mode_setting = constants.AirconMode.FAN
        setting.fan_speed_setting = constants.AirconFanSpeed.LOW
        setting.power_setting = constants.AirconPower.ON
    elif pmv <= 0.4:
        # pmvが1以下の場合の処理
        setting.temp_setting = "26"
        setting.mode_setting = constants.AirconMode.COOLING
        setting.fan_speed_setting = constants.AirconFanSpeed.LOW
        setting.power_setting = constants.AirconPower.ON
    elif pmv <= 0.45:
        # pmvが1.5以下の場合の処理
        setting.temp_setting = "23"
        setting.mode_setting = constants.AirconMode.COOLING
        setting.fan_speed_setting = constants.AirconFanSpeed.MEDIUM
        setting.power_setting = constants.AirconPower.ON
    elif pmv <= 0.5:
        # pmvが2以下の場合の処理
        setting.temp_setting = "23"
        setting.mode_setting = constants.AirconMode.COOLING
        setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
        setting.power_setting = constants.AirconPower.ON
    elif pmv <= 2.5:
        # pmvが2.5以下の場合の処理
        setting.temp_setting = "22"
        setting.mode_setting = constants.AirconMode.POWERFUL_COOLING
        setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
        setting.power_setting = constants.AirconPower.ON
    else:
        # pmvが3以上の場合の処理
        setting.temp_setting = "22"
        setting.mode_setting = constants.AirconMode.POWERFUL_COOLING
        setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
        setting.power_setting = constants.AirconPower.ON

    if setting.mode_setting == constants.AirconMode.FAN:
        if absolute_humidity > 12 or humidity > 55:
            # now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
            # #電気代が安い時間のみ
            # if now.hour < 8 or now.hour >= 18:
            setting.temp_setting = "27"
            setting.mode_setting = constants.AirconMode.DRY
            setting.fan_speed_setting = constants.AirconFanSpeed.LOW
            setting.power_setting = constants.AirconPower.ON
        
    # switchbot_api.aircon(setting.temp_setting, setting.mode_setting, setting.fan_speed_setting, setting.power_setting)

    return setting

def set_fan_speed_based_on_temperature_diff(outdoor_temperature: float, temperature_diff: float, current_power: str, current_fan_speed: str):
    """温度差に基づいて風量を設定する

    温度差が特定の閾値を超える場合、対応する風量に設定する。
    以下の閾値を参照：
    - 温度差が3.0以上：風量4
    - 温度差が2.5以上：風量4
    - 温度差が2.0以上：風量3
    - 温度差が1.5以上：風量2
    - 温度差が1.0以上：風量1
    それ以下の場合は風量を0に設定する。
    """
    x = [(3.0, 4), (2.5, 4), (2.0, 3), (1.5, 2), (1.0, 1)]

    for threshold, speed in x:
        if temperature_diff >= threshold:
            return set_circulator(current_power, current_fan_speed, speed), speed
        
    return set_circulator(current_power, current_fan_speed, 0), 0


def calculate_met_icl(outdoor_temperature: float, bedtime: bool):
    """外部温度と寝る時間かどうかに基づいて、METとICLを計算する

    外部温度が特定の閾値を超える場合、寝る時間かどうかに応じてMETとICLの値を設定する。
    以下の閾値を参照：
    - 外部温度が20以上：寝る時間ならMET=1.0, ICL=0.8、それ以外ならMET=1.1, ICL=0.6
    - 外部温度が10以上：寝る時間ならMET=1.0, ICL=1.0、それ以外ならMET=1.1, ICL=0.8
    - それ以下：寝る時間ならMET=1.0, ICL=2.0、それ以外ならMET=1.0, ICL=1.0
    """
    now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
    if outdoor_temperature >= 20 or 6 <= now.month <= 9:
        met = 1.0 if bedtime else 1.1
        icl = 0.8 if bedtime else 0.6
    elif outdoor_temperature >= 10:
        met = 1.0 if bedtime else 1.1
        icl = 1.0 if bedtime else 0.8
    else:
        met = 1.0 if bedtime else 1.0
        icl = 2.0 if bedtime else 1.0

    #たくさん活動する時間帯はmetを増やす
    if datetime.time(11, 0) <= now.time() <= datetime.time(17, 0):
        met += 0.25
    #食事する時間帯はmetを増やす
    if datetime.time(12, 0) <= now.time() <= datetime.time(13, 0):
        met += 0.2
    #食事する時間帯、入浴時間帯はmetを増やす
    if datetime.time(19, 0) <= now.time() <= datetime.time(21, 0):
        met += 0.3


    return met, icl

# メイン関数
def main():
    # 温度と湿度の取得
    ceiling_temperature, ceiling_humidity = switchbot_api.get_ceiling_temperature()
    floor_temperature, floor_humidity = switchbot_api.get_floor_temperature()
    outdoor_temperature, outdoor_humidity = switchbot_api.get_outdoor_temperature()

    # 天井と床の温度差の計算
    temperature_diff = ceiling_temperature - floor_temperature

    # 現在の日時とサーキュレーターの起動・停止時間の設定
    now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
    on_time = pytz.timezone(
        'Asia/Tokyo').localize(datetime.datetime(now.year, now.month, now.day, 6, 0, 0, 0))
    off_time = pytz.timezone(
        'Asia/Tokyo').localize(datetime.datetime(now.year, now.month, now.day, 23, 50, 0, 0))
    # 寝る時間かどうかを判断（起動時間内ならばFalse,それ以外はTrue）
    bedtime = True if on_time > now or off_time < now else False

    # ログに各種情報を出力
    logger.info(f"現在時刻:{now}")
    logger.info(f"ON時刻:{on_time}")
    logger.info(f"OFF時刻:{off_time}")
    logger.info(f"天井:温度{ceiling_temperature}°, 湿度{ceiling_humidity}%")
    logger.info(f"床:温度{floor_temperature}°, 湿度{floor_humidity}%")
    logger.info(f"外部:温度{outdoor_temperature}°, 湿度{outdoor_humidity}%")
    absolute_humidity = heat_comfort_calculator.calculate_absolute_humidity(floor_temperature, (ceiling_humidity + floor_humidity) / 2)
    logger.info(f"相対湿度{(ceiling_humidity + floor_humidity) / 2}°, 絶対湿度{absolute_humidity:.2f}g/㎥")

    # METとICLの値を計算
    met, icl = calculate_met_icl(outdoor_temperature, bedtime)

    # PMV値を計算
    result = heat_comfort_calculator.calculate_pmv(
        ceiling_temperature, ceiling_humidity, floor_temperature, floor_humidity, outdoor_temperature, met, icl, now)

    supabase: Client = create_client(PROJECT_URL, API_KEY)

    #前回の設定値を取得
    current_power, current_fan_speed = analytics.get_latest_circulator_setting(supabase)
    current_aircon_temp, current_aircon_mode, current_aircon_fan_spped, current_aircon__power, aircon_last_setting_time = analytics.get_latest_aircon_setting(supabase)

    # エアコンの設定
    last_setting_time = datetime.datetime.strptime(aircon_last_setting_time, "%Y-%m-%dT%H:%M:%S.%f%z")
    elapsed_time = now - last_setting_time
    hours, remainder = divmod(elapsed_time.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    logger.info(f"前回のエアコン設定からの経過: {hours}時間{minutes}分")

    # logger.info(f"前回のエアコン設定からの経過:{now - last_setting_time}")


    ac_settings_changed = False
    aircon_setting = set_aircon(result.pmv, outdoor_temperature, absolute_humidity, (ceiling_humidity + floor_humidity) / 2)
    # 現在の時刻と最後にエアコン設定を変更した時刻の差が1時間以上かどうかを確認します。
    if now - last_setting_time > datetime.timedelta(minutes=30):
        # 2時間以上経過していた場合、エアコンの設定を更新します。
        # 新たなエアコン設定は、現在のPMV値、屋外気温、絶対湿度を用いて set_aircon 関数で決定します。
        switchbot_api.aircon(aircon_setting.temp_setting, aircon_setting.mode_setting, aircon_setting.fan_speed_setting, aircon_setting.power_setting)
        ac_settings_changed = True
    else:
        # logger.info(current_aircon_mode)
        # logger.info(aircon_setting.mode_setting.id)
        # 1時間以内にエアコン設定が変更された場合、現在のモードが冷房または除湿モードかどうかを確認します。
        if current_aircon_mode == constants.AirconMode.COOLING.id or current_aircon_mode == constants.AirconMode.DRY.id:
            if current_aircon_mode != aircon_setting.mode_setting.id:
                if  aircon_setting.mode_setting.id == constants.AirconMode.COOLING.id or \
                    aircon_setting.mode_setting.id == constants.AirconMode.DRY.id or \
                    aircon_setting.mode_setting.id == constants.AirconMode.POWERFUL_COOLING.id:
                    logger.info("冷房を継続しつつ、設定を変更します")
                    switchbot_api.aircon(aircon_setting.temp_setting, aircon_setting.mode_setting, aircon_setting.fan_speed_setting, aircon_setting.power_setting)
                    ac_settings_changed = True
            if current_aircon_mode == aircon_setting.mode_setting.id and \
                (str(current_aircon_temp) != aircon_setting.temp_setting or
                    str(current_aircon_fan_spped) != aircon_setting.fan_speed_setting.id or
                    current_aircon__power != aircon_setting.power_setting.id):
                logger.info("現在のモードを継続しつつ、設定を変更します")
                switchbot_api.aircon(aircon_setting.temp_setting, aircon_setting.mode_setting, aircon_setting.fan_speed_setting, aircon_setting.power_setting)
                ac_settings_changed = True
            else:
                # 現在のモードが冷房または除湿の場合、そのモードを継続します。
                logger.info(f"現在の設定を継続します:{current_aircon_temp}:{constants.AirconMode.get_description(current_aircon_mode)}:{constants.AirconFanSpeed.get_description(str(current_aircon_fan_spped))}:{constants.AirconPower.get_description(current_aircon__power)}")
        else:
            # 現在のモードが冷房や除湿以外の場合は、エアコンの設定を更新します。
            switchbot_api.aircon(aircon_setting.temp_setting, aircon_setting.mode_setting, aircon_setting.fan_speed_setting, aircon_setting.power_setting)
            ac_settings_changed = True

    if ac_settings_changed:
        logger.info(f"{aircon_setting.mode_setting.description}:{aircon_setting.fan_speed_setting.description}:{aircon_setting.power_setting.description}")

    # 操作時間外なら風量を0に設定して終了
    power, fan_speed = None, None
    if bedtime:
        logger.info(f"操作時間外")
        power = set_circulator(current_power, current_fan_speed, 0)
        fan_speed = 0
        # return True
    else:
        # 温度差に基づいてサーキュレーターを設定
        power, fan_speed = set_fan_speed_based_on_temperature_diff(outdoor_temperature, temperature_diff, current_power, current_fan_speed)

    # ログ出力
    logger.info(f"現在のサーキュレーターの電源:{current_power}")
    logger.info(f"現在のサーキュレーターの風量:{current_fan_speed}")
    logger.info(f"サーキュレーターの風量を{fan_speed}に設定")

    # 観測結果を保存
    analytics.insert_temperature(supabase, constants.Location.FLOOR.id, floor_temperature, now)
    analytics.insert_temperature(supabase, constants.Location.CEILING.id, ceiling_temperature, now)
    analytics.insert_temperature(supabase, constants.Location.OUTDOOR.id, outdoor_temperature, now)
    analytics.insert_humidity(supabase, constants.Location.FLOOR.id, floor_humidity, now)
    analytics.insert_humidity(supabase, constants.Location.CEILING.id, ceiling_humidity, now)
    analytics.insert_humidity(supabase, constants.Location.OUTDOOR.id, outdoor_humidity, now)
    analytics.insert_surface_temperature(supabase, result.wall, result.ceiling, result.floor, now)
    analytics.insert_pmv(supabase, result.pmv, result.met, result.clo, result.air, now)
    if ac_settings_changed:
        analytics.insert_aircon_setting(supabase, aircon_setting.temp_setting, aircon_setting.mode_setting.id, aircon_setting.fan_speed_setting.id, aircon_setting.power_setting.id, now)
    analytics.insert_circulator_setting(supabase, fan_speed, power, now)

    return True

    
# メイン関数を呼び出す
if __name__ == "__main__":
    main()
