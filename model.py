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
    temp_scores = []

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
        worst_good_score = min(good_scores)

        final_score = (avg_good_score * 0.7) + (worst_good_score * 0.3)

        temp_scores.append(round(final_score * 100, 2))

        if final_score > best_score:
            best_score = final_score
            best_temp = candidate_temp
            best_predictions = model.predict(df)

    return best_temp, best_score, temp_scores, best_predictions