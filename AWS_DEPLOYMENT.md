# AWS EC2 Deployment Guide (Free Tier)

## Overview
Deploy your Phishing Detector on AWS EC2 using the free tier (t3.micro instance).

---

## Prerequisites
- AWS Account (free tier eligible)
- git installed locally
- Docker installed (on your machine to build images)
- ECR (Elastic Container Registry) access

---

## Step 1: Create EC2 Instance

### 1.1 Launch EC2 Instance
1. Go to AWS Console → EC2 → Instances → Launch Instances
2. **Name**: `phishing-detector-app`
3. **AMI**: Ubuntu Server 22.04 LTS (free tier eligible)
4. **Instance Type**: `t3.micro` (free tier)
5. **Key Pair**: Create new or use existing
   - Download `.pem` file and save securely
6. **Security Group**: Create new with rules:
   ```
   Type: SSH, Port: 22, Source: Your IP
   Type: HTTP, Port: 80, Source: 0.0.0.0/0
   Type: Custom TCP, Port: 8501, Source: 0.0.0.0/0
   Type: Custom TCP, Port: 8000, Source: 0.0.0.0/0
   ```
7. **Storage**: 30 GB (free tier includes 30GB/month)
8. Click **Launch Instance**

### 1.2 Get Instance Details
- Copy the **Public IPv4 address**
- Note the **Instance ID**

---

## Step 2: Connect to Instance

### Option A: SSH from Terminal (Recommended)
```bash
# Set key permissions (Mac/Linux)
chmod 400 your-key.pem

# SSH into instance
ssh -i your-key.pem ubuntu@<PUBLIC_IP>

# On Windows PowerShell
ssh -i .\your-key.pem ubuntu@<PUBLIC_IP>
```

### Option B: Using EC2 Instance Connect (Browser-based)
1. Select instance
2. Click **Connect** → **EC2 Instance Connect** tab
3. Click **Connect** (opens browser terminal)

---

## Step 3: Setup Docker on EC2

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

---

## Step 4: Clone Project & Deploy

### 4.1 Clone Repository
```bash
cd ~
git clone <YOUR_REPO_URL> phishing-detector
cd phishing-detector
```

### 4.2 Create Environment File (Optional)
```bash
# Create .env file for any environment variables
cat > .env << EOF
API_HOST=0.0.0.0
API_PORT=8000
PYTHONUNBUFFERED=1
EOF
```

### 4.3 Build & Run with Docker Compose
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f frontend
docker-compose logs -f backend
```

---

## Step 5: Access Application

### Access Points:
- **Streamlit Frontend**: `http://<PUBLIC_IP>:8501`
- **FastAPI Backend**: `http://<PUBLIC_IP>:8000`
- **API Docs**: `http://<PUBLIC_IP>:8000/docs`
- **MLflow UI** (if enabled): `http://<PUBLIC_IP>:5000`

---

## Step 6: Monitor & Maintain

### Check Logs
```bash
# View all logs
docker-compose logs

# Follow logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# View recent logs
docker-compose logs --tail 50
```

### Stop Services
```bash
# Stop all services (data persists)
docker-compose down

# Stop and remove volumes (careful - data loss!)
docker-compose down -v
```

### Restart Services
```bash
docker-compose restart
```

### Update Code
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Step 7: Domain Setup (Optional)

### Point Domain to EC2
1. Get instance **Elastic IP** (to keep IP static):
   - EC2 → Elastic IPs → Allocate
   - Associate with your instance
   
2. Point your domain to the Elastic IP:
   - In your domain registrar, update DNS A record to Elastic IP
   - Example: `A record: @ → 54.123.456.789`

3. Access via domain:
   - `http://yourdomain.com:8501`

---

## Cost Estimation

| Service | Free Tier Quota | Estimated Monthly Cost |
|---------|-----------------|------------------------|
| EC2 t3.micro | 750 hours/month | $0 (within free tier) |
| Data Transfer | 1 GB outbound/month | $0 (within free tier) |
| Storage (EBS) | 30 GB/month | $0 (within free tier) |
| **Total** | - | **$0** (first 12 months) |

After free tier (12 months):
- t3.micro: ~$7/month
- EBS Storage: ~$1/month
- Total: ~$8/month

---

## Troubleshooting

### Services Won't Start
```bash
# Check Docker status
docker ps -a

# View detailed error logs
docker-compose logs --tail 100

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8501

# Kill process (if needed)
sudo kill -9 <PID>
```

### Out of Memory
```bash
# Check memory usage
free -h

# Stop non-essential services
docker-compose down mlflow  # if not needed
```

### Cannot Connect to Backend
- Verify backend is running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`
- Verify security group allows port 8000
- Ensure both containers are on same network

---

## Advanced: Use AWS ECR (Optional)

Instead of building on EC2, build locally and push to ECR:

### Build & Push to ECR
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Tag images
docker tag phishing-detector:backend <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/phishing-detector:backend
docker tag phishing-detector:frontend <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/phishing-detector:frontend

# Push to ECR
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/phishing-detector:backend
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/phishing-detector:frontend

# Update docker-compose.yml to use ECR images
# Then run on EC2: docker-compose up -d
```

---

## Cleanup (When Done)

### Stop Services
```bash
docker-compose down
```

### Terminate EC2 Instance (WARNING: Deletes everything)
1. EC2 → Instances → Select instance
2. Instance State → Terminate

### Release Elastic IP (If Created)
1. EC2 → Elastic IPs
2. Select and Release

---

## Support & Documentation

- **Streamlit Docs**: https://docs.streamlit.io
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Docker Docs**: https://docs.docker.com
- **AWS Free Tier**: https://aws.amazon.com/free

