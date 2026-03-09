#!/usr/bin/env python3
"""
Model Setup Script for Email Phishing Detection

This script downloads and sets up the required AI models for the project.
Models are not included in the git repository due to size and licensing considerations.

Usage:
    python setup_models.py

Requirements:
    - huggingface_hub
    - transformers
    - torch
"""

import os
import sys
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download

# Model configurations
MODELS = {
    "email_classifier": {
        "repo_id": "microsoft/DialoGPT-medium",  # Placeholder - replace with actual model
        "local_dir": "ai_services/phishing_classifier_final",
        "description": "Email content classification model"
    },
    "url_classifier": {
        "repo_id": "microsoft/DialoGPT-small",  # Placeholder - replace with actual model
        "local_dir": "ai_services/url_phishing_classifier_final",
        "description": "URL classification model"
    }
}

def download_model(model_name, force=False):
    """Download a specific model"""
    if model_name not in MODELS:
        print(f"❌ Unknown model: {model_name}")
        print(f"Available models: {list(MODELS.keys())}")
        return False

    config = MODELS[model_name]
    local_dir = Path(config["local_dir"])

    # Check if model already exists
    if local_dir.exists() and not force:
        print(f"✅ {model_name} already exists at {local_dir}")
        return True

    # Remove existing directory if force download
    if force and local_dir.exists():
        import shutil
        shutil.rmtree(local_dir)
        print(f"🗑️ Removed existing {model_name} directory")

    print(f"⬇️ Downloading {model_name} ({config['description']})...")
    print(f"   From: {config['repo_id']}")
    print(f"   To: {local_dir}")

    try:
        # Download model
        snapshot_download(
            repo_id=config["repo_id"],
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            ignore_patterns=["*.md", "*.txt", "*.json"]  # Skip non-essential files
        )
        print(f"✅ Successfully downloaded {model_name}")
        return True

    except Exception as e:
        print(f"❌ Failed to download {model_name}: {e}")
        return False

def create_mock_model(model_name):
    """Create a mock model for development/testing purposes"""
    if model_name not in MODELS:
        print(f"❌ Unknown model: {model_name}")
        return False

    config = MODELS[model_name]
    local_dir = Path(config["local_dir"])

    # Create directory structure
    local_dir.mkdir(parents=True, exist_ok=True)

    # Create mock config.json
    config_path = local_dir / "config.json"
    mock_config = {
        "model_type": "distilbert",
        "vocab_size": 30522,
        "hidden_size": 768,
        "num_hidden_layers": 6,
        "num_attention_heads": 12,
        "intermediate_size": 3072,
        "hidden_act": "gelu",
        "hidden_dropout_prob": 0.1,
        "attention_probs_dropout_prob": 0.1,
        "max_position_embeddings": 512,
        "type_vocab_size": 2,
        "initializer_range": 0.02,
        "layer_norm_eps": 1e-12,
        "pad_token_id": 0,
        "position_embedding_type": "absolute",
        "architectures": ["DistilBertForSequenceClassification"],
        "model_class": "DistilBertForSequenceClassification",
        "num_labels": 2,
        "id2label": {"0": "NORMAL", "1": "PHISHING"},
        "label2id": {"NORMAL": 0, "PHISHING": 1}
    }

    import json
    with open(config_path, 'w') as f:
        json.dump(mock_config, f, indent=2)

    # Create mock tokenizer files
    tokenizer_config = {
        "do_lower_case": True,
        "unk_token": "[UNK]",
        "sep_token": "[SEP]",
        "pad_token": "[PAD]",
        "cls_token": "[CLS]",
        "mask_token": "[MASK]",
        "model_max_length": 512,
        "tokenizer_class": "DistilBertTokenizer"
    }

    with open(local_dir / "tokenizer_config.json", 'w') as f:
        json.dump(tokenizer_config, f, indent=2)

    # Create a simple vocab file (mock)
    vocab = {
        "[PAD]": 0,
        "[UNK]": 1,
        "[CLS]": 2,
        "[SEP]": 3,
        "[MASK]": 4,
        "hello": 5,
        "world": 6,
        "phishing": 7,
        "email": 8,
        "url": 9
    }

    with open(local_dir / "vocab.txt", 'w') as f:
        for token, _ in sorted(vocab.items(), key=lambda x: x[1]):
            f.write(f"{token}\n")

    print(f"✅ Created mock {model_name} at {local_dir}")
    print("   ⚠️ This is for development only - replace with real model for production")
    return True

def main():
    parser = argparse.ArgumentParser(description="Setup AI models for Email Phishing Detection")
    parser.add_argument("--model", choices=list(MODELS.keys()), help="Download specific model")
    parser.add_argument("--all", action="store_true", help="Download all models")
    parser.add_argument("--mock", action="store_true", help="Create mock models for development")
    parser.add_argument("--force", action="store_true", help="Force re-download existing models")

    args = parser.parse_args()

    # Install required packages if not available
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("📦 Installing required packages...")
        os.system(f"{sys.executable} -m pip install huggingface_hub transformers torch")

    # Determine which models to process
    if args.model:
        models_to_process = [args.model]
    elif args.all:
        models_to_process = list(MODELS.keys())
    else:
        # Interactive mode
        print("🤖 Email Phishing Detection - Model Setup")
        print("=" * 50)
        print("Available models:")
        for name, config in MODELS.items():
            print(f"  • {name}: {config['description']}")

        print("\nOptions:")
        print("  1. Download all real models")
        print("  2. Create mock models for development")
        print("  3. Download specific model")

        choice = input("\nChoose option (1-3): ").strip()

        if choice == "1":
            models_to_process = list(MODELS.keys())
            args.mock = False
        elif choice == "2":
            models_to_process = list(MODELS.keys())
            args.mock = True
        elif choice == "3":
            model_name = input("Enter model name: ").strip()
            if model_name in MODELS:
                models_to_process = [model_name]
                mock_choice = input("Use mock model? (y/n): ").strip().lower()
                args.mock = mock_choice == 'y'
            else:
                print(f"❌ Unknown model: {model_name}")
                return
        else:
            print("❌ Invalid choice")
            return

    # Process models
    success_count = 0
    for model_name in models_to_process:
        print(f"\n🔄 Processing {model_name}...")

        if args.mock:
            success = create_mock_model(model_name)
        else:
            success = download_model(model_name, args.force)

        if success:
            success_count += 1

    print(f"\n{'='*50}")
    if success_count == len(models_to_process):
        print("✅ All models processed successfully!")
        print("\n🚀 You can now run the project:")
        print("   python ai_services/app.py")
    else:
        print(f"⚠️ {success_count}/{len(models_to_process)} models processed successfully")

    print("\n📚 For more information, see CONTRIBUTING.md")

if __name__ == "__main__":
    main()