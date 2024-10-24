import datetime
import statistics
from util.aircon import Aircon
from util.circulator import Circulator
from util.logger import LoggerUtil
from util.time import TimeUtil
import util.analytics as analytics
import util.heat_comfort_calculator as heat_comfort_calculator
import api.switchbot_api as switchbot_api
import common.constants as constants


def calculate_met_icl(outdoor_temperature: float, max_temp: int, bedtime: bool):
    now = TimeUtil.get_current_time()
    # 現在の曜日を取得
    current_day = now.weekday()  # 0:月曜, 1:火曜, ..., 6:日曜
    ot = outdoor_temperature
    # 最高気温が30度以上は涼しい服装
    if max_temp >= 30:
        met = 1.0 if bedtime else 1.1
        icl = 0.8 if bedtime else 0.6
        # たくさん活動する時間帯はmetを増やす
        # if datetime.time(11, 0) <= now.time() <= datetime.time(17, 0):
        #     met += 0.25
        # 食事する時間帯はmetを増やす
        if datetime.time(12, 0) <= now.time() <= datetime.time(13, 0):
            met += 0.2
        # 食事する時間帯はmetを増やす
        if datetime.time(18, 0) <= now.time() <= datetime.time(20, 0):
            met += 0.4
        # 就寝前、入浴する時間帯はmetを増やす
        if datetime.time(23, 0) <= now.time() or now.time() <= datetime.time(0, 0):
            met += 0.3
    else:
        met = 1.0 if bedtime else 1.1

        # 最高気温が15度以下は暖かい服装
        if max_temp <= 15:
            icl_daytime = 1.05
            icl_bedtime = 1.6
            # 8時からは電気代が高くなるので暖房を抑制
            if (current_day != 5 and current_day != 6) and (datetime.time(7, 40) <= now.time() <= datetime.time(11, 0)):
                icl_daytime += 0.2
            # 18時から電気代が安くなるのでちょっと我慢
            if (current_day != 5 and current_day != 6) and (datetime.time(17, 0) <= now.time() <= datetime.time(18, 0)):
                icl_daytime += 0.2
        else:
            icl_daytime = max(1.05 - 0.025 * max(min(ot, 40) - 12, 0), 0.6)
            icl_bedtime = max(1.6 - 0.06 * max(min(ot, 15) - 9, 0), 1.2)

        icl = icl_bedtime if bedtime else icl_daytime

    return met, icl


