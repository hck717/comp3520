"""Generate balanced training data from Kaggle CSVs or improved synthetic data."""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

# Paths
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_kaggle_data():
    """
    Try to load Kaggle datasets if available.
    Returns None if files don't exist.
    """
    trade_settle_path = RAW_DATA_DIR / "globaltradesettlenet.csv"
    customs_path = RAW_DATA_DIR / "cross_border_customs.csv"
    
    if trade_settle_path.exists() and customs_path.exists():
        logger.info("✅ Found Kaggle datasets!")
        trade_df = pd.read_csv(trade_settle_path)
        customs_df = pd.read_csv(customs_path)
        return trade_df, customs_df
    else:
        logger.warning("⚠️  Kaggle datasets not found. Will generate synthetic data.")
        logger.info(f"    Expected: {trade_settle_path}")
        logger.info(f"    Expected: {customs_path}")
        return None, None

def generate_balanced_synthetic_data(n_samples: int = 1000, anomaly_ratio: float = 0.3):
    """
    Generate balanced synthetic trade finance data.
    
    Args:
        n_samples: Total number of samples to generate
        anomaly_ratio: Ratio of anomalous samples (default 30%)
    """
    logger.info(f"Generating {n_samples} samples ({anomaly_ratio*100:.0f}% anomalies)...")
    
    n_anomalies = int(n_samples * anomaly_ratio)
    n_normal = n_samples - n_anomalies
    
    data = []
    
    # Generate normal transactions
    for i in range(n_normal):
        transaction = {
            'transaction_id': f'TXN-{i:06d}',
            'amount_usd': np.random.lognormal(12, 1.5),  # Mean ~$160K
            'amount_deviation': np.random.normal(0, 0.3),
            'time_deviation': np.random.uniform(0, 0.3),
            'port_risk': np.random.choice([0.1, 0.2, 0.3], p=[0.6, 0.3, 0.1]),
            'doc_completeness': np.random.uniform(0.85, 1.0),
            'discrepancy_rate': np.random.uniform(0, 0.15),
            'late_shipment_rate': np.random.uniform(0, 0.20),
            'payment_delay_days': np.random.uniform(0, 10),
            'high_risk_country_exposure': np.random.uniform(0, 0.20),
            'amendment_rate': np.random.uniform(0, 0.15),
            'fraud_flag': 0,
            'is_anomaly': 0
        }
        data.append(transaction)
    
    # Generate anomalous transactions
    for i in range(n_anomalies):
        # Create anomalies with specific patterns
        anomaly_type = np.random.choice(['amount', 'time', 'fraud', 'country'])
        
        transaction = {
            'transaction_id': f'TXN-{n_normal + i:06d}',
            'amount_usd': np.random.lognormal(12, 1.5),
            'is_anomaly': 1
        }
        
        if anomaly_type == 'amount':
            # High amount deviation
            transaction['amount_deviation'] = np.random.uniform(2.5, 5.0)
            transaction['time_deviation'] = np.random.uniform(0, 0.5)
            transaction['port_risk'] = np.random.uniform(0.2, 0.6)
            transaction['doc_completeness'] = np.random.uniform(0.6, 0.9)
            transaction['discrepancy_rate'] = np.random.uniform(0.20, 0.50)
            
        elif anomaly_type == 'time':
            # Suspicious timing
            transaction['amount_deviation'] = np.random.uniform(0.5, 2.0)
            transaction['time_deviation'] = np.random.uniform(0.7, 1.0)
            transaction['port_risk'] = np.random.uniform(0.3, 0.7)
            transaction['doc_completeness'] = np.random.uniform(0.5, 0.85)
            transaction['discrepancy_rate'] = np.random.uniform(0.15, 0.40)
            
        elif anomaly_type == 'fraud':
            # Multiple fraud indicators
            transaction['amount_deviation'] = np.random.uniform(1.5, 4.0)
            transaction['time_deviation'] = np.random.uniform(0.4, 0.9)
            transaction['port_risk'] = np.random.uniform(0.5, 0.9)
            transaction['doc_completeness'] = np.random.uniform(0.3, 0.70)
            transaction['discrepancy_rate'] = np.random.uniform(0.30, 0.60)
            transaction['fraud_flag'] = np.random.randint(1, 4)
            
        else:  # country
            # High-risk country exposure
            transaction['amount_deviation'] = np.random.uniform(0.8, 2.5)
            transaction['time_deviation'] = np.random.uniform(0.2, 0.6)
            transaction['port_risk'] = np.random.uniform(0.7, 1.0)
            transaction['doc_completeness'] = np.random.uniform(0.6, 0.85)
            transaction['high_risk_country_exposure'] = np.random.uniform(0.5, 1.0)
            transaction['discrepancy_rate'] = np.random.uniform(0.15, 0.35)
        
        # Fill remaining fields with moderate values
        if 'late_shipment_rate' not in transaction:
            transaction['late_shipment_rate'] = np.random.uniform(0.20, 0.50)
        if 'payment_delay_days' not in transaction:
            transaction['payment_delay_days'] = np.random.uniform(10, 30)
        if 'high_risk_country_exposure' not in transaction:
            transaction['high_risk_country_exposure'] = np.random.uniform(0.1, 0.4)
        if 'amendment_rate' not in transaction:
            transaction['amendment_rate'] = np.random.uniform(0.15, 0.40)
        if 'fraud_flag' not in transaction:
            transaction['fraud_flag'] = 0
        
        data.append(transaction)
    
    df = pd.DataFrame(data)
    
    # Shuffle the dataset
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    logger.info(f"✅ Generated {len(df)} transactions")
    logger.info(f"   Normal: {(df['is_anomaly']==0).sum()}")
    logger.info(f"   Anomalies: {(df['is_anomaly']==1).sum()}")
    
    return df

