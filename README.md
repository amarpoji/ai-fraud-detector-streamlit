# 🔍 Phishing Detector - AI-Powered Fraud Detection

A machine learning application for detecting phishing and fraudulent messages using a FastAPI backend and a Streamlit frontend.

**Status**: ✅ Streamlit UI, Docker-ready, AWS deployment-ready with DVC pipelines

---

## 🎯 Features

- 🤖 **AI Models**: Pre-trained ML models for robust text classification
- 📊 **Risk Scoring**: Real-time phishing risk assessment (0-100%)
- 🚩 **Red Flag Detection**: Identifies suspicious patterns (urgency, requests for money, etc.)
- 📈 **Model Metrics**: Track F1, Accuracy, ROC-AUC
- 💾 **DVC & MLflow Integration**: Fully reproducible pipelines with DagsHub MLflow tracking
- 🐳 **Docker Support**: Full containerization for easy deployment with Nginx proxy
- ☁️ **AWS Ready**: Production-ready deployment instructions for EC2

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────┐
│         Streamlit Frontend (8501)           │
│  - Interactive UI for message analysis      │
│  - Risk visualization                       │
│  - Model selection                          │
└──────────────┬──────────────────────────────┘
               │ HTTP/REST
               ▼
┌─────────────────────────────────────────────┐
│        FastAPI Backend (8000)               │
│  - Static pre-trained model inference       │
│  - Fallback MLflow model loading            │
│  - Feature extraction & Risk calculation    │
└──────────────┬──────────────────────────────┘
               │
         ┌─────┴─────┐
         ▼           ▼
[backend/models/]  [DagsHub MLflow]
```

---

## 🚀 Quick Start

### Local Development

#### 1. Clone Repository
```bash
git clone <repo-url>
cd ai-fraud-detector
```

#### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Train Models (DVC Pipeline)
```bash
dvc repro
```
*This will run data transformation, train multiple models, evaluate them, and save the best model to `backend/models/`.*

#### 5. Start Backend & Frontend locally
```bash
# Terminal 1: Backend
uvicorn backend.src.app:app --reload
# API running at http://localhost:8000

# Terminal 2: Frontend
streamlit run frontend/app.py
# App running at http://localhost:8501
```

---

## 🐳 Docker Deployment

The project contains two separate Docker configurations:
- `docker-compose.yml`: Local development with hot-reloading and MLflow UI.
- `docker-compose.prod.yml`: Lightweight production environment using static pre-trained models.

### Local Development (With Hot Reload)
```bash
docker-compose up -d --build
```
**Access Points:**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- MLflow UI: http://localhost:5000

### Production Deployment (Pre-trained Models)
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```
**Access Points:**
- Application available at `http://localhost:80` (via Nginx proxy)
*Note: Make sure you have trained your models using `dvc repro` so that `backend/models/` contains your `.pkl` files before running the production compose file.*

---

## ☁️ AWS Deployment

We provide two deployment paths for AWS EC2:

1. **[PROD_DEPLOYMENT_GUIDE.md](./PROD_DEPLOYMENT_GUIDE.md)** *(Recommended)*: A lightweight, production-ready approach using `docker-compose.prod.yml` and pre-trained static models. Perfect for the EC2 Free Tier.

---

## 📁 Project Structure

```text
ai-fraud-detector/
├── backend/
│   ├── src/
│   │   ├── app.py              # FastAPI application
│   │   ├── training.py         # Model training
│   │   ├── evaluation.py       # Model evaluation
│   │   ├── utils.py            # Utility functions
│   │   └── data_transform.py   # Data processing
│   ├── data/                   # Raw & processed data
│   └── models/                 # Winning static models (.pkl)
├── frontend/
│   ├── app.py                  # Streamlit app
│   └── requirements.txt        # Frontend deps
├── docker-compose.yml          # Local dev orchestration
├── docker-compose.prod.yml     # Production orchestration
├── Dockerfile.backend          # Backend container
├── Dockerfile.frontend         # Frontend container
├── dvc.yaml                    # DVC pipeline configuration
├── params.yaml                 # Central configuration file
├── nginx.conf                  # Production reverse proxy config
├── PROD_DEPLOYMENT_GUIDE.md    # Production EC2 guide
└── AWS_DEPLOYMENT.md           # Full EC2 guide
```

---

## 🔧 Configuration

### Environment Variables

**Backend (`params.yaml`):**
Configure your DagsHub MLflow credentials, training splits, and model variations inside `params.yaml`.

**Frontend (`docker-compose.yml`):**
```yaml
environment:
  - BACKEND_URL=http://backend:8000
```

---

## 📊 API Endpoints

### Health Check
```bash
GET /health
# Response: {"status": "healthy"}
```

### Get Available Models
```bash
GET /models
# Response: {"total": 1, "models": [...], "best_model": {...}}
```

### Analyze Message
```bash
POST /analyze
Content-Type: application/json

{
  "message": "Click here to verify account immediately!",
  "model_run_id": null
}

# Response:
{
  "label": "Phishing",
  "risk_score": 85.5,
  "confidence": 0.92,
  "explanation": "⚠️ HIGH RISK: This message shows strong indicators...",
  "red_flags": [...],
  "model_used": "production"
}
```

---

## 📚 Documentation

- [Production Deployment Guide](./PROD_DEPLOYMENT_GUIDE.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Streamlit Documentation](https://docs.streamlit.io)
- [DVC Documentation](https://dvc.org/doc)

---

## 📄 License

MIT

---

## 👥 Support

For issues or questions, please open an issue in the repository.