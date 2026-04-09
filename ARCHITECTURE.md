# 🏗️ Architecture Overview

## System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    Users / Web Browsers                         │
│                          :8501                                  │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          │ HTTP
                          ▼
┌────────────────────────────────────────────────────────────────┐
│              ┌─────────────────────────────────┐                │
│              │   Streamlit Frontend (8501)     │                │
│              │                                 │                │
│              │  • Web UI Interface             │                │
│              │  • Message Input Form           │                │
│              │  • Risk Visualization           │                │
│              │  • Model Selection              │                │
│              │  • Analysis History             │                │
│              │  • Session Management           │                │
│              └────────────┬────────────────────┘                │
│                           │                                     │
│          Docker Bridge Network: phishing_network               │
│                           │                                     │
│                           │ HTTP REST API                       │
│                           ▼                                     │
│              ┌─────────────────────────────────┐                │
│              │   FastAPI Backend (8000)        │                │
│              │                                 │                │
│              │  • /analyze (POST)              │                │
│              │  • /models (GET)                │                │
│              │  • /health (GET)                │                │
│              │  • /docs (Swagger UI)           │                │
│              │  • /redoc (ReDoc)               │                │
│              │                                 │                │
│              └────────────┬────────────────────┘                │
│                           │                                     │
│              ┌────────────┴─────────┐                           │
│              │                      │                           │
│              ▼                      ▼                           │
│        ┌──────────────┐      ┌──────────────┐                  │
│        │  ML Models   │      │  MLflow UI   │                  │
│        │              │      │  (Port 5000) │                  │
│        │ • Phishing   │      │              │                  │
│        │   Detector   │      │ • Metrics    │                  │
│        │ • Prediction │      │ • Models     │                  │
│        │ • Scoring    │      │ • Params     │                  │
│        │ • Features   │      │ • Artifacts  │                  │
│        └──────────────┘      └──────────────┘                  │
│                                                                 │
│        ┌──────────────────────────────────────┐                │
│        │        Volumes (Data Persistence)    │                │
│        │                                      │                │
│        │ • ./backend/data/                   │                │
│        │   (Training data)                    │                │
│        │ • ./mlruns/                         │                │
│        │   (MLflow metadata)                  │                │
│        │ • ./mlflow_artifacts/               │                │
│        │   (Model artifacts)                  │                │
│        └──────────────────────────────────────┘                │
│                                                                 │
│            Docker Compose Orchestration                        │
└────────────────────────────────────────────────────────────────┘
```

---

## Service Dependencies

```
Frontend (Streamlit)
    ↓ depends_on
Backend (FastAPI)
    ↓ requires
MLflow UI (optional)
```

---

## Data Flow

### User Input Flow
```
1. User enters message in Streamlit UI
                ↓
2. Frontend sends POST request to /analyze
                ↓
3. Backend receives message & model_run_id
                ↓
4. Feature extraction & preprocessing
                ↓
5. ML model prediction
                ↓
6. Risk scoring & red flag detection
                ↓
7. Response returned to frontend
                ↓
8. Frontend displays results with visualizations
```

### Example Request/Response
```
POST /analyze
Content-Type: application/json

{
  "message": "Click here to verify account",
  "model_run_id": "model-123"
}

↓

