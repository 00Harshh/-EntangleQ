# Quantum QKD System

A full-stack Quantum Key Distribution simulator with BB84, E91, QBER monitoring, ML prediction, OTP encryption, and a live dashboard.

---

## Project Structure

```
quantum_qkd/
├── quantum_engine/
│   ├── bb84.py         # BB84 protocol simulation (Qiskit)
│   ├── e91.py          # E91 entanglement protocol (Qiskit)
│   └── qber.py         # QBER calculation + attack detection
├── api/
│   └── main.py         # FastAPI backend (all endpoints)
├── encryption/
│   └── otp.py          # OTP XOR encryption/decryption
├── ml_layer/
│   └── predictor.py    # ML QBER prediction (GradientBoosting)
├── dashboard/
│   ├── package.json    # React app config
│   └── src/
│       └── App.jsx     # Live quantum dashboard UI
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Python Backend

```bash
cd quantum_qkd
pip install -r requirements.txt
```

### 2. Start the FastAPI Server

```bash
uvicorn api.main:app --reload --port 8000
```

Visit: http://localhost:8000/docs  ← Interactive Swagger UI

### 3. Start the React Dashboard

```bash
cd dashboard
npm install
npm start
```

Visit: http://localhost:3000

---

## API Endpoints

| Method | Endpoint           | Description                         |
|--------|--------------------|-------------------------------------|
| POST   | `/generate_key`    | Run BB84 or E91, return quantum key |
| POST   | `/simulate_attack` | Simulate Eve's intercept-resend     |
| POST   | `/encrypt_message` | OTP-XOR encrypt with quantum key    |
| POST   | `/decrypt_message` | OTP-XOR decrypt                     |
| GET    | `/qber_monitor`    | Live QBER history + trend analysis  |
| POST   | `/predict_qber`    | ML-predicted QBER from channel params|

---

## Example API Usage

### Generate a Key (BB84)
```bash
curl -X POST http://localhost:8000/generate_key \
  -H "Content-Type: application/json" \
  -d '{"protocol": "BB84", "num_bits": 256, "noise_level": 0.02}'
```

### Simulate an Attack
```bash
curl -X POST http://localhost:8000/simulate_attack \
  -H "Content-Type: application/json" \
  -d '{"protocol": "BB84", "num_bits": 256, "noise_level": 0.02}'
```

### Encrypt a Message
```bash
curl -X POST http://localhost:8000/encrypt_message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Quantum!", "key": [0,1,1,0,...]}'
```

### ML Prediction
```bash
curl -X POST http://localhost:8000/predict_qber \
  -H "Content-Type: application/json" \
  -d '{"noise_level": 0.05, "attack_probability": 0.3, "channel_loss": 0.1}'
```

---

## Security Thresholds

| QBER Range | Status  | Meaning                        |
|------------|---------|--------------------------------|
| < 5%       | Secure  | Clean channel                  |
| 5–11%      | Warning | Noise or weak interference     |
| 11–20%     | Attack  | Likely eavesdropping (Eve)     |
| > 20%      | Abort   | Channel severely compromised   |

---

## Architecture

```
User → Dashboard (React)
         ↓ HTTP
      FastAPI (api/main.py)
       ├── BB84/E91 Engine (Qiskit + AerSimulator)
       ├── QBER Module (error rate + trend analysis)
       ├── OTP Encryption (XOR with quantum key)
       └── ML Predictor (GradientBoostingRegressor)
```

---

## How BB84 Works

1. Alice generates random bits + random bases (Z or X)
2. Alice encodes qubits and sends them
3. Bob measures in random bases
4. Alice and Bob publicly compare bases (keep matching ones)
5. A sample of matching bits is used to compute QBER
6. If QBER < 11%: secure key extracted; if higher → Eve detected

## How E91 Works

1. An entangled Bell pair (Φ+) is created per round
2. Alice and Bob each receive one qubit
3. They measure in different angles
4. Correlations are used to compute the CHSH value
5. Bell inequality violation (|S| > 2) confirms quantum entanglement
6. Matching bases yield the raw key; QBER is computed on it
