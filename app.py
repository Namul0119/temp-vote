import sqlite3
from data_storage import init_db, save_feedback_to_db
from datetime import datetime
import pandas as pd
import csv
import os
import qrcode
import base64
from io import BytesIO
from flask import Flask, render_template_string, request, redirect, url_for, session
from model import predict_with_ai, encoders
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

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>집단 온도 추천 AI</title>

<style>
    body {
        margin: 0;
        background: #101114;
        color: white;
        font-family: Arial, sans-serif;
    }

    .container {
        width: min(760px, 92vw);
        margin: 0 auto;
        padding: 60px 20px;
    }

    .badge {
        display: inline-block;
        background: #e9fff7;
        color: #111;
        padding: 8px 14px;
        border-radius: 6px;
        font-weight: bold;
        margin-bottom: 30px;
    }

    h1 {
        font-size: 42px;
        margin-bottom: 8px;
    }

    .subtitle {
        color: #aaa;
        font-size: 18px;
        margin-bottom: 40px;
    }

    .step-label {
        color: #62ffd5;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 12px;
    }

    .question {
        margin-bottom: 28px;
    }

    .question-title {
        font-size: 20px;
        margin-bottom: 10px;
    }

    .options {
        display: flex;
        gap: 0;
    }

    .options input {
        display: none;
    }

    .options label {
        flex: 1;
        text-align: center;
        padding: 15px 8px;
        background: #292b31;
        color: #ccc;
        cursor: pointer;
        border-right: 1px solid #1a1b1f;
    }

    .options input:checked + label {
        background: #2f6df6;
        color: white;
        font-weight: bold;
    }

    .temp-input {
        width: 100%;
        padding: 16px;
        box-sizing: border-box;
        background: #292b31;
        border: none;
        color: white;
        font-size: 20px;
    }

    .nav {
        display: flex;
        justify-content: space-between;
        margin-top: 40px;
    }

    button {
        background: #2f6df6;
        color: white;
        border: none;
        padding: 14px 28px;
        font-size: 18px;
        border-radius: 4px;
        cursor: pointer;
    }

    .hidden {
        display: none;
    }

    .result-box {
        text-align: center;
        margin-top: 70px;
        animation: fadeUp 0.8s ease;
    }

    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(24px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .result-title {
        font-size: 44px;
        font-weight: bold;
        margin-bottom: 30px;
    }

    .big-temp {
        font-size: 86px;
        color: #62ffd5;
        font-weight: bold;
        animation: popTemp 0.7s ease;
    }

    @keyframes popTemp {
        from {
            opacity: 0;
            transform: scale(0.75);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    .satisfaction {
        font-size: 32px;
        margin-top: 20px;
    }

    .message {
        margin-top: 30px;
        color: #ccc;
        font-size: 20px;
        line-height: 1.6;
    }

    .person-tabs {
        display: flex;
        gap: 10px;
        margin-bottom: 35px;
    }

    .person-tabs div {
        padding: 10px 18px;
        background: #292b31;
        border-radius: 20px;
        color: #bbb;
    }

    .person-tabs .active {
        background: #62ffd5;
        color: #111;
        font-weight: bold;
    }

    .chart {
        width: 520px;
        height: 260px;
        margin: 20px auto 40px;
        display: flex;
        align-items: flex-end;
        justify-content: space-around;
        border-left: 3px solid #eee;
        border-bottom: 3px solid #eee;
        padding: 20px 20px 0;
        margin-bottom: 50px;
    }

    .bar-wrap {
        width: 120px;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        align-items: center;
    }

    .bar {
        width: 90px;
        min-height: 4px;
        background: #3f7cff;
        box-shadow: 0 0 18px rgba(63, 124, 255, 0.45);
    }

    .bar-label {
        margin-top: 12px;
        font-size: 18px;
        color: #fff;
        line-height: 1.4;
    }

    .ai-chart {
        width: 100%;
        max-width: 680px;   /* ← 추가 */
        height: 260px;
        margin: 20px auto;
    }

    .ai-chart svg {
        width: 100%;
        height: 100%;
        overflow: visible;
    }

    .axis {
        stroke: #ddd;
        stroke-width: 2;
    }

    .ai-line {
        fill: none;
        stroke: #00e5a8;
        stroke-width: 4;
        filter: drop-shadow(0 0 8px rgba(0, 229, 168, 0.8));
    }

    .ai-dot {
        fill: #00e5a8;
        stroke: none;
        stroke-width: 2;
    }

    .ai-dot.best {
        fill: #62ffd5;
        stroke: white;
        stroke-width: 3;
        filter: drop-shadow(0 0 10px #62ffd5);
    }

    .x-label {
        fill: white;
        font-size: 12px;
        text-anchor: middle;
        transform: translateY(-5px);
    }

    .warning-box {
        margin-top: 20px;
        padding: 15px;
        border-radius: 10px;
        background: rgba(255, 100, 100, 0.1);
        color: #ff6b6b;
        font-weight: bold;
        text-align: center;
        border: 1px solid rgba(255, 100, 100, 0.3);
    }

</style>
</head>

<body>
<div class="container">

    <div class="badge">집단 온도 추천 AI</div>

    {% if not result %}
    <h1>예측하기</h1>
    <div class="subtitle">간단한 정보를 가지고 집단의 최적 온도를 예측합니다.</div>

    <form method="post">

        {% set PEOPLE = 5 %}

        {% for i in range(PEOPLE) %}
        <div class="person-block {% if i != 0 %}hidden{% endif %}" id="person{{i}}">

            <div class="person-tabs">
                {% for j in range(PEOPLE) %}
                    <div class="{% if i == j %}active{% endif %}">
                        {{ j + 1 }}번째 사람
                    </div>
                {% endfor %}
            </div>

            <div class="step-label">STEP 1</div>

            <div class="question">
                <div class="question-title">성별은 무엇인가요?</div>
                <div class="options">
                    <input type="radio" id="male{{i}}" name="sex{{i}}" value="male" checked>
                    <label for="male{{i}}">남성</label>

                    <input type="radio" id="female{{i}}" name="sex{{i}}" value="female">
                    <label for="female{{i}}">여성</label>
                </div>
            </div>

            <div class="question">
                <div class="question-title">나이대는 어떻게 되나요?</div>
                <div class="options">
                    <input type="radio" id="teen{{i}}" name="age{{i}}" value="teen" checked>
                    <label for="teen{{i}}">청소년</label>

                    <input type="radio" id="adult{{i}}" name="age{{i}}" value="adult">
                    <label for="adult{{i}}">성인</label>

                    <input type="radio" id="senior{{i}}" name="age{{i}}" value="senior">
                    <label for="senior{{i}}">노년층</label>
                </div>
            </div>

            <div class="question">
                <div class="question-title">원하는 온도는 몇 도인가요?</div>
                <input class="temp-input" type="number" name="temp{{i}}" min="18" max="30" required placeholder="18~30 사이 입력">
            </div>

            <div class="step-label">STEP 2</div>

            <div class="question">
                <div class="question-title">옷차림은 어떻습니까?</div>
                <div class="options">
                    <input type="radio" id="thin{{i}}" name="clothes{{i}}" value="thin" checked>
                    <label for="thin{{i}}">얇음</label>

                    <input type="radio" id="normal{{i}}" name="clothes{{i}}" value="normal">
                    <label for="normal{{i}}">보통</label>

                    <input type="radio" id="thick{{i}}" name="clothes{{i}}" value="thick">
                    <label for="thick{{i}}">두꺼움</label>
                </div>
            </div>

            <div class="question">
                <div class="question-title">현재 느낌은 어떻습니까?</div>
                <div class="options">
                    <input type="radio" id="cold{{i}}" name="feels{{i}}" value="cold" checked>
                    <label for="cold{{i}}">춥다</label>

                    <input type="radio" id="ok{{i}}" name="feels{{i}}" value="ok">
                    <label for="ok{{i}}">괜찮다</label>

                    <input type="radio" id="hot{{i}}" name="feels{{i}}" value="hot">
                    <label for="hot{{i}}">덥다</label>
                </div>
            </div>

            <div class="question">
                <div class="question-title">활동량은 어떻습니까?</div>
                <div class="options">
                    <input type="radio" id="still{{i}}" name="activity{{i}}" value="still" checked>
                    <label for="still{{i}}">가만히 있음</label>

                    <input type="radio" id="move{{i}}" name="activity{{i}}" value="move">
                    <label for="move{{i}}">조금 움직임</label>
                </div>
            </div>

            <div class="question">
                <div class="question-title">현재 어디에 위치해 있습니까?</div>
                <div class="options">
                    <input type="radio" id="center{{i}}" name="position{{i}}" value="center" checked>
                    <label for="center{{i}}">중앙</label>

                    <input type="radio" id="window{{i}}" name="position{{i}}" value="window">
                    <label for="window{{i}}">창가</label>

                    <input type="radio" id="ac{{i}}" name="position{{i}}" value="ac">
                    <label for="ac{{i}}">에어컨 근처</label>
                </div>
            </div>

            <div class="nav">
                {% if i > 0 %}
                    <button type="button" onclick="showPerson({{i - 1}})">이전</button>
                {% else %}
                    <span></span>
                {% endif %}

                {% if i < 4 %}
                    <button type="button" onclick="showPerson({{i + 1}})">다음</button>
                {% else %}
                    <button type="submit">제출하기</button>
                {% endif %}
            </div>
        </div>
        {% endfor %}

    </form>
    {% endif %}

    {% if result %}
    <div class="result-box">
    <div class="result-title">온도 만족도 예측</div>

    <div class="big-temp" id="tempCounter">0°C</div>
    <div class="satisfaction">예상 만족도 {{ satisfaction }}%</div>

    <div style="
        width:320px;
        height:18px;
        background:#1f2430;
        border-radius:20px;
        margin:16px auto 0;
        overflow:hidden;
    ">
        <div style="
            width:{{ satisfaction }}%;
            height:100%;
            background:linear-gradient(90deg, #00e5a8, #62ffd5);
            box-shadow:0 0 14px rgba(98,255,213,0.5);
            transition:width 1s ease;
        ">
        </div>
    </div>

    <div style="
        margin-top:8px;
        color:#aaa;
        font-size:14px;
    ">
        AI 확신도 {{ satisfaction }}%
    </div>

    <div style="color:#888; font-size:14px; margin-top:6px;">
        (AI 예측 기반)
    </div>

    <div style="margin-top:8px; color:#aaa; font-size:15px;">
        현재 참여 {{ current }} / {{ target }}명
    </div>

    {% if satisfaction < 50 %}
    <div class="warning-box">
        ⚠️ 집단 선호 차이가 큽니다<br>
        온도 조정만으로 해결하기 어려운 상태입니다
    </div>
    {% endif %}

    <div style="margin-top:10px; color:#aaa; font-size:15px;">
        {{ short_reason }}
    </div>

    <div style="color:#aaa; font-size:13px; margin-top:4px;">
        상황에 따라 체감 온도는 달라질 수 있습니다
    </div>

    <div style="
        margin-top:20px;
        color:#aaa;
        font-size:15px;
        text-align:center;
    ">
        입력 요약: 춥다 {{ cold_percent }}% / 괜찮다 {{ ok_percent }}% / 덥다 {{ hot_percent }}%
    </div>

    <!-- ✅ 기존 그래프 -->
    <div class="chart">
        <div class="bar-wrap">
            <div class="bar" style="height: {{ cold_percent }}%;"></div>
            <div class="bar-label">춥다<br>{{ cold_percent }}%</div>
        </div>

        <div class="bar-wrap">
            <div class="bar" style="height: {{ ok_percent }}%;"></div>
            <div class="bar-label">괜찮다<br>{{ ok_percent }}%</div>
        </div>

        <div class="bar-wrap">
            <div class="bar" style="height: {{ hot_percent }}%;"></div>
            <div class="bar-label">덥다<br>{{ hot_percent }}%</div>
        </div>
    </div>

    <!-- 🔥 여기 추가 (중요) -->
    <h3 style="margin-top:20px; margin-bottom:5px;">온도별 만족도 변화 (AI 예측)</h3>
    <div style="color:#aaa; font-size:14px; margin-bottom:10px;">
        온도가 변할 때 예상 만족도가 어떻게 달라지는지 보여줍니다
    </div>

    <div class="ai-chart">
        <svg viewBox="0 0 700 260">
            <line class="axis" x1="50" y1="220" x2="660" y2="220"></line>
            <line class="axis" x1="50" y1="20" x2="50" y2="220"></line>

            <polyline
                class="ai-line"
                points="{{ chart_points }}">
            </polyline>

            {% for point in chart_dots %}
                <circle
                    class="ai-dot {% if point.temp == best_chart_temp %}best{% endif %}"
                    cx="{{ point.x }}"
                    cy="{{ point.y }}"
                    r="{% if point.temp == best_chart_temp %}7{% else %}5{% endif %}">
                </circle>

                {% if point.temp == best_chart_temp %}
                    <text x="{{ point.x }}" y="{{ point.y - 18 }}" fill="#62ffd5" font-size="18" text-anchor="middle">
                        ★
                    </text>
                {% endif %}

                {% if point.temp % 2 == 0 %}
                    <text class="x-label" x="{{ point.x }}" y="245">
                        {{ point.temp }}
                    </text>
                {% endif %}
            {% endfor %}
        </svg>
    </div>

    <div style="
        color:#aaa;
        font-size:13px;
        margin-top:8px;
        text-align:center;
    ">
        ★ 최종 추천 온도
    </div>

    <div style="margin-top:20px;">
        <strong>👥 전체 요약</strong><br><br>

        <div style="
            background:#1a1f2b;
            padding:14px;
            border-radius:10px;
            line-height:1.7;
            color:#ddd;
        ">
            춥다 {{ cold_percent }}% / 괜찮다 {{ ok_percent }}% / 덥다 {{ hot_percent }}%
        </div>

        <details style="margin-top:18px; color:#aaa;">
            <summary style="cursor:pointer; color:#62ffd5;">개인별 예상 결과 보기</summary>

            {% for r in person_results %}
            <div style="
                background:#1a1f2b;
                padding:10px;
                margin-top:8px;
                border-radius:8px;
                text-align:center;
            ">
                {{ r }}
            </div>
            {% endfor %}
        </details>
    </div>

    <!-- 기존 설명 -->
    <div class="message" style="max-width:620px; margin:28px auto 0;">
        <div style="font-size:18px; font-weight:bold; color:#fff; margin-bottom:10px;">
            결과 해석
        </div>

        <div style="font-size:17px; line-height:1.7; color:#ddd;">
            {{ message }}
        </div>

        <div style="margin-top:14px; font-size:16px; line-height:1.7; color:#62ffd5;">
            {{ advice }}
        </div>

        <div style="
            margin-top:20px;
            padding:14px 18px;
            background:#1a1f2b;
            border-radius:10px;
            color:#bbb;
            font-size:14px;
            line-height:1.6;
        ">
            <strong style="color:#fff;">분석 근거</strong><br>
            {{ reason }}

            <div style="margin-top:12px;">
                {% for point in analysis_points %}
                    <div style="margin-top:6px;">✔ {{ point }}</div>
                {% endfor %}
            </div>
        </div>
    </div>

    {% if code %}
    <div style="margin-top:35px;">
        <p style="margin-top:24px; color:#66ffd1; font-size:16px; font-weight:bold;">
            피드백을 반영하면 다음 추천 온도는 {{ next_temp }}°C입니다.
        </p>
        <h3>내 추천 온도 피드백</h3>

        {% if my_result and not is_host %}
        <form method="post" action="{{ url_for('feedback', code=code) }}">
            <div style="
                background:#1a1f2b;
                padding:15px;
                margin-bottom:12px;
                border-radius:10px;
                text-align:left;
            ">
                <strong>{{ my_name }}</strong><br>
                <span style="color:#aaa;">{{ my_result }}</span><br><br>

                <label>
                    <input type="radio" name="feedback" value="too_cold" required>
                    추웠어요
                </label>

                <label style="margin-left:15px;">
                    <input type="radio" name="feedback" value="good">
                    괜찮았어요
                </label>

                <label style="margin-left:15px;">
                    <input type="radio" name="feedback" value="too_hot">
                    더웠어요
                </label>
            </div>

            <button type="submit">피드백 저장하기</button>
        </form>
        {% else %}
        <p style="color:#aaa;">방장은 전체 결과만 확인할 수 있습니다.</p>
        {% endif %}

            <br><br>
                <a href="/"><button>다시 예측하기</button></a>

                <button onclick="copyResult()" style="margin-top:14px;">
                    결과 복사
                </button>

                <form method="post"
                    action="{{ url_for('close_room', code=code) }}"
                    style="margin-top:14px;"
                    onsubmit="return confirm('정말 방을 종료하시겠습니까?');">
                                    <button type="submit" style="background:#444;">
                        방 종료하기
                    </button>
                </form>
            </div>
            {% endif %}
        </div>
    {% endif %}
    <script>
    function showPerson(index) {
        const blocks = document.querySelectorAll('.person-block');
        blocks.forEach(block => block.classList.add('hidden'));
        document.getElementById('person' + index).classList.remove('hidden');
    }

    const targetTemp = {{ result }};
    const tempElement = document.getElementById("tempCounter");

    if (tempElement) {

        let current = 0;

        const interval = setInterval(() => {
            current++;

            tempElement.innerText = current + "°C";

            if (current >= targetTemp) {
                clearInterval(interval);
            }
        }, 40);
    }

    function copyResult() {
        const text =
    `우리 방 AI 추천 온도는 {{ result }}°C 입니다!
    예상 만족도: {{ satisfaction }}%
    AI 집단 온도 추천 시스템`;

        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                alert("결과가 복사되었습니다!");
            }).catch(() => {
                fallbackCopy(text);
            });
        } else {
            fallbackCopy(text);
        }
    }

    function fallbackCopy(text) {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();

        try {
            document.execCommand("copy");
            alert("결과가 복사되었습니다!");
        } catch (err) {
            alert("복사에 실패했습니다. 직접 선택해서 복사해주세요.");
        }

        document.body.removeChild(textarea);
    }
    </script>

</body>
</html>
"""

CREATE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>방 만들기</title>
</head>
<body style="background:#101114; color:white; font-family:Arial; text-align:center; padding-top:100px;">
    <h1>집단 온도 추천 AI</h1>
    <p>몇 명이 투표할지 정해주세요.</p>

    <form method="post">
        <input type="number" name="target_count" min="2" max="30" value="5" required>
        <button type="submit">방 만들기</button>
    </form>
</body>
</html>
"""

@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        target_count = int(request.form["target_count"])
        room_code = make_room_code()

        create_room(room_code, target_count)

        return redirect(url_for("host", code=room_code))

    return render_template_string(CREATE_HTML)

@app.route("/host/<code>")
def host(code):
    current, target = get_room_status(code)

    if current >= target:
        return redirect(url_for("result", code=code))

    room_url = f"http://192.168.219.111:5000/room/{code}"
    qr_image = generate_qr_code(room_url)

    return render_template_string("""
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="3">
    <title>방장 대기 화면</title>
    </head>
    <body style="background:#101114; color:white; font-family:Arial; text-align:center; padding-top:100px;">
        <h1>방이 생성되었습니다</h1>

        <p style="font-size:24px;">{{ current }}/{{ target }}명 참여 완료</p>

        <p style="color:#aaa;">아래 링크를 참여자들에게 공유하세요.</p>

        <input id="roomLink" value="{{ room_url }}"
        style="width:min(330px, 90vw); padding:12px; text-align:center; border-radius:6px; border:none;">

        <br><br>

        <p style="color:#aaa;">QR로 참여하기</p>

        <img src="data:image/png;base64,{{ qr_image }}" 
             style="width:200px; border-radius:10px; background:white; padding:10px;">

        <br><br>

        <button onclick="copyLink()" style="padding:12px 24px; border:none; border-radius:6px; background:#62ffd5;">
            링크 복사
        </button>

        <br><br>

        <a href="{{ url_for('result', code=code) }}">
            <button style="padding:14px 28px; font-size:18px; background:#2f6df6; color:white; border:none; border-radius:6px;">
                결과 확인하기
            </button>
        </a>

        <script>
        function copyLink() {
            const link = document.getElementById("roomLink");
            link.select();
            document.execCommand("copy");
            alert("링크가 복사되었습니다!");
        }
        </script>
    </body>
    </html>
    """, code=code, current=current, target=target, qr_image=qr_image, room_url=room_url)

@app.route("/room/<code>", methods=["GET", "POST"])
def room(code):

    if code not in rooms:
        return render_template_string("""
        <html>
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>

        <body style="
        background:#101114;
        color:white;
        text-align:center;
        padding-top:120px;
        font-family:sans-serif;
        ">

        <h1>존재하지 않는 방입니다</h1>

        <p style="color:#aaa;">
        방 코드가 잘못되었거나 이미 종료된 방입니다.
        </p>

        <a href="/">
            <button style="
            margin-top:20px;
            padding:14px 28px;
            border:none;
            border-radius:8px;
            background:#2f6df6;
            color:white;
            font-size:16px;
            cursor:pointer;
            ">
                새 방 만들기
            </button>
        </a>

        </body>
        </html>
        """)

    joined_key = f"joined_{code}"

    if joined_key in session:
        return redirect(url_for("result", code=code))

    if request.method == "POST":
        current, target = get_room_status(code)

        if current >= target:
            return render_template_string("""
            <html>
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>

            <body style="
            background:#101114;
            color:white;
            text-align:center;
            padding-top:120px;
            font-family:sans-serif;
            ">

            <h1>참여가 마감되었습니다</h1>

            <p style="color:#aaa;">
            이미 모든 참여자가 입력을 완료했습니다.
            </p>

            <a href="/result/{{ code }}">
                <button style="
                margin-top:20px;
                padding:14px 28px;
                border:none;
                border-radius:8px;
                background:#2f6df6;
                color:white;
                font-size:16px;
                cursor:pointer;
                ">
                    결과 보기
                </button>
            </a>

            </body>
            </html>
            """, code=code)
        name = request.form["name"].strip()
        existing_names = [
            user.get("name", "").strip()
            for user in get_room_votes(code)
        ]

        if name in existing_names:
            return render_template_string("""
            <html>
            <head><meta charset="UTF-8"></head>
            <body style="background:#101114; color:white; text-align:center; padding-top:120px;">
                <h1>이미 사용 중인 이름입니다</h1>
                <p style="color:#aaa;">같은 방에서는 같은 이름으로 중복 참여할 수 없습니다.</p>
                <a href="{{ url_for('room', code=code) }}">
                    <button style="padding:14px 28px; background:#2f6df6; color:white; border:none; border-radius:6px;">
                        다시 입력하기
                    </button>
                </a>
            </body>
            </html>
            """, code=code)
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

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>입력 화면</title>

    <style>
    body {
        background:#101114;
        color:white;
        font-family:Arial;
        text-align:center;
        padding-top:60px;
    }

    .container {
        width: min(420px, 92vw);
        margin:0 auto;
    }

    h1 {
        margin-bottom:10px;
    }

    .subtitle {
        color:#aaa;
        margin-bottom:25px;
    }

    select, input {
        width:100%;
        padding:12px;
        margin-bottom:15px;
        background:#292b31;
        border:none;
        color:white;
        border-radius:6px;
    }

    button {
        width:100%;
        padding:14px;
        background:#2f6df6;
        border:none;
        color:white;
        font-size:16px;
        border-radius:6px;
        cursor:pointer;
    }

    button {
        transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
    }

    button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(47, 109, 246, 0.35);
        background: #3f7cff;
    }

    button:active {
        transform: translateY(0);
    }

    .status {
        margin-bottom:20px;
        font-size:18px;
        color:#62ffd5;
    }
    </style>
    </head>

    <body>

    <div class="container">

        <h1>정보 입력</h1>
        <div class="subtitle">현재 상태를 입력해주세요</div>

        <div class="status">
            {{ current }}/{{ target }}명 참여 완료
        </div>

        <form method="post">
            <input type="text" name="name" placeholder="이름 또는 닉네임" required>

            <select name="sex">
                <option value="male">남성</option>
                <option value="female">여성</option>
            </select>

            <select name="age_group">
                <option value="teen">청소년</option>
                <option value="adult">성인</option>
                <option value="senior">노년층</option>
            </select>

            <input type="number" name="temp" min="18" max="30" placeholder="원하는 온도 (18~30)" required>

            <select name="clothes">
                <option value="thin">얇음</option>
                <option value="normal">보통</option>
                <option value="thick">두꺼움</option>
            </select>

            <select name="feels">
                <option value="cold">춥다</option>
                <option value="ok">괜찮다</option>
                <option value="hot">덥다</option>
            </select>

            <select name="activity">
                <option value="still">가만히 있음</option>
                <option value="move">조금 움직임</option>
            </select>

            <select name="position">
                <option value="center">중앙</option>
                <option value="window">창가</option>
                <option value="ac">에어컨 근처</option>
            </select>

            <button type="submit">입력 완료</button>

        </form>

    </div>

    </body>
    </html>
    """, code=code, current=current, target=target)

@app.route("/result/<code>")
def result(code):

    if code not in rooms:
        return render_template_string("""
        <html>
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>

        <body style="
        background:#101114;
        color:white;
        text-align:center;
        padding-top:120px;
        font-family:sans-serif;
        ">

        <h1>존재하지 않는 방입니다</h1>

        <p style="color:#aaa;">
        방 코드가 잘못되었거나 이미 종료된 방입니다.
        </p>

        <a href="/">
            <button style="
            margin-top:20px;
            padding:14px 28px;
            border:none;
            border-radius:8px;
            background:#2f6df6;
            color:white;
            font-size:16px;
            cursor:pointer;
            ">
                새 방 만들기
            </button>
        </a>

        </body>
        </html>
        """)

    current, target = get_room_status(code)

    if current < target:
        return render_template_string("""
        <html>
        <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="2">
        <title>결과 분석 중</title>

        <style>
            body {
                margin: 0;
                height: 100vh;
                background:
                    radial-gradient(circle at center, rgba(98,255,213,0.08), transparent 35%),
                    #08090c;
                color: white;
                font-family: Arial, sans-serif;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
            }

            .formula {
                position: absolute;
                color: rgba(255,255,255,0.10);
                font-size: 34px;
                font-family: Georgia, serif;
                filter: blur(0.3px);
            }

            .f1 { top: 8%; left: 8%; }
            .f2 { top: 12%; right: 12%; }
            .f3 { top: 36%; left: 6%; }
            .f4 { bottom: 14%; right: 10%; }
            .f5 { bottom: 10%; left: 14%; }

            .loader {
                width: 120px;
                height: 120px;
                border: 14px solid rgba(255,255,255,0.18);
                border-top: 14px solid #62ffd5;
                border-radius: 50%;
                margin: 35px auto;
                animation: spin 1.2s linear infinite;
                box-shadow: 0 0 35px rgba(98,255,213,0.35);
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            .title {
                color: #62ffd5;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 16px;
            }

            h1 {
                font-size: 42px;
                margin: 0;
            }

            .status {
                font-size: 24px;
                margin-top: 20px;
                color: #62ffd5;
                font-weight: bold;
            }

            .desc {
                max-width: 760px;
                margin: 30px auto 0;
                color: #d6d6d6;
                font-size: 18px;
                line-height: 1.8;
            }

            .desc strong {
                color: #62ffd5;
            }

            .small {
                margin-top: 18px;
                color: #aaa;
                font-size: 15px;
            }
        </style>
        </head>

        <body>
            <div class="formula f1">T = argmax Σ Sᵢ(T)</div>
            <div class="formula f2">P(good | x)</div>
            <div class="formula f3">Sᵢ = f(temp, clothes, activity)</div>
            <div class="formula f4">ŷ = hθ(x)</div>
            <div class="formula f5">x₁, x₂, ... , xₙ</div>

            <div>
                <div class="title">집단 온도 추천 AI</div>
                <h1>참여 데이터를 기다리는 중입니다</h1>

                <div class="loader"></div>

                <div class="status">{{ current }}/{{ target }}명 참여 완료</div>

                <div class="desc">
                    사용자의 체감 온도, 선호 온도, 옷차림, 활동량, 위치 데이터를 수집하고 있습니다.<br>
                    수집된 데이터를 기반으로 <strong>머신러닝 알고리즘</strong>이 집단이 가장 만족할 가능성이 높은 온도를 예측합니다.
                </div>

                <div class="small">
                    모든 사람이 입력을 완료하면 자동으로 결과 화면으로 이동합니다.
                </div>
            </div>
        </body>
        </html>
        """, current=current, target=target)

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

    next_temp = result

    if cold_count > hot_count:
        next_temp = min(result + 1, 30)
    elif hot_count > cold_count:
        next_temp = max(result - 1, 18)

    return render_template_string(
        HTML,
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
        return render_template_string("""
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="background:#101114; color:white; text-align:center; padding-top:120px;">
            <h1>피드백을 저장할 수 없습니다</h1>
            <p style="color:#aaa;">참여자 정보가 확인되지 않습니다.</p>
            <a href="/"><button>새 방 만들기</button></a>
        </body>
        </html>
        """)

    if is_feedback_already_saved(code, person_index):
        return render_template_string("""
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="background:#101114; color:white; text-align:center; padding-top:120px;">
            <h1>이미 피드백이 저장되었습니다</h1>
            <p style="color:#aaa;">같은 참여자는 한 번만 피드백을 남길 수 있습니다.</p>
            <a href="/"><button>새 방 만들기</button></a>
        </body>
        </html>
        """)

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
    
    return render_template_string("""
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>방 종료</title>
    </head>

    <body style="
    background:#101114;
    color:white;
    text-align:center;
    padding-top:120px;
    font-family:Arial;
    ">

    <h1>방이 종료되었습니다</h1>

    <p style="color:#aaa;">
    해당 방의 참여 정보가 초기화되었습니다.
    </p>

    <a href="/">
        <button style="
        margin-top:20px;
        padding:14px 28px;
        border:none;
        border-radius:8px;
        background:#2f6df6;
        color:white;
        font-size:16px;
        cursor:pointer;
        ">
            새 방 만들기
        </button>
    </a>

    </body>
    </html>
    """)

@app.route("/admin")
def admin():

    key = request.args.get("key")

    if key != ADMIN_KEY:
        return render_template_string("""
        <html>
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>접근 제한</title>
        </head>

        <body style="
        background:#101114;
        color:white;
        text-align:center;
        padding-top:120px;
        font-family:Arial;
        ">

        <h1>관리자 권한이 없습니다</h1>
        <p style="color:#aaa;">올바른 관리자 키가 필요합니다.</p>

        <a href="/">
            <button style="
            margin-top:20px;
            padding:14px 28px;
            border:none;
            border-radius:8px;
            background:#2f6df6;
            color:white;
            font-size:16px;
            cursor:pointer;
            ">
                메인으로 돌아가기
            </button>
        </a>

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

    return render_template_string("""
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="10">

    <title>관리자 페이지</title>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>

    body{
        background:#101114;
        color:white;
        font-family:Arial;
        padding:40px;
    }

    .card{
        background:#1a1f2b;
        padding:20px;
        border-radius:12px;
        margin-bottom:20px;
    }

    table{
        width:100%;
        border-collapse:collapse;
    }

    th, td{
        border-bottom:1px solid #333;
        padding:12px;
        text-align:center;
        font-size:14px;
    }

    th{
        color:#66ffd1;
    }

    h1{
        color:#66ffd1;
    }

    </style>
    </head>

    <body>

    <h1>관리자 통계 페이지</h1>

    <div class="card">
        <h2>AI 모델 성능</h2>

        <p style="
        font-size:30px;
        color:#66ffd1;
        font-weight:bold;
        margin-top:20px;
        ">
            {{ model_accuracy }}%
        </p>

        <p style="
        color:#aaa;
        margin-top:10px;
        ">
            현재 AI 예측 정확도
        </p>

        <div style="
        margin-top:16px;
        color:#66ffd1;
        font-size:14px;
        ">
            ✔ 최근 재학습 상태 정상
        </div>
    </div>

    <div class="card">
        <h2>AI 학습 상태</h2>

        <p style="font-size:22px; color:#66ffd1; font-weight:bold;">
            현재 학습 데이터: {{ ai_data_count }}개
        </p>

        <p style="color:#aaa; margin-top:10px;">
            다음 자동 재학습까지 {{ remain_for_train }}개 남음
        </p>

        <div style="
            margin-top:18px;
            width:100%;
            height:18px;
            background:#11151f;
            border-radius:20px;
            overflow:hidden;
        ">
            <div style="
                width:{{ ((ai_data_count % 10) * 10) }}%;
                height:100%;
                background:linear-gradient(90deg, #00e5a8, #66ffd1);
                transition:width 0.6s ease;
            ">
            </div>
        </div>

        <p style="margin-top:8px; color:#888; font-size:13px;">
            데이터가 10개 누적될 때마다 자동 재학습됩니다
        </p>
    </div>

    <div class="card">
        <h2>전체 피드백 수</h2>
        <h1>{{ total_count }}</h1>
    </div>

    <div class="card">
        <h2>피드백 분포</h2>

        {% for stat in feedback_stats %}
            <p>
                {{ stat[0] }} : {{ stat[1] }}개
                ({{ ((stat[1] / total_count) * 100) | round(1) }}%)
            </p>
        {% endfor %}

        <canvas id="feedbackChart"
                style="margin-top:20px;"></canvas>
    </div>

    <div class="card">
        <h2>추천 온도 분포</h2>

        {% for stat in temp_stats %}
            <p>{{ stat[0] }}°C : {{ stat[1] }}개</p>
        {% endfor %}

        <canvas id="tempChart" style="margin-top:20px;"></canvas>
    </div>

    <div class="card">
        <h2>시간대별 피드백 수</h2>

        {% for stat in hour_stats %}
            <p>{{ stat[0] }}시 : {{ stat[1] }}개</p>
        {% endfor %}

        <canvas id="hourChart" style="margin-top:20px;"></canvas>
    </div>

    <div class="card">
        <h2>최근 피드백</h2>

        <table>

        <tr>
            <th>방 코드</th>
            <th>성별</th>
            <th>연령</th>
            <th>희망 온도</th>
            <th>추천 온도</th>
            <th>피드백</th>
            <th>시간</th>
        </tr>

        {% for row in recent_logs %}

        <tr>
            <td>{{ row[0] }}</td>
            <td>{{ row[1] }}</td>
            <td>{{ row[2] }}</td>
            <td>{{ row[3] }}</td>
            <td>{{ row[4] }}</td>
            <td>{{ row[5] }}</td>
            <td>{{ row[6] }}</td>
        </tr>

        {% endfor %}

        </table>

        <script>

        const feedbackLabels = [
            {% for stat in feedback_stats %}
                "{{ stat[0] }}",
            {% endfor %}
        ];

        const feedbackCounts = [
            {% for stat in feedback_stats %}
                {{ stat[1] }},
            {% endfor %}
        ];

        const ctx = document.getElementById("feedbackChart");

        new Chart(ctx, {
            type: "bar",

            data: {
                labels: feedbackLabels,

                datasets: [{
                    label: "피드백 수",

                    data: feedbackCounts,

                    backgroundColor: [
                        "#66ffd1",
                        "#4da3ff",
                        "#ff6b6b"
                    ],

                    borderRadius: 8
                }]
            },

            options: {

                plugins: {
                    legend: {
                        labels: {
                            color: "white"
                        }
                    }
                },

                scales: {

                    x: {
                        ticks: {
                            color: "white"
                        },

                        grid: {
                            color: "#333"
                        }
                    },

                    y: {
                        beginAtZero: true,
                        suggestedMax: 5,

                        ticks: {
                            color: "white"
                        },

                        grid: {
                            color: "#333"
                        }
                    }
                }
            }
        });

        const tempLabels = [
            {% for stat in temp_stats %}
                "{{ stat[0] }}°C",
            {% endfor %}
        ];

        const tempCounts = [
            {% for stat in temp_stats %}
                {{ stat[1] }},
            {% endfor %}
        ];

        const tempCtx = document.getElementById("tempChart");

        new Chart(tempCtx, {
            type: "bar",

            data: {
                labels: tempLabels,

                datasets: [{
                    label: "추천 온도 수",
                    data: tempCounts,
                    backgroundColor: "#66ffd1",
                    borderRadius: 8
                }]
            },

            options: {
                plugins: {
                    legend: {
                        labels: {
                            color: "white"
                        }
                    }
                },

                scales: {
                    x: {
                        ticks: {
                            color: "white"
                        },
                        grid: {
                            color: "#333"
                        }
                    },

                    y: {
                        beginAtZero: true,
                        suggestedMax: 5,

                        ticks: {
                            color: "white"
                        },
                        grid: {
                            color: "#333"
                        }
                    }
                }
            }
        });

        const hourLabels = [
            {% for stat in hour_stats %}
                "{{ stat[0] }}시",
            {% endfor %}
        ];

        const hourCounts = [
            {% for stat in hour_stats %}
                {{ stat[1] }},
            {% endfor %}
        ];

        const hourCtx = document.getElementById("hourChart");

        new Chart(hourCtx, {
            type: "line",

            data: {
                labels: hourLabels,

                datasets: [{
                    label: "시간대별 피드백 수",
                    data: hourCounts,
                    borderColor: "#66ffd1",
                    backgroundColor: "rgba(102, 255, 209, 0.15)",
                    tension: 0.35,
                    fill: true,
                    pointRadius: 5,
                    pointBackgroundColor: "#66ffd1"
                }]
            },

            options: {
                plugins: {
                    legend: {
                        labels: {
                            color: "white"
                        }
                    }
                },

                scales: {
                    x: {
                        ticks: {
                            color: "white"
                        },
                        grid: {
                            color: "#333"
                        }
                    },

                    y: {
                        beginAtZero: true,
                        suggestedMax: 5,

                        ticks: {
                            color: "white"
                        },
                        grid: {
                            color: "#333"
                        }
                    }
                }
            }
        });

        </script>

    </div>

    </body>
    </html>
    """,
    total_count=total_count,
    feedback_stats=feedback_stats,
    temp_stats=temp_stats,
    hour_stats=hour_stats,
    recent_logs=recent_logs,
    ai_data_count=ai_data_count,
    remain_for_train=remain_for_train,
    model_accuracy=model_accuracy)

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

    return render_template_string(
        HTML,
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