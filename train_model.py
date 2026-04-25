import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


df = pd.read_csv("temperature_data.csv")

print("===== feedback 분포 =====")
print(df["feedback"].value_counts())

encoders = {}

for col in ["sex", "age_group", "feels", "clothes", "activity", "position", "feedback"]:
    encoder = LabelEncoder()
    df[col] = encoder.fit_transform(df[col])
    encoders[col] = encoder

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

print()
print("===== 모델 평가 =====")
print("정확도:", round(accuracy_score(Y_test, pred) * 100, 2), "%")

print()
print("===== 상세 평가 =====")
print(classification_report(
    Y_test,
    pred,
    target_names=encoders["feedback"].classes_
))

print()
print("===== feature 중요도 =====")
importances = model.feature_importances_

for name, importance in sorted(zip(feature_columns, importances), key=lambda x: x[1], reverse=True):
    print(name, ":", round(importance, 4))

joblib.dump(model, "temperature_model.pkl")
joblib.dump(encoders, "encoders.pkl")

print()
print("모델 저장 완료!")