{
  "label": "phishing",
  "risk_score": 85.5,
  "confidence": 0.92,
  "explanation": "Message contains suspicious urgency and verification request",
  "red_flags": [
    {
      "category": "Urgency Language",
      "description": "Contains urgent action words",
      "confidence": 0.95
    },
    {
      "category": "Verification Request",
      "description": "Asks user to verify credentials",
      "confidence": 0.88
    }
  ],
  "model_used": "phishing-detector-v2"
}
```

---

## Network Architecture

```
┌──────────────────────────────────────┐
│        Host Machine / VM              │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │  Docker Bridge Network          │  │
│  │  (phishing_network)             │  │
│  │                                 │  │
│  │  ┌──────────────┐ ┌──────────┐ │  │
│  │  │ Frontend     │ │ Backend  │ │  │
│  │  │ 172.18.0.2   │ │ 172.18.0.3
│  │  │              │ │          │ │  │
│  │  │ Port 8501    │ │ Port 8000
│  │  └──────────────┘ └──────────┘ │  │
│  │                                 │  │
│  │  ┌──────────────┐              │  │
│  │  │ MLflow       │              │  │
│  │  │ 172.18.0.4   │              │  │
│  │  │              │              │  │
│  │  │ Port 5000    │              │  │
│  │  └──────────────┘              │  │
│  └─────────────────────────────────┘  │
│          ↑         ↑         ↑         │
│      Port 8501  Port 8000  Port 5000   │
│                                       │
│  Host Ports Mapped:                   │
│  - 8501:8501 (Frontend)              │
│  - 8000:8000 (Backend)               │
│  - 5000:5000 (MLflow)                │
└──────────────────────────────────────┘
```

---

## Component Details

### Frontend (Streamlit)
**Purpose**: Interactive UI for users
**Technology**: Python + Streamlit
**Port**: 8501
**Key Features**:
- Real-time message analysis interface
- Risk visualization (gauge chart)
- Model selection dropdown
- Analysis history tracking
- Red flag explanations
- Session-based state management

**Dockerfile**: Multi-stage build eliminated
- Base: `python:3.11-slim`
- Runtime: Streamlit server
- Size: ~200 MB
- Build Time: 1-2 minutes

### Backend (FastAPI)
**Purpose**: ML inference & API endpoints
**Technology**: Python + FastAPI + scikit-learn
**Port**: 8000
**Key Features**:
- RESTful API endpoints
- Model inference
- Feature extraction & preprocessing
- Risk scoring algorithm
- MLflow integration
- Automatic API documentation

**Docker**: Unchanged from original
- Base: `python:3.11-slim`
- Runtime: Uvicorn ASGI server
- Size: ~300 MB
- Build Time: 2-3 minutes

### MLflow UI (Optional)
**Purpose**: Model tracking & experimentation
**Port**: 5000
**Features**:
- Experiment metadata
- Model metrics & parameters
- Artifact storage
- Model registry
- Experiment comparison

**Docker**: Pre-built image from GitHub Container Registry

---

## Volume Structure

```
ai-fraud-detector/
├── backend/
│   ├── data/                     ← Training data
│   │   └── [CSV files]
│   └── src/
├── mlruns/                       ← MLflow experiment data
│   └── [Run directories]
├── mlflow_artifacts/             ← Model artifacts
│   └── [Model files]
└── [code files]
```

### Volume Mounts in docker-compose
```yaml
volumes:
  - ./backend:/app/backend         # Backend code
  - ./backend/data:/app/data       # Training data
  - ./mlruns:/app/mlruns           # MLflow metadata
  - ./mlflow_artifacts:/app/mlflow_artifacts  # Models
```

---

## Environment Variables

### Frontend
```
API_URL=http://backend:8000    # Backend endpoint (docker network)
```

### Backend
```
PYTHONUNBUFFERED=1             # Immediate logging
MLFLOW_TRACKING_URI=sqlite:///mlflow.db  # MLflow metadata
API_HOST=0.0.0.0               # Listen on all interfaces
API_PORT=8000                  # Service port
```

---

## Health Checks

### Frontend (Streamlit)
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8501')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```

### Backend (FastAPI)
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## API Endpoints

### Health Check
```
GET /health
Response: {"status": "ok"}
```

### Get Available Models
```
GET /models
Response: {
  "models": [
    {
      "name": "Model v1",
      "run_id": "abc123",
      "f1_score": 0.92,
      "accuracy": 0.89,
      "roc_auc": 0.95
    }
  ]
}
```

### Analyze Message
```
POST /analyze
Request: {
  "message": "string",
  "model_run_id": "string or null"
}
Response: {
  "label": "phishing or legitimate",
  "risk_score": 0-100,
  "confidence": 0-1,
  "explanation": "string",
  "red_flags": [...],
  "model_used": "string"
}
```

### Swagger UI
```
GET /docs
```

### ReDoc
```
GET /redoc
```

