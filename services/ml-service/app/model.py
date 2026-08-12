import pickle
import numpy as np
import xgboost as xgb
from keras.models import load_model
from ultralytics import YOLO

model_angle = None
model_part = None
yolo_models = {}
xgb_model = None
feature_encoders = None
severity_encoder = None

def load_models():
    global model_angle, model_part, yolo_models, xgb_model, feature_encoders, severity_encoder
    model_angle = load_model("models/model.keras")
    model_part = load_model("models/CarPartINExmodel.h5")
    yolo_models = {
        "airbag":  YOLO("models/airbag.pt"),
        "damage":  YOLO("models/damage.pt"),
        "carpart": YOLO("models/carpart.pt"),
    }
    xgb_model = xgb.XGBClassifier(
        n_estimators=200, learning_rate=0.1, max_depth=6,
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )
    xgb_model.load_model("models/xgb_model.json")
    with open("models/feature_encoders.pkl", "rb") as f:
        feature_encoders = pickle.load(f)
    with open("models/severity_encoder.pkl", "rb") as f:
        severity_encoder = pickle.load(f)
    print("✅ All 6 models loaded")
