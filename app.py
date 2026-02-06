# app.py
# 홀덤 데일리 게임 관리 시스템 (통합 완성본)

import streamlit as st
import pandas as pd
from datetime import date, datetime

st.set_page_config(page_title="홀덤 데일리 매니저", layout="wide")

# -----------------------
# 세션 상태 초기화
# -----------------------
if "games" not in st.session_state:
    st.session_state.games = []  # 게임 로그

if "players" not in st.session_state:
    st.session_state.players = {}  # 닉네임별 누적 데이터

# -----------------------
# 사이드바 메뉴
# -----------------------
menu = st.sidebar.radio(
    "메뉴",
    ["운영 (게임 입력)", "게임별 상세 로그", "랭킹 / 조회", "플레이어 전적"]
)

# -----------------------
# 운영 - 게임 입력
# -----------------------
if menu == "운영 (게임 입력)":
    st.header("🎮 게임 입력")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        game_name = st.text_input("게임명")
    with col2:
        game_date = st.date_input("게임 날짜", value=date.today())
    with col3:
        open_time = st.time_input("오픈 시간")
    with col4:
        buyin_cost = st.number_input("1회 참가비", min_value=0, step=1000)

    st.subheader("👥 참가자 입력")

    default_players = pd.DataFrame({
        "닉네임": [""],
        "바이인 횟수": [1],
        "등수": [1]
    })

    players_df = st.data_editor(
        default_players,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("게임 저장"):
        game_players = []
        for _, row in players_df.iterrows():
            if row["닉네임"]:
                total_cost = row["바이인 횟수"] * buyin_cost
                game_players.append({
                    "nickname": row["닉네임"],
                    "buyins": row["바이인 횟수"],
                    "rank": row["등수"],
                    "total_cost": total_cost
                })

                # 누적 플레이어 기록
                p = st.session_state.players.get(row["닉네임"], {"games": 0, "cost": 0})
                p["games"] += 1
                p["cost"] += total_cost
                st.session_state.players[row["닉네임"]] = p

        st.session_state.games.append({
            "name": game_name,
            "date": game_date,
            "open_time": open_time.strftime("%H:%M"),
            "buyin_cost": buyin_cost,
            "players": game_players
        })

        st.success("게임이 저장되었습니다")

    st.divider()
    st.subheader("📅 오늘 오픈된 게임")

    today_games = [g for g in st.session_state.games if g["date"] == date.today()]
    for g in today_games:
        st.markdown(f"**{g['name']}** ({g['open_time']})")

# -----------------------
# 게임별 상세 로그
# -----------------------
elif menu == "게임별 상세 로그":
    st.header("🧾 게임별 상세 로그")

    selected_date = st.date_input("조회 날짜 선택", value=date.today())

    games = st.session_state.games

    filtered = []
    for g in games:
        if g["date"] == date.today() or g["date"] == selected_date:
            filtered.append(g)

    if not filtered:
        st.info("표시할 게임이 없습니다")

    for g in filtered:
        st.subheader(f"🎮 {g['name']} ({g['date']})")
        st.caption(f"오픈 {g['open_time']} / 참가비 {g['buyin_cost']}")

        df = pd.DataFrame(g["players"])
        df.rename(columns={
            "nickname": "닉네임",
            "buyins": "바이인 횟수",
            "rank": "등수",
            "total_cost": "총 참가비"
        }, inplace=True)

        st.dataframe(df, use_container_width=True)

# -----------------------
# 랭킹 / 조회
# -----------------------
elif menu == "랭킹 / 조회":
    st.header("🏆 누적 랭킹")

    if not st.session_state.players:
        st.info("데이터가 없습니다")
    else:
        df = pd.DataFrame([
            {"닉네임": k, "게임수": v["games"], "누적 참가비": v["cost"]}
            for k, v in st.session_state.players.items()
        ])

        st.dataframe(df.sort_values("게임수", ascending=False), use_container_width=True)

# -----------------------
# 플레이어 전적
# -----------------------
elif menu == "플레이어 전적":
    st.header("👤 플레이어 전적")

    nicknames = sorted(st.session_state.players.keys())

    if not nicknames:
        st.info("플레이어 기록이 없습니다")
    else:
        selected = st.selectbox("닉네임 선택", nicknames)

        st.subheader(f"{selected} 전적")

        logs = []
        for g in st.session_state.games:
            for p in g["players"]:
                if p["nickname"] == selected:
                    logs.append({
                        "게임": g["name"],
                        "날짜": g["date"],
                        "등수": p["rank"],
                        "바이인": p["buyins"],
                        "참가비": p["total_cost"]
                    })

        df = pd.DataFrame(logs)
        st.dataframe(df, use_container_width=True)
