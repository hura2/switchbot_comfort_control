import datetime
from common.data_types import AirconSetting, PMVCalculation, TemperatureHumidity
import common.constants as constants
from util.time import TimeUtil
from util.logger import logger
import api.switchbot_api as switchbot_api
import util.heat_comfort_calculator as heat_comfort_calculator


class Aircon:
    # エアコンの動作を設定する関数
    @staticmethod
    def set_aircon(
        pmvCalculation: PMVCalculation,
        floor_temperature: float,
        study_temperature: float,
        outdoor_temperature: float,
        absolute_humidity: float,
        dew_point: float,
    ):
        # 初期値の設定
        setting = AirconSetting("", "", constants.AirconFanSpeed.AUTO, constants.AirconPower.ON)
        pmv = pmvCalculation.pmv
        if pmv <= -0.2:
            # pmvが-0.2以下の場合の処理
            setting.temp_setting = "29"
            setting.mode_setting = constants.AirconMode.POWERFUL_HEATING
        elif pmv <= -0.16:
            # pmvが-0.16以下の場合の処理
            setting.temp_setting = "23"
            setting.mode_setting = constants.AirconMode.HEATING
        elif pmv <= -0.10:
            # pmvが-0.15以下の場合の処理
            if outdoor_temperature >= 25:
                # 天気が25℃以上の場合はそのうち暖かくなるので送風
                setting.temp_setting = "25"
                setting.mode_setting = constants.AirconMode.FAN
                setting.fan_speed_setting = constants.AirconFanSpeed.LOW
            else:
                setting.temp_setting = "23"
                setting.mode_setting = constants.AirconMode.HEATING

        elif pmv <= 0:
            # pmvが-0.3から0の場合の処理
            setting.temp_setting = "28"
            setting.mode_setting = constants.AirconMode.FAN
            setting.fan_speed_setting = constants.AirconFanSpeed.LOW
        elif pmv <= 0.10:
            # pmvが0から0.10の場合の処理
            setting.temp_setting = "28"
            setting.mode_setting = constants.AirconMode.FAN
            setting.fan_speed_setting = constants.AirconFanSpeed.LOW
        elif pmv <= 0.15:
            # pmvが0.10から0.15の場合の処理
            setting.temp_setting = "26"
            setting.mode_setting = constants.AirconMode.COOLING
            #setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
        elif pmv <= 0.18:
            # pmvが0.15から0.18の場合の処理
            setting.temp_setting = "25"
            setting.mode_setting = constants.AirconMode.COOLING
            #setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
        elif pmv <= 0.2:
            # pmvが0.18から0.2の場合の処理
            setting.temp_setting = "24"
            setting.mode_setting = constants.AirconMode.COOLING
            #setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
        else:
            # pmvが0.2以上の場合の処理
            setting.temp_setting = "22"
            setting.mode_setting = constants.AirconMode.POWERFUL_COOLING
            #setting.mode_setting = constants.AirconMode.COOLING

        # 冷房設定の場合
        if (
            setting.mode_setting == constants.AirconMode.POWERFUL_COOLING
            or setting.mode_setting == constants.AirconMode.COOLING
        ):
            if pmvCalculation.mean_radiant_temperature - 5 > outdoor_temperature and pmv < 0.3:
                # 平均放射温度より外気温-5°が低い場合はそのうち涼しくなるので送風
                setting.temp_setting = "28"
                setting.mode_setting = constants.AirconMode.FAN
                setting.fan_speed_setting = constants.AirconFanSpeed.LOW

        # 暖房設定の場合
        if (
            setting.mode_setting == constants.AirconMode.POWERFUL_HEATING
            or setting.mode_setting == constants.AirconMode.HEATING
        ):
            if pmvCalculation.mean_radiant_temperature - 5 < outdoor_temperature:
                # 平均放射温度-5°より外気温が高い場合はそのうち暖かくなるので送風
                setting.temp_setting = "28"
                setting.mode_setting = constants.AirconMode.FAN
                setting.fan_speed_setting = constants.AirconFanSpeed.LOW

        if setting.mode_setting == constants.AirconMode.FAN:
            # 絶対湿度が12.5以上の場合は除湿運転
            if absolute_humidity > 12.5:
                logger.info("絶対湿度が12.5以上")
                setting.temp_setting = "26"
                setting.mode_setting = constants.AirconMode.DRY
                setting.fan_speed_setting = constants.AirconFanSpeed.HIGH

        #床温度と書斎の温度の差が2度以上の場合は風量を上げる
        diff = abs(floor_temperature - study_temperature)
        if diff > 1:
            logger.info("床温度と書斎の温度の差が1度以上の場合は風量をHIGH")
            setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
                    
        # 室内温度が露点温度より低い場合は送風
        if floor_temperature < dew_point - 1:
            if pmv > 0.4:
                logger.info("室内温度が露点温度より低いが、暑すぎる場合は冷房")
                setting.temp_setting = "26"
                setting.mode_setting = constants.AirconMode.COOLING
                setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
                setting.force_fan_below_dew_point = True
            else:
                logger.info("室内温度が露点温度より低い場合は送風")
                setting.temp_setting = "28"
                setting.mode_setting = constants.AirconMode.FAN
                setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
                setting.force_fan_below_dew_point = True

            

        return setting

    # エアコンの設定を更新するかどうかを判断
    @staticmethod
    def should_update_aircon_settings(last_setting_time):
        # 1時間以上経過している場合は更新しない
        return TimeUtil.get_current_time() - TimeUtil.parse_datetime_string(last_setting_time) > datetime.timedelta(
            hours=24
        )

    # エアコンの設定を変更
    @staticmethod
    def update_aircon_settings(aircon_setting):
        switchbot_api.aircon(aircon_setting)

    # エアコンの設定を更新するかどうかを判断
    @staticmethod
    def update_aircon_if_necessary(
        aircon_setting: AirconSetting,
        current_aircon_setting: AirconSetting,
        last_setting_time: str,
    ):
        #露点温度に近い場合は強制的に送風
        if aircon_setting.force_fan_below_dew_point:
            Aircon.update_aircon_settings(aircon_setting)
            return True

        # エアコンの設定を最後に変更した時間と現在の時間を比較して、
        # 1時間以上経過しているかどうかをチェックします。
        if Aircon.should_update_aircon_settings(last_setting_time):
            # もし1時間以上経過していれば、新しい設定を適用します。
            logger.info("1時間経過したので、設定を変更します")
            Aircon.update_aircon_settings(aircon_setting)
            return True
        else:
            # もし1時間以内であれば、現在のエアコンのモードを確認します。
            if current_aircon_setting.mode_setting.id in [
                constants.AirconMode.COOLING.id,
                constants.AirconMode.POWERFUL_COOLING.id,
            ]:
                # もし現在のモードが冷房モードの場合、
                # 新しいモードと現在のモードが違うかどうかをチェックします。
                if current_aircon_setting.mode_setting.id != aircon_setting.mode_setting.id:
                    # 冷房系のモード内での変更の場合はそのまま設定変更します。
                    if aircon_setting.mode_setting.id in [
                        constants.AirconMode.COOLING.id,
                        constants.AirconMode.POWERFUL_COOLING.id,
                    ]:
                        logger.info("冷房を継続しつつ、設定を変更します")
                        Aircon.update_aircon_settings(aircon_setting)
                        return False
                    else:
                        logger.info("冷房を継続しつつ、最弱の設定にします")
                        aircon_setting.temp_setting = "27"
                        aircon_setting.mode_setting = constants.AirconMode.COOLING
                        #aircon_setting.fan_speed_setting = constants.AirconFanSpeed.HIGH
                        aircon_setting.fan_speed_setting = constants.AirconFanSpeed.AUTO
                        Aircon.update_aircon_settings(aircon_setting)
                        return False
                # モードが同じ場合でも、温度、ファン速度、電源のいずれかが異なる場合、
                # 設定を更新します。
                if current_aircon_setting.mode_setting.id == aircon_setting.mode_setting.id and (
                    current_aircon_setting.temp_setting != aircon_setting.temp_setting
                    or current_aircon_setting.fan_speed_setting.id != aircon_setting.fan_speed_setting.id
                    or current_aircon_setting.power_setting.id != aircon_setting.power_setting.id
                ):
                    logger.info("現在のモードを継続しつつ、設定を変更します")
                    Aircon.update_aircon_settings(aircon_setting)
                    return False
            else:
                # 現在のモードが冷房モードでない場合、
                # 新しい設定を適用します。
                Aircon.update_aircon_settings(aircon_setting)
                return True
        # 設定を変更しない場合、Falseを返します。
        return False
