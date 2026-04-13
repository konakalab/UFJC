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
    end_period = df['EndDate'].max().strftime('%Y/%m/%d')

    st.title("🏆 非公式Jリーグ王座(Unofficial Football J-League Champion, UFJC) 歴代ランキング")

    # --- 算出対象期間の表示（ここがご要望の箇所です） ---
    # 小さめの文字（caption）や、枠囲み（info）で表示すると公式感が出ます
    st.info(f"📅 **算出対象期間**: {start_period} ～ {end_period}")

    # --- ツールチップ・キャプション ---
    with st.expander("💡 算出内容"):
        st.markdown(f"""
        * このWebサイトでは「非公式Jリーグ王者(Unofficial Football J-League Champion)を集計・公開しています．
        * 1993年のJリーグ開幕戦勝者(横浜マリノス)を初代UFJCとします．
            * UFJCが次の試合で敗北した場合は王者が勝者に移動，引き分けと勝利で防衛．
            * 90分での引き分けは防衛
            * 以下の試合を対象とします．Ｊ１リーグ, Ｊ２リーグ, Ｊ３リーグ, 100年構想リーグ, ＪリーグYBCルヴァンカップ, チャンピオンシップ, Ｊ１・Ｊ２入れ替え戦, ＦＵＪＩ　ＸＥＲＯＸ　ＳＵＰＥＲ　ＣＵＰ, Ｊ１参入決定戦, Ｊ１昇格プレーオフ, Ｊ２・ＪＦＬ入れ替え戦, Ｊ２・Ｊ３入れ替え戦, Ｊ１参入プレーオフ, 明治安田生命チャンピオンシップ
        """)
        
    st.caption(f"Developed by [@konakalab](https://x.com/konakalab)")

    # --- データ集計 ---
    ranking_df = df.groupby('Champion').agg({
        'Duration': 'sum',
        'NumOfMatches': 'sum'
    }).sort_values(by='Duration', ascending=False).reset_index()

    # ★ここを追加：列名を日本語に書き換え
    ranking_df = ranking_df.rename(columns={
        'Champion': 'クラブ名',
        'Duration': '累計保持日数',
        'NumOfMatches': '累計防衛試合数'
    })
    # --- レイアウト ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⏳ 累計保持日数 (Total Days)")
        fig_days = px.bar(
            ranking_df.head(20),
            x='累計保持日数',  # 変更
            y='クラブ名',      # 変更
            orientation='h',
            color='累計保持日数', # 変更
            color_continuous_scale='Reds',
            labels={'累計保持日数': '日数', 'クラブ名': 'クラブ'}
        )
        fig_days.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_days, use_container_width=True)

    with col2:
        st.subheader("⚽ 累計防衛試合数 (Total Matches)")
        fig_matches = px.bar(
            ranking_df.head(20),
            x='累計防衛試合数', # 変更
            y='クラブ名',       # 変更
            orientation='h',
            color='累計防衛試合数', # 変更
            color_continuous_scale='Blues',
            labels={'累計防衛試合数': '試合数', 'クラブ名': 'クラブ'}
        )
        fig_matches.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_matches, use_container_width=True)

    # --- 詳細データの表示 ---
    st.subheader("📋 クラブ別データ一覧")
    st.dataframe(ranking_df, use_container_width=True)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
    st.info("リポジトリに 'UFJC.csv' が正しく配置されているか確認してください。")
