import datetime
import logging

from common.data_types import AirconSetting, PMVCalculation, TemperatureHumidity

formatter = "%(message)s"
logging.basicConfig(level=logging.INFO, format=formatter)

logger = logging.getLogger(__name__)


class LoggerUtil:
    @staticmethod
    def log_environment_data(
        ceiling: TemperatureHumidity,
        floor: TemperatureHumidity,
        outdoor: TemperatureHumidity,
        absolute_humidity: float,
        now: datetime.datetime,
    ):
        logger.info(f"現在時刻:{now}")
        logger.info(f"天井:温度{ceiling.temperature}°, 湿度{ceiling.humidity}%")
        logger.info(f"床:温度{floor.temperature}°, 湿度{floor.humidity}%")
        logger.info(f"外部:温度{outdoor.temperature}°, 湿度{outdoor.humidity}%")
        logger.info(f"相対湿度{(ceiling.humidity + floor.humidity) / 2}°, 絶対湿度{absolute_humidity:.2f}g/㎥")

    @staticmethod
    def log_pmv_results(pmv: PMVCalculation, met: float, icl: float):
        logger.info(f"壁表面温度: {pmv.wall:.1f}°")
        logger.info(f"天井表面温度: {pmv.ceiling:.1f}°")
        logger.info(f"床表面温度: {pmv.floor:.1f}°")
        logger.info(f"平均放射温度: {pmv.mean_radiant_temperature:.1f}°")
        logger.info(f"体感温度: {(pmv.dry_bulb_temperature + pmv.mean_radiant_temperature) / 2:.1f}°")
        logger.info(f"met: {met}")
        logger.info(f"icl: {icl}")
        logger.info(f"相対風速: {pmv.relative_air_speed:.1f}m/s")
        logger.info(f"動的な衣服の断熱性: {pmv.dynamic_clothing_insulation}")
        logger.info(f"pmv = {pmv.pmv}, ppd = {pmv.ppd}%")

    @staticmethod
    def log_elapsed_time(hours, minutes):
        logger.info(f"前回のエアコン設定からの経過: {hours}時間{minutes}分")

    @staticmethod
    def log_aircon_setting(aircon_setting: AirconSetting):
        logger.info(
            f"{aircon_setting.mode_setting.description}:{aircon_setting.temp_setting}:{aircon_setting.fan_speed_setting.description}:{aircon_setting.power_setting.description}"
        )

    @staticmethod
    def log_circulator_setting(current_fan_power: str, current_fan_speed: str, fan_speed: str):
        logger.info(f"現在のサーキュレーターの電源:{current_fan_power}")
        logger.info(f"現在のサーキュレーターの風量:{current_fan_speed}")
        logger.info(f"サーキュレーターの風量を{fan_speed}に設定")
