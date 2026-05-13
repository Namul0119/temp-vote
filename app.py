import sqlite3
from data_storage import init_db, save_feedback_to_db
from datetime import datetime
import pandas as pd
import csv
import os
import qrcode
import base64
from io import BytesIO
from flask import Flask, render_template, render_template_string, request, redirect, url_for, session
from model import predict_with_ai, encoders
from chart_utils import build_chart_data
from rooms import (
    rooms,
    create_room,
    add_vote,
    is_room_complete,
    get_room_votes,
    get_room_status,
    delete_room
)
import random
import string
import subprocess
import threading
 
app = Flask(__name__)
app.secret_key = "temp-vote-secret-key"

ADMIN_KEY = "temp-admin-2026"

init_db()

def get_clothes_weight(clothes):
    if clothes == "thin":
        return 1.2
    elif clothes == "thick":
        return 0.8
    return 1.0


def get_activity_weight(activity):
    if activity == "move":
        return 1.2
    return 1.0


def get_position_weight(position):
    if position == "ac":
        return 1.3
    elif position == "window":
        return 1.1
    return 1.0

def make_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_qr_code(url):
    qr = qrcode.make(url)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    img_str = base64.b64encode(buffer.getvalue()).decode()

    return img_str


def is_feedback_already_saved(code, person_index):
    if not os.path.exists("real_temperature_data.csv"):
        return False

    df = pd.read_csv("real_temperature_data.csv")

    if "person_index" not in df.columns:
        return False

    saved = df[
        (df["room_code"] == code) &
        (df["person_index"] == person_index)
    ]

    return len(saved) > 0


def save_real_feedback(code, person_index, feedback):
    votes = get_room_votes(code)

    best_temp, expected_satisfaction, temp_scores, predictions = predict_with_ai(votes)

    file_exists = os.path.exists("real_temperature_data.csv")

    user = votes[person_index - 1]

    with open("real_temperature_data.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "room_code",
                "person_index",
                "sex",
                "age_group",
                "temp",
                "recommended_temp",
                "feels",
                "clothes",
                "activity",
                "position",
                "weight",
                "feedback",
                "timestamp"
            ])

        writer.writerow([
            code,
            person_index,
            user["sex"],
            user["age_group"],
            user["temp"],
            best_temp,
            user["feels"],
            user["clothes"],
            user["activity"],
            user["position"],
            user["weight"],
            feedback,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])

        save_feedback_to_db(code, person_index, user, best_temp, feedback)

@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        target_count = int(request.form["target_count"])
        room_code = make_room_code()

        create_room(room_code, target_count)

        return redirect(url_for("host", code=room_code))

    return render_template("create.html")

@app.route("/host/<code>")
def host(code):
    current, target = get_room_status(code)

    if current >= target:
        return redirect(url_for("result", code=code))

    room_url = f"http://192.168.219.111:5000/room/{code}"
    qr_image = generate_qr_code(room_url)

    return render_template(
        "host.html",
        code=code,
        current=current,
        target=target,
        qr_image=qr_image,
        room_url=room_url
    )

