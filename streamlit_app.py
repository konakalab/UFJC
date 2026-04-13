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
        # club_names.csv を読み込む（id, japanese_name, short_name, club_color を想定）
        names_df = pd.read_csv('club_names.csv')
        df = pd.merge(df, names_df, left_on='Champion', right_on='id', how='left')
        df['Champion_Disp'] = df['short_name'].fillna(df['Champion'])
        
        # 【重要】クラブ名と色の対応辞書を作成
        # short_name をキーにするか、Champion_Disp をキーにするかに合わせます
        color_map = dict(zip(names_df['short_name'], names_df['club_color']))
        # 辞書をセッション状態などで保持するか、関数の戻り値に追加します
        st.session_state['color_map'] = color_map
        
    except Exception:
        df['Champion_Disp'] = df['Champion']
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

    # 1. ランキング順（保持日数が長い順）のクラブリストを取得
    # ranking_df は既に Duration で降順ソートされているため、その順番を利用します
    sorted_clubs = ranking_df['クラブ名'].tolist()

    # 2. タイムライン用の図を作成
    fig_timeline = px.timeline(
        df, 
        x_start="StartDate", 
        x_end="EndDate", 
        y="Champion_Disp", # ここはマージ後の元列名
        color="Champion_Disp", 
        hover_data={"StartDate": "|%Y/%m/%d", "EndDate": "|%Y/%m/%d", "Champion_Disp": False},
        labels={"Champion_Disp": "王者"}
    )

    # 3. レイアウトのカスタマイズ
    fig_timeline.update_layout(
        xaxis_title="年",
        yaxis_title="クラブ名",
        height=800, # クラブ数が多いので少し高さを出すと見やすいです
        showlegend=False,
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date",
            showgrid=True,           # 縦線を表示
            gridcolor="LightGray",    # 線の色
            tickformat="%Y",         # 目盛りを「年」のみに
            dtick="M12",             # ★ 12ヶ月（1年）ごとに線を引く
            tick0="1993-01-01"       # ★ 1993年1月1日を基準点にする
        ),
        # ★ ここがポイント：y軸の並び順をランキング順（sorted_clubs）に指定
        yaxis=dict(
            categoryorder="array",
            categoryarray=sorted_clubs,
            autorange="reversed",  # リストの先頭（1位）を一番上にする
            showgrid=True,       # グリッド線を表示
            gridcolor="LightGray", # 線の色（薄いグレー）
            gridwidth=1,         # 線の太さ
            dtick=1,              # 全ての項目（クラブ名）に線を引く
            layer="below traces", # 線をバー（帯）の下に配置
            ticks="outside",      # 目盛りを外側に出して区切りを強調
            tickson="boundaries"  # 目盛りとグリッド線を「項目の境界」に配置する
        )
    )

    st.plotly_chart(fig_timeline, use_container_width=True)
except Exception as e:
    st.error(f"エラーが発生しました: {e}")
