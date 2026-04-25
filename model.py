import joblib
import pandas as pd

model = joblib.load("temperature_model.pkl")
encoders = joblib.load("encoders.pkl")


def encode_user_for_temp(user, candidate_temp):
    return {
        "sex": encoders["sex"].transform([user["sex"]])[0],
        "age_group": encoders["age_group"].transform([user["age_group"]])[0],
        "preferred_temp": user["temp"],
        "candidate_temp": candidate_temp,
        "feels": encoders["feels"].transform([user["feels"]])[0],
        "clothes": encoders["clothes"].transform([user["clothes"]])[0],
        "activity": encoders["activity"].transform([user["activity"]])[0],
        "position": encoders["position"].transform([user["position"]])[0],
        "weight": user["weight"]
    }


def predict_with_ai(votes):
    best_temp = None
    best_score = -1
    best_predictions = None
    temp_scores = []  # ✅ 이게 빠져 있었음

    feedback_classes = list(encoders["feedback"].classes_)
    good_index = feedback_classes.index("good")

    for candidate_temp in range(18, 31):
        rows = []

        for user in votes:
            rows.append(encode_user_for_temp(user, candidate_temp))

        df = pd.DataFrame(rows)

        probabilities = model.predict_proba(df)

        good_scores = [prob[good_index] for prob in probabilities]
        avg_good_score = sum(good_scores) / len(good_scores)

        temp_scores.append(round(avg_good_score * 100, 2))  # ✅ 그래프용 점수 저장

        if avg_good_score > best_score:
            best_score = avg_good_score
            best_temp = candidate_temp
            best_predictions = model.predict(df)

    return best_temp, best_score, temp_scores, best_predictions