"""Data management endpoints: upload, demo case, processing status."""
from __future__ import annotations

import time

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.api.deps import get_current_user, require
from app.demo import case as demo_case
from app.engine import ingestion
from app.engine.pipeline import load_dataset
from app.security import audit

router = APIRouter(prefix="/api/data", tags=["data"])


class ResetRequest(BaseModel):
    confirm: bool = False


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...),
                     user: dict = Depends(require("upload"))):
    """Upload and analyse a CSV of transactions."""
    import os
    from app.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400,
                            "Upload failed: only CSV files are accepted.")

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400,
                            f"Upload failed: file exceeds "
                            f"{MAX_UPLOAD_MB} MB limit.")

    try:
        df, report = ingestion.parse_csv(raw, file.filename or "upload.csv")
    except ingestion.ValidationError as exc:
        audit.log(user["investigator_id"],
                  "Rejected CSV upload",
                  action_type="upload", result="failure",
                  details=str(exc))
        raise HTTPException(422, str(exc))

    started = time.time()
    result = load_dataset(df, name=file.filename or "upload.csv",
                            source="upload")
    result["validation"] = report
    result["processing_seconds"] = round(time.time() - started, 2)
    audit.log(user["investigator_id"],
              f"Uploaded dataset '{file.filename}'",
              entity_type="dataset", entity_id=str(result["dataset_id"]),
              action_type="upload")
    return result


@router.post("/demo")
def load_demo(user: dict = Depends(require("upload"))):
    """Load the prepared synthetic demonstration case."""
    started = time.time()
    df = demo_case.generate_demo_case()
    result = load_dataset(df,
                          name=demo_case.case_metadata()["name"],
                          source="demo")
    result["processing_seconds"] = round(time.time() - started, 2)
    result["case"] = demo_case.case_metadata()
    audit.log(user["investigator_id"],
              "Loaded demonstration case",
              action_type="load_demo")
    return result


@router.post("/reset-demo")
def reset_demo(req: ResetRequest,
                 user: dict = Depends(require("upload"))):
    """Reset transaction data to the demonstration case.

    Requires explicit confirmation. Preserves investigations,
    users and the audit log — only transaction analysis data
    (transactions, features, risk, clusters, alerts, trails)
    is replaced.
    """
    if not req.confirm:
        raise HTTPException(
            400,
            "Reset requires explicit confirmation. "
            "Call again with confirm=true.",
        )
    from app.db.database import get_connection
    from app.engine.pipeline import invalidate_cache
    started = time.time()
    df = demo_case.generate_demo_case()
    result = load_dataset(df,
                          name=demo_case.case_metadata()["name"],
                          source="demo")
    result["processing_seconds"] = round(time.time() - started, 2)
    result["preserved"] = [
        "investigations", "users", "audit log",
    ]
    invalidate_cache()
    audit.log(user["investigator_id"],
              "Reset to demonstration data",
              action_type="reset_demo",
              details="Transaction data replaced; "
                      "investigations and audit log preserved.")
    return result


@router.get("/status")
def status(user: dict = Depends(get_current_user)):
    """Current dataset / processing status."""
    from app.db.database import get_connection
    conn = get_connection()
    ds = conn.execute(
        "SELECT * FROM datasets ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not ds:
        return {"loaded": False,
                "message": "No transactions loaded. Upload a dataset "
                            "or use the demonstration dataset."}
    return {
        "loaded": True,
        "dataset": dict(ds),
        "accounts": conn.execute("SELECT COUNT(*) AS n FROM accounts"
                                   ).fetchone()["n"],
        "transactions": conn.execute(
            "SELECT COUNT(*) AS n FROM transactions"
        ).fetchone()["n"],
        "high_risk": conn.execute(
            "SELECT COUNT(*) AS n FROM risk_scores WHERE risk_category='high'"
        ).fetchone()["n"],
        "detection_method": conn.execute(
            "SELECT detection_method FROM risk_scores LIMIT 1"
        ).fetchone()["detection_method"],
    }
