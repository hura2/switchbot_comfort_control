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
    def get_max_temperature_by_date(target_date: str) -> Optional[int]:
        """
        指定された日付の指定エリアの最大気温を取得する関数。

        :param target_date: 取得したい日付（フォーマット: 'YYYY-MM-DD'）
        :return: 最大気温 (度) または None
        """
        # 気象庁データの取得
        jma_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{AREA_CODE}.json"
        jma_json = requests.get(jma_url).json()

        # 指定された日付の指定エリアの最大気温を取得
        for time_series in jma_json[0]["timeSeries"]:
            time_defines = time_series.get("timeDefines", [])
            areas = time_series.get("areas", [])
            
            # 日付のフォーマットを統一して比較
            formatted_time_defines = [datetime.strptime(td, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d") for td in time_defines]
            
            if not formatted_time_defines:
                continue

            for area_data in areas:
                if area_data["area"]["name"] == AREA_NAME:  # 環境変数から取得したエリア名に基づく
                    temps = area_data.get("temps", [])
                    
                    if temps:  # tempsデータがある場合
                        # 対象の日付がtimeDefinesに存在するか確認
                        if target_date in formatted_time_defines:
                            # 日付のインデックスを取得して、その日以降の気温データを抽出
                            date_index = formatted_time_defines.index(target_date)
                            subsequent_temps = temps[date_index:]  # 対象日以降の気温データを取得
                            
                            if subsequent_temps:
                                max_temp = max(subsequent_temps, key=int)  # 最大気温を取得
                                return int(max_temp)  # 整数に変換して戻す
        
        return 20  # 対象データが見つからなかった場合は 20 を返す

# 使用例
# target_date = "2024-10-08"  # 取得したい日付を指定
# max_temp = WeatherData.get_max_temperature_by_date(target_date)
# if max_temp is not None:
#     print(f"{target_date}の{AREA_NAME}エリアの最大気温: {max_temp}度")
# else:
#     print(f"{target_date}のデータが見つかりませんでした。")