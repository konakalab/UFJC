import streamlit as st
import pandas as pd
import plotly.express as px

# ページ設定
st.set_page_config(page_title="UFJC Dashboard", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    # 1. メインデータの読み込み
    df = pd.read_csv('UFJC.csv', parse_dates=['StartDate', 'EndDate'])
    
    # 2. 公式クラブ名対応表の読み込み
    try:
        names_df = pd.read_csv('club_names.csv')
        # IDをキーに結合
        df = pd.merge(df, names_df, left_on='Champion', right_on='id', how='left')
        # 短縮名(short_name)があれば使い、なければ元のID(Champion)を表示用にする
        df['Champion_Disp'] = df['short_name'].fillna(df['Champion'])
    except Exception:
        # 対応表がない場合の予備処理
        df['Champion_Disp'] = df['Champion']
        
    return df

try:
    df = load_data()

    # --- 算出対象期間の取得 ---
    start_period = df['StartDate'].min().strftime('%Y/%m/%d')
    end_period = df['EndDate'].max().strftime('%Y/%m/%d')

    st.title("🏆 非公式Jリーグ王座(Unofficial Football J-League Champion, UFJC) 歴代ランキング")

    # --- 算出対象期間の表示 ---
    st.info(f"📅 **算出対象期間**: {start_period} ～ {end_period}")

    # --- 説明文 ---
    with st.expander("💡 算出内容について"):
        st.markdown(f"""
        * このWebサイトでは「非公式Jリーグ王者(Unofficial Football J-League Champion)」を集計・公開しています。
        * 1993年のJリーグ開幕戦勝者を初代UFJCとし、王者が敗北した際に勝者へ王座が移動するルールで算出しています。
        """)
        
    st.caption(f"Developed by [@konakalab](https://x.com/konakalab)")

    # --- データ集計 (日本語表示用の列で集計) ---
    ranking_df = df.groupby('Champion_Disp').agg({
        'Duration': 'sum',
        'NumOfMatches': 'sum'
    }).sort_values(by='Duration', ascending=False).reset_index()

    # 表示用の列名に変更
    ranking_df = ranking_df.rename(columns={
        'Champion_Disp': 'クラブ名',
        'Duration': '累計保持日数',
        'NumOfMatches': '累計防衛試合数'
    })

    # --- レイアウト ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⏳ 累計保持日数")
        fig_days = px.bar(
            ranking_df.head(20),
            x='累計保持日数',
            y='クラブ名',
            orientation='h',
            color='累計保持日数',
            color_continuous_scale='Reds',
            labels={'累計保持日数': '日数', 'クラブ名': 'クラブ'}
        )
        fig_days.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_days, use_container_width=True)

    with col2:
        st.subheader("⚽ 累計防衛試合数")
        fig_matches = px.bar(
            ranking_df.head(20),
            x='累計防衛試合数',
            y='クラブ名',
            orientation='h',
            color='累計防衛試合数',
            color_continuous_scale='Blues',
            labels={'累計防衛試合数': '試合数', 'クラブ名': 'クラブ'}
        )
        fig_matches.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_matches, use_container_width=True)

    # --- 詳細データの表示 ---
    st.subheader("📋 クラブ別データ一覧")
    st.dataframe(ranking_df, use_container_width=True)

    # --- 時系列タイムラインの追加 ---
    st.write("---")
    st.subheader("📅 UFJC 王座変遷タイムライン (1993 - 現在)")
    st.markdown("下のスライダーを動かすことで、特定の年代を詳しく見ることができます。")

    # タイムライン用の図を作成
    fig_timeline = px.timeline(
        df, 
        x_start="StartDate", 
        x_end="EndDate", 
        y="Champion_Disp",
        color="Champion_Disp", # クラブごとに色分け
        hover_data={"StartDate": "|%Y/%m/%d", "EndDate": "|%Y/%m/%d", "Champion_Disp": False},
        labels={"Champion_Disp": "王者"}
    )

    # レイアウトのカスタマイズ
    fig_timeline.update_layout(
        xaxis_title="年",
        yaxis_title="クラブ名",
        height=600,
        showlegend=False, # クラブ数が多いので凡例は非表示
        xaxis=dict(
            rangeslider=dict(visible=True), # 下部にスクロール/ズーム用のスライダーを追加
            type="date"
        ),
        yaxis=dict(categoryorder="array", categoryarray=df["Champion_Disp"].unique())
    )

    st.plotly_chart(fig_timeline, use_container_width=True)
except Exception as e:
    st.error(f"エラーが発生しました: {e}")
