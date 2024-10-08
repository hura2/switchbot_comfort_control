
import common.constants as constants # Enum定義があるファイルをインポート

# エアコン強度を計算するクラス
class AirconIntensityCalculator:
    @staticmethod
    def calculate_intensity(temperature: float, mode: str, fan_speed: str, power: str) -> int:
        if power == constants.AirconPower.OFF.id:
            return 0

        # 温度スコア
        if mode in [constants.AirconMode.COOLING.id, constants.AirconMode.POWERFUL_COOLING.id]:
            if temperature <= 24:
                temp_score = 5
            elif temperature == 25:
                temp_score = 4
            elif temperature == 26:
                temp_score = 3
            elif temperature == 27:
                temp_score = 2
            else:
                temp_score = 1
        elif mode in [constants.AirconMode.HEATING.id, constants.AirconMode.POWERFUL_HEATING.id]:
            if temperature <= 24:
                temp_score = 5
            elif temperature == 25:
                temp_score = 4
            else:
                temp_score = 3
        else:
            temp_score = 0

        # 風量スコア
        if fan_speed == constants.AirconFanSpeed.HIGH.id:
            fan_score = 3
        elif fan_speed == constants.AirconFanSpeed.MEDIUM.id:
            fan_score = 2
        elif fan_speed == constants.AirconFanSpeed.AUTO.id:  # AUTOを考慮
            fan_score = 2
        else:
            fan_score = 1

        # モードスコア
        mode_score = 4 if mode in [
            constants.AirconMode.POWERFUL_COOLING.id, 
            constants.AirconMode.POWERFUL_HEATING.id
        ] else 3 if mode in [
            constants.AirconMode.COOLING.id, 
            constants.AirconMode.HEATING.id
        ] else 2 if mode == constants.AirconMode.DRY.id else 1

        return temp_score + fan_score + mode_score

