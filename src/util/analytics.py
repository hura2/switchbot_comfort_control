from typing import Tuple
import datetime
from supabase import Client

def insert_location(client: Client, location_name, created_at):
    # ロケーションを挿入
    result = client.from_("locations").insert([{"name": location_name, "created_at": created_at.isoformat()}], upsert=True).execute()
    return result['data'][0]['id']

def insert_temperature(client: Client, location_id, temperature, created_at):
    # 温度を挿入
    result = client.from_("temperatures").insert([{"location_id": location_id, "temperature": temperature, "created_at": created_at.isoformat()}]).execute()
    return result

def insert_humidity(client: Client, location_id, humidity, created_at):
    # 湿度を挿入
    result = client.from_("humidities").insert([{"location_id": location_id, "humidity": humidity, "created_at": created_at.isoformat()}]).execute()
    return result

def insert_surface_temperature(client: Client, wall_temp, ceiling_temp, floor_temp, created_at):
    # 表面温度を挿入
    result = client.from_("surface_temperatures").insert([{"wall": wall_temp, "ceiling": ceiling_temp, "floor": floor_temp, "created_at": created_at.isoformat()}]).execute()
    return result

def insert_pmv(client: Client, pmv, met, clo, air, created_at):
    # PMV値を挿入
    result = client.from_("pmvs").insert([{"pmv": pmv, "met": met, "clo": clo, "air": air, "created_at": created_at.isoformat()}]).execute()
    return result

# def get_circulator_setting(client: Client):
#     data = client.table("circulator").select("power, wind").eq("id", 1).execute()
#     return data.data[0]["power"], data.data[0]["wind"]

# def update_circulator(client: Client, power, wind):
#     data = client.table("circulator").update({"power": power, "wind": wind}).eq("id", 1).execute()
#     return data

def insert_aircon_setting(client: Client, temperature, mode, fan_speed, power, created_at):
    result = client.from_("aircon_settings").insert([{"temperature": temperature, "mode": mode, "fan_speed": fan_speed, "power": power, "created_at": created_at.isoformat()}]).execute()
    return result

def get_latest_aircon_setting(client: Client) -> Tuple[int, str, int, str, datetime.datetime]:
    data = client.table("aircon_settings").select("*").order("created_at",desc=True).limit(1).execute()
    return data.data[0]["temperature"], data.data[0]["mode"], data.data[0]["fan_speed"], data.data[0]["power"],  data.data[0]["created_at"]

def insert_circulator_setting(client: Client, fan_speed, power, created_at):
    result = client.from_("circulator_settings").insert([{"fan_speed": fan_speed, "power": power, "created_at": created_at.isoformat()}]).execute()
    return result

def get_latest_circulator_setting(client: Client):
    data = client.table("circulator_settings").select("power, fan_speed").order("created_at",desc=True).limit(1).execute()
    return data.data[0]["power"], data.data[0]["fan_speed"]