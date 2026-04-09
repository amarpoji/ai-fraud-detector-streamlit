# 🎯 Complete Deployment Guide & Checklist

## Overview
Your Phishing Detector has been converted from React to Streamlit and is now **production-ready** for Docker and AWS deployment.

---

## ✅ Verification Checklist

### 1. Frontend Changes
- ✅ React files deleted (App.jsx, main.jsx, index.html, package.json, vite.config.js)
- ✅ Streamlit app preserved (app.py)
- ✅ frontend/requirements.txt created with Streamlit dependencies
- ✅ app.py updated to use `API_URL` environment variable
- ✅ nginx.conf removed

**Verification**:
```bash
# Check frontend folder
ls -la frontend/
# Should show: app.py, requirements.txt (and .gitignore if exists)
```

### 2. Docker Files
- ✅ Dockerfile.frontend updated for Streamlit
- ✅ docker-compose.yml updated for Streamlit (port 8501)
- ✅ Dockerfile.backend unchanged (FastAPI)
- ✅ Health checks configured for all services

**Verification**:
```bash
# Check Dockerfiles exist and are valid
cat Dockerfile.frontend | head -5
cat Dockerfile.backend | head -5
```

### 3. Documentation
- ✅ AWS_DEPLOYMENT.md created (full guide)
- ✅ README.md updated
- ✅ QUICKSTART.md created
- ✅ DEPLOYMENT_SUMMARY.md created

---

## 🚀 Deploy Locally (Test First)

### Step 1: Verify Docker Installed
```bash
docker --version
docker-compose --version
```

### Step 2: Build Images
```bash
cd ai-fraud-detector
docker-compose build
```

**Expected output**:
```
frontend | Successfully tagged ai-fraud-detector-frontend:latest
backend  | Successfully tagged ai-fraud-detector-backend:latest
```

### Step 3: Start Services
```bash
docker-compose up -d
```

**Check status**:
```bash
docker-compose ps
# Should show all services running (healthy)
```

### Step 4: Test Access
```bash
# Frontend (Streamlit)
curl http://localhost:8501

# Backend (FastAPI)
curl http://localhost:8000/health

# API Docs
open http://localhost:8000/docs
```

### Step 5: View Logs
```bash
# All logs
docker-compose logs

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend
```

### Step 6: Stop (When Done Testing)
```bash
docker-compose down
```

---

## ☁️ Deploy to AWS EC2 (Free Tier)

### Full Guide
See **[AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md)** for complete step-by-step instructions.

### Quick Summary
1. **Launch EC2 Instance**:
   - Type: t3.micro (free tier)
   - OS: Ubuntu 22.04 LTS
   - Security: Open ports 22 (SSH), 80, 8000, 8501

2. **SSH & Setup**:
   ```bash
   ssh -i your-key.pem ubuntu@<PUBLIC_IP>
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Deploy**:
   ```bash
   git clone <YOUR_REPO>
   cd ai-fraud-detector
   docker-compose build
   docker-compose up -d
   ```

4. **Access**:
   - Frontend: `http://<PUBLIC_IP>:8501`
   - Backend: `http://<PUBLIC_IP>:8000`
   - Docs: `http://<PUBLIC_IP>:8000/docs`

---

## 📊 Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                  Docker Network                          │
│                  (phishing_network)                       │
│                                                          │
│  ┌──────────────────┐        ┌──────────────────┐       │
│  │   Frontend       │        │    Backend       │       │
│  │  (Streamlit)     │        │   (FastAPI)      │       │
│  │   Port 8501      │◄─HTTP──│   Port 8000      │       │
│  │                  │        │                  │       │
│  │  • UI            │        │ • Models         │       │
│  │  • Visualization │        │ • API            │       │
│  │  • User Input    │        │ • Prediction     │       │
│  └──────────────────┘        │                  │       │
│                              │ • ML Training    │       │
│                              │ • Data Process   │       │
│  ┌──────────────────┐        └──────────────────┘       │
│  │     MLflow       │             │                     │
│  │   (Optional)     │             ├─ Models             │
│  │    Port 5000     │             ├─ Data               │
│  │                  │             └─ Artifacts          │
│  │ • Experiments    │                                    │
│  │ • Metrics        │                                    │
│  │ • Models         │                                    │
│  └──────────────────┘                                    │
│                                                          │
│  Volumes:                                                │
│  • ./mlruns (MLflow metadata)                            │
│  • ./mlflow_artifacts (Model artifacts)                 │
│  • ./backend/data (Training data)                        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration Reference

### Environment Variables

**Frontend** (docker-compose):
```yaml
environment:
  - API_URL=http://backend:8000
```

**Backend** (docker-compose):
```yaml
environment:
  - PYTHONUNBUFFERED=1
  - MLFLOW_TRACKING_URI=sqlite:///mlflow.db
  - API_HOST=0.0.0.0
  - API_PORT=8000
```

