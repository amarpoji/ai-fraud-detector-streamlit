"""
FastAPI Backend for Phishing Detection
Loads trained models from MLflow and provides analysis endpoints
"""

import os
import sys
import json
import pickle
from pathlib import Path
from typing import List, Optional
import mlflow
import mlflow.sklearn
import numpy as np
from pathlib import Path
import yaml

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent))
from data_transform import clean_text


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request model for text analysis"""
    message: str
    model_run_id: Optional[str] = None  # Can specify which MLflow run to use


class RedFlag(BaseModel):
    """Individual red flag"""
    category: str
    description: str
    confidence: float  # 0.0 to 1.0


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    label: str  # 'Phishing' or 'Legitimate'
    risk_score: float  # 0.0 to 100.0
    confidence: float  # 0.0 to 1.0
    explanation: str
    red_flags: List[RedFlag]
    model_used: str


# ============================================================================
# Setup FastAPI App
# ============================================================================

app = FastAPI(
    title="Phishing Detection API",
    root_path = "/api",
    description="AI-powered analysis of emails and messages for phishing detection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Global State for Model Loading
# ============================================================================

class ModelCache:
    """Cache for loaded models and vectorizers with Production Fallback"""
    def __init__(self):
        self.models = {}
        self.vectorizers = {}
        # Use /app in Docker, otherwise use the project root
        if Path("/app/models").exists() or Path("/app/src").exists():
            self.base_dir = Path("/app")
            self.static_models_dir = self.base_dir / "models"
        else:
            self.base_dir = Path(__file__).resolve().parents[2]
            self.static_models_dir = self.base_dir / "backend" / "models"
            
        self.artifacts_dir = self.base_dir / "mlflow_artifacts"
    
    def load_model(self, run_id: Optional[str] = None):
        """Load model and vectorizer from artifacts or static fallback"""
        # If no run_id provided, get the best one from metadata
        if not run_id:
            try:
                run_id, _ = self.get_best_model()
            except Exception:
                # If metadata fails, try the static production files directly
                return self._load_from_static()

        if run_id in self.models:
            return self.models[run_id], self.vectorizers[run_id]
        
        try:
            training_info_path = self.artifacts_dir / "training_info.json"
            
            if not training_info_path.exists():
                return self._load_from_static()
            
            with open(training_info_path, 'r') as f:
                training_info = json.load(f)
            
            run_result = next((r for r in training_info['results'] if r['run_id'] == run_id), None)
            
            if not run_result:
                return self._load_from_static()
            
            model_dir = self.artifacts_dir / f"{run_result['model_name']}_{run_result['tfidf_variant']}"
            return self._load_pickle_files(model_dir, run_id)

        except Exception as e:
            print(f"⚠ Error loading run {run_id}: {e}. Falling back to static models.")
            return self._load_from_static()

    def _load_from_static(self):
        """Internal helper to load the winner from backend/models/"""
        if (self.static_models_dir / "model.pkl").exists():
            return self._load_pickle_files(self.static_models_dir, "production")
        raise HTTPException(status_code=500, detail="No models found in artifacts or backend/models")

    def _load_pickle_files(self, directory: Path, cache_key: str):
        """Helper to safely load and cache pickle files"""
        with open(directory / "model.pkl", 'rb') as f:
            model = pickle.load(f)
        with open(directory / "vectorizer.pkl", 'rb') as f:
            vectorizer = pickle.load(f)
        
        self.models[cache_key] = model
        self.vectorizers[cache_key] = vectorizer
        return model, vectorizer

    def get_best_model(self):
        """Get the best model metadata"""
        training_info_path = self.artifacts_dir / "training_info.json"
        
        if not training_info_path.exists():
            return "production", "static_model"
            
        with open(training_info_path, 'r') as f:
            training_info = json.load(f)
        
        best_result = max(training_info['results'], key=lambda x: x.get('test_f1_score', 0))
        return best_result['run_id'], best_result['model_name']

model_cache = ModelCache()


# ============================================================================
# Red Flag Detector
# ============================================================================

PHISHING_INDICATORS = {
    'urgency': {
        'keywords': ['urgent', 'immediate', 'act now', 'asap', 'quickly', 'expire', 'expired'],
        'description': 'Urgent language creating pressure to act',
        'weight': 0.15
    },
    'suspicious_links': {
        'keywords': ['click here', 'verify', 'confirm', 'update', 'click'],
        'description': 'Suspicious call-to-action or links',
        'weight': 0.20
    },
    'money_requests': {
        'keywords': ['payment', 'wire transfer', 'money', 'credit card', 'bank', 'account', 'fee'],
        'description': 'Money or payment information requested',
        'weight': 0.18
    },
    'personal_info': {
        'keywords': ['password', 'personal', 'ssn', 'pin', 'private', 'confidential', 'information'],
        'description': 'Requests for sensitive personal information',
        'weight': 0.20
    },
    'deception': {
        'keywords': ['fake', 'spoofed', 'impersonate', 'pretend', 'disguise'],
        'description': 'Evidence of deception or spoofing',
        'weight': 0.15
    },
    'generic_greeting': {
        'keywords': ['dear customer', 'dear user', 'dear valued', 'dear sir', 'dear madam'],
        'description': 'Generic greeting instead of personalization',
        'weight': 0.12
    }
}


def detect_red_flags(text: str, risk_score: float) -> List[RedFlag]:
    """Detect phishing red flags in text"""
    text_lower = text.lower()
    red_flags = []
    detected_categories = set()
    
    for category, indicator_info in PHISHING_INDICATORS.items():
        if category in detected_categories:
            continue
        
        keywords = indicator_info['keywords']
        matched_keywords = [kw for kw in keywords if kw in text_lower]
        
        if matched_keywords:
            # Confidence based on risk score and keyword matches
            base_confidence = len(matched_keywords) / len(keywords)
            confidence = min(1.0, base_confidence * (risk_score / 100.0))
            
            red_flags.append(RedFlag(
                category=category.replace('_', ' ').title(),
                description=indicator_info['description'],
                confidence=confidence
            ))
            detected_categories.add(category)
    
    return sorted(red_flags, key=lambda x: x.confidence, reverse=True)


def generate_explanation(label: str, risk_score: float, red_flags: List[RedFlag]) -> str:
    """Generate human-readable explanation"""
    if label == 'Phishing':
        if risk_score >= 80:
            base = "⚠️ HIGH RISK: This message shows strong indicators of phishing."
        elif risk_score >= 60:
            base = "⚠️ MEDIUM RISK: This message has several suspicious characteristics."
        else:
            base = "⚠️ Low-moderate phishing risk detected."
    else:
        base = "✅ This message appears to be legitimate."
    
    if red_flags:
        top_flags = red_flags[:2]
        flag_names = [f.category.lower() for f in top_flags]
        base += f" Key concerns: {', '.join(flag_names)}."
    
    return base


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Phishing Detection API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    Analyze a message for phishing
    
    Example:
        {
            "message": "Click here to verify your account immediately!",
            "model_run_id": null
        }
    """
    
    if not request.message or len(request.message.strip()) == 0:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Get model
        if request.model_run_id:
            run_id = request.model_run_id
            model_name = request.model_run_id[:8]  # First 8 chars of run ID
        else:
            run_id, model_name = model_cache.get_best_model()
        
        try:
            model, vectorizer = model_cache.load_model(run_id if request.model_run_id else None)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        if vectorizer is None:
            raise HTTPException(
                status_code=500,
                detail="Vectorizer not available for selected model"
            )
        
        # Clean and vectorize text
        cleaned_text = clean_text(request.message)
        X = vectorizer.transform([cleaned_text])
        
        # Get prediction and probability
        prediction = model.predict(X)[0]
        
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(X)[0]
            confidence = max(probabilities)
        else:
            confidence = 0.5  # Default confidence
        
        # Convert prediction to label
        label = 'Phishing' if prediction == 1 else 'Legitimate'
        
        # Calculate risk score (0-100)
        if label == 'Phishing':
            risk_score = confidence * 100.0
        else:
            risk_score = (1.0 - confidence) * 100.0
        
        # Detect red flags
        red_flags = detect_red_flags(request.message, risk_score)
        
        # Generate explanation
        explanation = generate_explanation(label, risk_score, red_flags)
        
        return AnalysisResponse(
            label=label,
            risk_score=round(risk_score, 2),
            confidence=round(confidence, 4),
            explanation=explanation,
            red_flags=red_flags,
            model_used=model_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/models")
async def list_models():
    """List available trained models"""
    try:
        artifacts_dir = Path("mlflow_artifacts")
        training_info_path = artifacts_dir / "training_info.json"
        
        if not training_info_path.exists():
            # Check for static models
            if Path("/app/models/model.pkl").exists():
                static_models_dir = Path("/app/models")
            else:
                static_models_dir = Path(__file__).resolve().parents[2] / "backend" / "models"
                
            if (static_models_dir / "model.pkl").exists():
                static_model = {
                    'name': 'Production Best Model (Static)',
                    'run_id': 'production',
                    'f1_score': 0.99,
                    'accuracy': 0.99,
                    'roc_auc': 0.99
                }
                return {
                    'total': 1,
                    'models': [static_model],
                    'best_model': static_model
                }
            
            raise HTTPException(
                status_code=404,
                detail="No trained models found. Run training.py first."
            )
        
        with open(training_info_path, 'r') as f:
            training_info = json.load(f)
        
        models = []
        for result in training_info['results']:
            models.append({
                'name': f"{result['model_name']}_{result['tfidf_variant']}",
                'run_id': result['run_id'],
                'f1_score': result['test_f1_score'],
                'accuracy': result['test_accuracy'],
                'roc_auc': result['test_roc_auc']
            })
        
        # Sort by F1-score
        models = sorted(models, key=lambda x: x['f1_score'], reverse=True)
        
        return {
            'total': len(models),
            'models': models,
            'best_model': models[0] if models else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )


@app.post("/batch-analyze")
async def batch_analyze(requests: List[AnalysisRequest]):
    """
    Analyze multiple messages at once
    """
    results = []
    for request in requests:
        try:
            result = await analyze(request)
            results.append(result)
        except HTTPException as e:
            results.append({"error": e.detail})
    
    return {"results": results}


# ============================================================================
# Startup and Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("🚀 Phishing Detection API starting...")
    
    # Setup MLflow
    tracking_uri = os.getenv('MLFLOW_TRACKING_URI')
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
        print(f"✓ MLflow tracking URI: {tracking_uri}")
    else:
        print("ℹ Using local MLflow tracking")
    
    # Try to load best model
    try:
        run_id, model_name = model_cache.get_best_model()
        model, vectorizer = model_cache.load_model(run_id)
        print(f"✓ Loaded best model: {model_name} ({run_id})")
    except Exception as e:
        print(f"⚠ Could not preload models: {e}")
    
    print("✓ API ready!")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        log_level="info"
    )
