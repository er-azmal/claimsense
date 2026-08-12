import cv2
import numpy as np
import pandas as pd
from PIL import Image
from app import model

# ---------- helpers (straight from your app_secure.py) ----------

def preprocess(image: Image.Image, size: int):
    img = image.convert("RGB")
    img = np.asarray(img)
    img = cv2.resize(img, (size, size))
    return img / 255.0

def yolo_detect(image: Image.Image, yolo, model_name: str):
    """Runs one YOLO model, returns (primary_class, detections_list)."""
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    results = yolo(img_cv)[0]

    detections = []
    for box in results.boxes:
        detections.append({
            "class_name": yolo.names[int(box.cls)],
            "confidence": round(float(box.conf), 3),
        })

    if detections:
        primary = detections[0]["class_name"]
    else:
        primary = ("Not Deployed" if model_name == "airbag"
                   else "No Damage" if model_name == "damage"
                   else "Unknown")
    return primary, detections

PART_LABELS = ['Air intake', 'Console', 'Dashboard', 'Fog light',
               'Gear stick', 'Headlight', 'Steering wheel', 'Tail light']
ANGLE_LABEL_MAP = {'0': 0, '130': 1, '180': 2, '230': 3,
                   '270': 4, '320': 5, '40': 6, '90': 7}
ANGLE_MAPPING = {"right": 0, "front_left": 130, "left": 180, "rear_left": 230,
                 "rear": 270, "rear_right": 320, "front_right": 40, "front": 90}
INTERNAL_PARTS = ['Console', 'Dashboard', 'Gear stick', 'Steering wheel', 'Air intake']

def classify_angle_and_part(img_angle: Image.Image, img_part: Image.Image):
    x_angle = np.expand_dims(preprocess(img_angle, 331), axis=0)
    x_part  = np.expand_dims(preprocess(img_part, 224), axis=0)

    pred_angle = model.model_angle.predict([x_angle, x_angle], verbose=0)  # dual input!
    pred_part  = model.model_part.predict(x_part, verbose=0)

    part_name = PART_LABELS[int(np.argmax(pred_part))]
    conf_part = float(np.max(pred_part)) * 100

    idx_to_angle = {v: k for k, v in ANGLE_LABEL_MAP.items()}
    angle_value = int(idx_to_angle[int(np.argmax(pred_angle))])
    angle_name = {v: k for k, v in ANGLE_MAPPING.items()}[angle_value]
    conf_angle = float(np.max(pred_angle)) * 100

    return part_name, angle_name, angle_value, conf_part, conf_angle

# ---------- the full pipeline: 5 images in, verdict out ----------

def run_full_analysis(paths: dict) -> dict:
    """paths = {'airbag': ..., 'damage': ..., 'carpart': ..., 'angle': ..., 'part': ...}"""

    # STAGE 1a — three YOLO detections
    airbag_status, airbag_dets = yolo_detect(Image.open(paths["airbag"]),
                                             model.yolo_models["airbag"], "airbag")
    damage_type, damage_dets   = yolo_detect(Image.open(paths["damage"]),
                                             model.yolo_models["damage"], "damage")
    carpart_name, carpart_dets = yolo_detect(Image.open(paths["carpart"]),
                                             model.yolo_models["carpart"], "carpart")

    # STAGE 1b — two Keras classifications
    part_name, angle_name, angle_value, conf_part, conf_angle = classify_angle_and_part(
        Image.open(paths["angle"]), Image.open(paths["part"]))

    # STAGE 2 — assemble features exactly like training
    view_type = "internal" if part_name in INTERNAL_PARTS else "external"
    airbag_mapped = "deployed" if "deployed" in airbag_status.lower() else "not_applicable"

    data = pd.DataFrame({
        "view_type": [view_type],
        "angle":     [angle_name],
        "part":      [carpart_name],
        "damage":    [damage_type],
        "airbag":    [airbag_mapped],
    })
    for col in data.columns:
        if col in model.feature_encoders:
            try:
                data[col] = model.feature_encoders[col].transform(data[col])
            except ValueError:          # unseen label → fallback
                data[col] = 0

    y_pred = model.xgb_model.predict(data)
    severity = model.severity_encoder.inverse_transform(y_pred)[0]
    confidence = float(np.max(model.xgb_model.predict_proba(data))) * 100

    return {
        "severity": severity,
        "severity_confidence": round(confidence, 1),
        "view_type": view_type,
        "damaged_part": carpart_name,
        "damage_type": damage_type,
        "airbag_status": airbag_status,
        "camera_angle": {"name": angle_name, "degrees": angle_value},
        "part_classification": {"name": part_name, "confidence": round(conf_part, 1)},
        "detections": {"airbag": airbag_dets, "damage": damage_dets, "carpart": carpart_dets},
    }
