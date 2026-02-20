from fastapi import APIRouter

from app.schemas.predict import PredictRequest, PredictResponse
from app.services.prediction_service import predict

router = APIRouter()


@router.post("/", response_model=PredictResponse)
def run_prediction(payload: PredictRequest) -> PredictResponse:
    value = predict(payload.features)
    return PredictResponse(prediction=value)
