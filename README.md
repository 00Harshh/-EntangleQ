# EntangleQ

A full-stack Quantum Key Distribution simulator — BB84, E91, real-time QBER monitoring, ML-powered eavesdropper detection, OTP encryption, and a live 3D visualisation. Also runs BB84 and Bell State circuits on **real IBM Quantum hardware**.

Got the idea watching Dark. Learned quantum computing in a week. Built it for a hackathon.

---

## What It Does

### BB84 Protocol
Alice encodes random bits into qubits using two non-orthogonal bases (Z and X). Bob measures in a random basis. They publicly compare bases and keep only matching ones — the **sifted key**. Any eavesdropper (Eve) is forced to intercept and re-send, collapsing the quantum state and introducing detectable bit errors. That error rate is the **QBER (Quantum Bit Error Rate)**. Above 11% — Eve is in the channel.

### E91 Protocol (Ekert 1991)
Uses entangled Bell pairs — `(|00⟩ + |11⟩) / √2`. Alice and Bob each receive one qubit and measure at different angles. Correlations are tested against the **CHSH inequality**. If `|S| > 2`, Bell's theorem holds — the channel is quantum and untampered. If S drops to classical values, entanglement is broken. Eve is detected not through errors, but through the **violation of quantum mechanics itself**.

### CHSH Score
- Classical limit: `|S| ≤ 2`
- Quantum (Bell pair): `|S| → 2√2 ≈ 2.828`
- EntangleQ achieves: `S ≈ 2.71` ✅

### OTP-XOR Encryption
Messages encrypted with the quantum-generated sifted key using one-time pad XOR. Key is consumed once and never reused.

### ML Threat Engine
GradientBoosting model trained on noise level, attack probability, and channel loss to predict QBER before key exchange — giving early warning before a full QKD run.

### Live Dashboard
- Real-time QBER trend chart with anomaly detection
- Qubit exchange visualiser (Alice bits, bases, Bob bases, sifted key)
- 3D quantum network built in Three.js
- Session stats, security status gauge, system log

---

## Project Structure

```
EntangleQ/
├── quantum_engine/
│   ├── bb84.py           # BB84 protocol (Qiskit + AerSimulator)
│   ├── e91.py            # E91 entanglement protocol (Qiskit)
│   └── qber.py           # QBER calculation + attack detection
├── api/
│   └── main.py           # FastAPI backend
├── encryption/
│   └── otp.py            # OTP XOR encryption/decryption
├── ml_layer/
│   └── predictor.py      # ML QBER prediction (GradientBoosting)
├── dashboard/
│   ├── index.html        # Landing page with 3D visualisation
│   └── simulator.html    # Full interactive simulator
├── quantum_ibm.py        # Runs on real IBM Quantum hardware
└── requirements.txt
```



## Security Thresholds

| QBER | Status | Meaning |
|------|--------|---------|
| < 5% | ✅ Secure | Clean channel |
| 5–11% | ⚠️ Warning | Noise or weak interference |
| 11–20% | 🚨 Attack | Likely eavesdropping |
| > 20% | ❌ Abort | Channel severely compromised |

---

## Stack

- **Qiskit + AerSimulator** — quantum circuit simulation
- **IBM Quantum** — real hardware execution
- **scikit-learn** — ML threat prediction
- **Frontend** — it's plain HTML/CSS/JS, not a React/JS framework app
- **No API needed ** — everything runs locally in the browser, no FastAPI server required for the simulator

---

## Why Quantum Cryptography

Classical encryption relies on computational hardness — it's hard to break, but not impossible. Quantum cryptography is different. The act of observing a quantum channel physically disturbs it. Any eavesdropper leaves a mathematically guaranteed trace. You don't need to trust the math — the laws of physics enforce it.

---
<img width="1460" height="843" alt="Screenshot 2026-03-05 at 3 17 30 PM" src="https://github.com/user-attachments/assets/f8451015-3605-4d95-86ea-fbc801977748" />
<img width="1467" height="824" alt="Screenshot 2026-03-05 at 3 16 45 PM" src="https://github.com/user-attachments/assets/d57123fa-7d6a-45b2-898e-7c55229ccdfb" />
<img width="1126" height="836" alt="Screenshot 2026-03-05 at 3 24 31 PM" src="https://github.com/user-attachments/assets/fd97ff6b-f9c9-448c-b04c-c574d70e4867" />


