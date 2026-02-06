# Streamlit 기반 홀덤 데일리 포인트 & 승점 랭킹 시스템 (완성본)
# 설정 / 운영 / 보정 / 조회 / 엑셀 다운로드 포함

import streamlit as st
import json
from datetime import date
import pandas as pd

DATA_FILE = "data.json"
ADMIN_PASSWORD = "admin"

# -------------------- 데이터 로드/저장 --------------------
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "games": [],
            "ranking_rules": {
                "rank_points": {"1": 10, "2": 6, "3": 3},
                "first_buyin": 1,
                "participation": 1
            },
            "point_adjustments": []
        }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data = load_data()

st.set_page_config(page_title="홀덤 데일리 관리", layout="wide")
st.title("🃏 홀덤 데일리 포인트 & 승점 랭킹 시스템")

menu = st.sidebar.radio("메뉴", ["설정 (관리자)", "운영 (게임 입력)", "포인트 보정", "랭킹 / 조회", "게임별 상세 로그", "플레이어 전적"])("메뉴", ["설정 (관리자)", "운영 (게임 입력)", "포인트 보정", "랭킹 / 조회", "게임별 상세 로그"])

# -------------------- 설정 영역 --------------------
if menu == "설정 (관리자)":
    st.header("🔧 승점 설정")
    pw = st.text_input("관리자 비밀번호", type="password")
    if pw != ADMIN_PASSWORD:
        st.warning("비밀번호 필요")
    else:
        rules = data["ranking_rules"]
        st.subheader("등수별 승점")
        for r in [1, 2, 3]:
            rules["rank_points"][str(r)] = st.number_input(f"{r}등 승점", value=rules["rank_points"].get(str(r), 0))
        st.subheader("기타 승점")
        rules["first_buyin"] = st.number_input("첫 바이인 승점", value=rules.get("first_buyin", 0))
        rules["participation"] = st.number_input("참가 승점", value=rules.get("participation", 0))
        if st.button("💾 설정 저장"):
            save_data(data)
            st.success("저장 완료")

# -------------------- 운영 영역 --------------------
elif menu == "운영 (게임 입력)":
    st.header("🎮 게임 입력")
    game_name = st.text_input("게임명")
    game_date = st.date_input("게임 날짜", value=date.today())
    players = []
    for i in range(1, 7):
        with st.expander(f"플레이어 {i}"):
            nick = st.text_input("닉네임", key=f"n{i}")
            buyin = st.number_input("바이인", min_value=0, key=f"b{i}")
            rebuy = st.number_input("리바이", min_value=0, key=f"r{i}")
            cashout = st.number_input("캐시아웃", min_value=0, key=f"c{i}")
            rank = st.number_input("등수", min_value=1, key=f"rk{i}")
            if nick:
                players.append({"nickname": nick, "buyin": buyin, "rebuy": rebuy, "cashout": cashout, "rank": rank})
    if st.button("➕ 게임 저장") and players:
        data["games"].append({"name": game_name, "date": str(game_date), "players": players})
        save_data(data)
        st.success("게임 저장 완료")

    st.subheader("🗑 게임 삭제")
    for idx, g in enumerate(data["games"]):
        if st.button(f"삭제: {g['name']} ({g['date']})", key=f"del{idx}"):
            data["games"].pop(idx)
            save_data(data)
            st.experimental_rerun()

# -------------------- 포인트 보정 --------------------
elif menu == "포인트 보정":
    st.header("➕➖ 포인트 보정")
    nick = st.text_input("닉네임")
    amount = st.number_input("포인트 (+/-)")
    reason = st.text_input("사유")
    adate = st.date_input("보정 날짜", value=date.today())
    if st.button("보정 저장"):
        data["point_adjustments"].append({"nickname": nick, "amount": amount, "reason": reason, "date": str(adate)})
        save_data(data)
        st.success("보정 반영 완료")

    st.subheader("보정 내역")
    st.table(data["point_adjustments"])

