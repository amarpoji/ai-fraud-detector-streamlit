import os
import yaml
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
import sys
import json
from pathlib import Path
from datetime import datetime
import pickle
import warnings
import shutil  # Added this - CRITICAL for copying files

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, confusion_matrix, classification_report,
                             roc_auc_score, roc_curve, matthews_corrcoef)
from utils import load_config, setup_mlflow

warnings.filterwarnings('ignore')



def load_test_data(processed_path, test_size=0.2, random_state=42):

    """Load test data with stratification."""

    print(f"\n📂 Loading test data from {processed_path}...")
    if not Path(processed_path).exists():
        print(f"❌ ERROR: Processed data not found at {processed_path}")
        sys.exit(1)
    df = pd.read_csv(processed_path)

    X_train, X_test, y_train, y_test = train_test_split(
        df['cleaned_text'],
        df['label'],
        test_size=test_size,
        random_state=random_state,
        stratify=df['label']
    )
    print(f"   Test set size: {len(X_test)}")
    print(f"   Class distribution: {np.bincount(y_test.values)}")
    return X_test, y_test





def evaluate_model(model, X_test, y_test, model_name):
    """Evaluate model and return comprehensive metrics."""
    print(f"\n🔍 Evaluating {model_name}...")
    y_pred = model.predict(X_test)

    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'matthews_cc': matthews_corrcoef(y_test, y_pred)
    }

    try:
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba)
    except:
        metrics['roc_auc'] = None

    return metrics, y_pred

def log_evaluation_artifacts(y_test, y_pred, y_pred_proba=None, model_name='model'):
    """Log evaluation artifacts to MLflow."""
    project_root = Path(__file__).resolve().parents[2]
    artifacts_dir = project_root / "mlflow_artifacts" / model_name
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    clf_report = classification_report(y_test, y_pred)
    report_path = artifacts_dir / "classification_report.txt"
    with open(report_path, 'w') as f:
        f.write(clf_report)
    mlflow.log_artifact(str(report_path), artifact_path="evaluation/reports")
    
    cm = confusion_matrix(y_test, y_pred)
    cm_path = artifacts_dir / "confusion_matrix.txt"
    with open(cm_path, 'w') as f:
        f.write(str(cm))
    mlflow.log_artifact(str(cm_path), artifact_path="evaluation/matrices")
    
    print(f"   ✓ Evaluation artifacts logged")

def evaluate_single_model(run_id, model_name, tfidf_variant, config, X_test, y_test):
    """Evaluate a single model using locally stored pickle files."""
    display_name = f"{model_name}_{tfidf_variant}"
    print(f"\n📊 Evaluating: {display_name}")
    
    project_root = Path(__file__).resolve().parents[2]
    model_dir = project_root / "mlflow_artifacts" / display_name
    
    model_file = model_dir / "model.pkl"
    vectorizer_file = model_dir / "vectorizer.pkl"

    if not model_file.exists() or not vectorizer_file.exists():
        print(f"   ❌ Error: Local artifacts not found in {model_dir}")
        return None

    with mlflow.start_run(run_name=f"eval_{display_name}") as eval_run:
        mlflow.log_param("training_run_id", run_id)
        
        try:
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            
            with open(vectorizer_file, 'rb') as f:
                vectorizer = pickle.load(f)
            
            X_test_vec = vectorizer.transform(X_test)
            metrics, y_pred = evaluate_model(model, X_test_vec, y_test, display_name)
            
            for metric_name, metric_value in metrics.items():
                if metric_value is not None:
                    mlflow.log_metric(f"eval_{metric_name}", metric_value)
            
            # Prediction proba for ROC-AUC logging
            try:
                y_pred_proba = model.predict_proba(X_test_vec)[:, 1]
            except:
                y_pred_proba = None
            
            log_evaluation_artifacts(y_test, y_pred, y_pred_proba, display_name)
            return metrics
            
        except Exception as e:
            print(f"   ❌ Error during evaluation: {str(e)}")
            return None

def export_winning_model(best_model_name):
    """Copies winning model artifacts to backend/models/"""
    print(f"\n🏆 Exporting Winning Model: {best_model_name}")
    
    project_root = Path(__file__).resolve().parents[2]
    target_dir = project_root / "backend" / "models"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    source_dir = project_root / "mlflow_artifacts" / best_model_name
    source_model = source_dir / "model.pkl"
    source_vec = source_dir / "vectorizer.pkl"
    
    if source_model.exists() and source_vec.exists():
        shutil.copy2(source_model, target_dir / "model.pkl")
        shutil.copy2(source_vec, target_dir / "vectorizer.pkl")
        print(f"✅ Production artifacts saved to: {target_dir}")
    else:
        print(f"❌ Error: Could not find source artifacts in {source_dir}")

def main():
    """Main evaluation pipeline."""
    project_root = Path(__file__).resolve().parents[2]
    config = load_config(project_root / 'params.yaml')
    
    data_config = config.get('data', {})
    rel_processed_path = data_config.get('processed_path', 'backend/data/processed/email_dataset_processed.csv')
    processed_path = project_root / rel_processed_path
    
    setup_mlflow(config)
    
    X_test, y_test = load_test_data(
        str(processed_path),
        test_size=config.get('preprocessing', {}).get('train_test_split', 0.2),
        random_state=config.get('preprocessing', {}).get('random_state', 42)
    )
    
    training_info_path = project_root / "mlflow_artifacts" / "training_info.json"
    if not training_info_path.exists():
        print(f"\n❌ ERROR: Training info not found.")
        sys.exit(1)
    
    with open(training_info_path, 'r') as f:
        training_info = json.load(f)
    
    evaluation_results = {}
    for result in training_info['results']:
        metrics = evaluate_single_model(result['run_id'], result['model_name'], result['tfidf_variant'], config, X_test, y_test)
        if metrics:
            display_name = f"{result['model_name']}_{result['tfidf_variant']}"
            evaluation_results[display_name] = metrics
    
    eval_df = pd.DataFrame(evaluation_results).T
    if not eval_df.empty:
        print("\n" + eval_df.to_string())
        
        # Save the evaluation report for DVC
        report_path = project_root / "mlflow_artifacts" / "evaluation_report.csv"
        eval_df.to_csv(report_path)
        
        # Export the model with the highest F1 Score
        best_model_name = eval_df['f1_score'].idxmax()
        export_winning_model(best_model_name)

    return evaluation_results

if __name__ == '__main__':
    main()