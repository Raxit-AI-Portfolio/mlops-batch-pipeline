from pydantic import BaseModel, Field

SPECIES_LABELS = {0: "setosa", 1: "versicolor", 2: "virginica"}


class IrisFeatures(BaseModel):
    sepal_length: float = Field(..., ge=0.0, le=10.0)
    sepal_width: float = Field(..., ge=0.0, le=10.0)
    petal_length: float = Field(..., ge=0.0, le=10.0)
    petal_width: float = Field(..., ge=0.0, le=10.0)


class PredictResponse(BaseModel):
    species: str
    species_id: int
    model_version: str
