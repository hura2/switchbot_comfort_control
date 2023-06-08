from common.data_types import PMVResult
from pythermalcomfort.models import pmv_ppd
from pythermalcomfort.utilities import v_relative, clo_dynamic
from common.logger import logger

# 壁、天井、床の熱伝導率[W/(m K)]
WALL_THERMAL_CONDUCTIVITY = 0.5
CEILING_THERMAL_CONDUCTIVITY = 0.15
FLOOR_THERMAL_CONDUCTIVITY = 0.26

# 壁、天井、床の表面熱伝達抵抗[(m K)/W]
WALL_SURFACE_HEAT_TRANSFER_RESISTANCE = 0.11
CEILING_SURFACE_HEAT_TRANSFER_RESISTANCE = 0.09
FLOOR_SURFACE_HEAT_TRANSFER_RESISTANCE = 0.15

# 床下の温度差係数
TEMP_DIFF_COEFFICIENT_UNDER_FLOOR = 0.7

# 外気温が特定の温度以上の屋根表面温度
ROOF_SURFACE_TEMP_OVER_30 = 40
ROOF_SURFACE_TEMP_OVER_35 = 60
ROOF_SURFACE_TEMP_OVER_40 = 80


def calculate_roof_surface_temperature(outdoor_temperature):
    """外気温に基づき屋根の表面温度を計算する"""
    if outdoor_temperature >= 40:
        return ROOF_SURFACE_TEMP_OVER_40
    elif outdoor_temperature >= 35:
        return ROOF_SURFACE_TEMP_OVER_35
    elif outdoor_temperature >= 30:
        return ROOF_SURFACE_TEMP_OVER_30
    else:
        return outdoor_temperature


def calculate_pmv(
        ceiling_temperature,
        ceiling_humidity,
        floor_temperature,
        floor_humidity,
        outdoor_temperature,
        met,
        icl
):
    # 屋根の表面温度を取得
    roof_surface_temp = calculate_roof_surface_temperature(outdoor_temperature)

    # 壁、天井、床の内部表面温度を計算
    wall_temp = calculate_interior_surface_temperature(
        outdoor_temperature, floor_temperature, WALL_THERMAL_CONDUCTIVITY, WALL_SURFACE_HEAT_TRANSFER_RESISTANCE)
    ceiling_temp = calculate_interior_surface_temperature(
        roof_surface_temp, ceiling_temperature, CEILING_THERMAL_CONDUCTIVITY, CEILING_SURFACE_HEAT_TRANSFER_RESISTANCE)
    floor_temp = calculate_interior_surface_temperature((floor_temperature + outdoor_temperature) * (
        1 - TEMP_DIFF_COEFFICIENT_UNDER_FLOOR), floor_temperature, FLOOR_THERMAL_CONDUCTIVITY, FLOOR_SURFACE_HEAT_TRANSFER_RESISTANCE)

    # 平均放射温度を計算
    mean_radiant_temp = (wall_temp + ceiling_temp + floor_temp) / 3

    # 室温と風速、湿度を定義
    dry_bulb_temp = floor_temperature
    wind_speed = 0.15
    humidity = (ceiling_humidity + floor_humidity) / 2

    # 相対風速と動的な衣服の断熱性を計算
    relative_air_speed = v_relative(v=wind_speed, met=met)
    dynamic_clothing_insulation = clo_dynamic(clo=icl, met=met)

    # ISOに従ってPMVを計算
    pmv_results = pmv_ppd(tdb=dry_bulb_temp, tr=mean_radiant_temp, vr=relative_air_speed,
                          rh=humidity, met=met, clo=dynamic_clothing_insulation, standard="ISO")

    # 結果をログに出力
    logger.info(f"壁表面温度: {wall_temp:.1f}°")
    logger.info(f"天井表面温度: {ceiling_temp:.1f}°")
    logger.info(f"床表面温度: {floor_temp:.1f}°")
    logger.info(f"平均放射温度: {mean_radiant_temp:.1f}°")
    logger.info(f"体感温度: {(dry_bulb_temp + mean_radiant_temp) / 2:.1f}°")
    logger.info(f"met: {met}")
    logger.info(f"icl: {icl}")
    logger.info(f"相対風速: {relative_air_speed}")
    logger.info(f"動的な衣服の断熱性: {dynamic_clothing_insulation}")
    logger.info(f"pmv = {pmv_results['pmv']}, ppd = {pmv_results['ppd']}%")

    # namedtupleを返す
    return PMVResult(pmv=float(pmv_results['pmv']), clo=dynamic_clothing_insulation.item(0), air=relative_air_speed.item(0), met=met, wall=wall_temp, ceiling=ceiling_temp, floor=floor_temp)


def calculate_interior_surface_temperature(
        outdoor_temperature,
        indoor_temperature,
        thermal_conductivity,
        surface_heat_transfer_resistance
):
    """壁、天井、床の内部表面温度を計算する"""
    thermal_resistance = 1 / thermal_conductivity  # 熱抵抗値[m2 K/W]
    logger.info("熱抵抗値 = {:.2f} [m2 K/W]".format(thermal_resistance))
    return indoor_temperature - ((surface_heat_transfer_resistance * (indoor_temperature - outdoor_temperature)) / thermal_resistance)
