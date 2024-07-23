from datetime import time
from common.data_types import PMVCalculation, TemperatureHumidity
from pythermalcomfort.models import pmv_ppd
from pythermalcomfort.utilities import v_relative, clo_dynamic
from util.logger import logger
from util.time import TimeUtil
import math

# 壁、天井、床、窓の熱伝導率[W/(m K)]
WALL_THERMAL_CONDUCTIVITY = 0.5
CEILING_THERMAL_CONDUCTIVITY = 0.15
FLOOR_THERMAL_CONDUCTIVITY = 0.26
WINDOW_THERMAL_CONDUCTIVITY = 2.1

# 窓の面積の壁に対する比率
WINDOW_TO_WALL_RATIO = 0.3

# 壁、天井、床の表面熱伝達抵抗[(m K)/W]
WALL_SURFACE_HEAT_TRANSFER_RESISTANCE = 0.11
CEILING_SURFACE_HEAT_TRANSFER_RESISTANCE = 0.09
FLOOR_SURFACE_HEAT_TRANSFER_RESISTANCE = 0.15

# 床下の温度差係数
TEMP_DIFF_COEFFICIENT_UNDER_FLOOR = 0.7

# 外気温が特定の温度以上の屋根表面温度
ROOF_SURFACE_TEMP_OVER_25 = 40
ROOF_SURFACE_TEMP_OVER_30 = 50
ROOF_SURFACE_TEMP_OVER_35 = 70
ROOF_SURFACE_TEMP_OVER_40 = 80

# 外気温が特定の温度以上の時の西側外壁表面温度
WALL_SURFACE_TEMP_OVER_25 = 30
WALL_SURFACE_TEMP_OVER_30 = 35
WALL_SURFACE_TEMP_OVER_35 = 40
WALL_SURFACE_TEMP_OVER_40 = 50


def calculate_west_wall_temperature(outdoor_temperature):
    """外気温と時間に基づき西側外壁の表面温度を計算する"""
    if not (time(13, 0) <= TimeUtil.get_current_time().time() < time(18, 0)):
        return outdoor_temperature

    if outdoor_temperature >= 40:
        return WALL_SURFACE_TEMP_OVER_40
    elif outdoor_temperature >= 35:
        return WALL_SURFACE_TEMP_OVER_35
    elif outdoor_temperature >= 30:
        return WALL_SURFACE_TEMP_OVER_30
    elif outdoor_temperature >= 25:
        return WALL_SURFACE_TEMP_OVER_25
    else:
        return outdoor_temperature


def calculate_roof_surface_temperature(outdoor_temperature):
    """外気温に基づき屋根の表面温度を計算する"""
    if outdoor_temperature >= 40:
        return ROOF_SURFACE_TEMP_OVER_40
    elif outdoor_temperature >= 35:
        return ROOF_SURFACE_TEMP_OVER_35
    elif outdoor_temperature >= 30:
        return ROOF_SURFACE_TEMP_OVER_30
    elif outdoor_temperature >= 25:
        return ROOF_SURFACE_TEMP_OVER_25
    else:
        return outdoor_temperature


