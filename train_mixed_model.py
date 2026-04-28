import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


fake_df = pd.read_csv("temperature_data.csv")
real_df = pd.read_csv("real_temperature_data.csv")

real_df = real_df.rename(columns={
    "temp": "preferred_temp",
    "recommended_temp": "candidate_temp"
})

feature_columns = [
    "sex",
    "age_group",
    "preferred_temp",
    "candidate_temp",
    "feels",
    "clothes",
    "activity",
    "position",
    "weight"
]

real_df = real_df[feature_columns + ["feedback"]]
fake_df = fake_df[feature_columns + ["feedback"]]

# 실제 데이터 영향력을 조금 키움
real_df = pd.concat([real_df] * 10, ignore_index=True)

df = pd.concat([fake_df, real_df], ignore_index=True)

print("===== 전체 데이터 개수 =====")
print(len(df))

print("\n===== feedback 분포 =====")
print(df["feedback"].value_counts())

encoders = {}

for col in ["sex", "age_group", "feels", "clothes", "activity", "position", "feedback"]:
    encoder = LabelEncoder()
    df[col] = encoder.fit_transform(df[col])
    encoders[col] = encoder

X = df[feature_columns]
Y = df["feedback"]

X_train, X_test, Y_train, Y_test = train_test_split(
    X,
    Y,
    test_size=0.2,
    random_state=42,
    stratify=Y
)

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    random_state=42,
    class_weight="balanced"
)

model.fit(X_train, Y_train)

pred = model.predict(X_test)

print("\n===== 모델 평가 =====")
print("정확도:", round(accuracy_score(Y_test, pred) * 100, 2), "%")

print("\n===== 상세 평가 =====")
print(classification_report(
    Y_test,
    pred,
    target_names=encoders["feedback"].classes_
))

print("\n===== feature 중요도 =====")
for name, importance in sorted(zip(feature_columns, model.feature_importances_), key=lambda x: x[1], reverse=True):
    print(name, ":", round(importance, 4))

joblib.dump(model, "temperature_model.pkl")
joblib.dump(encoders, "encoders.pkl")

print("\n실제 피드백 반영 모델 저장 완료!")