@app.route("/room/<code>", methods=["GET", "POST"])
def room(code):

    if code not in rooms:

        return render_template(
            "error.html",
            title="존재하지 않는 방",
            message="방 코드가 잘못되었거나 이미 종료된 방입니다."
        )

    joined_key = f"joined_{code}"

    if joined_key in session:
        return redirect(url_for("result", code=code))

    if request.method == "POST":
        current, target = get_room_status(code)

        if current >= target:

            return render_template(
                "error.html",
                title="참여 마감",
                message="이미 모든 참여자가 입력을 완료했습니다."
            )

        name = request.form["name"].strip()
        existing_names = [
            user.get("name", "").strip()
            for user in get_room_votes(code)
        ]

        if name in existing_names:

            return render_template(
                "error.html",
                title="이미 사용 중인 이름",
                message="같은 방에서는 같은 이름으로 중복 참여할 수 없습니다."
            )

        temp = int(request.form["temp"])
        clothes = request.form["clothes"]
        feels = request.form["feels"]
        activity = request.form["activity"]
        position = request.form["position"]
        sex = request.form["sex"]
        age_group = request.form["age_group"]

        total_weight = (
            get_clothes_weight(clothes)
            * get_activity_weight(activity)
            * get_position_weight(position)
        )

        person_index = len(get_room_votes(code)) + 1

        if name == "":
            name = f"{person_index}번 사람"

        vote = {
            "name": name,
            "sex": sex,
            "age_group": age_group,
            "temp": temp,
            "weight": total_weight,
            "feels": feels,
            "clothes": clothes,
            "activity": activity,
            "position": position
        }

        add_vote(code, vote)

        session[joined_key] = True
        session[f"person_index_{code}"] = person_index

        return redirect(url_for("result", code=code))

    current, target = get_room_status(code)

    return render_template(
        "room.html",
        code=code,
        current=current,
        target=target
    )

