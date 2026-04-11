import os
import yaml
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
import sys
from pathlib import Path
import json
import pickle
import time
from datetime import datetime

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, cross_validate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
import dagshub
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, roc_curve
import warnings
from utils import load_config, setup_mlflow
warnings.filterwarnings('ignore')



def load_processed_data(processed_path, test_size=0.2, random_state=42):
    """Load already transformed data and split into train/test."""
    print(f"\n📂 Loading processed data from {processed_path}...")
    
    if not Path(processed_path).exists():
        print(f"❌ ERROR: Processed data not found at {processed_path}")
        print("   Run data transformation first: python backend/src/data_transform.py")
        sys.exit(1)
    
    # Load data
    df = pd.read_csv(processed_path)
    print(f"   Loaded {len(df)} records")
    
    # Check required columns
    if 'cleaned_text' not in df.columns or 'label' not in df.columns:
        print(f"❌ ERROR: Missing required columns. Found: {list(df.columns)}")
        sys.exit(1)
    
    X = df['cleaned_text'].values
    y = df['label'].values
    
    # Split data with stratification for imbalanced datasets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    print(f"   Train set: {len(X_train)} samples")
    print(f"   Test set: {len(X_test)} samples")
    print(f"   Class distribution (train): {np.bincount(y_train)}")
    
    return X_train, X_test, y_train, y_test


def vectorize_text(X_train, X_test, tfidf_config):
    """
    Vectorize text using TfidfVectorizer with specified configuration.
    
    Returns:
        X_train_vec: Vectorized training data
        X_test_vec: Vectorized test data
        vectorizer: Fitted TfidfVectorizer instance
    """
    vectorizer = TfidfVectorizer(
        max_features=tfidf_config.get('max_features', 5000),
        ngram_range=tuple(tfidf_config.get('ngram_range', [1, 2])),
        min_df=tfidf_config.get('min_df', 2),
        max_df=tfidf_config.get('max_df', 0.95),
        stop_words='english'
    )
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    print(f"   TF-IDF vectorization complete")
    print(f"   Feature dimensions: {X_train_vec.shape[1]}")
    
    return X_train_vec, X_test_vec, vectorizer


def get_model(model_name, model_config):
    """Create model instance based on configuration."""
    model_type = model_config.get('type')
    
    if model_type == 'RandomForest':
        return RandomForestClassifier(
            n_estimators=model_config.get('n_estimators', 100),
            max_depth=model_config.get('max_depth', 15),
            min_samples_split=model_config.get('min_samples_split', 5),
            min_samples_leaf=model_config.get('min_samples_leaf', 2),
            random_state=model_config.get('random_state', 42),
            n_jobs=model_config.get('n_jobs', -1)
        )
    elif model_type == 'LogisticRegression':
        return LogisticRegression(
            C=model_config.get('C', 1.0),
            solver=model_config.get('solver', 'lbfgs'),
            max_iter=model_config.get('max_iter', 1000),
            random_state=model_config.get('random_state', 42)
        )
    elif model_type == 'NaiveBayes':
        return MultinomialNB(
            alpha=model_config.get('alpha', 1.0)
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def evaluate_model(model, X_train, X_test, y_train, y_test, model_name):
    """
    Evaluate model on test set and return comprehensive metrics.
    
    Returns:
        metrics_dict: Dictionary with all evaluation metrics
    """
    y_pred = model.predict(X_test)
    
    # For probabilistic metrics, use probability predictions
    if hasattr(model, 'predict_proba'):
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    else:
        y_pred_proba = model.decision_function(X_test)
        # Normalize to [0, 1]
        y_pred_proba = (y_pred_proba - y_pred_proba.min()) / (y_pred_proba.max() - y_pred_proba.min())
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0.0
    }
    
    return metrics, y_pred, y_pred_proba


