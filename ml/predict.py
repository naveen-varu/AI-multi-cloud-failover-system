import os

import joblib
import pandas as pd


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "artifacts",
    "failure_prediction_model.pkl",
)


class FailurePredictor:

    def __init__(self):
        self.model = joblib.load(MODEL_PATH)

    def predict(
        self,
        cpu_usage,
        memory_usage,
        disk_usage,
        response_time,
    ):
        data = pd.DataFrame(
            [
                {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "disk_usage": disk_usage,
                    "response_time": response_time,
                }
            ]
        )

        prediction = self.model.predict(data)

        return prediction[0]


if __name__ == "__main__":
    predictor = FailurePredictor()

    result = predictor.predict(
        cpu_usage=95,
        memory_usage=92,
        disk_usage=50,
        response_time=2500,
    )

    print(f"Predicted status: {result}")