# -------------------- 랭킹 / 조회 --------------------
elif menu == "랭킹 / 조회":
    st.header("🏆 랭킹 / 조회")
    c1, c2 = st.columns(2)
    with c1:
        start = st.date_input("시작일")
    with c2:
        end = st.date_input("종료일")

    rules = data["ranking_rules"]
    point, score = {}, {}

    for g in data["games"]:
        gdate = date.fromisoformat(g["date"])
        if not (start <= gdate <= end):
            continue
        for p in g["players"]:
            nick = p["nickname"]
            net = p["cashout"] - (p["buyin"] * (1 + p["rebuy"]))
            point[nick] = point.get(nick, 0) + net
            s = rules["rank_points"].get(str(p["rank"]), 0)
            if p["rebuy"] == 0:
                s += rules.get("first_buyin", 0)
            s += rules.get("participation", 0)
            score[nick] = score.get(nick, 0) + s

    for a in data["point_adjustments"]:
        ad = date.fromisoformat(a["date"])
        if start <= ad <= end:
            point[a["nickname"]] = point.get(a["nickname"], 0) + a["amount"]

    df_point = pd.DataFrame(sorted(point.items(), key=lambda x: x[1], reverse=True), columns=["닉네임", "포인트"])
    df_score = pd.DataFrame(sorted(score.items(), key=lambda x: x[1], reverse=True), columns=["닉네임", "승점"])

    st.subheader("누적 포인트 랭킹")
    st.dataframe(df_point)
    st.download_button("📥 포인트 엑셀 다운로드", df_point.to_excel(index=False), file_name="point.xlsx")

    st.subheader("승점 랭킹")
    st.dataframe(df_score)
    st.download_button("📥 승점 엑셀 다운로드", df_score.to_excel(index=False), file_name="score.xlsx")

# -------------------- 게임별 상세 로그 --------------------
elif menu == "게임별 상세 로그":
    st.header("📊 게임별 상세 로그")

    if not data["games"]:
        st.info("등록된 게임이 없습니다")
    else:
        game_options = [f"{i+1}. {g['name']} ({g['date']})" for i, g in enumerate(data["games"])]
        sel = st.selectbox("게임 선택", game_options)
        idx = game_options.index(sel)
        game = data["games"][idx]

        st.subheader(f"🃏 {game['name']} / {game['date']}")
        rules = data["ranking_rules"]
        rows = []
        for p in game["players"]:
            net = p["cashout"] - (p["buyin"] * (1 + p["rebuy"]))
            score = rules["rank_points"].get(str(p["rank"]), 0)
            if p["rebuy"] == 0:
                score += rules.get("first_buyin", 0)
            score += rules.get("participation", 0)
            rows.append({"닉네임": p["nickname"], "등수": p["rank"], "바이인": p["buyin"], "리바이": p["rebuy"], "캐시아웃": p["cashout"], "게임 포인트": net, "획득 승점": score})
        df = pd.DataFrame(rows).sort_values("등수")
        st.dataframe(df, use_container_width=True)

# -------------------- 플레이어 전적 --------------------
elif menu == "플레이어 전적":
    st.header("👤 플레이어 개인 전적")

    players = sorted({p['nickname'] for g in data['games'] for p in g['players']})
    if not players:
        st.info("플레이어 기록이 없습니다")
    else:
        sel = st.selectbox("닉네임 선택", players)
        rules = data["ranking_rules"]
        rows = []
        total_point, total_score, games_cnt = 0, 0, 0

        for g in data['games']:
            for p in g['players']:
                if p['nickname'] != sel:
                    continue
                games_cnt += 1
                net = p['cashout'] - (p['buyin'] * (1 + p['rebuy']))
                score = rules['rank_points'].get(str(p['rank']), 0)
                if p['rebuy'] == 0:
                    score += rules.get('first_buyin', 0)
                score += rules.get('participation', 0)
                total_point += net
                total_score += score
                rows.append({
                    "날짜": g['date'],
                    "게임명": g['name'],
                    "등수": p['rank'],
                    "게임 포인트": net,
                    "획득 승점": score
                })

        st.metric("총 게임 수", games_cnt)
        st.metric("누적 포인트", total_point)
        st.metric("누적 승점", total_score)

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
