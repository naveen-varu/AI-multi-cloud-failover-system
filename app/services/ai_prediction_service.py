from ml.predict import FailurePredictor


class AIPredictionService:

    _predictor = FailurePredictor()

    @staticmethod
    def predict_metric(metric):
        return AIPredictionService._predictor.predict(
            cpu_usage=metric.cpu_usage,
            memory_usage=metric.memory_usage,
            disk_usage=metric.disk_usage,
            response_time=metric.response_time,
        )