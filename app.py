# app.py
# 홀덤 데일리 게임 관리 시스템 (참가자 명부 + 상금 + 외부 승점 지급 포함 최종)

import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="홀덤 데일리 매니저", layout="wide")

# -----------------------
# 세션 상태 초기화
# -----------------------
if "games" not in st.session_state:
    st.session_state.games = []

if "players" not in st.session_state:
    # 누적 통계용
    st.session_state.players = {}

if "player_registry" not in st.session_state:
    # 참가자 명부
    st.session_state.player_registry = []

if "score_rules" not in st.session_state:
    st.session_state.score_rules = {1: 10, 2: 5, 3: 3}

# -----------------------
# 사이드바 메뉴
# -----------------------
menu = st.sidebar.radio(
    "메뉴",
    ["참가자 명부", "설정 (승점)", "운영 (게임 입력)", "게임별 상세 로그", "승점 랭킹", "플레이어 전적"]
)

# -----------------------
# 참가자 명부 관리
# -----------------------
if menu == "참가자 명부":
    st.header("👥 참가자 명부")
    st.caption("게임에 참여하는 모든 이용자를 먼저 등록하세요")

    new_player = st.text_input("참가자 닉네임 추가")
    if st.button("명부에 추가") and new_player:
        if new_player not in st.session_state.player_registry:
            st.session_state.player_registry.append(new_player)
            st.success("참가자가 등록되었습니다")
        else:
            st.warning("이미 등록된 닉네임입니다")

    if st.session_state.player_registry:
        st.subheader("📋 현재 참가자 명부")
        st.dataframe(pd.DataFrame({"닉네임": st.session_state.player_registry}), use_container_width=True)

# -----------------------
# 설정 - 승점 규칙
# -----------------------
elif menu == "설정 (승점)":
    st.header("⚙️ 승점 설정")
    st.caption("등수별 승점을 자유롭게 설정하세요")

    rules_df = pd.DataFrame([
        {"등수": k, "승점": v}
        for k, v in st.session_state.score_rules.items()
    ])

    edited = st.data_editor(rules_df, num_rows="dynamic", use_container_width=True)

    if st.button("승점 규칙 저장"):
        st.session_state.score_rules = {
            int(row["등수"]): int(row["승점"])
            for _, row in edited.iterrows()
        }
        st.success("승점 규칙이 저장되었습니다")

