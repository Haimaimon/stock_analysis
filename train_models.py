from stock_analysis.ml.periodic_trainer import train_models

if __name__ == "__main__":
    train_models(artifacts_dir="artifacts", save_legacy_copy=True)
