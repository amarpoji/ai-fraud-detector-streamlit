import os
import yaml
import mlflow
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

def load_config(config_path='params.yaml'):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config or {}
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error loading config: {e}")
        return {}

def setup_mlflow(config):
    """Setup MLflow tracking using params.yaml settings."""
    mlflow_config = config.get('mlflow_ui', {})
    use_dagshub = mlflow_config.get('use_dagshub', False)
    
    if use_dagshub:
        try:
            import dagshub
            repo_owner = mlflow_config.get('repo_owner')
            repo_name = mlflow_config.get('repo_name')
            
            if repo_owner and repo_name:
                dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
                print(f"✓ Connected to DagsHub MLflow: {repo_owner}/{repo_name}")
            else:
                print("⚠ DagsHub config missing repo_owner or repo_name.")
        except ImportError:
            print("⚠ dagshub library not installed. Run: pip install dagshub")
    
    if not mlflow.get_tracking_uri() or "http" not in mlflow.get_tracking_uri():
        tracking_uri = os.getenv('MLFLOW_TRACKING_URI')
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
            print(f"✓ Using MLFLOW_TRACKING_URI: {tracking_uri}")
        else:
            print("ℹ Using local MLflow tracking (mlruns folder)")

    experiment_name = mlflow_config.get('experiment_name', 'email-phishing-detection')
    mlflow.set_experiment(experiment_name)
    print(f"✓ Active Experiment: {experiment_name}")


if __name__ == '__main__':
    config = load_config()
    setup_mlflow(config)
    sys.exit(0)


