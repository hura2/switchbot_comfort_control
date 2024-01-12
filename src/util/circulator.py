import api.switchbot_api as switchbot_api
import common.constants as constants

class Circulator:
    @staticmethod
    def adjust_fan_speed(current_speed, target_speed):
        while current_speed != target_speed:
            if target_speed > current_speed:
                switchbot_api.increase_air_volume()
                current_speed += 1
            else:
                switchbot_api.decrease_air_volume()
                current_speed -= 1
        return current_speed



    @staticmethod
    def set_circulator(current_power, current_fan_speed, target_fan_speed):
        power = current_power
        if target_fan_speed == 0:
            if current_power == constants.CirculatorPower.ON.description:
                Circulator.adjust_fan_speed(current_fan_speed, target_fan_speed)
                switchbot_api.power_on_off()
                power = constants.CirculatorPower.OFF.description
        else:
            if current_power == constants.CirculatorPower.OFF.description:
                switchbot_api.power_on_off()
                power = constants.CirculatorPower.ON.description
            Circulator.adjust_fan_speed(current_fan_speed, target_fan_speed)

        return power
    
    @staticmethod
    def set_fan_speed_based_on_temperature_diff(
        outdoor_temperature: float, temperature_diff: float, current_power: str, current_fan_speed: str
    ):
        high_temps = [(3.0, 2), (2.5, 1), (2.0, 1), (1.5, 0), (1.0, 0)]
        low_temps = [(3.0, 4), (2.5, 3), (2.0, 3), (1.5, 2), (1.0, 1)]

        threshold_speeds = high_temps if outdoor_temperature >= 25 else low_temps

        for threshold, speed in threshold_speeds:
            if temperature_diff >= threshold:
                return Circulator.set_circulator(current_power, current_fan_speed, speed), speed

        return Circulator.set_circulator(current_power, current_fan_speed, 0), 0