---

## Deployment Architecture

### Local Development
```
Your Machine
├── Backend (uvicorn, port 8000)
├── Frontend (streamlit, port 8501)
└── MLflow (optional)
```

### Docker Local
```
Host Machine
├── Docker Daemon
│   ├── Frontend Container (8501)
│   ├── Backend Container (8000)
│   └── MLflow Container (5000)
└── Docker Bridge Network
```

### AWS EC2
```
AWS EC2 Instance (t3.micro)
├── Docker & Docker Compose
│   ├── Frontend Container (8501)
│   ├── Backend Container (8000)
│   └── MLflow Container (5000)
└── Security Group
    ├── Port 22 (SSH)
    ├── Port 8501 (Streamlit)
    ├── Port 8000 (API)
    └── Port 5000 (MLflow)
```

---

## Scalability Considerations

### Current Setup (Single Instance)
- All services on one host
- Suitable for: Development, prototyping, small usage
- Limitations: Single point of failure, resource sharing

### Future Scaling Options
1. **Horizontal Scaling**:
   - Multiple backend instances with load balancer
   - Separate frontend server
   - Dedicated MLflow server

2. **Cloud Native**:
   - Kubernetes deployment
   - AWS ECS/Fargate
   - AWS Lambda functions

3. **Microservices**:
   - Separate model serving layer
   - Message queue for async processing
   - Caching layer (Redis)
   - Database for results history

---

## Security Considerations

### Current Implementation
```
Internet
    │
    └─ (HTTPS recommended)
          │
    AWS Security Group
    ├─ Port 22: SSH (restricted IP)
    ├─ Port 8501: Streamlit (restricted IP)
    ├─ Port 8000: API (internal)
    └─ Port 5000: MLflow (internal)
          │
    Docker Bridge Network
    ├─ Frontend (isolated)
    ├─ Backend (isolated)
    └─ MLflow (isolated)
```

### Recommendations for Production
1. **Network Security**:
   - Use HTTPS/TLS
   - Restrict access by IP
   - API authentication (JWT, OAuth)

2. **Data Security**:
   - Encrypt sensitive data at rest
   - Encrypted connections between services
   - Secure credential management (AWS Secrets Manager)

3. **Access Control**:
   - Role-based access control (RBAC)
   - API rate limiting
   - Input validation & sanitization

---

## Performance Metrics

### Typical Response Times
- Frontend Load: ~2-3 seconds
- API Response: ~500-1000ms
- Model Inference: ~200-500ms
- Full Round Trip: ~1-2 seconds

### Resource Usage
- Frontend: ~100-200 MB RAM
- Backend: ~300-500 MB RAM
- MLflow: ~200-300 MB RAM
- Total: ~600-1000 MB RAM

### Storage
- Frontend Image: ~200 MB
- Backend Image: ~300 MB
- MLflow Image: ~300 MB
- Data Volumes: Depends on training data size

---

## Update Flow

```
Developer commits code
    ↓
Git push to repository
    ↓
Pull on deployment server
    ↓
docker-compose down
    ↓
docker-compose build
    ↓
docker-compose up -d
    ↓
Services restart automatically
    ↓
Users access updated application
```

---

## Monitoring Points

### Health Checks
- Frontend health endpoint
- Backend /health endpoint
- MLflow availability

### Metrics to Monitor
- Response time
- Error rates
- Resource usage (CPU, RAM)
- Model prediction accuracy
- User activity logs

### Logging
- Application logs (Docker logs)
- MLflow tracking
- API request/response logging

---

## Disaster Recovery

### Backup Points
- Code: Git repository
- Data: Volume backups
- Models: MLflow artifacts
- Configuration: docker-compose.yml

### Recovery Process
```
1. Restore code from git
2. Restore volumes from backup
3. docker-compose up -d
4. Verify health checks
5. Validate model performance
```

---

## Next Steps

- Deploy locally for testing
- Deploy to AWS for production
- Implement monitoring & alerting
- Plan for scaling & optimization

See **DEPLOY_GUIDE.md** for detailed deployment instructions.

