from fastapi import FastAPI, UploadFile, File
from app import model
from app.pipeline import run_full_analysis
from app.estimator import estimate_cost
import shutil, uuid, os

app = FastAPI(title="ClaimSense ML Service")

@app.on_event("startup")
def startup():
    model.load_models()

@app.get("/health")
def health():
    return {"status": "ok", "models_loaded": model.xgb_model is not None}

@app.post("/assess")
async def assess(
    airbag: UploadFile = File(...),
    damage: UploadFile = File(...),
    carpart: UploadFile = File(...),
    angle: UploadFile = File(...),
    part: UploadFile = File(...),
):
    uid = uuid.uuid4().hex[:8]
    paths = {}
    try:
        for name, f in [("airbag", airbag), ("damage", damage),
                        ("carpart", carpart), ("angle", angle), ("part", part)]:
            p = f"temp_{uid}_{name}.jpg"
            with open(p, "wb") as out:
                shutil.copyfileobj(f.file, out)
            paths[name] = p

        result = run_full_analysis(paths)
        result["estimated_cost"] = estimate_cost(result)
        return result
    finally:
        for p in paths.values():
            if os.path.exists(p):
                os.remove(p)
