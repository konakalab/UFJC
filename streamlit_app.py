import streamlit as st
import pandas as pd
import plotly.express as px

# ページ設定
st.set_page_config(page_title="UFJC Dashboard", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    # CSV読み込み
    df = pd.read_csv('UFJC.csv', parse_dates=['StartDate', 'EndDate'])
    return df

try:
    df = load_data()

    # --- 算出対象期間の取得 ---
    # StartDateの最初と最後を取得してフォーマット
    start_period = df['StartDate'].min().strftime('%Y/%m/%d')
    end_period = df['StartDate'].max().strftime('%Y/%m/%d')

    st.title("🏆 非公式Jリーグ王座 歴代ランキング")

    # --- 算出対象期間の表示（ここがご要望の箇所です） ---
    # 小さめの文字（caption）や、枠囲み（info）で表示すると公式感が出ます
    st.info(f"📅 **算出対象期間**: {start_period} ～ {end_period}")

    # --- データ集計 ---
    # クラブごとの合計保持日数と試合数を計算
    ranking_df = df.groupby('Champion').agg({
        'Duration': 'sum',
        'NumOfMatches': 'sum'
    }).sort_values(by='Duration', ascending=False).reset_index()

    # --- レイアウト ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⏳ 累計保持日数 (Total Days)")
        fig_days = px.bar(
            ranking_df.head(20), # 上位20チーム
            x='Duration',
            y='Champion',
            orientation='h',
            color='Duration',
            color_continuous_scale='Reds',
            labels={'Duration': '累計保持日数', 'Champion': 'クラブ名'}
        )
        fig_days.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_days, use_container_width=True)

    with col2:
        st.subheader("⚽ 累計防衛試合数 (Total Matches)")
        fig_matches = px.bar(
            ranking_df.head(20),
            x='NumOfMatches',
            y='Champion',
            orientation='h',
            color='NumOfMatches',
            color_continuous_scale='Blues',
            labels={'NumOfMatches': '累計試合数', 'Champion': 'クラブ名'}
        )
        fig_matches.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_matches, use_container_width=True)

    # --- 詳細データの表示 ---
    st.subheader("📋 クラブ別データ一覧")
    st.dataframe(ranking_df, use_container_width=True)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
    st.info("リポジトリに 'UFJC.csv' が正しく配置されているか確認してください。")
