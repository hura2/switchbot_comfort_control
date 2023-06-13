import base64
import hashlib
import hmac
import json
import os
import time
import requests
from dotenv import load_dotenv

# ロギング用のライブラリ
from common.logger import logger

# 定数を管理するファイル
import common.constants as constants

# 環境変数の読み込み
load_dotenv(".env")
ACCESS_TOKEN = os.environ["SWITCHBOT_ACCESS_TOKEN"]
SECRET = os.environ["SWITCHBOT_SECRET"]
CIRCULATOR_DEVICE_ID = os.environ["SWITCHBOT_CIRCULATOR_DEVICE_ID"]
CEILING_DEVICE_ID = os.environ["SWITCHBOT_CEILING_DEVICE_ID"]
FLOOR_DEVICE_ID = os.environ["SWITCHBOT_FLOOR_DEVICE_ID"]
OUTDOOR_DEVICE_ID = os.environ["SWITCHBOT_OUTDOOR_DEVICE_ID"]
AIR_CONDITIONER_DEVICE_ID = os.environ["SWITCHBOT_AIR_CONDITIONER_DEVICE_ID"]
AIR_CONDITIONER_SUPPORT_DEVICE_ID = os.environ["SWITCHBOT_AIR_CONDITIONER_SUPPORT_DEVICE_ID"]

# APIのベースURL
API_BASE_URL = "https://api.switch-bot.com"


def generate_swt_header():
    """
    SwitchBotのヘッダーを生成する関数
    """
    t, sign, nonce = generate_sign(ACCESS_TOKEN, SECRET)
    headers = {
        "Content-Type": "application/json; charset: utf8",
        "Authorization": ACCESS_TOKEN,
        "t": t,
        "sign": sign,
        "nonce": nonce,
    }
    return headers


def generate_sign(token: str, secret: str, nonce: str = "") -> tuple[str, str, str]:
    """
    HMAC-SHA256署名を生成する関数
    """
    t = int(round(time.time() * 1000))
    string_to_sign = "{}{}{}".format(token, t, nonce)
    string_to_sign = bytes(string_to_sign, "utf-8")
    secret = bytes(secret, "utf-8")
    sign = base64.b64encode(
        hmac.new(secret, msg=string_to_sign, digestmod=hashlib.sha256).digest()
    )
    return (str(t), str(sign, "utf-8"), nonce)


def get_temperature_and_humidity(device_id: str):
    """
    指定したデバイスの温度と湿度を取得する関数
    """
    url = f"{API_BASE_URL}/v1.1/devices/{device_id}/status"
    try:
        r = requests.get(url, headers=generate_swt_header())
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(e)
    else:
        json = r.json()
        temperature = json["body"]["temperature"]
        humidity = json["body"]["humidity"]
        return temperature, humidity


def post_command(device_id: str, command: str, parameter: str = "default", command_type: str = "command"):
    """
    SwitchBotにコマンドを送信する関数
    """
    url = f"{API_BASE_URL}/v1.1/devices/{device_id}/commands"
    body = {"command": command, "parameter": parameter,
            "commandType": command_type}
    data = json.dumps(body)
    try:
        time.sleep(0.5)
        logger.debug(data)
        r = requests.post(url, data=data, headers=generate_swt_header())
    except requests.exceptions.RequestException as e:
        # エラーログを出力します
        logger.error(e)

    # レスポンスを返します
    return r


def increase_air_volume():
    """
    風量を増加させる関数
    """
    # スイッチボットに風量を増加させるコマンドを送ります
    post_command(CIRCULATOR_DEVICE_ID, constants.CirculatorFanSpeed.UP.value, "default", "customize")


def decrease_air_volume():
    """
    風量を減少させる関数
    """
    # スイッチボットに風量を減少させるコマンドを送ります
    post_command(CIRCULATOR_DEVICE_ID, constants.CirculatorFanSpeed.DOWN.value, "default", "customize")


def power_on_off():
    """
    電源をオン/オフする関数
    """
    # スイッチボットに電源をオン/オフするコマンドを送ります
    post_command(CIRCULATOR_DEVICE_ID, constants.CirculatorPower.ON.id, "default", "customize")


def aircon(temp_setting: str, mode_setting: constants.AirconMode, fan_speed_setting: constants.AirconFanSpeed,  power_setting: constants.AirconPower):
    """
    エアコンの操作を行う関数
    """
    if mode_setting == constants.AirconMode.POWERFUL_COOLING:
        post_command(AIR_CONDITIONER_SUPPORT_DEVICE_ID,
                     constants.AirconMode.POWERFUL_COOLING.description, "default", "customize")
        return
    if mode_setting == constants.AirconMode.POWERFUL_HEATING.id:
        post_command(AIR_CONDITIONER_SUPPORT_DEVICE_ID,
                     constants.AirconMode.POWERFUL_COOLING.POWERFUL_HEATING, "default", "customize")
        return
    post_command(AIR_CONDITIONER_DEVICE_ID, "setAll", f"{temp_setting},{mode_setting.id},{fan_speed_setting.id},{power_setting.id}", "command")


def get_ceiling_temperature():
    """
    天井の温度を取得する関数
    """
    return get_temperature_and_humidity(CEILING_DEVICE_ID)


def get_floor_temperature():
    """
    床の温度を取得する関数
    """
    return get_temperature_and_humidity(FLOOR_DEVICE_ID)


def get_outdoor_temperature():
    """
    屋外の温度を取得する関数
    """
    return get_temperature_and_humidity(OUTDOOR_DEVICE_ID)