# メイン関数
def main():
    # 温度と湿度の取得
    ceiling = switchbot_api.get_ceiling_temperature()
    floor = switchbot_api.get_floor_temperature()
    study = switchbot_api.get_study_temperature()
    outdoor = switchbot_api.get_outdoor_temperature()
    bedroom = switchbot_api.get_co2_bedroom_data()
    # 天気予報を取得
    max_temp = analytics.get_or_insert_max_temperature()

    # サーキュレーターの起動・停止時間の設定
    now = TimeUtil.get_current_time()
    on_time = TimeUtil.timezone().localize(datetime.datetime(now.year, now.month, now.day, 5, 0, 0, 0))
    off_time = TimeUtil.timezone().localize(datetime.datetime(now.year, now.month, now.day, 22, 50, 0, 0))
    # 寝る時間かどうかを判断（起動時間内ならばFalse,それ以外はTrue）
    bedtime = bedtime = on_time > now or off_time < now

    # 各部屋の温度と湿度をリスト化
    temperature_humidity_pairs = [
        (floor.temperature, ceiling.humidity),
        (ceiling.temperature, ceiling.humidity),
        (study.temperature, study.humidity),
        (bedroom.temperature_humidity.temperature, bedroom.temperature_humidity.humidity)
    ]

    # 絶対湿度を計算
    absolute_humidities = [
        heat_comfort_calculator.calculate_absolute_humidity(temp, hum) 
        for temp, hum in temperature_humidity_pairs
    ]

    # 絶対湿度の平均を計算
    absolute_humidity = statistics.mean(absolute_humidities)
    
    # 外部の絶対湿度を計算
    outdoor_absolute_humidity = heat_comfort_calculator.calculate_absolute_humidity(
        outdoor.temperature, outdoor.humidity
    )

    # 露点温度を計算
    dew_point = heat_comfort_calculator.calculate_dew_point(outdoor.temperature, outdoor.humidity)

    # ログに各種情報を出力
    LoggerUtil.log_environment_data(
        ceiling,
        floor,
        study,
        outdoor,
        bedroom,
        absolute_humidity,
        outdoor_absolute_humidity,
        dew_point,
        max_temp,
        TimeUtil.get_current_time(),
    )
    # METとICLの値を計算
    met, icl = calculate_met_icl(outdoor.temperature, max_temp, bedtime)

    # PMV値を計算
    pmv = heat_comfort_calculator.calculate_pmv(ceiling, floor, outdoor, study, met, icl)

    # 夏の間
    circulator_on = False
    circulator_on_spped = 0
    if 6 <= now.month <= 9:
        circulator_on = True
        # pmvが0以上か、湿度が13以上の場合はサーキュレーターを起動
        if pmv.pmv >= 0 or absolute_humidity >= 13:
            # サーキュレーターを稼働する
            circulator_on_spped = 2
        else:
            # サーキュレーターを停止する
            circulator_on_spped = 0

    # 風量を増やしてPMV値を再計算
    if circulator_on:
        pmv = heat_comfort_calculator.calculate_pmv(ceiling, floor, outdoor, study, met, icl, wind_speed=0.3)

    # 結果をログに出力
    LoggerUtil.log_pmv_results(pmv, met, icl)

    # 前回のサーキュレーターの設定を取得
    current_fan_power, current_fan_speed = analytics.get_latest_circulator_setting()
    # 前回のエアコンの設定を取得
    current_aircon_setting, aircon_last_setting_time = analytics.get_latest_aircon_setting()
    # 前回のエアコン設定からの経過時間を計算
    hours, minutes = TimeUtil.calculate_elapsed_time(aircon_last_setting_time)
    LoggerUtil.log_elapsed_time(hours, minutes)

    # PMVを元にエアコンの設定を更新
    aircon_setting = Aircon.set_aircon(
        pmv, floor.temperature, study.temperature, outdoor.temperature, absolute_humidity, dew_point
    )

    # 寝る時間の送風はLOWにする
    if bedtime == True and aircon_setting.mode_setting.id == constants.AirconMode.FAN.id:
        aircon_setting.fan_speed_setting = constants.AirconFanSpeed.LOW

    # エアコンの設定を更新
    ac_settings_changed = Aircon.update_aircon_if_necessary(
        aircon_setting, current_aircon_setting, aircon_last_setting_time
    )

    # エアコンの設定をログに出力
    LoggerUtil.log_aircon_setting(aircon_setting)

    # 操作時間外なら風量を0に設定して終了
    power, fan_speed = None, None
    if bedtime:
        power = Circulator.set_circulator(current_fan_power, current_fan_speed, 0)
        fan_speed = 0
    else:
        # 送風で節電
        if circulator_on:
            power = Circulator.set_circulator(current_fan_power, current_fan_speed, circulator_on_spped)
            fan_speed = circulator_on_spped
        else:
            # 温度差に基づいてサーキュレーターを設定
            power, fan_speed = Circulator.set_fan_speed_based_on_temperature_diff(
                outdoor.temperature, ceiling.temperature - floor.temperature, current_fan_power, current_fan_speed
            )

    # ログ出力
    LoggerUtil.log_circulator_setting(current_fan_power, current_fan_speed, fan_speed)
    LoggerUtil.log_aircon_scores(analytics.get_aircon_intensity_scores(now))

    # 結果を保存
    analytics.insert_temperature_humidity(ceiling, floor, outdoor, study, bedroom.temperature_humidity)
    analytics.insert_co2_sensor_data(bedroom)
    analytics.insert_surface_temperature(pmv.wall, pmv.ceiling, pmv.floor)
    analytics.insert_pmv(pmv.pmv, pmv.met, pmv.clo, pmv.air)
    if ac_settings_changed:
        analytics.insert_aircon_setting(aircon_setting)
    else:
        analytics.insert_aircon_setting(aircon_setting, aircon_last_setting_time)
    analytics.insert_circulator_setting(fan_speed, power)
    analytics.register_yesterday_intensity_score()
    # analytics.register_last_month_intensity_scores()

    return True


# メイン関数を呼び出す
if __name__ == "__main__":
    main()
