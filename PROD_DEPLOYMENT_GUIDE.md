# Production Deployment Guide (Pre-Trained Model)

## Overview
This guide covers how to deploy the Phishing Detector on AWS EC2 using a lightweight, production-ready approach. Instead of training the model on the live server or running MLflow, this method uses your **pre-trained best model** via the `docker-compose.prod.yml` configuration.

---

## Step 0: Local Preparation

Before deploying, ensure your best-trained models are ready in your repository:
1. Train your model locally.
2. Copy your best `model.pkl` and `vectorizer.pkl` into the `backend/models/` directory of your project.
3. Push these changes to your Git repository (or plan to manually upload them to the EC2 instance).

---

## Step 1: Create the EC2 Instance

1. Go to **AWS Console → EC2 → Instances → Launch Instances**.
2. **Name**: `phishing-detector-prod`
3. **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
4. **Instance Type**: `t3.micro` (Free tier eligible)
5. **Key Pair**: Create a new key pair (save the `.pem` file) or use an existing one.
6. **Network Settings (Security Group)**: Create a new security group with these inbound rules:
   * **Type**: `HTTP`, **Port**: `80`, **Source**: `Anywhere-IPv4 (0.0.0.0/0)` *(Allows web access)*
   * **Type**: `SSH`, **Port**: `22`, **Source**: `Anywhere-IPv4 (0.0.0.0/0)` *(Required if you want to use the AWS Browser Connect tool!)*
7. **Storage**: `30 GB` gp3 (Free tier includes 30GB/month).
8. Click **Launch Instance**.

> Wait a few minutes for the instance status to show **2/2 checks passed**. Note down your instance's **Public IPv4 address**.

---

## Step 2: Connect to Your Instance

### Option A: Browser-Based Connect (Easiest)
1. Select your instance in the AWS Console.
2. Click **Connect** at the top.
3. Choose the **EC2 Instance Connect** tab.
4. Click **Connect**. A terminal will open right in your browser. *(Note: This only works if your SSH Security Group is set to `0.0.0.0/0` as instructed above).*

### Option B: Local Terminal
1. Open PowerShell or your Mac/Linux Terminal.
2. Navigate to where you saved your key pair:
   ```bash
   cd ~/Downloads
   ```
3. Connect using SSH:
   ```bash
   # On Mac/Linux, restrict permissions first:
   # chmod 400 your-key.pem
   
   ssh -i your-key.pem ubuntu@<YOUR_PUBLIC_IP>
   ```

---

## Step 3: Install Docker & Docker Compose

Once connected to your EC2 instance terminal, run these commands to prepare the server:

```bash
# 1. Update the system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. Add your user to the docker group so you don't need 'sudo'
sudo usermod -aG docker $USER
newgrp docker

# 4. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

---

## Step 4: Clone the Code

Clone your repository to the server:

```bash
cd ~
git clone https://github.com/amarpoji/ai-fraud-detector-streamlit.git
cd ai-fraud-detector-streamlit

# If you need to switch to a specific branch:
# git checkout main
```

*(If you didn't commit your `model.pkl` and `vectorizer.pkl` to GitHub, you will need to upload them securely from your local machine to the EC2 `backend/models/` folder using `scp` or a tool like FileZilla).*

---

## Step 5: Deploy the App (Production Mode)

Because we are doing a production deployment with pre-trained models, we will use the `docker-compose.prod.yml` file. This skips the heavy MLflow container and model training setup.

```bash
# 1. Build the Docker images
docker-compose -f docker-compose.prod.yml build

# 2. Start the application in detached mode
docker-compose -f docker-compose.prod.yml up -d
```

Check to ensure all containers are running successfully:
```bash
docker ps
```
You should see `phishing_frontend`, `phishing_backend`, and `phishing_proxy`.

---

## Step 6: Access the Application

Open your browser and navigate to your instance's Public IP address:
```
http://<YOUR_PUBLIC_IP>
```
Your app should load immediately and be ready to classify text using the static models you provided.

---

## Helpful Commands

**View Application Logs**
```bash
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f backend
```

**Restart the Application**
```bash
docker-compose -f docker-compose.prod.yml restart
```

**Updating Code in the Future**
```bash
# 1. Pull the latest code
git pull

# 2. Rebuild and restart the containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```
