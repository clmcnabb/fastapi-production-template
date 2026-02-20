import pickle
from pathlib import Path

_model: object | None = None


def load_model(path: str) -> object:
    global _model
    if _model is None:
        model_path = Path(path)
        with model_path.open("rb") as file:
            _model = pickle.load(file)
    return _model
