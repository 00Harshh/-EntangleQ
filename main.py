"""
Quantum QKD API — FastAPI Backend
Endpoints:
  POST /generate_key       → Run BB84 or E91 and return a quantum key
  POST /simulate_attack    → Run protocol with Eve present
  POST /encrypt_message    → Encrypt a message with OTP using a quantum key
  GET  /qber_monitor       → Get QBER history and trend analysis
  POST /predict_qber       → ML-predicted QBER from channel parameters
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
import time

# Flat imports — all files are in the same directory
from bb84 import run_bb84
from e91 import run_e91
from qber import qber_from_protocol_result, qber_series_analysis, QBERResult
from otp import xor_encrypt, xor_decrypt, check_key_capacity
from predictor import predict_qber

app = FastAPI(
    title="Quantum QKD API",
    description="BB84/E91 Quantum Key Distribution with QBER monitoring and ML prediction",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory QBER history for monitoring
qber_history: list[dict] = []


# ─── Request / Response Models ─────────────────────────────────────────────────

class GenerateKeyRequest(BaseModel):
    protocol: Literal["BB84", "E91"] = "BB84"
    num_bits: int = Field(default=256, ge=64, le=2048)
    noise_level: float = Field(default=0.0, ge=0.0, le=0.5)


class SimulateAttackRequest(BaseModel):
    protocol: Literal["BB84", "E91"] = "BB84"
    num_bits: int = Field(default=256, ge=64, le=2048)
    noise_level: float = Field(default=0.02, ge=0.0, le=0.5)


class EncryptRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    key: list[int] = Field(..., min_length=8)


class DecryptRequest(BaseModel):
    ciphertext: str
    key: list[int]


class PredictQBERRequest(BaseModel):
    noise_level: float = Field(default=0.05, ge=0.0, le=1.0)
    attack_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    channel_loss: float = Field(default=0.1, ge=0.0, le=1.0)


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "Quantum QKD API",
        "version": "1.0.0",
        "endpoints": ["/generate_key", "/simulate_attack", "/encrypt_message",
                      "/decrypt_message", "/qber_monitor", "/predict_qber"],
    }


@app.post("/generate_key")
def generate_key(req: GenerateKeyRequest):
    """Generate a quantum key using BB84 or E91 protocol."""
    start = time.time()
    try:
        if req.protocol == "BB84":
            result = run_bb84(num_bits=req.num_bits, eve_present=False, noise_level=req.noise_level)
        else:
            result = run_e91(num_pairs=req.num_bits, eve_present=False, noise_level=req.noise_level)

        qber_result = qber_from_protocol_result(result)
        elapsed = round(time.time() - start, 3)

        qber_history.append({
            "timestamp": time.time(),
            "qber": qber_result.qber,
            "protocol": req.protocol,
            "attack": False,
        })
        if len(qber_history) > 100:
            qber_history.pop(0)

        return {
            "success": True,
            "elapsed_seconds": elapsed,
            "key": result["raw_key"],
            "key_length_bits": len(result["raw_key"]),
            "protocol": result["protocol"],
            "qber": qber_result.qber,
            "qber_status": qber_result.status,
            "secure": result["secure"],
            "message": qber_result.message,
            **({"chsh_value": result.get("chsh_value"), "bell_violated": result.get("bell_violated")}
               if req.protocol == "E91" else {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate_attack")
def simulate_attack(req: SimulateAttackRequest):
    """Simulate Eve's intercept-resend attack on the quantum channel."""
    start = time.time()
    try:
        if req.protocol == "BB84":
            result = run_bb84(num_bits=req.num_bits, eve_present=True, noise_level=req.noise_level)
        else:
            result = run_e91(num_pairs=req.num_bits, eve_present=True, noise_level=req.noise_level)

        qber_result = qber_from_protocol_result(result)
        elapsed = round(time.time() - start, 3)

        qber_history.append({
            "timestamp": time.time(),
            "qber": qber_result.qber,
            "protocol": req.protocol,
            "attack": True,
        })
        if len(qber_history) > 100:
            qber_history.pop(0)

        return {
            "success": True,
            "elapsed_seconds": elapsed,
            "attack_simulated": True,
            "key": result["raw_key"],
            "key_length_bits": len(result["raw_key"]),
            "protocol": result["protocol"],
            "qber": qber_result.qber,
            "qber_status": qber_result.status,
            "attack_detected": qber_result.attack_detected,
            "secure": result["secure"],
            "message": qber_result.message,
            "confidence": qber_result.confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/encrypt_message")
def encrypt_message(req: EncryptRequest):
    """Encrypt a message using OTP-XOR with a provided quantum key."""
    try:
        capacity = check_key_capacity(req.key, req.message)
        if not capacity["sufficient"]:
            raise HTTPException(
                status_code=400,
                detail=f"Key too short. Need {capacity['message_bytes']} bytes, "
                       f"have {capacity['key_capacity_bytes']}. Generate a longer key.",
            )
        result = xor_encrypt(req.message, req.key)
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/decrypt_message")
def decrypt_message(req: DecryptRequest):
    """Decrypt an OTP-XOR ciphertext using a quantum key."""
    try:
        plaintext = xor_decrypt(req.ciphertext, req.key)
        return {"success": True, "plaintext": plaintext}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/qber_monitor")
def qber_monitor():
    """Return live QBER history and trend analysis."""
    values = [entry["qber"] for entry in qber_history]
    trend  = qber_series_analysis(values) if len(values) >= 3 else {"trend": "insufficient_data"}

    return {
        "history": qber_history[-50:],
        "total_readings": len(qber_history),
        "latest_qber": values[-1] if values else None,
        "trend_analysis": trend,
        "attack_alert": trend.get("alert", False),
    }


@app.post("/predict_qber")
def predict_qber_endpoint(req: PredictQBERRequest):
    """ML-powered QBER prediction from channel parameters."""
    try:
        prediction = predict_qber(
            noise_level=req.noise_level,
            attack_probability=req.attack_probability,
            channel_loss=req.channel_loss,
        )
        return {"success": True, **prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))