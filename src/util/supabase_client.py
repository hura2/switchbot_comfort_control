import os
from supabase import Client
from dotenv import load_dotenv

# .envファイルから環境変数を読み込みます
load_dotenv(".env")

# SupabaseのプロジェクトURLとAPIキーを環境変数から取得します
PROJECT_URL = os.environ["SUPABASE_PROJECT_URL"]
API_KEY = os.environ["SUPABASE_API_KEY"]

class SupabaseClient:
    """
    Supabaseクライアントのインスタンスを管理するクラス。

    Attributes:
        _supabase (Client or None): Supabaseクライアントのインスタンス。初回の取得時に生成されます。
    """

    _supabase = None

    @staticmethod
    def get_supabase() -> Client:
        """
        Supabaseクライアントのインスタンスを取得します。存在しない場合は新たに生成します。

        Returns:
            Client: Supabaseクライアントのインスタンス。
        """
        if SupabaseClient._supabase is None:
            SupabaseClient._supabase = Client(PROJECT_URL, API_KEY)
        return SupabaseClient._supabase
