import datetime
from common.data_types import AirconSetting, PMVCalculation
import common.constants as constants
from util.time import TimeUtil
from util.logger import logger
import api.switchbot_api as switchbot_api


class Aircon:
    # エアコンの動作を設定する関数
    @staticmethod
    def set_aircon(pmvCalculation: PMVCalculation, outdoor_temperature: float, absolute_humidity: float, humidity: float):
        # Define aircon settings
        setting = AirconSetting("", "", constants.AirconFanSpeed.AUTO, constants.AirconPower.ON)
        pmv = pmvCalculation.pmv
        if pmv <= -0.4:
            # pmvが-0.4以下の場合の処理
            setting.temp_setting = "25"
            setting.mode_setting = constants.AirconMode.POWERFUL_HEATING
        elif pmv <= -0.2:
            # pmvが-0.2以下の場合の処理
            setting.temp_setting = "24"
            setting.mode_setting = constants.AirconMode.HEATING
        elif pmv <= -0.15:
            # pmvが-0.15以下の場合の処理
            if outdoor_temperature >= 25:
                # 天気が25℃以上の場合はそのうち暖かくなるので送風
                setting.temp_setting = "25"
                setting.mode_setting = constants.AirconMode.FAN
            else:
                setting.temp_setting = "24"
                setting.mode_setting = constants.AirconMode.HEATING

        elif pmv <= 0:
            # pmvが-0.3から0の場合の処理
            setting.temp_setting = "28"
            setting.mode_setting = constants.AirconMode.FAN
        elif pmv <= 0.2:
            # pmvが0から0.2の場合の処理
            setting.temp_setting = "28"
            setting.mode_setting = constants.AirconMode.FAN
        elif pmv <= 0.3:
            # pmvが0.2から0.3の場合の処理
            setting.temp_setting = "26"
            setting.mode_setting = constants.AirconMode.COOLING
        elif pmv <= 0.35:
            # pmvが0.3から0.35の場合の処理
            setting.temp_setting = "25"
            setting.mode_setting = constants.AirconMode.COOLING
        elif pmv <= 0.4:
            # pmvが0.35から0.4の場合の処理
            setting.temp_setting = "24"
            setting.mode_setting = constants.AirconMode.COOLING
        else:
            # pmvが0.4以上の場合の処理
            setting.temp_setting = "22"
            setting.mode_setting = constants.AirconMode.POWERFUL_COOLING

        #冷房設定の場合
        if (
            setting.mode_setting == constants.AirconMode.POWERFUL_COOLING
            or setting.mode_setting == constants.AirconMode.COOLING
        ):
            if pmvCalculation.mean_radiant_temperature > outdoor_temperature + 5:
                # 平均放射温度より外気温が5度以上低い場合はそのうち涼しくなるので送風
                setting.temp_setting = "28"
                setting.mode_setting = constants.AirconMode.FAN

        if setting.mode_setting == constants.AirconMode.FAN:
            # 絶対湿度が12以上の場合は除湿運転
            if absolute_humidity > 12:
                # #電気代が安い時間のみ
                # if now.hour < 8 or now.hour >= 18:
                setting.temp_setting = "28"
                setting.mode_setting = constants.AirconMode.DRY
        return setting

    # エアコンの設定を更新するかどうかを判断
    @staticmethod
    def should_update_aircon_settings(last_setting_time):
        # 2時間以上経過している場合は更新しない
        return TimeUtil.get_current_time() - TimeUtil.parse_datetime_string(last_setting_time) > datetime.timedelta(
            hours=1
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
        # エアコンの設定を最後に変更した時間と現在の時間を比較して、
        # 2時間以上経過しているかどうかをチェックします。
        if Aircon.should_update_aircon_settings(last_setting_time):
            # もし2時間以上経過していれば、新しい設定を適用します。
            Aircon.update_aircon_settings(aircon_setting)
            return True
        else:
            # もし2時間以内であれば、現在のエアコンのモードを確認します。
            if current_aircon_setting.mode_setting.id in [constants.AirconMode.COOLING.id, constants.AirconMode.DRY.id]:
                # もし現在のモードが冷房モードまたは除湿モードの場合、
                # 新しいモードと現在のモードが違うかどうかをチェックします。
                if current_aircon_setting.mode_setting.id != aircon_setting.mode_setting.id:
                    # 冷房系のモード内での変更の場合はそのまま設定変更します。
                    if aircon_setting.mode_setting.id in [
                        constants.AirconMode.COOLING.id,
                        constants.AirconMode.DRY.id,
                        constants.AirconMode.POWERFUL_COOLING.id,
                    ]:
                        logger.info("冷房を継続しつつ、設定を変更します")
                        Aircon.update_aircon_settings(aircon_setting)
                        return True
                # モードが同じ場合でも、温度、ファン速度、電源のいずれかが異なる場合、
                # 設定を更新します。
                if current_aircon_setting.mode_setting.id == aircon_setting.mode_setting.id and (
                    current_aircon_setting.temp_setting != aircon_setting.temp_setting
                    or current_aircon_setting.fan_speed_setting.id != aircon_setting.fan_speed_setting.id
                    or current_aircon_setting.power_setting.id != aircon_setting.power_setting.id
                ):
                    logger.info("現在のモードを継続しつつ、設定を変更します")
                    Aircon.update_aircon_settings(aircon_setting)
                    return True
            else:
                # 現在のモードが冷房モードまたは除湿モードでない場合、
                # 新しい設定を適用します。
                Aircon.update_aircon_settings(aircon_setting)
                return True
        # 設定を変更しない場合、Falseを返します。
        return False