@app.route("/result/<code>")
def result(code):

    if code not in rooms:

        return render_template(
            "error.html",
            title="존재하지 않는 방",
            message="방 코드가 잘못되었거나 이미 종료된 방입니다."
        )

    current, target = get_room_status(code)

    if current < target:

        return render_template(
            "loading.html",
            current=current,
            target=target
        )

    votes = get_room_votes(code)

    best_temp, expected_satisfaction, temp_scores, predictions = predict_with_ai(votes)
    feedback_labels = encoders["feedback"].inverse_transform(predictions)

    result = best_temp
    satisfaction = round(expected_satisfaction * 100, 1)

    person_results = []

    for i, fb in enumerate(feedback_labels):

        display_name = votes[i].get("name", f"{i+1}번 사람")

        if fb == "too_cold":
            msg = f"{display_name} → 추울 가능성 높음"
        elif fb == "too_hot":
            msg = f"{display_name} → 더울 가능성 높음"
        else:
            msg = f"{display_name} → 만족 가능성 높음"

        person_results.append(msg)

    person_index = session.get(f"person_index_{code}")
    is_host = f"joined_{code}" not in session

    my_result = None
    my_name = None

    if person_index:
        my_result = person_results[person_index - 1]
        my_name = votes[person_index - 1].get("name", f"{person_index}번 사람")

    cold_count = sum(1 for user in votes if user["feels"] == "cold")
    hot_count = sum(1 for user in votes if user["feels"] == "hot")
    ok_count = sum(1 for user in votes if user["feels"] == "ok")
    ac_count = sum(1 for user in votes if user["position"] == "ac")

    total_count = len(votes)
    cold_percent = round(cold_count / total_count * 100)
    ok_percent = round(ok_count / total_count * 100)
    hot_percent = round(hot_count / total_count * 100)

    temps = [user["temp"] for user in votes]
    temp_gap = max(temps) - min(temps)

    reason = f"춥다고 느낀 사람 {cold_count}명, 덥다고 느낀 사람 {hot_count}명, 에어컨 근처 사용자 {ac_count}명을 반영했습니다. 선호 온도 차이는 {temp_gap}도입니다."

    temps = [user["temp"] for user in votes]
    temp_gap = max(temps) - min(temps)
    avg_temp = round(sum(temps) / len(temps), 1)

    analysis_points = []

    if cold_count > hot_count:
        analysis_points.append("추위를 느끼는 사용자가 더 많습니다.")

    elif hot_count > cold_count:
        analysis_points.append("더위를 느끼는 사용자가 더 많습니다.")

    else:
        analysis_points.append("추위와 더위 의견이 비슷합니다.")

    if ac_count > 0:
        analysis_points.append(f"에어컨 근처 사용자가 {ac_count}명 있습니다.")

    if temp_gap >= 4:
        analysis_points.append(f"사용자 선호 온도 차이가 {temp_gap}°C로 큰 편입니다.")
    else:
        analysis_points.append(f"사용자 선호 온도 차이는 {temp_gap}°C입니다.")

    analysis_points.append(f"평균 희망 온도는 {avg_temp}°C입니다.")

    reason = f"춥다고 느낀 사람 {cold_count}명, 덥다고 느낀 사람 {hot_count}명, 에어컨 근처 사용자 {ac_count}명을 반영했습니다. 선호 온도 차이는 {temp_gap}도입니다."

    if cold_count > hot_count:
        short_reason = "추위를 느끼는 사용자가 더 많아 온도를 높이는 방향을 고려했습니다."
    elif hot_count > cold_count:
        short_reason = "더위를 느끼는 사용자가 더 많아 온도를 낮추는 방향을 고려했습니다."
    else:
        short_reason = "추위와 더위 의견이 비슷해 가장 균형 잡힌 온도를 선택했습니다."

    if expected_satisfaction < 0.5:
        message = "선호 차이가 커 일부 사용자 불편 가능"

        if cold_count > hot_count:
            advice = "추위를 느끼는 사용자가 더 많습니다. 온도를 조금 올리거나, 에어컨 바람을 직접 맞는 사용자의 자리를 조정하는 것이 좋습니다."
        elif hot_count > cold_count:
            advice = "더위를 느끼는 사용자가 더 많습니다. 온도를 조금 낮추거나, 더운 사용자가 바람이 잘 닿는 자리로 이동하는 것이 좋습니다."
        else:
            advice = "추운 사용자와 더운 사용자가 비슷합니다. 온도 변경보다는 담요, 자리 이동, 바람 방향 조정 같은 보조 조치가 더 적합합니다."

    elif expected_satisfaction < 0.7:
        message = "대체로 괜찮지만 일부 불편 가능"
        advice = "추천 온도를 바로 크게 바꾸기보다는 0.5~1°C 정도만 미세 조정하면서 반응을 확인하는 것이 좋습니다."

    else:
        message = "대부분 사용자 만족 가능"
        advice = "추천 온도를 적용해도 무리가 적습니다. 다만 시간이 지나면 활동량이나 자리 위치에 따라 체감이 달라질 수 있습니다."

    best_chart_temp = temp_scores.index(max(temp_scores)) + 18

    chart_points, chart_dots = build_chart_data(temp_scores)

    next_temp = result

    if cold_count > hot_count:
        next_temp = min(result + 1, 30)
    elif hot_count > cold_count:
        next_temp = max(result - 1, 18)

    return render_template(
        "result.html",
        code=code,
        result=result,
        satisfaction=satisfaction,
        current=current,
        target=target,
        message=message,
        advice=advice,
        reason=reason,
        short_reason=short_reason,
        person_results=person_results,
        cold_percent=cold_percent,
        ok_percent=ok_percent,
        hot_percent=hot_percent,
        temp_scores=temp_scores,
        chart_points=chart_points,
        chart_dots=chart_dots,
        best_chart_temp=best_chart_temp,
        next_temp=next_temp,
        person_index=person_index,
        my_result=my_result,
        my_name=my_name,
        is_host=is_host,
        analysis_points=analysis_points
    )

