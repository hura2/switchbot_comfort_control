import pandas as pd
import plotly.graph_objects as go
from util.supabase_client import SupabaseClient


class AirconIntensityScores:
    @staticmethod
    def fetch_data():
        supabase = SupabaseClient.get_supabase()
        response = (
            supabase.table("aircon_intensity_scores")
            .select("record_date, intensity_score")
            .order("record_date")
            .execute()
        )

        data = response.data
        df = pd.DataFrame(data)
        return df


# データを取得してグラフを作成
df = AirconIntensityScores.fetch_data()

if df is not None and not df.empty:
    # 日付をdatetime型に変換
    df["record_date"] = pd.to_datetime(df["record_date"])

    # 週単位で平均を計算
    df.set_index("record_date", inplace=True)
    weekly_avg = df.resample("W").mean().reset_index()  # 週ごとの平均を計算

    # 前年の同じ週のデータを取得するために "year" と "week" を列として追加
    weekly_avg["year"] = weekly_avg["record_date"].dt.year
    weekly_avg["week"] = weekly_avg["record_date"].dt.isocalendar().week

    # 前年のデータを取得するため、1年前の日付をシフト
    previous_year = weekly_avg.copy()
    previous_year["year"] = previous_year["year"] + 1  # 1年前に調整
    previous_year = previous_year[["year", "week", "intensity_score"]]

    # 今年のデータに前年の同週のデータをマージ
    merged_df = pd.merge(weekly_avg, previous_year, on=["year", "week"], how="left", suffixes=("", "_previous"))

    fig = go.Figure()

    # 今年の週平均エアコン強度スコアのプロット
    fig.add_trace(
        go.Scatter(
            x=merged_df["record_date"], y=merged_df["intensity_score"], mode="lines+markers", name="今年の週平均"
        )
    )

    # 前年同週の強度スコアのプロット
    fig.add_trace(
        go.Scatter(
            x=merged_df["record_date"],
            y=merged_df["intensity_score_previous"],
            mode="lines+markers",
            name="前年同週のスコア",
            line=dict(dash="dash", color="red"),
        )
    )

    # ローリングウィンドウ移動平均 (例: 4週移動平均)
    merged_df["rolling_avg"] = merged_df["intensity_score"].rolling(window=4).mean()
    fig.add_trace(
        go.Scatter(
            x=merged_df["record_date"],
            y=merged_df["rolling_avg"],
            mode="lines",
            name="移動平均 (4週)",
            line=dict(color="green"),
            opacity=0.5,
        )
    )

    # グラフのレイアウト設定
    fig.update_layout(
        title="エアコン強度スコアの週平均推移 (前年同週比較)",
        xaxis_title="記録日",
        yaxis_title="強度スコア",
        xaxis=dict(
            tickformat="%Y-%m",  # 月単位のフォーマット（年-月形式）
            dtick="M1",  # 1ヶ月ごとにティックを表示
            tickangle=45,  # ラベルを45度回転
        ),
        yaxis=dict(title="強度スコア"),
        hovermode="x unified",  # X軸に沿った値を同時にホバーで表示
        xaxis_rangeslider_visible=True,  # スライダーを表示してズーム可能にする
    )

    # インタラクティブなグラフの表示
    fig.show()
else:
    print("表示するデータがありません")