def process_kaggle_data(trade_df, customs_df):
    """
    Process Kaggle datasets into training format.
    
    Args:
        trade_df: GlobalTradeSettleNet DataFrame
        customs_df: Cross-Border Customs DataFrame
    """
    logger.info("Processing Kaggle datasets...")
    
    # Map Kaggle fields to our schema
    processed_data = []
    
    for idx, row in trade_df.iterrows():
        # Extract features from trade settlement data
        transaction = {
            'transaction_id': f'KAG-{idx:06d}',
            'amount_usd': row.get('trade_value', 100000),
            'amount_deviation': abs(row.get('trade_value', 100000) - 100000) / 100000,
            'time_deviation': row.get('settlement_duration', 5) / 30,  # Normalize by 30 days
            'port_risk': 0.5 if row.get('blockchain_status', '') == 'Failed' else 0.2,
            'doc_completeness': 1.0 if row.get('payment_method', '') == 'Bank Transfer' else 0.8,
            'fraud_flag': int(row.get('fraud_flag', 0)),
            'is_anomaly': int(row.get('fraud_flag', 0) > 0)
        }
        
        # Add synthetic fields not in Kaggle data
        transaction['discrepancy_rate'] = np.random.uniform(0, 0.2) if transaction['is_anomaly'] == 0 else np.random.uniform(0.2, 0.5)
        transaction['late_shipment_rate'] = np.random.uniform(0, 0.2) if transaction['is_anomaly'] == 0 else np.random.uniform(0.2, 0.5)
        transaction['payment_delay_days'] = np.random.uniform(0, 10) if transaction['is_anomaly'] == 0 else np.random.uniform(10, 30)
        transaction['high_risk_country_exposure'] = 0.3 if transaction['is_anomaly'] == 1 else 0.1
        transaction['amendment_rate'] = np.random.uniform(0, 0.15) if transaction['is_anomaly'] == 0 else np.random.uniform(0.15, 0.4)
        
        processed_data.append(transaction)
    
    df = pd.DataFrame(processed_data)
    
    # Balance the dataset
    normal_samples = df[df['is_anomaly'] == 0].sample(n=min(700, len(df[df['is_anomaly'] == 0])), random_state=42)
    anomaly_samples = df[df['is_anomaly'] == 1].sample(n=min(300, len(df[df['is_anomaly'] == 1])), random_state=42, replace=True)
    
    df_balanced = pd.concat([normal_samples, anomaly_samples]).sample(frac=1, random_state=42).reset_index(drop=True)
    
    logger.info(f"✅ Processed {len(df_balanced)} Kaggle transactions")
    logger.info(f"   Normal: {(df_balanced['is_anomaly']==0).sum()}")
    logger.info(f"   Anomalies: {(df_balanced['is_anomaly']==1).sum()}")
    
    return df_balanced

def main():
    """Generate balanced training data."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("="*60)
    logger.info("BALANCED TRAINING DATA GENERATION")
    logger.info("="*60)
    
    # Try to load Kaggle data first
    trade_df, customs_df = load_kaggle_data()
    
    if trade_df is not None:
        # Use Kaggle data
        df = process_kaggle_data(trade_df, customs_df)
    else:
        # Generate synthetic data
        df = generate_balanced_synthetic_data(n_samples=1000, anomaly_ratio=0.3)
    
    # Save to processed folder
    output_path = PROCESSED_DATA_DIR / "training_data_balanced.csv"
    df.to_csv(output_path, index=False)
    
    logger.info(f"\n💾 Saved to: {output_path}")
    logger.info(f"\n📊 Dataset Statistics:")
    logger.info(f"   Total samples: {len(df)}")
    logger.info(f"   Normal: {(df['is_anomaly']==0).sum()} ({(df['is_anomaly']==0).sum()/len(df)*100:.1f}%)")
    logger.info(f"   Anomalies: {(df['is_anomaly']==1).sum()} ({(df['is_anomaly']==1).sum()/len(df)*100:.1f}%)")
    logger.info(f"\n✅ COMPLETE!")
    
    return df

if __name__ == '__main__':
    main()
