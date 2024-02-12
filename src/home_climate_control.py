import datetime
from util.aircon import Aircon
from util.circulator import Circulator
from util.logger import LoggerUtil
from util.time import TimeUtil
import util.analytics as analytics
import util.heat_comfort_calculator as heat_comfort_calculator
import api.switchbot_api as switchbot_api
import common.constants as constants


def calculate_met_icl(outdoor_temperature: float, bedtime: bool):
    now = TimeUtil.get_current_time()
    # 現在の曜日を取得
    current_day = now.weekday()  # 0:月曜, 1:火曜, ..., 6:日曜
    ot = outdoor_temperature
    if ot >= 20 or 6 <= now.month <= 9:
        met = 1.0 if bedtime else 1.1
        icl = 0.6 if bedtime else 0.6
        # たくさん活動する時間帯はmetを増やす
        if datetime.time(11, 0) <= now.time() <= datetime.time(17, 0):
            met += 0.25
        # 食事する時間帯はmetを増やす
        if datetime.time(12, 0) <= now.time() <= datetime.time(13, 0):
            met += 0.2
        # 食事する時間帯、入浴時間帯はmetを増やす
        if datetime.time(19, 0) <= now.time() <= datetime.time(21, 0):
            met += 0.3
    else:
        met = 1.0 if bedtime else 1.1

        # 冬の時期は暖かい服装で固定
        if 12 <= now.month or 2 >= now.month:
            icl_daytime = 1.05
            icl_bedtime = 1.6
        else:
            icl_daytime = max(1.05 - 0.03 * max(min(ot, 15) - 9, 0), 0.6)
            icl_bedtime = max(1.6 - 0.06 * max(min(ot, 15) - 9, 0), 0.8)

        icl = icl_bedtime if bedtime else icl_daytime

        # 8時からは電気代が高くなるので暖房を抑制
        if (current_day != 5 and current_day != 6) and (datetime.time(7, 40) <= now.time() <= datetime.time(11, 0)):
            icl += 0.2
        # 18時から電気代が安くなるのでちょっと我慢
        if (current_day != 5 and current_day != 6) and (datetime.time(17, 0) <= now.time() <= datetime.time(18, 0)):
            icl += 0.2

    return met, icl


# メイン関数
def main():
    # 温度と湿度の取得
    ceiling = switchbot_api.get_ceiling_temperature()
    floor = switchbot_api.get_floor_temperature()
    outdoor = switchbot_api.get_outdoor_temperature()

    # サーキュレーターの起動・停止時間の設定
    now = TimeUtil.get_current_time()
    on_time = TimeUtil.timezone().localize(datetime.datetime(now.year, now.month, now.day, 5, 0, 0, 0))
    off_time = TimeUtil.timezone().localize(datetime.datetime(now.year, now.month, now.day, 22, 50, 0, 0))
    # 寝る時間かどうかを判断（起動時間内ならばFalse,それ以外はTrue）
    bedtime = bedtime = on_time > now or off_time < now

    absolute_humidity = heat_comfort_calculator.calculate_absolute_humidity(
        floor.temperature, (ceiling.humidity + floor.humidity) / 2
    )
    # ログに各種情報を出力
    LoggerUtil.log_environment_data(ceiling, floor, outdoor, absolute_humidity, TimeUtil.get_current_time())
    # METとICLの値を計算
    met, icl = calculate_met_icl(outdoor.temperature, bedtime)

    # PMV値を計算
    pmv = heat_comfort_calculator.calculate_pmv(ceiling, floor, outdoor, met, icl)

    # 結果をログに出力
    LoggerUtil.log_pmv_results(pmv, met, icl)

    # 前回のサーキュレーターの設定を取得
    current_fan_power, current_fan_speed = analytics.get_latest_circulator_setting()
    # 前回のエアコンの設定を取得
    current_aircon_setting, aircon_last_setting_time = analytics.get_latest_aircon_setting()
    # 回のエアコン設定からの経過時間を計算
    hours, minutes = TimeUtil.calculate_elapsed_time(aircon_last_setting_time)
    LoggerUtil.log_elapsed_time(hours, minutes)

    # PMVを元にエアコンの設定を更新
    aircon_setting = Aircon.set_aircon(
        pmv, outdoor.temperature, absolute_humidity, (ceiling.humidity + floor.humidity) / 2
    )

    # 寝る時間の送風はLOWにする
    if bedtime == True and aircon_setting.mode_setting.id == constants.AirconMode.FAN.id:
        aircon_setting.fan_speed_setting = constants.AirconFanSpeed.LOW

    ac_settings_changed = Aircon.update_aircon_if_necessary(
        aircon_setting, current_aircon_setting, aircon_last_setting_time
    )

    if ac_settings_changed:
        LoggerUtil.log_aircon_setting(aircon_setting)
    else:
        LoggerUtil.log_aircon_setting(current_aircon_setting)

    # 操作時間外なら風量を0に設定して終了
    power, fan_speed = None, None
    if bedtime:
        power = Circulator.set_circulator(current_fan_power, current_fan_speed, 0)
        fan_speed = 0
    else:
        # 温度差に基づいてサーキュレーターを設定
        power, fan_speed = Circulator.set_fan_speed_based_on_temperature_diff(
            outdoor.temperature, ceiling.temperature - floor.temperature, current_fan_power, current_fan_speed
        )

    # ログ出力
    LoggerUtil.log_circulator_setting(current_fan_power, current_fan_speed, fan_speed)

    # 結果を保存
    analytics.insert_temperature_humidity(ceiling, floor, outdoor)
    analytics.insert_surface_temperature(pmv.wall, pmv.ceiling, pmv.floor)
    analytics.insert_pmv(pmv.pmv, pmv.met, pmv.clo, pmv.air)
    if ac_settings_changed:
        analytics.insert_aircon_setting(aircon_setting)
    analytics.insert_circulator_setting(fan_speed, power)

    return True


# メイン関数を呼び出す
if __name__ == "__main__":
    main()