def cross_validate_model(model, X_train, y_train, n_splits=5):
    """
    Perform cross-validation on training data.
    
    Returns:
        cv_scores: Dictionary with mean and std of CV scores
    """
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    scoring = {
        'accuracy': 'accuracy',
        'precision': 'precision',
        'recall': 'recall',
        'f1': 'f1',
        'roc_auc': 'roc_auc'
    }
    
    cv_results = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring, return_train_score=True)
    
    cv_scores = {}
    for metric in scoring.keys():
        train_scores = cv_results[f'train_{metric}']
        test_scores = cv_results[f'test_{metric}']
        
        cv_scores[f'cv_{metric}_mean'] = test_scores.mean()
        cv_scores[f'cv_{metric}_std'] = test_scores.std()
        cv_scores[f'cv_train_{metric}_mean'] = train_scores.mean()
    
    return cv_scores


def train_single_model(model_name, model_config, X_train, X_test, y_train, y_test, 
                       vectorizer, tfidf_name, tfidf_config, config):
    """
    Train a single model and log to MLflow.
    
    Returns:
        run_info: Dictionary with run information
    """
    print(f"\n{'='*60}")
    print(f"🤖 Training {model_name} with {tfidf_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    with mlflow.start_run(run_name=f"train_{model_name}_{tfidf_name}"):
        # Log parameters
        model_type = model_config.get('type')
        mlflow.log_param('model_name', model_name)
        mlflow.log_param('model_type', model_type)
        mlflow.log_param('tfidf_variant', tfidf_name)
        
        # Log model hyperparameters
        for param_name, param_value in model_config.items():
            if param_name != 'type':
                mlflow.log_param(f'model_{param_name}', param_value)
        
        # Log TF-IDF parameters
        for param_name, param_value in tfidf_config.items():
            mlflow.log_param(f'tfidf_{param_name}', param_value)
        
        # Create and train model
        model = get_model(model_name, model_config)
        model.fit(X_train, y_train)
        training_time = time.time() - start_time
        
        print(f"✓ Model trained in {training_time:.2f}s")
        
        # Evaluate on test set
        test_metrics, y_pred, y_pred_proba = evaluate_model(model, X_train, X_test, y_train, y_test, model_name)
        
        # Cross-validation
        cv_metrics = cross_validate_model(model, X_train, y_train, n_splits=5)
        
        # Log metrics
        mlflow.log_metric('training_time_seconds', training_time)
        
        # Log test metrics
        for metric_name, metric_value in test_metrics.items():
            mlflow.log_metric(f'test_{metric_name}', metric_value)
        
        # Log CV metrics
        for metric_name, metric_value in cv_metrics.items():
            mlflow.log_metric(metric_name, metric_value)
        
        # Create model signature
        try:
            signature = infer_signature(X_train, model.predict(X_train[:100]))
            print(f"✓ Model signature created")
        except Exception as e:
            print(f"⚠ Could not create signature: {e}")
            signature = None
        
        # Log model
        mlflow.sklearn.log_model(model, "model", signature=signature)
        
        # Save vectorizer as artifact
        vectorizer_path = "vectorizer.pkl"
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(vectorizer, f)
        mlflow.log_artifact(vectorizer_path)
        os.remove(vectorizer_path)
        
        run_id = mlflow.active_run().info.run_id
        
        # Also save model and vectorizer locally for direct loading
        model_dir = Path("mlflow_artifacts") / f"{model_name}_{tfidf_name}"
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_pkl_path = model_dir / "model.pkl"
        with open(model_pkl_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Save vectorizer
        vec_pkl_path = model_dir / "vectorizer.pkl"
        with open(vec_pkl_path, 'wb') as f:
            pickle.dump(vectorizer, f)
        
        print(f"✓ Saved model and vectorizer locally to {model_dir}")
        
        # Print metrics summary
        print(f"\n📊 Test Metrics:")
        print(f"   Accuracy:  {test_metrics['accuracy']:.4f}")
        print(f"   Precision: {test_metrics['precision']:.4f}")
        print(f"   Recall:    {test_metrics['recall']:.4f}")
        print(f"   F1-Score:  {test_metrics['f1_score']:.4f}")
        print(f"   ROC-AUC:   {test_metrics['roc_auc']:.4f}")
        
        print(f"\n📈 Cross-Validation (5-fold):")
        print(f"   CV Accuracy:  {cv_metrics['cv_accuracy_mean']:.4f} ± {cv_metrics['cv_accuracy_std']:.4f}")
        print(f"   CV F1-Score:  {cv_metrics['cv_f1_mean']:.4f} ± {cv_metrics['cv_f1_std']:.4f}")
        print(f"   CV ROC-AUC:   {cv_metrics['cv_roc_auc_mean']:.4f} ± {cv_metrics['cv_roc_auc_std']:.4f}")
        
        return {
            'model_name': model_name,
            'tfidf_variant': tfidf_name,
            'run_id': run_id,
            'test_metrics': test_metrics,
            'cv_metrics': cv_metrics,
            'training_time': training_time
        }


def main():
    """Main training orchestration."""
    print("\n" + "="*60)
    print("🚀 PHISHING DETECTOR - MODEL TRAINING")
    print("="*60)
    
    # Load configuration
    config = load_config('params.yaml')
    
    # Setup MLflow
    setup_mlflow(config)
    
    # Load and prepare data
    data_config = config.get('data', {})
    processed_path = data_config.get('processed_path', 'backend/data/processed/email_dataset_processed.csv')
    test_size = config.get('preprocessing', {}).get('train_test_split', 0.2)
    
    X_train, X_test, y_train, y_test = load_processed_data(processed_path, test_size=test_size)
    
    # Get TF-IDF variants
    tfidf_variants = config.get('preprocessing', {}).get('tfidf_variants', {
        'tfidf_v1': {
            'max_features': 5000,
            'ngram_range': [1, 2],
            'min_df': 2,
            'max_df': 0.95
        }
    })
    
    # Get model variants
    model_variants = config.get('model_variants', {})
    
    # Training results
    training_results = []
    
    # Train all model combinations
    total_experiments = len(tfidf_variants) * len(model_variants)
    current_experiment = 0
    
    for tfidf_name, tfidf_config in tfidf_variants.items():
        # Vectorize text
        print(f"\n🔄 Vectorizing text with {tfidf_name}...")
        X_train_vec, X_test_vec, vectorizer = vectorize_text(X_train, X_test, tfidf_config)
        
        for model_name, model_config in model_variants.items():
            current_experiment += 1
            print(f"\n[{current_experiment}/{total_experiments}]")
            
            # Train model
            result = train_single_model(
                model_name, model_config,
                X_train_vec, X_test_vec, y_train, y_test,
                vectorizer, tfidf_name, tfidf_config,
                config
            )
            
            training_results.append(result)
    
    # Save training info
    print(f"\n{'='*60}")
    print("💾 Saving training information...")
    
    # Create artifacts directory
    artifacts_dir = Path('mlflow_artifacts')
    artifacts_dir.mkdir(exist_ok=True)
    
    # Save training results
    training_info = {
        'timestamp': datetime.now().isoformat(),
        'total_experiments': len(training_results),
        'results': [
            {
                'model_name': r['model_name'],
                'tfidf_variant': r['tfidf_variant'],
                'run_id': r['run_id'],
                'test_f1_score': r['test_metrics']['f1_score'],
                'test_accuracy': r['test_metrics']['accuracy'],
                'test_roc_auc': r['test_metrics']['roc_auc'],
                'cv_f1_mean': r['cv_metrics']['cv_f1_mean']
            }
            for r in training_results
        ]
    }
    
    info_path = artifacts_dir / 'training_info.json'
    with open(info_path, 'w') as f:
        json.dump(training_info, f, indent=2)
    
    print(f"✓ Training info saved to {info_path}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ TRAINING COMPLETE - {len(training_results)} models trained")
    print(f"{'='*60}")
    print(f"\n📊 Top 3 Models by F1-Score:")
    
    sorted_results = sorted(training_results, key=lambda x: x['test_metrics']['f1_score'], reverse=True)
    for i, result in enumerate(sorted_results[:3], 1):
        print(f"\n{i}. {result['model_name']} ({result['tfidf_variant']})")
        print(f"   F1-Score: {result['test_metrics']['f1_score']:.4f}")
        print(f"   Accuracy: {result['test_metrics']['accuracy']:.4f}")
        print(f"   ROC-AUC:  {result['test_metrics']['roc_auc']:.4f}")
        print(f"   Run ID:   {result['run_id']}")
    
    print(f"\n💡 View results in MLflow:")
    print(f"   mlflow ui")
    print(f"   Then open http://localhost:5000")


if __name__ == '__main__':
    main()