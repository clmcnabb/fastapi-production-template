import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ml.dummy_model import DummyModel


def main() -> None:
    out = Path("app/ml/dummy_model.pkl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as file:
        pickle.dump(DummyModel(), file)


if __name__ == "__main__":
    main()
