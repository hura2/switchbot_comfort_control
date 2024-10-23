from typing import Dict
import base64
import hashlib
import hmac
import json
import os
import time
import requests
from dotenv import load_dotenv
from common.data_types import AirconSetting, CO2SensorData, TemperatureHumidity

# ロギング用のライブラリ
from util.logger import logger

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
STUDY_DEVICE_ID = os.environ["SWITCHBOT_STUDY_DEVICE_ID"]
CO2_BEDROOM_DEVICE_ID = os.environ["SWITCHBOT_CO2_BEDROOM_DEVICE_ID"]
AIR_CONDITIONER_DEVICE_ID = os.environ["SWITCHBOT_AIR_CONDITIONER_DEVICE_ID"]
AIR_CONDITIONER_SUPPORT_DEVICE_ID = os.environ["SWITCHBOT_AIR_CONDITIONER_SUPPORT_DEVICE_ID"]

# APIのベースURL
API_BASE_URL = os.environ["SWITCHBOT_BASE_URL"]


def generate_swt_header() -> Dict[str, str]:
    """
    SWTリクエスト用のヘッダーを生成します。

    Returns:
        headers (Dict[str, str]): 生成されたヘッダー。
    """
    # ACCESS_TOKENとSECRETを使用して署名を生成します
    t, sign, nonce = generate_sign(ACCESS_TOKEN, SECRET)

    # ヘッダーの辞書を作成します
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
    トークン、シークレット、およびノンスから署名を生成します。

    Args:
        token (str): アクセストークン
        secret (str): シークレットキー
        nonce (str, optional): ノンス (デフォルトは空文字列)

    Returns:
        tuple[str, str, str]: タイムスタンプ、署名、ノンスのタプル
    """
    t = int(round(time.time() * 1000))
    string_to_sign = "{}{}{}".format(token, t, nonce)
    string_to_sign = bytes(string_to_sign, "utf-8")
    secret = bytes(secret, "utf-8")
    sign = base64.b64encode(hmac.new(secret, msg=string_to_sign, digestmod=hashlib.sha256).digest())
    return (str(t), str(sign, "utf-8"), nonce)


# def get_temperature_and_humidity(device_id: str) -> TemperatureHumidity:
#     """
#     指定したデバイスの温度と湿度を取得し、TemperatureHumidityオブジェクトを返します。

#     Args:
#         device_id (str): デバイスID

#     Returns:
#         TemperatureHumidity: 温度と湿度を格納したTemperatureHumidityオブジェクト
#     """
#     url = f"{API_BASE_URL}/v1.1/devices/{device_id}/status"
#     try:
#         with requests.Session() as session:
#             response = session.get(url, headers=generate_swt_header())
#             response.raise_for_status()
#             data = response.json()
#             temperature = data["body"]["temperature"]
#             humidity = data["body"]["humidity"]
#             return TemperatureHumidity(temperature, humidity)
#     except requests.exceptions.RequestException as e:
#         logger.error(e)



def get_temperature_and_humidity(device_id: str) -> TemperatureHumidity:
    """
    指定したデバイスの温度と湿度を取得し、TemperatureHumidityオブジェクトを返します。

    Args:
        device_id (str): デバイスID

    Returns:
        TemperatureHumidity: 温度と湿度を格納したTemperatureHumidityオブジェクト
    """
    retry_count = 3  # リトライの試行回数
    retry_delay = 5  # リトライ間の遅延（秒）

    url = f"{API_BASE_URL}/v1.1/devices/{device_id}/status"
    for _ in range(retry_count):
        try:
            with requests.Session() as session:
                response = session.get(url, headers=generate_swt_header())
                response.raise_for_status()
                data = response.json()
                temperature = data["body"]["temperature"]
                humidity = data["body"]["humidity"]
                return TemperatureHumidity(temperature, humidity)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error occurred: {e}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    # リトライ後も成功しない場合はエラーを発生させる
    raise RuntimeError("Failed to retrieve temperature and humidity after multiple retries.")

def get_co2_sensor_data(device_id: str) -> CO2SensorData:
    """
    指定したCO2センサーの温度、湿度、CO2を取得し、CO2SensorDataオブジェクトを返します。

    Args:
        device_id (str): デバイスID

    Returns:
        CO2SensorData: 温度、湿度、CO2を格納したCO2SensorDataオブジェクト
    """
    retry_count = 3  # リトライの試行回数
    retry_delay = 5  # リトライ間の遅延（秒）

    url = f"{API_BASE_URL}/v1.1/devices/{device_id}/status"
    for _ in range(retry_count):
        try:
            with requests.Session() as session:
                response = session.get(url, headers=generate_swt_header())
                response.raise_for_status()
                data = response.json()
                temperature = data["body"]["temperature"]
                humidity = data["body"]["humidity"]
                co2 = data["body"]["CO2"]

                # TemperatureHumidityのインスタンスを作成
                temperature_humidity = TemperatureHumidity(temperature=temperature, humidity=humidity)
                return CO2SensorData(temperature_humidity=temperature_humidity, co2=co2)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error occurred: {e}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    # リトライ後も成功しない場合はエラーを発生させる
    raise RuntimeError("Failed to retrieve CO2 sensor data after multiple retries.")