@app.route("/feedback/<code>", methods=["POST"])
def feedback(code):
    person_index = session.get(f"person_index_{code}")

    if not person_index:

        return render_template(
            "error.html",
            title="피드백 저장 실패",
            message="참여자 정보가 확인되지 않습니다."
        )

    if is_feedback_already_saved(code, person_index):

        return render_template(
            "error.html",
            title="이미 저장된 피드백",
            message="같은 참여자는 한 번만 피드백을 남길 수 있습니다."
        )

    user_feedback = request.form["feedback"]

    save_real_feedback(code, person_index, user_feedback)

    df = pd.read_csv("real_temperature_data.csv")

    def retrain_model():
        subprocess.run(["python", "train_model.py"])

    if len(df) % 10 == 0:
        threading.Thread(target=retrain_model).start()

    votes = get_room_votes(code)
    best_temp, expected_satisfaction, temp_scores, predictions = predict_with_ai(votes)

    return render_template_string("""
    <html>
    <head>
    <meta charset="UTF-8">
    <title>피드백 저장 완료</title>
    </head>
    <body style="background:#101114; color:white; text-align:center; padding-top:120px;">
        <h1>피드백이 저장되었습니다</h1>
        <p style="color:#aaa;">내 반응 데이터가 저장되었습니다.</p>

        <p style="margin-top:25px; font-size:24px; color:#66ffd1; font-weight:bold;">
            다음 추천 온도: {{ next_temp }}°C
        </p>

        <br>

        <a href="/">
            <button style="padding:14px 28px; background:#2f6df6; color:white; border:none; border-radius:6px;">
                새 방 만들기
            </button>
        </a>
    </body>
    </html>
    """, next_temp=best_temp)

@app.route("/close/<code>", methods=["POST"])
def close_room(code):
    delete_room(code)
    session.pop(f"joined_{code}", None)
    
    return render_template("closed.html")

@app.route("/admin")
def admin():

    key = request.args.get("key")

    if key != ADMIN_KEY:
        return render_template_string("""
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="background:#101114; color:white; text-align:center; padding-top:120px;">
            <h1>관리자 권한이 없습니다</h1>
            <p style="color:#aaa;">올바른 관리자 키가 필요합니다.</p>
            <a href="/"><button>메인으로 돌아가기</button></a>
        </body>
        </html>
        """)

    conn = sqlite3.connect("temperature_feedback.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM feedback_logs")
    total_count = cursor.fetchone()[0]

    cursor.execute("""
    SELECT feedback, COUNT(*)
    FROM feedback_logs
    GROUP BY feedback
    """)
    feedback_stats = cursor.fetchall()

    cursor.execute("""
    SELECT recommended_temp, COUNT(*)
    FROM feedback_logs
    GROUP BY recommended_temp
    ORDER BY recommended_temp
    """)
    temp_stats = cursor.fetchall()

    cursor.execute("""
    SELECT substr(timestamp, 12, 2) AS hour, COUNT(*)
    FROM feedback_logs
    GROUP BY hour
    ORDER BY hour
    """)
    hour_stats = cursor.fetchall()

    cursor.execute("""
    SELECT
        room_code,
        sex,
        age_group,
        temp,
        recommended_temp,
        feedback,
        timestamp
    FROM feedback_logs
    ORDER BY id DESC
    LIMIT 20
    """)

    recent_logs = cursor.fetchall()

    import pandas as pd

    if os.path.exists("real_temperature_data.csv"):
        df = pd.read_csv("real_temperature_data.csv")

        ai_data_count = len(df)

        remain_for_train = 10 - (ai_data_count % 10)

        if remain_for_train == 10:
            remain_for_train = 0
    else:
        ai_data_count = 0
        remain_for_train = 10

    if os.path.exists("model_accuracy.txt"):
        with open("model_accuracy.txt", "r", encoding="utf-8") as file:
            model_accuracy = file.read()
    else:
        model_accuracy = "0"

    conn.close()

    return render_template(
        "admin.html",
        total_count=total_count,
        feedback_stats=feedback_stats,
        temp_stats=temp_stats,
        hour_stats=hour_stats,
        recent_logs=recent_logs,
        ai_data_count=ai_data_count,
        remain_for_train=remain_for_train,
        model_accuracy=model_accuracy
    )

@app.route("/")
def home():
    return redirect(url_for("create"))

