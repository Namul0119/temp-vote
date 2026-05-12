from datetime import datetime
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
        "weight": user["weight"],
        "hour": datetime.now().hour
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

    if best_temp is not None:
        avg_input_temp = sum(user["temp"] for user in votes) / len(votes)

        cold_count = sum(1 for user in votes if user["feels"] == "cold")
        hot_count = sum(1 for user in votes if user["feels"] == "hot")

        # 1차: 평균 기준 ±2도 안으로 제한
        min_allowed = round(avg_input_temp - 2)
        max_allowed = round(avg_input_temp + 2)
        best_temp = max(min_allowed, min(best_temp, max_allowed))

        # 2차: 현재 체감 방향 반영
        if hot_count > cold_count:
            # 더운 사람이 많으면 평균보다 최소 1도 낮게
            best_temp = min(best_temp, round(avg_input_temp - 1))

        elif cold_count > hot_count:
            best_temp = max(best_temp, round(avg_input_temp + 1))

        # 보정된 최종 추천 온도 기준으로 예측값과 만족도 다시 계산
        rows = []

        for user in votes:
            rows.append(encode_user_for_temp(user, best_temp))

        final_df = pd.DataFrame(rows)

        final_probabilities = model.predict_proba(final_df)
        final_good_scores = [prob[good_index] for prob in final_probabilities]

        avg_good_score = sum(final_good_scores) / len(final_good_scores)
        worst_good_score = min(final_good_scores)

        best_score = (avg_good_score * 0.7) + (worst_good_score * 0.3)
        best_predictions = model.predict(final_df)

    return best_temp, best_score, temp_scores, best_predictions