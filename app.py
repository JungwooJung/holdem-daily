# holdem-daily Streamlit App (비밀번호 제거 최종본)

import streamlit as st
import pandas as pd
import json
import os
from datetime import date

st.set_page_config(page_title="홀덤 데일리", layout="wide")

DATA_FILE = "data.json"

# ------------------ 데이터 로드 / 저장 ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "games": [],
            "ranking_rules": {
                "rank_points": {"1": 10, "2": 6, "3": 3},
                "first_buyin": 1,
                "last_buyin": 1
            },
            "point_adjustments": []
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data = load_data()

# ------------------ 사이드바 메뉴 ------------------

menu = st.sidebar.radio(
    "메뉴",
    [
        "설정",
        "운영 (게임 입력)",
        "포인트 보정",
        "랭킹 / 조회",
        "게임별 상세 로그",
        "플레이어 전적"
    ]
)

# ------------------ 설정 ------------------

if menu == "설정":
    st.header("⚙️ 승점 설정")

    st.subheader("등수별 승점")
    ranks = {}
    for i in range(1, 6):
        ranks[str(i)] = st.number_input(
            f"{i}등 승점",
            value=int(data["ranking_rules"]["rank_points"].get(str(i), 0))
        )

    first_buyin = st.number_input(
        "첫 게임 바이인 승점",
        value=data["ranking_rules"].get("first_buyin", 0)
    )

    last_buyin = st.number_input(
        "마지막 게임 바이인 승점",
        value=data["ranking_rules"].get("last_buyin", 0)
    )

    if st.button("설정 저장"):
        data["ranking_rules"] = {
            "rank_points": ranks,
            "first_buyin": first_buyin,
            "last_buyin": last_buyin
        }
        save_data(data)
        st.success("저장 완료")

# ------------------ 운영 (게임 입력) ------------------

elif menu == "운영 (게임 입력)":
    st.header("🎮 게임 입력")

    game_name = st.text_input("게임명")
    game_date = st.date_input("게임 날짜", value=date.today())

    players = st.text_area(
        "참가자 입력 (닉네임,등수 / 줄바꿈)",
        placeholder="예:\n철수,1\n영희,2"
    )

    if st.button("게임 저장"):
        game = {
            "id": len(data["games"]) + 1,
            "name": game_name,
            "date": str(game_date),
            "players": []
        }

        for line in players.split("\n"):
            if "," in line:
                nick, rank = line.split(",", 1)
                game["players"].append({
                    "nickname": nick.strip(),
                    "rank": rank.strip()
                })

        data["games"].append(game)
        save_data(data)
        st.success("게임 저장 완료")

# ------------------ 포인트 보정 ------------------

elif menu == "포인트 보정":
    st.header("➕➖ 포인트 보정")

    nick = st.text_input("닉네임")
    point = st.number_input("포인트 (±)", step=1)
    reason = st.text_input("사유")

    if st.button("보정 저장"):
        data["point_adjustments"].append({
            "nickname": nick,
            "point": point,
            "reason": reason,
            "date": str(date.today())
        })
        save_data(data)
        st.success("저장 완료")

# ------------------ 랭킹 / 조회 ------------------

elif menu == "랭킹 / 조회":
    st.header("🏆 랭킹")

    scores = {}

    for g in data["games"]:
        for p in g["players"]:
            nick = p["nickname"]
            rank = p["rank"]
            scores.setdefault(nick, 0)
            scores[nick] += data["ranking_rules"]["rank_points"].get(rank, 0)

    for adj in data["point_adjustments"]:
        scores.setdefault(adj["nickname"], 0)
        scores[adj["nickname"]] += adj["point"]

    df = (
        pd.DataFrame(scores.items(), columns=["닉네임", "포인트"])
        .sort_values(by="포인트", ascending=False)
        .reset_index(drop=True)
    )

    st.dataframe(df, use_container_width=True)

# ------------------ 게임별 상세 로그 ------------------

elif menu == "게임별 상세 로그":
    st.header("📜 게임별 상세 로그")

    for g in data["games"]:
        st.subheader(f"{g['name']} ({g['date']})")
        st.table(pd.DataFrame(g["players"]))

# ------------------ 플레이어 전적 ------------------

elif menu == "플레이어 전적":
    st.header("👤 플레이어 전적")

    nicknames = sorted({p["nickname"] for g in data["games"] for p in g["players"]})

    if not nicknames:
        st.info("아직 등록된 플레이어가 없습니다")
    else:
        nick = st.selectbox("닉네임 선택", nicknames)

        records = []
        for g in data["games"]:
            for p in g["players"]:
                if p["nickname"] == nick:
                    records.append({
                        "게임": g["name"],
                        "날짜": g["date"],
                        "등수": p["rank"]
                    })

        st.dataframe(pd.DataFrame(records), use_container_width=True)
