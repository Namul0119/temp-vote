import qrcode
import base64
from io import BytesIO
from flask import Flask, render_template_string, request, redirect, url_for, session
from model import predict_with_ai, encoders
from rooms import create_room, add_vote, is_room_complete, get_room_votes, get_room_status
import random
import string

app = Flask(__name__)
app.secret_key = "temp-vote-secret-key"

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

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>집단 온도 추천 AI</title>

<style>
    body {
        margin: 0;
        background: #101114;
        color: white;
        font-family: Arial, sans-serif;
    }

    .container {
        width: 760px;
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

    <div class="big-temp">{{ result }}°C</div>
    <div class="satisfaction">예상 만족도 {{ satisfaction }}%</div>

    {% if satisfaction < 50 %}
    <div class="warning-box">
        ⚠️ 집단 선호 차이가 큽니다<br>
        온도만으로 해결하기 어려운 상태입니다
    </div>
    {% endif %}

    <div style="margin-top:18px; font-size:20px; color:#62ffd5; font-weight:bold;">
        → 이 환경에서는 {{ result }}°C가 가장 균형 잡힌 온도입니다
    </div>

    <div style="margin-top:8px; color:#aaa; font-size:16px;">
        AI 신뢰도: {{ satisfaction }}%
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
                    class="ai-dot {% if point.temp == result %}best{% endif %}"
                    cx="{{ point.x }}"
                    cy="{{ point.y }}"
                    r="{% if point.temp == result %}7{% else %}5{% endif %}">
                </circle>

                {% if point.temp == result %}
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
        ★ 가장 높은 점 = 최적 온도
    </div>

    <div style="margin-top:20px;">
    <strong>👤 개인별 예상 결과</strong><br><br>

    {% for r in person_results %}
    <div style="
        background:#1a1f2b;
        padding:10px;
        margin-bottom:8px;
        border-radius:8px;
        text-align:center;
    ">
        {{ r }}
    </div>
        {% endfor %}
    </div>

    <!-- 기존 설명 -->
    <div class="message">
        {{ message }}<br>
        {{ advice }}<br><br>
        <strong>분석 근거</strong><br>
        {{ reason }}
    </div>

    <br><br>
        <a href="/"><button>다시 예측하기</button></a>
    </div>
    {% endif %}
</div>

<script>
function showPerson(index) {
    const blocks = document.querySelectorAll('.person-block');
    blocks.forEach(block => block.classList.add('hidden'));
    document.getElementById('person' + index).classList.remove('hidden');
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
    <meta http-equiv="refresh" content="3">
    <title>방장 대기 화면</title>
    </head>
    <body style="background:#101114; color:white; font-family:Arial; text-align:center; padding-top:100px;">
        <h1>방이 생성되었습니다</h1>

        <p style="font-size:24px;">{{ current }}/{{ target }}명 참여 완료</p>

        <p style="color:#aaa;">아래 링크를 참여자들에게 공유하세요.</p>

        <input id="roomLink" value="{{ room_url }}"
        style="width:330px; padding:12px; text-align:center; border-radius:6px; border:none;">

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

    joined_key = f"joined_{code}"

    if joined_key in session:
        return render_template_string("""
        <html>
        <head>
        <meta charset="UTF-8">
        <title>이미 입력 완료</title>
        </head>
        <body style="background:#101114; color:white; font-family:Arial; text-align:center; padding-top:120px;">
            <h1>이미 입력을 완료했습니다</h1>
            <p style="color:#aaa;">같은 방에는 한 번만 참여할 수 있습니다.</p>

            <br>

            <a href="{{ url_for('result', code=code) }}">
                <button style="padding:14px 28px; font-size:18px; background:#2f6df6; color:white; border:none; border-radius:6px;">
                    결과 확인하기
                </button>
            </a>
        </body>
        </html>
        """, code=code)

    if request.method == "POST":
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

        vote = {
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

        if is_room_complete(code):
            return redirect(url_for("result", code=code))

    current, target = get_room_status(code)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
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
        width:420px;
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
    current, target = get_room_status(code)

    if current < target:
        return render_template_string("""
        <html>
        <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="2">
        <title>결과 대기 중</title>
        </head>
        <body style="background:#101114; color:white; font-family:Arial; text-align:center; padding-top:120px;">
            <h1>아직 결과를 계산할 수 없습니다</h1>
            <p style="font-size:24px;">{{ current }}/{{ target }}명 참여 완료</p>
            <p style="color:#aaa;">모든 사람이 입력을 완료하면 자동으로 결과가 표시됩니다.</p>
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
        if fb == "too_cold":
            msg = f"{i+1}번 사람 → 추울 가능성 높음"
        elif fb == "too_hot":
            msg = f"{i+1}번 사람 → 더울 가능성 높음"
        else:
            msg = f"{i+1}번 사람 → 만족 가능성 높음"
        person_results.append(msg)

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

    if expected_satisfaction < 0.5:
        message = "사용자들의 선호 차이가 커서 모두가 만족하기 어려운 상태입니다."
        advice = "온도 조정보다 자리 이동, 담요, 바람 방향 조정 같은 보조 조치가 필요할 수 있습니다."
    elif expected_satisfaction < 0.7:
        message = "어느 정도 타협 가능한 온도이지만 일부 사용자는 불편할 수 있습니다."
        advice = "현재 추천 온도를 기준으로 0.5~1도 정도 미세 조정해보는 것이 좋습니다."
    else:
        message = "현재 입력 기준으로 비교적 많은 사용자가 만족할 가능성이 높습니다."
        advice = "추천 온도를 적용해도 무리가 적은 상태입니다."

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
        chart_dots=chart_dots
    )

@app.route("/")
def home():
    return redirect(url_for("create"))

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
        chart_dots=chart_dots
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)