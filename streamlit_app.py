import streamlit as st
import pandas as pd
import plotly.express as px

# ページ設定
st.set_page_config(page_title="UFJC Dashboard", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    # 1. メインデータの読み込み
    df = pd.read_csv('UFJC.csv', parse_dates=['StartDate', 'EndDate'])
    
    # 2. クラブ名対応表の読み込み
    try:
        names_df = pd.read_csv('club_names.csv')
        # IDをキーに結合
        df = pd.merge(df, names_df, left_on='Champion', right_on='id', how='left')
        
        # 基本の表示用列は「短縮名(short_name)」を使用
        df['Champion_Disp'] = df['short_name'].fillna(df['Champion'])
        # 現王者用の「正式名称(name)」を保持
        df['Champion_Full'] = df['name'].fillna(df['Champion'])
        
        # 短縮名をキーにして色対応辞書を作成
        color_map = dict(zip(names_df['short_name'], names_df['club_color']))
        st.session_state['color_map'] = color_map
        
    except Exception:
        df['Champion_Disp'] = df['Champion']
        df['Champion_Full'] = df['Champion']
        st.session_state['color_map'] = {}
        
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

    # --- レイアウト ---
    # --- 現王者の表示（ここだけ長いクラブ名を使用） ---
    latest_row = df.iloc[-1]
    current_champion_full = latest_row['Champion_Full']
    st.markdown(f"### 👑 現王者: **{current_champion_full}**")

    # 一回り小さな文字で詳細を表示
    # StartDate, Duration, NumOfMatches を使用
    start_date_str = latest_row['StartDate'].strftime('%Y/%m/%d')
    duration = latest_row['Duration']
    matches = latest_row['NumOfMatches']
    
    st.markdown(f"##### 📅 開始日: {start_date_str} ｜ ⏳ 保持日数: {duration}日 ｜ ⚽ 防衛回数: {matches}回")
    st.write("---")

    # --- データ集計（以降は短縮名を使用） ---
    ranking_df = df.groupby('Champion_Disp').agg({
        'Duration': 'sum',
        'NumOfMatches': 'sum'
    }).sort_values(by='Duration', ascending=False).reset_index()

    ranking_df = ranking_df.rename(columns={
        'Champion_Disp': 'クラブ名',
        'Duration': '累計保持日数',
        'NumOfMatches': '累計防衛試合数'
    })
    
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

    # ==========================================================
    # ★ ここから下を追加・上書きしてください ★
    # ==========================================================
    # --- 時系列タイムラインの追加 ---
    st.write("---")
    st.subheader("📅 UFJC 王座変遷タイムライン (1993 - 現在)")

    # 1. ランキング順のクラブリストを取得（y軸の並び順に使用）
    sorted_clubs = ranking_df['クラブ名'].tolist()

    # 2. カラーマップの準備（load_dataで作成した辞書を取得）
    # load_dataの中で st.session_state['color_map'] = color_map としている前提
    cmap = st.session_state.get('color_map', {})

    # 3. タイムライン用の図を作成
    fig_timeline = px.timeline(
        df, 
        x_start="StartDate", 
        x_end="EndDate", 
        y="Champion_Disp",
        color="Champion_Disp", 
        color_discrete_map=cmap, # ★ ここでCSVの色を適用
        hover_data={"StartDate": "|%Y/%m/%d", "EndDate": "|%Y/%m/%d", "Champion_Disp": False},
        labels={"Champion_Disp": "王者"}
    )

    # 4. レイアウトのカスタマイズ（横線・縦線の設定込）
    fig_timeline.update_layout(
        xaxis_title="年",
        yaxis_title="クラブ名",
        height=800, 
        showlegend=False,
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date",
            showgrid=True,
            gridcolor="LightGray",
            tickformat="%Y",
            dtick="M12",
            tick0="1993-01-01"
        ),
        yaxis=dict(
            categoryorder="array",
            categoryarray=sorted_clubs,
            autorange="reversed",
            showgrid=True,
            gridcolor="LightGray",
            gridwidth=1,
            dtick=1,
            layer="below traces",
            tickson="boundaries"
        ),
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig_timeline, use_container_width=True)

# エラーハンドリングの締め（既存のコードの末尾）
except Exception as e:
    st.error(f"エラーが発生しました: {e}")
