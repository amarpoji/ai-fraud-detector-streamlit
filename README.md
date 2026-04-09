
# 🔍 Phishing Detector - AI-Powered Fraud Detection

A machine learning application for detecting phishing and fraudulent messages using FastAPI backend and Streamlit frontend.

**Status**: ✅ Streamlit-only, Docker-ready, AWS deployment-ready

---

## 🎯 Features

- 🤖 **AI Models**: Multiple trained ML models for classification
- 📊 **Risk Scoring**: Real-time phishing risk assessment (0-100%)
- 🚩 **Red Flag Detection**: Identifies suspicious patterns
- 📈 **Model Metrics**: Track F1, Accuracy, ROC-AUC
- 💾 **MLflow Integration**: Experiment tracking and model versioning
- 🐳 **Docker Support**: Full containerization for easy deployment
- ☁️ **AWS Ready**: Deploy on EC2 free tier

---

## 🏗️ Architecture

```
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
│  - ML model inference                       │
│  - Feature extraction                       │
│  - Risk calculation                         │
└──────────────┬──────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
    [Models]     [MLflow UI]
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

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Start Backend (Terminal 1)
```bash
cd backend
python -m uvicorn src.app:app --reload
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

#### 5. Start Frontend (Terminal 2)
```bash
cd frontend
streamlit run app.py
# App running at http://localhost:8501
```

---

## 🐳 Docker Deployment

### Build & Run with Docker Compose

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access Points:**
- Frontend: http://localhost:8501
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MLflow: http://localhost:5000

---

## ☁️ AWS Deployment

### Deploy on EC2 (Free Tier)

See **[AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md)** for detailed instructions:

1. ✅ Launch EC2 t3.micro instance
2. ✅ Install Docker & Docker Compose
3. ✅ Clone repository
4. ✅ Run docker-compose up -d
5. ✅ Access via public IP

**Cost**: ~$0/month (free tier), ~$8/month after

---

## 📁 Project Structure

```
ai-fraud-detector/
├── backend/
│   ├── src/
│   │   ├── app.py              # FastAPI application
│   │   ├── training.py         # Model training
│   │   ├── evaluation.py       # Model evaluation
│   │   └── data_transform.py   # Data processing
│   ├── data/                   # Training data
│   └── requirements.txt        # Backend deps
├── frontend/
│   ├── app.py                  # Streamlit app
│   └── requirements.txt        # Frontend deps
├── docker-compose.yml          # Service orchestration
├── Dockerfile.backend          # Backend container
├── Dockerfile.frontend         # Frontend container
├── AWS_DEPLOYMENT.md           # Deployment guide
└── README.md                   # This file
```

---

## 🔧 Configuration

### Environment Variables

Backend (.env or docker-compose):
```
PYTHONUNBUFFERED=1
MLFLOW_TRACKING_URI=sqlite:///mlflow.db
API_HOST=0.0.0.0
API_PORT=8000
```

Frontend (docker-compose):
```
API_URL=http://backend:8000  # Docker network
# or
API_URL=http://localhost:8000  # Local dev
```

---

## 📊 API Endpoints

### Health Check
```bash
GET /health
# Response: {"status": "ok"}
```

### Get Available Models
```bash
GET /models
# Response: {"models": [...]}
```

### Analyze Message
```bash
POST /analyze
Content-Type: application/json

{
  "message": "Click here to verify account",
  "model_run_id": "model-123"
}

# Response:
{
  "label": "phishing",
  "risk_score": 85.5,
  "confidence": 0.92,
  "explanation": "...",
  "red_flags": [...]
}
```

---

## 🧪 Testing

### Health Check
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:8501
```

### API Test
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Verify your account now!",
    "model_run_id": null
  }'
```

---

## 📈 Model Training

Run training pipeline:
```bash
cd backend
python -m dvc repro
# or
python src/training.py
```

Track experiments in MLflow:
```
http://localhost:5000
```

---

## 🐛 Troubleshooting

### Frontend can't connect to backend
- Check backend is running: `docker-compose ps`
- Verify API_URL environment variable
- Check network connectivity: `curl http://localhost:8000/health`

### Docker build fails
```bash
# Clear cache
docker-compose build --no-cache

# Check logs
docker-compose logs backend
```

### Port already in use
```bash
# Linux/Mac: Kill process on port
lsof -i :8501 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Windows: 
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

---

## 📝 Development

### Add Dependencies

Frontend:
```bash
# Add to frontend/requirements.txt
pip install <package>
pip freeze > frontend/requirements.txt
```

Backend:
```bash
# Add to requirements.txt
pip install <package>
pip freeze > requirements.txt
```

Then rebuild Docker:
```bash
docker-compose build
```

---

## 📚 Documentation

- [AWS Deployment Guide](./AWS_DEPLOYMENT.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Docker Documentation](https://docs.docker.com)

---

## 📄 License

MIT

---

## 👥 Support

For issues or questions, please open an issue in the repository.