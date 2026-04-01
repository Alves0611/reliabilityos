import os
import random

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/chaos", tags=["chaos"])

_error_rate: int = 0
_latency_ms: int = 0


@router.post("/error-rate")
async def set_error_rate(percent: int = Query(ge=0, le=100)):
    if os.getenv("FEATURE_CHAOS_ENABLED", "true").lower() != "true":
        raise HTTPException(status_code=403, detail="Chaos endpoints disabled via feature flag")
    global _error_rate
    _error_rate = percent
    return {"error_rate_percent": _error_rate}


@router.post("/latency")
async def set_latency(ms: int = Query(ge=0, le=10000)):
    if os.getenv("FEATURE_CHAOS_ENABLED", "true").lower() != "true":
        raise HTTPException(status_code=403, detail="Chaos endpoints disabled via feature flag")
    global _latency_ms
    _latency_ms = ms
    return {"latency_ms": _latency_ms}


@router.post("/reset")
async def reset():
    global _error_rate, _latency_ms
    _error_rate = 0
    _latency_ms = 0
    return {"error_rate_percent": 0, "latency_ms": 0}


@router.get("/status")
async def status():
    return {
        "error_rate_percent": _error_rate,
        "latency_ms": _latency_ms,
        "chaos_enabled": os.getenv("FEATURE_CHAOS_ENABLED", "true").lower() == "true",
    }


def should_fail() -> bool:
    return _error_rate > 0 and random.randint(1, 100) <= _error_rate


def get_latency_seconds() -> float:
    return _latency_ms / 1000.0 if _latency_ms > 0 else 0.0