def post_command(
    device_id: str, command: str, parameter: str = "default", command_type: str = "command"
) -> requests.Response:
    """
    指定したデバイスにコマンドを送信し、その結果を取得します。

    Args:
        device_id (str): デバイスID
        command (str): 送信するコマンド
        parameter (str, optional): コマンドのパラメータ（デフォルトは"default"）
        command_type (str, optional): コマンドの種類（デフォルトは"command"）

    Returns:
        requests.Response: コマンドの実行結果を表すResponseオブジェクト
    """
    url = f"{API_BASE_URL}/v1.1/devices/{device_id}/commands"
    body = {"command": command, "parameter": parameter, "commandType": command_type}
    data = json.dumps(body)
    try:
        # コマンド送信前に一時停止（例: 0.5秒待つ）
        time.sleep(0.5)
        with requests.Session() as session:
            response = session.post(url, data=data, headers=generate_swt_header())
        return response
    except requests.exceptions.RequestException as e:
        # エラーログを出力します
        logger.error(e)




def increase_air_volume() -> requests.Response:
    """
    スイッチボットに風量を増加させるコマンドを送信します。

    Returns:
        requests.Response: コマンドの実行結果を表すResponseオブジェクト
    """
    return post_command(CIRCULATOR_DEVICE_ID, constants.CirculatorFanSpeed.UP.value, "default", "customize")


def decrease_air_volume() -> requests.Response:
    """
    スイッチボットに風量を減少させるコマンドを送信します。

    Returns:
        requests.Response: コマンドの実行結果を表すResponseオブジェクト
    """
    return post_command(CIRCULATOR_DEVICE_ID, constants.CirculatorFanSpeed.DOWN.value, "default", "customize")


def power_on_off() -> requests.Response:
    """
    スイッチボットに電源をオン/オフするコマンドを送信します。

    Returns:
        requests.Response: コマンドの実行結果を表すResponseオブジェクト
    """
    return post_command(CIRCULATOR_DEVICE_ID, constants.CirculatorPower.ON.id, "default", "customize")



def aircon(settings: AirconSetting) -> requests.Response:
    """
    エアコンの設定を変更するコマンドを送信します。

    Args:
        settings (AirconSetting): エアコンの設定を含むオブジェクト

    Returns:
        requests.Response: コマンドの実行結果を表すResponseオブジェクト
    """
    if settings.mode_setting.id == constants.AirconMode.POWERFUL_COOLING.id:
        # パワフルモードは通常のエアコン設定では行えないため、別のデバイスIDで送信する
        return post_command(
            AIR_CONDITIONER_SUPPORT_DEVICE_ID, constants.AirconMode.POWERFUL_COOLING.description, "default", "customize"
        )

    if settings.mode_setting.id == constants.AirconMode.POWERFUL_HEATING.id:
        # パワフルモードは通常のエアコン設定では行えないため、別のデバイスIDで送信する
        return post_command(
            AIR_CONDITIONER_SUPPORT_DEVICE_ID, constants.AirconMode.POWERFUL_HEATING.description, "default", "customize"
        )

    return post_command(
        AIR_CONDITIONER_DEVICE_ID,
        "setAll",
        f"{settings.temp_setting},{settings.mode_setting.id},{settings.fan_speed_setting.id},{settings.power_setting.id}",
        "command",
    )

def get_ceiling_temperature() -> TemperatureHumidity:
    """
    天井の温度と湿度を取得します。

    Returns:
        TemperatureHumidity: 温度と湿度を表すオブジェクト
    """
    return get_temperature_and_humidity(CEILING_DEVICE_ID)


def get_floor_temperature() -> TemperatureHumidity:
    """
    床の温度と湿度を取得するします。

    Returns:
        TemperatureHumidity: 温度と湿度を表すオブジェクト
    """
    return get_temperature_and_humidity(FLOOR_DEVICE_ID)


def get_outdoor_temperature() -> TemperatureHumidity:
    """
    屋外の温度と湿度を取得するします。

    Returns:
        TemperatureHumidity: 温度と湿度を表すオブジェクト
    """
    return get_temperature_and_humidity(OUTDOOR_DEVICE_ID)


def get_study_temperature() -> TemperatureHumidity:
    """
    書斎の温度と湿度を取得するします。

    Returns:
        TemperatureHumidity: 温度と湿度を表すオブジェクト
    """
    return get_temperature_and_humidity(STUDY_DEVICE_ID)

def get_co2_bedroom_data() -> CO2SensorData:
    """
    寝室のCO2センサーから温度、湿度、CO2濃度を取得します。

    Returns:
        CO2SensorData: 温度、湿度、CO2濃度を表すオブジェクト
    """
    return get_co2_sensor_data(CO2_BEDROOM_DEVICE_ID)