# =========================
# 예전 5인 고정 테스트용 페이지
# 현재 실제 room 시스템에서는 사용하지 않음
# =========================
@app.route("/vote", methods=["GET", "POST"])
def index():
    result = None
    satisfaction = None
    message = None
    advice = None
    reason = None

    person_results = []

    cold_percent = 0
    ok_percent = 0
    hot_percent = 0
    temp_scores = []

    chart_points = ""
    chart_dots = []

    if request.method == "POST":
        votes = []

        for i in range(5):
            sex = request.form[f"sex{i}"]
            age_group = request.form[f"age{i}"]
            temp = int(request.form[f"temp{i}"])
            clothes = request.form[f"clothes{i}"]
            feels = request.form[f"feels{i}"]
            activity = request.form[f"activity{i}"]
            position = request.form[f"position{i}"]

            total_weight = (
                get_clothes_weight(clothes)
                * get_activity_weight(activity)
                * get_position_weight(position)
            )

            votes.append({
                "sex": sex,
                "age_group": age_group,
                "temp": temp,
                "weight": total_weight,
                "feels": feels,
                "clothes": clothes,
                "activity": activity,
                "position": position
            })

        best_temp, expected_satisfaction, temp_scores, predictions = predict_with_ai(votes)

        feedback_labels = encoders["feedback"].inverse_transform(predictions)

        result = best_temp
        satisfaction = round(expected_satisfaction * 100, 1)

        person_results = []

        for i, fb in enumerate(feedback_labels):
            if fb == "too_cold":
                msg = f"{i+1}번 사람 → 추울 가능성 높음"
            elif fb == "too_hot":
                msg = f"{i+1}번 사람 → 더울 가능성 높음"
            else:
                msg = f"{i+1}번 사람 → 만족 가능성 높음"

            person_results.append(msg)

        chart_dots = []
        points = []

        for idx, score in enumerate(temp_scores):
            temp_value = 18 + idx
            x = 50 + idx * (610 / 12)
            y = 220 - (score / 100) * 180

            chart_dots.append({
                "temp": temp_value,
                "x": round(x, 1),
                "y": round(y, 1)
            })

            points.append(f"{round(x, 1)},{round(y, 1)}")

        chart_points = " ".join(points)

        cold_count = sum(1 for user in votes if user["feels"] == "cold")
        hot_count = sum(1 for user in votes if user["feels"] == "hot")
        ac_count = sum(1 for user in votes if user["position"] == "ac")

        ok_count = sum(1 for user in votes if user["feels"] == "ok")
        total_count = len(votes)

        cold_percent = round(cold_count / total_count * 100)
        ok_percent = round(ok_count / total_count * 100)
        hot_percent = round(hot_count / total_count * 100)

        temps = [user["temp"] for user in votes]
        temp_gap = max(temps) - min(temps)

        reason = f"춥다고 느낀 사람 {cold_count}명, 덥다고 느낀 사람 {hot_count}명, 에어컨 근처 사용자 {ac_count}명을 반영했습니다. 선호 온도 차이는 {temp_gap}도입니다."

        if expected_satisfaction < 0.5:
            message = "사용자들의 선호 차이가 커서 모두가 만족하기 어려운 상태입니다."
            advice = "온도 조정보다 자리 이동, 담요, 바람 방향 조정 같은 보조 조치가 필요할 수 있습니다."
        elif expected_satisfaction < 0.7:
            message = "어느 정도 타협 가능한 온도이지만 일부 사용자는 불편할 수 있습니다."
            advice = "현재 추천 온도를 기준으로 0.5~1도 정도 미세 조정해보는 것이 좋습니다."
        else:
            message = "현재 입력 기준으로 비교적 많은 사용자가 만족할 가능성이 높습니다."
            advice = "추천 온도를 적용해도 무리가 적은 상태입니다."

    return render_template(
        "result.html",
        result=result,
        satisfaction=satisfaction,
        message=message,
        advice=advice,
        reason=reason,
        person_results=person_results,
        cold_percent=cold_percent,
        ok_percent=ok_percent,
        hot_percent=hot_percent,
        temp_scores=temp_scores,
        chart_points=chart_points,
        chart_dots=chart_dots,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)