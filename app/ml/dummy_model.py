class DummyModel:
    def predict(self, features_batch: list[list[float]]) -> list[float]:
        outputs: list[float] = []
        for features in features_batch:
            outputs.append(sum(features) / len(features))
        return outputs
