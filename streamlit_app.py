import streamlit as st
import pandas as pd
import plotly.express as px

# ページ設定
st.set_page_config(page_title="UFJC Dashboard", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv('UFJC.csv', parse_dates=['StartDate', 'EndDate'])
    color_map = {} # デフォルトの空辞書
    
    try:
        names_df = pd.read_csv('club_names.csv')
        df = pd.merge(df, names_df, left_on='Champion', right_on='id', how='left')
        
        df['Champion_Disp'] = df['short_name'].fillna(df['Champion'])
        df['Champion_Full'] = df['name'].fillna(df['Champion'])
        
        # 色辞書を作成
        color_map = dict(zip(names_df['short_name'], names_df['club_color']))
        
    except Exception:
        df['Champion_Disp'] = df['Champion']
        df['Champion_Full'] = df['Champion']
        
    # df と color_map の両方を返す
    return df, color_map

# 呼び出し側
try:
    df, cmap = load_data() # 両方受け取る
    # st.session_state.get('color_map', {}) を使っていた箇所を、すべて cmap に置き換える

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

    # ランキング順のリストを作成しておく
    sorted_clubs = ranking_df['クラブ名'].tolist()
    
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

    # --- 時系列タイムライン ---
    st.write("---")
    st.subheader("📅 UFJC 王座変遷タイムライン (1993 - 現在)")

    # 期間選択スライダー
    min_date = df['StartDate'].min().to_pydatetime()
    max_date = df['EndDate'].max().to_pydatetime()
    
    selected_range = st.slider(
        "表示期間を選択してください（絞り込むと縦軸のクラブも連動します）",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY/MM"
    )

    # データフィルタリング
    mask = (df['EndDate'] >= pd.Timestamp(selected_range[0])) & \
           (df['StartDate'] <= pd.Timestamp(selected_range[1]))
    filtered_df = df.loc[mask].copy()

    # ★ 期間内に存在するクラブだけに絞り込む
    current_sorted_clubs = [c for c in sorted_clubs if c in filtered_df['Champion_Disp'].unique()]

    # タイムライン描画 (filtered_df を使用)
    fig_timeline = px.timeline(
        filtered_df, 
        x_start="StartDate", 
        x_end="EndDate", 
        y="Champion_Disp",
        color="Champion_Disp", 
        color_discrete_map=cmap,
        # ★ 修正ポイント1: Duration を hover_data に含める（表示自体は False にしておく）
        hover_data={
            "StartDate": False, 
            "EndDate": False, 
            "Champion_Disp": False, 
            "Duration": True # ここを True にして内部的に保持させる
        },
        labels={"Champion_Disp": "王者"}
    )

    # ツールチップのカスタマイズ
    fig_timeline.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>" +                  # {クラブ名}
            "%{base|%Y/%m/%d}から" +             # {開始日}
            "%{x|%Y/%m/%d} " +                  # {終了日}
            "(%{customdata[0]}日)" +             # {日数} ※hover_dataの1番目が渡されます
            "<extra></extra>"
        )
        # customdata=... の行は不要になったので削除
    )
    
    fig_timeline.update_layout(
        xaxis_title="年",
        yaxis_title="クラブ名",
        height=max(400, len(current_sorted_clubs) * 25), 
        showlegend=False,
        xaxis=dict(
            type="date",
            showgrid=True,
            gridcolor="LightGray",
            tickformat="%Y",
            dtick="M12",
            tick0="1993-01-01",
            range=[selected_range[0], selected_range[1]] # 横幅の範囲指定
        ),
        yaxis=dict(
            categoryorder="array",
            categoryarray=current_sorted_clubs, # ここで定義した変数を使う
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
