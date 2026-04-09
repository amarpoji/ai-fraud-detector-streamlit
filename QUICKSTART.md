# Quick Start Guide

## Local Development (No Docker)

```bash
# Terminal 1: Backend
cd backend
pip install -r ../requirements.txt
python -m uvicorn src.app:app --reload

# Terminal 2: Frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

**Access**: http://localhost:8501

---

## Docker Compose (Recommended)

```bash
# Build and start
docker-compose build
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f frontend
docker-compose logs -f backend

# Stop
docker-compose down
```

**Access**: http://localhost:8501

---

## AWS Deployment (EC2)

See `AWS_DEPLOYMENT.md` for full guide. Quick version:

```bash
# On EC2 instance
sudo apt update
sudo apt install -y docker.io docker-compose git

# Clone & run
git clone <repo-url> phishing-detector
cd phishing-detector
docker-compose up -d

# Access
http://<PUBLIC_IP>:8501
```

---

## Deleted Files (React -> Streamlit)

✅ Removed:
- `frontend/App.jsx`
- `frontend/main.jsx`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/vite.config.js`
- `frontend/.gitignore`
- `nginx.conf`

✅ Kept:
- `frontend/app.py` (Streamlit app)
- `backend/` (FastAPI)
- `docker-compose.yml` (updated for Streamlit)
- `Dockerfile.backend` (unchanged)
- `Dockerfile.frontend` (updated)

---

## Key Changes

### docker-compose.yml
- Frontend port: `80` → `8501` (Streamlit)
- Environment: Updated API_URL
- Healthcheck: Updated for Python/Streamlit

### Dockerfile.frontend
- Node.js build → Python runtime
- Nginx → Streamlit
- Size: ~400MB → ~200MB

### app.py
- Added `os.getenv("API_URL")` for Docker environment

---

## Architecture

```
Frontend (Streamlit 8501)
    ↓ HTTP
Backend (FastAPI 8000)
    ↓
ML Models + MLflow
```

---

## Costs

| Resource | Free Tier | After 12mo |
|----------|-----------|-----------|
| EC2 t3.micro | $0 | ~$7/mo |
| EBS Storage 30GB | $0 | ~$1/mo |
| **Total** | **$0/mo** | **~$8/mo** |

---

## Support

- **Streamlit**: https://docs.streamlit.io
- **FastAPI**: https://fastapi.tiangolo.com
- **Docker**: https://docs.docker.com
- **AWS EC2**: https://aws.amazon.com/ec2