def calculate_pmv(
    ceiling: TemperatureHumidity,
    floor: TemperatureHumidity,
    outdoor: TemperatureHumidity,
    met: float,
    icl: float,
) -> PMVCalculation:
    # 屋根の表面温度を取得
    roof_surface_temp = calculate_roof_surface_temperature(outdoor.temperature)
    # 夏の西日の影響を考慮する
    west_wall_temp = calculate_west_wall_temperature(outdoor.temperature)
    # 壁、天井、床の内部表面温度を計算
    wall_temp = calculate_wall_surface_temperature(
        west_wall_temp,
        floor.temperature,
        WALL_THERMAL_CONDUCTIVITY,
        WINDOW_THERMAL_CONDUCTIVITY,
        WINDOW_TO_WALL_RATIO,
        WALL_SURFACE_HEAT_TRANSFER_RESISTANCE,
    )
    #壁、天井、床の内部表面温度を計算する
    ceiling_temp = calculate_interior_surface_temperature(
        roof_surface_temp, ceiling.temperature, CEILING_THERMAL_CONDUCTIVITY, CEILING_SURFACE_HEAT_TRANSFER_RESISTANCE
    )
    #壁、天井、床の内部表面温度を計算する
    floor_temp = calculate_interior_surface_temperature(
        (floor.temperature + outdoor.temperature) * (1 - TEMP_DIFF_COEFFICIENT_UNDER_FLOOR),
        floor.temperature,
        FLOOR_THERMAL_CONDUCTIVITY,
        FLOOR_SURFACE_HEAT_TRANSFER_RESISTANCE,
    )

    # 平均放射温度を計算
    mean_radiant_temp = (wall_temp + ceiling_temp + floor_temp) / 3

    # 室温と風速、湿度を定義
    dry_bulb_temp = floor.temperature
    wind_speed = 0.2
    humidity = (ceiling.humidity + floor.humidity) / 2

    # 相対風速と動的な衣服の断熱性を計算
    relative_air_speed = v_relative(v=wind_speed, met=met)
    dynamic_clothing_insulation = clo_dynamic(clo=icl, met=met)

    # ISOに従ってPMVを計算
    results = pmv_ppd(
        tdb=dry_bulb_temp,
        tr=mean_radiant_temp,
        vr=relative_air_speed,
        rh=humidity,
        met=met,
        clo=dynamic_clothing_insulation,
        standard="ISO",
    )

    # namedtupleを返す
    return PMVCalculation(
        pmv=float(results["pmv"]),
        ppd=float(results["ppd"]),
        clo=dynamic_clothing_insulation.item(0),
        air=relative_air_speed.item(0),
        met=met,
        wall=wall_temp,
        ceiling=ceiling_temp,
        floor=floor_temp,
        mean_radiant_temperature=mean_radiant_temp,
        dry_bulb_temperature=dry_bulb_temp,
        relative_air_speed=relative_air_speed,
        dynamic_clothing_insulation=dynamic_clothing_insulation,
    )


def calculate_interior_surface_temperature(
    outdoor_temperature, indoor_temperature, thermal_conductivity, surface_heat_transfer_resistance
):
    """壁、天井、床の内部表面温度を計算する"""
    thermal_resistance = 1 / thermal_conductivity  # 熱抵抗値[m2 K/W]
    logger.info("熱抵抗値 = {:.2f} [m2 K/W]".format(thermal_resistance))
    return indoor_temperature - (
        (surface_heat_transfer_resistance * (indoor_temperature - outdoor_temperature)) / thermal_resistance
    )


def calculate_wall_surface_temperature(
    outdoor_temperature,
    indoor_temperature,
    wall_thermal_conductivity,
    window_thermal_conductivity,
    window_to_wall_ratio,
    surface_heat_transfer_resistance,
):
    """壁の内部表面温度を計算する"""
    # 窓と壁の複合熱伝導率を計算する
    composite_thermal_conductivity = (
        window_to_wall_ratio * window_thermal_conductivity + (1 - window_to_wall_ratio) * wall_thermal_conductivity
    )

    return calculate_interior_surface_temperature(
        outdoor_temperature, indoor_temperature, composite_thermal_conductivity, surface_heat_transfer_resistance
    )


def calculate_absolute_humidity(temperature, relative_humidity):
    # 室温を絶対温度（ケルビン）に変換
    temperature_kelvin = temperature + 273.15

    # 飽和水蒸気圧を計算 (Tetensの式)
    saturated_vapor_pressure = 6.1078 * 10 ** ((7.5 * temperature) / (temperature + 237.3))

    # 絶対湿度を計算
    absolute_humidity = (217 * (relative_humidity / 100) * saturated_vapor_pressure) / temperature_kelvin

    return absolute_humidity

    # 露点温度を計算する関数

def calculate_dew_point(temperature_celsius: float, relative_humidity: float) -> float:
    """
    :param temperature_celsius: 気温（摂氏）
    :param relative_humidity: 相対湿度（%）
    :return: 露点温度（摂氏）
    """
    # 定数
    a = 17.27
    b = 237.7
    
    # 中間計算
    alpha = ((a * temperature_celsius) / (b + temperature_celsius)) + math.log(relative_humidity / 100.0)
    
    # 露点温度の計算
    dew_point = math.ceil(((b * alpha) / (a - alpha)) * 10) / 10

    return dew_point