# -----------------------
# 운영 - 게임 입력
# -----------------------
elif menu == "운영 (게임 입력)":
    st.header("🎮 게임 입력")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        game_name = st.text_input("게임명")
    with col2:
        game_date = st.date_input("게임 날짜", value=date.today())
    with col3:
        open_time = st.time_input("오픈 시간")
    with col4:
        buyin_cost = st.number_input("1회 참가비", min_value=0, step=1000)
    with col5:
        prize_pool = st.number_input("총 상금", min_value=0, step=1000)

    st.subheader("👥 참가자 입력 (명부 기반)")

    if not st.session_state.player_registry:
        st.warning("참가자 명부를 먼저 등록하세요")
    else:
        players_df = st.data_editor(
            pd.DataFrame({
                "닉네임": st.session_state.player_registry[:1],
                "바이인 횟수": [1],
                "등수": [1]
            }),
            num_rows="dynamic",
            use_container_width=True
        )

        st.subheader("➕ 외부 승점 지급 (비참가자 가능)")
        bonus_df = st.data_editor(
            pd.DataFrame({"닉네임": st.session_state.player_registry[:1], "추가 승점": [0]}),
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("게임 저장"):
            game_players = []

            # 게임 참가자 처리
            for _, row in players_df.iterrows():
                if row["닉네임"]:
                    total_cost = row["바이인 횟수"] * buyin_cost
                    score = st.session_state.score_rules.get(row["등수"], 0)

                    game_players.append({
                        "nickname": row["닉네임"],
                        "buyins": row["바이인 횟수"],
                        "rank": row["등수"],
                        "total_cost": total_cost,
                        "score": score
                    })

                    p = st.session_state.players.get(row["닉네임"], {"games": 0, "cost": 0, "score": 0, "prize": 0})
                    p["games"] += 1
                    p["cost"] += total_cost
                    p["score"] += score
                    st.session_state.players[row["닉네임"]] = p

            # 외부 승점 지급 처리
            for _, row in bonus_df.iterrows():
                if row["닉네임"] and row["추가 승점"] != 0:
                    p = st.session_state.players.get(row["닉네임"], {"games": 0, "cost": 0, "score": 0, "prize": 0})
                    p["score"] += row["추가 승점"]
                    st.session_state.players[row["닉네임"]] = p

            st.session_state.games.append({
                "name": game_name,
                "date": game_date,
                "open_time": open_time.strftime("%H:%M"),
                "buyin_cost": buyin_cost,
                "prize_pool": prize_pool,
                "players": game_players,
                "bonus": bonus_df.to_dict("records")
            })

            st.success("게임이 저장되었습니다")

    st.divider()
    st.subheader("📅 오늘 오픈된 게임")
    for g in [g for g in st.session_state.games if g["date"] == date.today()]:
        st.markdown(f"• **{g['name']}** ({g['open_time']}) / 상금 {g['prize_pool']}")

# -----------------------
# 게임별 상세 로그
# -----------------------
elif menu == "게임별 상세 로그":
    st.header("🧾 게임별 상세 로그")
    selected_date = st.date_input("조회 날짜", value=date.today())

    for g in st.session_state.games:
        if g["date"] == date.today() or g["date"] == selected_date:
            st.subheader(f"🎮 {g['name']} ({g['date']})")
            st.caption(f"오픈 {g['open_time']} / 참가비 {g['buyin_cost']} / 상금 {g['prize_pool']}")

            df = pd.DataFrame(g["players"])
            if not df.empty:
                df.rename(columns={
                    "nickname": "닉네임",
                    "buyins": "바이인",
                    "rank": "등수",
                    "total_cost": "참가비",
                    "score": "승점"
                }, inplace=True)
                st.dataframe(df, use_container_width=True)

            if g.get("bonus"):
                st.caption("외부 승점 지급")
                st.dataframe(pd.DataFrame(g["bonus"]), use_container_width=True)

# -----------------------
# 승점 랭킹 (기간 설정)
# -----------------------
elif menu == "승점 랭킹":
    st.header("🏆 승점 랭킹")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("랭킹 시작일", value=date.today())
    with col2:
        end_date = st.date_input("랭킹 종료일", value=date.today())

    ranking = {}
    for g in st.session_state.games:
        if start_date <= g["date"] <= end_date:
            for p in g["players"]:
                ranking[p["nickname"]] = ranking.get(p["nickname"], 0) + p["score"]
            for b in g.get("bonus", []):
                ranking[b["닉네임"]] = ranking.get(b["닉네임"], 0) + b.get("추가 승점", 0)

    if not ranking:
        st.info("선택한 기간에 데이터가 없습니다")
    else:
        df = pd.DataFrame([
            {"닉네임": k, "누적 승점": v}
            for k, v in ranking.items()
        ])
        st.dataframe(df.sort_values("누적 승점", ascending=False), use_container_width=True)

# -----------------------
# 플레이어 전적
# -----------------------
elif menu == "플레이어 전적":
    st.header("👤 플레이어 전적")

    if not st.session_state.players:
        st.info("플레이어 기록이 없습니다")
    else:
        nickname = st.selectbox("닉네임 선택", list(st.session_state.player_registry))

        logs = []
        for g in st.session_state.games:
            for p in g["players"]:
                if p["nickname"] == nickname:
                    logs.append({
                        "게임": g["name"],
                        "날짜": g["date"],
                        "등수": p["rank"],
                        "바이인": p["buyins"],
                        "참가비": p["total_cost"],
                        "승점": p["score"]
                    })
            for b in g.get("bonus", []):
                if b.get("닉네임") == nickname and b.get("추가 승점", 0) != 0:
                    logs.append({
                        "게임": g["name"] + " (외부)",
                        "날짜": g["date"],
                        "등수": "-",
                        "바이인": 0,
                        "참가비": 0,
                        "승점": b.get("추가 승점", 0)
                    })

        st.dataframe(pd.DataFrame(logs), use_container_width=True)
