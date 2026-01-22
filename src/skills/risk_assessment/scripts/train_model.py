"""Train XGBoost classifier for entity risk assessment."""

import logging
import pandas as pd
import joblib
from pathlib import Path
from typing import Dict
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import xgboost as xgb
from imblearn.over_sampling import SMOTE

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    'transaction_count',
    'total_exposure',
    'avg_lc_amount',
    'discrepancy_rate',
    'late_shipment_rate',
    'payment_delay_avg',
    'counterparty_diversity',
    'high_risk_country_exposure',
    'sanctions_exposure',
    'doc_completeness',
    'amendment_rate',
    'fraud_flags',
]

def train_xgboost_model(
    training_data_path: str = "data/processed/training_data.csv",
    model_output_path: str = "models/risk_model.pkl",
    test_size: float = 0.2,
    n_estimators: int = 100,
    use_smote: bool = True
) -> Dict:
    """
    Train XGBoost classifier for risk assessment.
    
    Args:
        training_data_path: Path to training CSV
        model_output_path: Path to save trained model
        test_size: Fraction for test set
        n_estimators: Number of boosting rounds
        use_smote: Whether to use SMOTE for class imbalance
        
    Returns:
        Dictionary with evaluation metrics
    """
    # Load training data
    logger.info(f"Loading training data from {training_data_path}")
    df = pd.read_csv(training_data_path)
    
    # Prepare features and labels
    X = df[FEATURE_COLUMNS]
    y = df['label']
    
    logger.info(f"Training samples: {len(df)}")
    logger.info(f"High-risk ratio: {y.mean()*100:.1f}%")
    
    # Split into train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    # Handle class imbalance with SMOTE
    if use_smote and y_train.mean() < 0.4:  # Only if imbalanced
        logger.info("Applying SMOTE to balance classes")
        smote = SMOTE(random_state=42)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        logger.info(f"After SMOTE: {len(y_train)} samples, {y_train.mean()*100:.1f}% high-risk")
    
    # Train XGBoost
    logger.info("Training XGBoost classifier...")
    model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=5,
        learning_rate=0.1,
        objective='binary:logistic',
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    auc_roc = roc_auc_score(y_test, y_pred_proba)
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred)
    
    logger.info(f"\nModel Performance:")
    logger.info(f"  AUC-ROC: {auc_roc:.3f}")
    logger.info(f"  Precision: {report['1']['precision']:.3f}")
    logger.info(f"  Recall: {report['1']['recall']:.3f}")
    logger.info(f"  F1-Score: {report['1']['f1-score']:.3f}")
    logger.info(f"\nConfusion Matrix:")
    logger.info(f"  TN: {cm[0][0]}, FP: {cm[0][1]}")
    logger.info(f"  FN: {cm[1][0]}, TP: {cm[1][1]}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': FEATURE_COLUMNS,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info("\nTop 5 Most Important Features:")
    for _, row in feature_importance.head(5).iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.3f}")
    
    # Save model
    Path(model_output_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output_path)
    logger.info(f"\nModel saved to {model_output_path}")
    
    return {
        'auc_roc': auc_roc,
        'precision': report['1']['precision'],
        'recall': report['1']['recall'],
        'f1_score': report['1']['f1-score'],
        'confusion_matrix': cm.tolist(),
        'feature_importance': feature_importance.to_dict('records')
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Train model
    metrics = train_xgboost_model(
        training_data_path='data/processed/training_data.csv',
        model_output_path='models/risk_model.pkl',
        n_estimators=100
    )
    
    print("\nTraining Complete!")
