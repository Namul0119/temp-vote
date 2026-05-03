import csv
import random
import os


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


def generate_person():
    sex = random.choice(["male", "female"])
    age_group = random.choice(["teen", "adult", "senior"])
    clothes = random.choice(["thin", "normal", "thick"])
    activity = random.choice(["still", "move"])
    position = random.choice(["center", "window", "ac"])

    preferred_temp = random.randint(21, 26)

    if sex == "male":
        preferred_temp -= random.choice([0, 1])
    elif sex == "female":
        preferred_temp += random.choice([0, 1])

    if age_group == "senior":
        preferred_temp += 1

    if clothes == "thin":
        preferred_temp += 1
    elif clothes == "thick":
        preferred_temp -= 1

    if activity == "move":
        preferred_temp -= 1

    if position == "ac":
        preferred_temp += 1
    elif position == "window":
        preferred_temp += random.choice([0, 1])

    preferred_temp = max(18, min(30, preferred_temp))

    if preferred_temp <= 22:
        feels = random.choice(["hot", "ok"])
    elif preferred_temp >= 25:
        feels = random.choice(["cold", "ok"])
    else:
        feels = random.choice(["cold", "ok", "hot"])

    weight = (
        get_clothes_weight(clothes)
        * get_activity_weight(activity)
        * get_position_weight(position)
    )

    return {
        "sex": sex,
        "age_group": age_group,
        "preferred_temp": preferred_temp,
        "feels": feels,
        "clothes": clothes,
        "activity": activity,
        "position": position,
        "weight": round(weight, 2)
    }


def generate_feedback(user, candidate_temp):
    preferred = user["preferred_temp"]
    feels = user["feels"]
    weight = user["weight"]

    diff = candidate_temp - preferred

    # 기본 불쾌도
    discomfort = abs(diff)

    # 추위/더위 민감도 차이
    if diff < 0:
        discomfort *= 1.5  # 추위 더 민감
    else:
        discomfort *= 1.0

    # 현재 상태 반영
    if feels == "cold":
        discomfort *= 1.3
    elif feels == "hot":
        discomfort *= 1.1

    # 개인 특성 반영
    discomfort *= weight

    # 확률 기반 판단 (핵심)
    if discomfort < 1.5:
        return random.choices(["good", "too_hot", "too_cold"], [0.7, 0.15, 0.15])[0]
    elif discomfort < 3:
        return random.choices(["good", "too_hot", "too_cold"], [0.4, 0.3, 0.3])[0]
    else:
        if diff > 0:
            return "too_hot"
        else:
            return "too_cold"


def generate_room_data(room_count=100, people_per_room=5):
    file_exists = os.path.exists("temperature_data.csv")

    with open("temperature_data.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "sex",
                "age_group",
                "preferred_temp",
                "candidate_temp",
                "feels",
                "clothes",
                "activity",
                "position",
                "weight",
                "feedback"
            ])

        for _ in range(room_count):
            users = [generate_person() for _ in range(people_per_room)]

            for user in users:
                for candidate_temp in range(18, 31):
                    feedback = generate_feedback(user, candidate_temp)

                    writer.writerow([
                        user["sex"],
                        user["age_group"],
                        user["preferred_temp"],
                        candidate_temp,
                        user["feels"],
                        user["clothes"],
                        user["activity"],
                        user["position"],
                        user["weight"],
                        feedback
                    ])


generate_room_data(room_count=100, people_per_room=5)

print("가짜 데이터 생성 완료!")
print("temperature_data.csv에 저장되었습니다.")