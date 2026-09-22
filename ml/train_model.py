import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


def classify_health(cpu, memory, disk, response):
    """
    Generate the training label using the existing
    monitoring thresholds.
    """

    if (
        cpu >= 90
        or memory >= 90
        or disk >= 95
        or response >= 2000
    ):
        return "FAILED"

    if (
        cpu >= 70
        or memory >= 75
        or disk >= 80
        or response >= 500
    ):
        return "WARNING"

    return "ACTIVE"


# Reproducible random data
np.random.seed(42)

samples = 1000

cpu = np.random.uniform(10, 100, samples)
memory = np.random.uniform(10, 100, samples)
disk = np.random.uniform(10, 100, samples)
response = np.random.uniform(50, 3000, samples)

data = pd.DataFrame(
    {
        "cpu_usage": cpu,
        "memory_usage": memory,
        "disk_usage": disk,
        "response_time": response,
    }
)

data["status"] = data.apply(
    lambda row: classify_health(
        row["cpu_usage"],
        row["memory_usage"],
        row["disk_usage"],
        row["response_time"],
    ),
    axis=1,
)


X = data[
    [
        "cpu_usage",
        "memory_usage",
        "disk_usage",
        "response_time",
    ]
]

y = data["status"]


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
)


model.fit(X_train, y_train)


predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print(f"Training samples: {len(X_train)}")
print(f"Testing samples: {len(X_test)}")
print(f"Model accuracy: {accuracy:.2%}")

print("\nClassification report:")
print(
    classification_report(
        y_test,
        predictions,
        zero_division=0,
    )
)


artifacts_dir = os.path.join(
    os.path.dirname(__file__),
    "artifacts",
)

os.makedirs(artifacts_dir, exist_ok=True)


model_path = os.path.join(
    artifacts_dir,
    "failure_prediction_model.pkl",
)

joblib.dump(model, model_path)

print(f"\nModel saved to: {model_path}")