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
    preferred_temp = user["preferred_temp"]
    diff = candidate_temp - preferred_temp

    if diff <= -2:
        return "too_cold"
    elif diff >= 2:
        return "too_hot"
    else:
        return "good"


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