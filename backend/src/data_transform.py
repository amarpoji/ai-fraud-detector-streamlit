import pandas as pd
import yaml
import re
from pathlib import Path
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import sys

# --- OPTIONAL: Force NLTK path if you still see resolution errors ---
# nltk.data.path.append(str(Path.home() / "AppData" / "Roaming" / "nltk_data"))

# Download required NLTK data
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)

# 1. GLOBAL VARIABLES: Loaded once to save time and memory
STOP_WORDS = set(stopwords.words('english'))
IMPORTANT_TOKENS = {'url', 'email', 'click', 'verify', 'confirm', 'urgent', 'act', 'now', 'expire'}

def load_config(config_path='params.yaml'):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}

def clean_text(text):
    """Advanced text cleaning for phishing detection."""
    if not isinstance(text, str):
        return ""
    
    # URL and Email masking
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', 'URL', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL', text)
    
    # Normalization
    text = re.sub(r'\s+', ' ', text).strip().lower()
    text = re.sub(r'[^a-z0-9\s$€£¥%()[\]\-]', ' ', text)
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    
    # Tokenization using global stop_words for speed
    tokens = word_tokenize(text)
    tokens = [
        token for token in tokens 
        if (token not in STOP_WORDS or token in IMPORTANT_TOKENS) and len(token) > 1
    ]
    
    return " ".join(tokens)

def transform_data(input_path, output_path=None):
    """Transform raw email dataset with cleaning and label encoding."""
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} records from {input_path}")

    # 1. DROP INITIAL NaNs
    initial_len = len(df)
    df = df.dropna(subset=['text', 'label'])
    print(f"Dropped {initial_len - len(df)} rows with missing text or labels.")

    # 2. LABEL TRANSFORMATION (Numeric only)
    label_map = {
        'spam': 1, 'Spam': 1, 'SPAM': 1,
        'ham': 0, 'Ham': 0, 'HAM': 0,
        1: 1, 0: 0, '1': 1, '0': 0 
    }
    df['label'] = df['label'].map(label_map).fillna(0).astype(int)
    print("✓ Labels converted to integers.")

    # 3. APPLY TEXT CLEANING
    print("🔄 Cleaning text (this may take a minute)...")
    df['cleaned_text'] = df['text'].apply(clean_text)
    
    # 4. FINAL CLEANUP: Remove rows that became empty after cleaning
    # Use pd.NA and then dropna for the most reliable removal
    df.loc[df['cleaned_text'].str.strip() == "", 'cleaned_text'] = pd.NA
    df = df.dropna(subset=['cleaned_text'])
    
    print(f"✓ Transformation complete. {len(df)} valid records remaining.")
    
    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"💾 Saved transformed data to {output_path}")
    
    return df

# ... (rest of your get_data_paths and main functions)


def get_data_paths():
    """Get data paths from config or use defaults."""
    config = load_config('params.yaml')
    
    # Try to get paths from config
    if config and 'data' in config:
        raw_path = config['data'].get('raw_path')
        processed_path = config['data'].get('processed_path')
    else:
        raw_path = None
        processed_path = None
    
    # Use defaults if not in config
    if not raw_path:
        raw_path = 'backend/data/raw/email_dataset.csv'
    if not processed_path:
        processed_path = 'backend/data/processed/email_dataset_processed.csv'
    
    return raw_path, processed_path


def main():
    """Main execution function."""
    # Get data paths
    raw_path, processed_path = get_data_paths()
    
    # Convert to absolute paths if they're relative
    if not Path(raw_path).is_absolute():
        raw_path = Path.cwd() / raw_path
    if not Path(processed_path).is_absolute():
        processed_path = Path.cwd() / processed_path
    
    print(f"Raw data path: {raw_path}")
    print(f"Processed data path: {processed_path}")
    
    # Verify raw data exists
    if not raw_path.exists():
        print(f"ERROR: Raw data file not found at {raw_path}")
        sys.exit(1)
    
    # Transform data
    df = transform_data(str(raw_path), str(processed_path))
    
    # Display sample
    print("\nSample of transformed data:")
    print(df[['text', 'cleaned_text']].head())
    
    return df


if __name__ == '__main__':
    main()
