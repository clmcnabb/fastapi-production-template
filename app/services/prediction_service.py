from threading import Lock
from typing import Protocol, cast

from app.core.config import settings
from app.ml.model_loader import load_model


class PredictModel(Protocol):
    def predict(self, features_batch: list[list[float]]) -> list[float]: ...


_model_lock = Lock()
_model: PredictModel | None = None


def preload_model() -> None:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = cast(PredictModel, load_model(settings.model_path))


def predict(features: list[float]) -> float:
    preload_model()
    assert _model is not None
    prediction = _model.predict([features])
    return float(prediction[0])
