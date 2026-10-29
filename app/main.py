import pandas as pd
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.metrics import set_model_version
from app.model_loader import get_model_version, load_model_from_registry
from app.schemas import SPECIES_LABELS, IrisFeatures, PredictResponse

app = FastAPI()

Instrumentator().instrument(app).expose(app)

VERSION = get_model_version()
MODEL = load_model_from_registry(VERSION)
set_model_version(VERSION)


@app.get("/health")
def health():
    return {"status": "ok", "model_version": VERSION}


@app.post("/predict", response_model=PredictResponse)
def predict(iris_features: IrisFeatures):
    X_test = pd.DataFrame([iris_features.model_dump()])

    class_id = int(MODEL.predict(X_test)[0])
    class_label = SPECIES_LABELS[class_id]

    return PredictResponse(species=class_label, species_id=class_id, model_version=VERSION)
