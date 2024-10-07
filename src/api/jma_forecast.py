# -*- coding:utf-8 -*-
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional

# 環境変数の読み込み
load_dotenv(".env")

# 環境変数からエリア名とコードを取得
AREA_NAME = os.environ["JMA_AREA_NAME"]
AREA_CODE = os.environ["JMA_AREA_CODE"]

class WeatherData:
    @staticmethod
    def get_max_temperature() -> Optional[int]:
        """
        最初の日付の指定エリアの最大気温を取得する関数。

        :return: 最大気温 (度) または None
        """
        # 気象庁データの取得
        jma_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{AREA_CODE}.json"
        jma_json = requests.get(jma_url).json()

        # 最初の日付の指定エリアの最大気温を取得
        for time_series in jma_json[0]["timeSeries"]:
            time_defines = time_series.get("timeDefines", [])
            areas = time_series.get("areas", [])
            
            if not time_defines:
                continue
            
            for area_data in areas:
                if area_data["area"]["name"] == AREA_NAME:  # 環境変数から取得したエリア名に基づく
                    temps = area_data.get("temps", [])
                    
                    if temps:  # tempsデータがある場合
                        # 最初の日付の気温を取得
                        first_day_temps = temps[:len(time_defines) // 2]  # 最初の日付の気温を取得
                        max_temp = max(first_day_temps, key=int)  # 最大気温を取得
                        return int(max_temp)  # 整数に変換して戻す
        
        return None  # 対象データが見つからなかった場合は None を返す
