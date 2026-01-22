# Kaggle Dataset Setup (Optional)

This project can use real Kaggle datasets for more realistic training data. If you don't download them, the system will generate improved synthetic data automatically.

## Option 1: Use Kaggle Data (Recommended)

### 1. Setup Kaggle API

```bash
# Install Kaggle CLI
pip install kaggle

# Get your API credentials
# 1. Go to https://www.kaggle.com/settings
# 2. Click "Create New API Token"
# 3. Download kaggle.json

# Move to ~/.kaggle/
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

### 2. Download Datasets

```bash
cd ~/comp3520

# Download GlobalTradeSettleNet (~5,000 trade settlement transactions)
kaggle datasets download -d ziya07/globaltradesettlenet -p data/raw/ --unzip

# Download Cross-Border Trade & Customs Delay Dataset (~10,000 shipment records)
kaggle datasets download -d ziya07/cross-border-trade-and-customs-delay-dataset -p data/raw/ --unzip
```

### 3. Verify Downloads

```bash
ls -lh data/raw/
# Should see:
# globaltradesettlenet.csv
# cross_border_customs.csv
```

## Option 2: Use Synthetic Data (Default)

If you don't download Kaggle data, the system automatically generates balanced synthetic data with:
- **70% normal transactions**
- **30% anomalous transactions**
- Realistic feature distributions
- Multiple anomaly patterns (amount, timing, fraud, country risk)

## Using the Data

### Generate Balanced Training Data

```bash
# This will:
# 1. Try to load Kaggle CSVs if available
# 2. Fall back to improved synthetic data if not
# 3. Save balanced data to data/processed/training_data_balanced.csv

python src/data_generation/generate_balanced_data.py
```

### Run Full Test Suite

```bash
# This will:
# 1. Generate balanced data
# 2. Train Risk Assessment model (XGBoost)
# 3. Train Quantum VQC with balanced data
# 4. Run quantum vs classical benchmark

python test_improvements.py
```

## Dataset Details

### GlobalTradeSettleNet
- **Source**: [Kaggle - GlobalTradeSettleNet](https://www.kaggle.com/datasets/ziya07/globaltradesettlenet)
- **Records**: ~5,000 trade settlement transactions
- **Key Fields**:
  - `trade_value`: Transaction amount
  - `currency`: Currency code (USD, EUR, etc.)
  - `payment_method`: Payment type
  - `fraud_flag`: Anomaly indicator ✅
  - `settlement_duration`: Days to settle
  - `blockchain_status`: Smart contract execution status

### Cross-Border Trade & Customs Delay Dataset
- **Source**: [Kaggle - Cross-Border Customs](https://www.kaggle.com/datasets/ziya07/cross-border-trade-and-customs-delay-dataset)
- **Records**: ~10,000 shipment records
- **Key Fields**:
  - `shipment_id`: Unique identifier
  - `origin_port`, `destination_port`: Port names
  - `customs_delay`: Days delayed at customs ✅
  - `risk_flag`: Compliance risk indicator ✅
  - `commodity`: Product category
  - `inspection_status`: Customs inspection result

## Troubleshooting

### "401 Unauthorized" Error
- Check `~/.kaggle/kaggle.json` exists and has correct credentials
- Make sure file permissions are `600`: `chmod 600 ~/.kaggle/kaggle.json`

### "Dataset not found" Error
- Verify the dataset URLs are still active on Kaggle
- Check your internet connection

### CSV files too large for git
- These files are in `.gitignore` and won't be committed
- Each team member needs to download them separately

## Data Privacy Note

⚠️ The Kaggle datasets are synthetic/public data. For production systems:
- Use real transaction data from your institution
- Anonymize PII (Personally Identifiable Information)
- Follow GDPR/regulatory compliance requirements
- Secure data storage with encryption

## Next Steps

After downloading data:
1. ✅ Run `python test_improvements.py` to test everything
2. ✅ Check `data/processed/training_data_balanced.csv` was created
3. ✅ Verify models trained successfully in `models/` folder
4. ✅ Review metrics in terminal output

For questions, check [README.md](README.md) or skill-specific documentation in `src/skills/*/SKILL.md`.
