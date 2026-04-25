from model import predict_with_ai
import csv
import os
from datetime import datetime

def get_clothes_weight(clothes):
    if clothes == "thin":
        return 1.2
    elif clothes == "thick":
        return 0.8
    else:
        return 1.0


def calculate_discomfort(user, candidate):
    wanted = user["temp"]
    weight = user["weight"]
    feels = user["feels"]

    diff = candidate - wanted

    if diff < 0:
        # 더 추워지는 경우 (더 민감)
        discomfort = abs(diff) * 1.8
    else:
        # 더 더워지는 경우
        discomfort = abs(diff) * 1.0

    # 현재 상태 반영
    if feels == "cold":
        discomfort *= 1.3
    elif feels == "hot":
        discomfort *= 1.1

    return discomfort * weight


def find_best_temperature(votes):
    best_temp = None
    best_score = float("inf")

    for candidate in range(18, 31):
        total_discomfort = 0

        for user in votes:
            d = calculate_discomfort(user, candidate)

            # 한 사람의 고통이 너무 크면 강하게 벌점
            if d > 8:
                d *= 2.5

            total_discomfort += d

        print(candidate, "도일 때 총 불만:", total_discomfort)

        if total_discomfort < best_score:
            best_score = total_discomfort
            best_temp = candidate

    return best_temp, best_score

def get_activity_weight(activity):
    if activity == "move":
        return 1.2
    else:
        return 1.0


def get_position_weight(position):
    if position == "ac":
        return 1.3
    elif position == "window":
        return 1.1
    else:
        return 1.0

def print_result_summary(votes, best_temp, best_score):
    temps = [user["temp"] for user in votes]

    avg_temp = sum(temps) / len(temps)
    min_temp = min(temps)
    max_temp = max(temps)

    cold_count = sum(1 for user in votes if user["feels"] == "cold")
    hot_count = sum(1 for user in votes if user["feels"] == "hot")
    ok_count = sum(1 for user in votes if user["feels"] == "ok")

    print()
    print("===== 결과 요약 =====")
    print("추천 온도:", best_temp)
    if best_score is not None:
        print("최소 총 불만:", best_score)
    else:
        print("AI 예측 기반 추천입니다.")
    print("입력 평균 온도:", round(avg_temp, 1))
    print("가장 낮은 선호 온도:", min_temp)
    print("가장 높은 선호 온도:", max_temp)
    print("춥다고 느낀 사람:", cold_count, "명")
    print("덥다고 느낀 사람:", hot_count, "명")
    print("괜찮다고 느낀 사람:", ok_count, "명")


def print_recommendation_reason(votes, best_temp):
    cold_count = sum(1 for user in votes if user["feels"] == "cold")
    hot_count = sum(1 for user in votes if user["feels"] == "hot")

    ac_count = sum(1 for user in votes if user["position"] == "ac")
    thin_count = sum(1 for user in votes if user["clothes"] == "thin")
    thick_count = sum(1 for user in votes if user["clothes"] == "thick")

    avg_temp = sum(user["temp"] for user in votes) / len(votes)

    print()
    print("===== 추천 이유 =====")

    if best_temp > avg_temp:
        print("- 추천 온도는 평균 선호 온도보다 높습니다.")
        print("- 전체적으로 추위를 줄이는 방향으로 보정되었습니다.")
    elif best_temp < avg_temp:
        print("- 추천 온도는 평균 선호 온도보다 낮습니다.")
        print("- 전체적으로 더위를 줄이는 방향으로 보정되었습니다.")
    else:
        print("- 추천 온도는 평균 선호 온도와 비슷합니다.")

    if hot_count > cold_count and hot_count > ok_count:
        print("- 덥다고 느낀 사람이 가장 많아 온도를 낮추는 방향으로 반영했습니다.")
    elif cold_count > hot_count and cold_count > ok_count:
        print("- 춥다고 느낀 사람이 가장 많아 온도를 높이는 방향으로 반영했습니다.")
    else:
        print("- 사용자들의 체감 온도가 비교적 균형 잡혀 있어 평균 기반으로 조정했습니다.")

    if ac_count > 0:
        print(f"- 에어컨 가까운 자리에 앉은 사람이 {ac_count}명 있어 위치 가중치를 반영했습니다.")

    if thin_count > 0:
        print(f"- 얇게 입은 사람이 {thin_count}명 있어 추위 민감도를 반영했습니다.")

    if thick_count > 0:
        print(f"- 두껍게 입은 사람이 {thick_count}명 있어 더위 민감도를 일부 완화했습니다.")

    print("- 학습된 모델이 사용자 조건을 바탕으로 추천 온도를 예측했습니다.")


def save_result_to_csv(votes, best_temp, best_score, feedback):
    file_exists = os.path.exists("temperature_data.csv")

    with open("temperature_data.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "sex",
                "age_group",
                "temp",
                "feels",
                "clothes",
                "activity",
                "position",
                "weight",
                "best_temp",
                "feedback"
            ])

        for user in votes:
            writer.writerow([
                user["sex"],
                user["age_group"],
                user["temp"],
                user["feels"],
                user["clothes"],
                user["activity"],
                user["position"],
                user["weight"],
                best_temp,
                feedback
            ])

def input_choice(prompt, choices):
    while True:
        value = input(prompt).strip()

        if value in choices:
            return value

        print("잘못된 입력입니다.")
        print("가능한 값:", ", ".join(choices))


def input_temperature(prompt):
    while True:
        value = input(prompt).strip()

        try:
            temp = int(value)
            if 18 <= temp <= 30:
                return temp
            print("온도는 18~30 사이로 입력해주세요.")
        except ValueError:
            print("숫자로 입력해주세요.")

votes = []

for i in range(3):
    sex = input_choice("성별 (male / female): ", ["male", "female"])
    age_group = input_choice("나이대 (teen / adult / senior): ", ["teen", "adult", "senior"])
    temp = input_temperature("원하는 온도 입력 (18~30): ")
    clothes = input_choice("옷차림 (thin / normal / thick): ", ["thin", "normal", "thick"])
    feels = input_choice("지금 느낌 (hot / cold / ok): ", ["hot", "cold", "ok"])
    activity = input_choice("활동량 (still / move): ", ["still", "move"])
    position = input_choice("위치 (center / window / ac): ", ["center", "window", "ac"])

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

best_temp, expected_satisfaction = predict_with_ai(votes)
best_score = None

print_result_summary(votes, best_temp, best_score)
print("예상 만족도:", round(expected_satisfaction * 100, 1), "%")
if expected_satisfaction < 0.5:
    print("주의: 사용자들의 선호 차이가 커서 모두가 만족하기 어려운 상황입니다.")
    print("온도 조정보다 자리 이동, 담요, 바람 방향 조정 같은 보조 조치가 필요할 수 있습니다.")
elif expected_satisfaction < 0.7:
    print("부분 만족 예상: 어느 정도 타협 가능한 온도이지만 일부 사용자는 불편할 수 있습니다.")
else:
    print("높은 만족 예상: 현재 입력 기준으로 비교적 많은 사용자가 만족할 가능성이 높습니다.")
print_recommendation_reason(votes, best_temp)

feedback = input("추천 온도는 어땠나요? (too_cold / good / too_hot): ")

save_result_to_csv(votes, best_temp, best_score, feedback)

print("결과가 temperature_data.csv에 저장되었습니다.")