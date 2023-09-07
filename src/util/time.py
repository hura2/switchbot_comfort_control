import pytz
from datetime import datetime

class TimeUtil:
    """
    現在時刻の管理を行うクラス。

    Attributes:
        _now (datetime or None): 現在の日時情報を格納するクラス変数。初回の取得時に生成されます。
    """

    _now = None

    @staticmethod
    def timezone():
        """
        タイムゾーンを設定します。

        Returns:
            tzinfo: タイムゾーン情報 (Asia/Tokyo など)
        """
        return pytz.timezone("Asia/Tokyo")

    @staticmethod
    def get_current_time() -> datetime:
        """
        現在の日時情報を取得します。初回の呼び出し時に生成された情報を再利用します。

        Returns:
            datetime: 現在の日時情報
        """
        if TimeUtil._now is None:
            TimeUtil._now = datetime.now(TimeUtil.timezone())
        return TimeUtil._now


    @staticmethod
    def parse_datetime_string(datetime_str):
        return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f%z")


    @staticmethod
    def calculate_elapsed_time(last_setting_time_str):
        # 文字列からdatetimeオブジェクトへの変換
        last_setting_time = TimeUtil.parse_datetime_string(last_setting_time_str)

        # 経過時間の計算
        elapsed_time = TimeUtil.get_current_time() - last_setting_time

        # 時間と分への分割
        hours, remainder = divmod(elapsed_time.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        return hours, minutes