### Port Mapping

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Frontend | 8501 | HTTP | Streamlit UI |
| Backend | 8000 | HTTP/REST | FastAPI API |
| MLflow | 5000 | HTTP | Experiment tracking |

---

## 🐛 Troubleshooting

### Frontend can't connect to backend
```bash
# Check backend is running
docker-compose ps

# Check logs
docker-compose logs backend

# Test connection
curl http://backend:8000/health

# Fix: Restart backend
docker-compose restart backend
```

### Docker build fails
```bash
# Clear cache
docker-compose build --no-cache

# Check for file errors
docker-compose build --progress=plain

# View detailed logs
docker build -f Dockerfile.frontend . --progress=plain
```

### Port already in use
```bash
# Find process using port
sudo lsof -i :8501

# Kill if needed
sudo kill -9 <PID>

# Or change docker-compose port mapping:
# ports:
#   - "8502:8501"
```

### Out of memory
```bash
# Check memory usage
free -h

# Reduce MLflow if needed:
docker-compose stop mlflow

# Or remove from docker-compose.yml temporarily
```

---

## 📈 Monitoring & Maintenance

### Daily Checks
```bash
# Service status
docker-compose ps

# Resource usage
docker stats

# Recent logs
docker-compose logs --tail 20
```

### Weekly Tasks
```bash
# Update system
git pull
docker-compose build
docker-compose up -d

# Clean unused images
docker image prune

# Backup MLflow artifacts
tar -czf mlflow_backup_$(date +%Y%m%d).tar.gz mlruns/ mlflow_artifacts/
```

### Monthly Tasks
```bash
# Review model performance
# Access MLflow UI: http://localhost:5000

# Archive old experiment runs
# Clean up old data

# Update dependencies
pip install --upgrade -r requirements.txt
pip install --upgrade -r frontend/requirements.txt
```

---

## 💰 Cost Breakdown

### AWS Free Tier (12 months)
| Resource | Quota | Cost |
|----------|-------|------|
| EC2 t3.micro | 750 hours/month | $0 |
| Data Transfer | 1 GB outbound | $0 |
| EBS Storage | 30 GB/month | $0 |
| **Total** | - | **$0/month** |

### After Free Tier
| Resource | Usage | Cost/Month |
|----------|-------|-----------|
| EC2 t3.micro | 730 hours | ~$7.00 |
| EBS Storage | 30 GB | ~$1.50 |
| **Total** | - | **~$8.50/month** |

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **[AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md)** | Full AWS EC2 setup guide |
| **[README.md](./README.md)** | Project overview & architecture |
| **[QUICKSTART.md](./QUICKSTART.md)** | Quick reference for common tasks |
| **[DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)** | Summary of changes made |
| **[docker-compose.yml](./docker-compose.yml)** | Service configuration |

---

## 🎓 Key Concepts

### Docker Compose
- Orchestrates multiple services (frontend, backend, MLflow)
- Manages networking between containers
- Handles volume mounting for data persistence
- Defines health checks and restart policies

### Streamlit
- Python web framework for data apps
- Single-file application (app.py)
- Automatic hot reloading during development
- Built-in UI components and visualizations

### FastAPI
- Modern Python API framework
- Automatic API documentation
- Type hints and validation
- Async support

### EC2 Free Tier
- t3.micro: 1 vCPU, 1 GB RAM
- 30 GB storage/month
- 1 GB data transfer/month
- 750 hours/month compute (≈ always-on)

---

## ✨ Next Steps

1. **Test Locally** (5 min)
   ```bash
   docker-compose build && docker-compose up -d
   # Test at http://localhost:8501
   ```

2. **Review AWS Guide** (10 min)
   - Read AWS_DEPLOYMENT.md
   - Plan AWS account setup

3. **Deploy to AWS** (15-20 min)
   - Launch EC2 instance
   - SSH and install Docker
   - Run docker-compose

4. **Go Live** (5 min)
   - Share public IP or domain
   - Monitor logs
   - Track metrics in MLflow

---

## 🆘 Getting Help

| Issue | Resource |
|-------|----------|
| Docker/Compose | [Docker Docs](https://docs.docker.com) |
| Streamlit | [Streamlit Docs](https://docs.streamlit.io) |
| FastAPI | [FastAPI Docs](https://fastapi.tiangolo.com) |
| AWS EC2 | [AWS Docs](https://docs.aws.amazon.com/ec2/) |
| MLflow | [MLflow Docs](https://mlflow.org/docs/) |

---

## 📞 Quick Reference

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Logs
docker-compose logs -f

# Status
docker-compose ps

# Stop
docker-compose down

# SSH to AWS (example)
ssh -i key.pem ubuntu@54.123.45.67

# Deploy on AWS
git clone <repo> && cd ai-fraud-detector && docker-compose up -d
```

---

**Ready to deploy!** 🚀

Start with local testing, then follow AWS_DEPLOYMENT.md for cloud deployment.

