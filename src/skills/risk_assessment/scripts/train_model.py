"""Train XGBoost model for credit risk assessment."""

import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, 
    precision_recall_curve, auc
)
import xgboost as xgb

logger = logging.getLogger(__name__)


def train_xgboost_model(
    training_data_path: str = "data/processed/training_data.csv",
    model_output_path: str = "models/risk_model.pkl",
    test_size: float = 0.2,
    random_state: int = 42
) -> dict:
    """
    Train XGBoost classifier for credit risk prediction.
    
    Args:
        training_data_path: Path to CSV with features and labels
        model_output_path: Path to save trained model
        test_size: Fraction of data for validation
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary with performance metrics
    """
    logger.info("="*60)
    logger.info("  XGBOOST RISK MODEL TRAINING")
    logger.info("="*60)
    
    # Load training data
    logger.info(f"\n📂 Loading training data from {training_data_path}...")
    df = pd.read_csv(training_data_path)
    logger.info(f"  ✅ Loaded {len(df)} samples")
    
    # Handle both 'label' and 'is_anomaly' column names
    label_col = 'label' if 'label' in df.columns else 'is_anomaly'
    if label_col not in df.columns:
        raise ValueError("CSV must contain either 'label' or 'is_anomaly' column")
    
    logger.info(f"     Clean (0): {(df[label_col] == 0).sum()}")
    logger.info(f"     High-risk (1): {(df[label_col] == 1).sum()}")
    
    # Prepare features and labels
    exclude_cols = [label_col, 'label', 'is_anomaly', 'entity_name', 'transaction_id']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    X = df[feature_cols].values
    y = df[label_col].values
    
    logger.info(f"\n📊 Feature set: {len(feature_cols)} features")
    for i, col in enumerate(feature_cols):
        logger.info(f"     {i+1:2d}. {col}")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    logger.info(f"\n📈 Dataset split:")
    logger.info(f"     Training: {len(X_train)} samples")
    logger.info(f"     Testing: {len(X_test)} samples")
    
    # Calculate scale_pos_weight for class imbalance
    n_negative = (y_train == 0).sum()
    n_positive = (y_train == 1).sum()
    scale_pos_weight = n_negative / n_positive if n_positive > 0 else 1
    
    logger.info(f"\n⚖️  Class balance:")
    logger.info(f"     Negative class: {n_negative}")
    logger.info(f"     Positive class: {n_positive}")
    logger.info(f"     Scale weight: {scale_pos_weight:.2f}")
    
    # Train XGBoost model
    logger.info(f"\n🤖 Training XGBoost model...")
    
    model = xgb.XGBClassifier(
        max_depth=6,
        learning_rate=0.1,
        n_estimators=100,
        objective='binary:logistic',
        eval_metric='auc',
        scale_pos_weight=scale_pos_weight,
        random_state=random_state,
        use_label_encoder=False
    )
    
    # Fit with early stopping
    eval_set = [(X_test, y_test)]
    model.fit(
        X_train, y_train,
        eval_set=eval_set,
        verbose=False
    )
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    auc_roc = roc_auc_score(y_test, y_pred_proba)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    
    # Precision-Recall AUC
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = auc(recall, precision)
    
    logger.info("\n" + "="*60)
    logger.info("📊 VALIDATION RESULTS")
    logger.info("="*60)
    logger.info(f"\n  AUC-ROC:   {auc_roc:.3f}")
    logger.info(f"  PR-AUC:    {pr_auc:.3f}")
    
    if '1' in report:
        logger.info(f"  Precision: {report['1']['precision']:.3f}")
        logger.info(f"  Recall:    {report['1']['recall']:.3f}")
        logger.info(f"  F1-Score:  {report['1']['f1-score']:.3f}")
    else:
        logger.warning("  ⚠️  High-risk class not predicted!")
        logger.info(f"  Precision: 0.000")
        logger.info(f"  Recall:    0.000")
        logger.info(f"  F1-Score:  0.000")
    
    logger.info(f"\n  Confusion Matrix:")
    logger.info(f"     TN: {cm[0][0]:4d}  |  FP: {cm[0][1]:4d}")
    logger.info(f"     FN: {cm[1][0]:4d}  |  TP: {cm[1][1]:4d}")
    
    # Feature importance
    logger.info(f"\n  Top 5 Features by Importance:")
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for i, row in feature_importance.head(5).iterrows():
        logger.info(f"     {row['feature']:30s}: {row['importance']:.3f}")
    
    # Save model
    Path(model_output_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        'model': model,
        'feature_cols': feature_cols,
        'training_date': pd.Timestamp.now().isoformat(),
        'metrics': {
            'auc_roc': float(auc_roc),
            'pr_auc': float(pr_auc),
            'precision': float(report['1']['precision']) if '1' in report else 0.0,
            'recall': float(report['1']['recall']) if '1' in report else 0.0,
            'f1_score': float(report['1']['f1-score']) if '1' in report else 0.0
        }
    }, model_output_path)
    
    logger.info(f"\n💾 Model saved to: {model_output_path}")
    logger.info("\n" + "="*60)
    logger.info("🎉 TRAINING COMPLETE!")
    logger.info("="*60)
    
    return {
        'auc_roc': float(auc_roc),
        'pr_auc': float(pr_auc),
        'precision': float(report['1']['precision']) if '1' in report else 0.0,
        'recall': float(report['1']['recall']) if '1' in report else 0.0,
        'f1_score': float(report['1']['f1-score']) if '1' in report else 0.0,
        'train_samples': len(X_train),
        'test_samples': len(X_test)
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    metrics = train_xgboost_model(
        training_data_path="data/processed/training_data.csv",
        model_output_path="models/risk_model.pkl"
    )
    
    print(f"\n✅ Model AUC-ROC: {metrics['auc_roc']:.3f}")
