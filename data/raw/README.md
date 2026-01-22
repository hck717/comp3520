# Raw Data Sources

## Downloaded Datasets from Kaggle

### 1. GlobalTradeSettleNet
- **Source**: [https://www.kaggle.com/datasets/ziya07/globaltradesettlenet](https://www.kaggle.com/datasets/ziya07/globaltradesettlenet)
- **Downloaded**: 2026-01-22
- **File**: `globaltradesettlenet.csv` (not committed to git)
- **Records**: ~5,000 trade settlement transactions
- **Key Fields**: 
  - `trade_value`: Transaction amount
  - `currency`: Currency code (USD, EUR, etc.)
  - `payment_method`: Payment type
  - `fraud_flag`: Anomaly indicator
  - `settlement_duration`: Days to settle
  - `blockchain_status`: Smart contract execution status

### 2. Cross-Border Trade & Customs Delay Dataset
- **Source**: [https://www.kaggle.com/datasets/ziya07/cross-border-trade-and-customs-delay-dataset](https://www.kaggle.com/datasets/ziya07/cross-border-trade-and-customs-delay-dataset)
- **Downloaded**: 2026-01-22
- **File**: `cross_border_customs.csv` (not committed to git)
- **Records**: ~10,000 shipment records
- **Key Fields**:
  - `shipment_id`: Unique shipment identifier
  - `origin_port`, `destination_port`: Port names
  - `customs_delay`: Days delayed at customs
  - `risk_flag`: Compliance risk indicator
  - `commodity`: Product category
  - `inspection_status`: Customs inspection result

## How to Download

1. **Install Kaggle CLI**:
   ```bash
   pip install kaggle
   ```

2. **Setup Kaggle API credentials**:
   - Go to [kaggle.com/settings](https://www.kaggle.com/settings)
   - Click "Create New API Token"
   - Save `kaggle.json` to `~/.kaggle/`

3. **Download datasets**:
   ```bash
   # GlobalTradeSettleNet
   kaggle datasets download -d ziya07/globaltradesettlenet -p data/raw/ --unzip
   
   # Cross-Border Customs
   kaggle datasets download -d ziya07/cross-border-trade-and-customs-delay-dataset -p data/raw/ --unzip
   ```

## Usage

These raw datasets are processed by scripts in `/src/data_generation/` to create:
- Letter of Credit (LC) documents
- Commercial Invoices
- Bills of Lading (B/L)
- Packing Lists
- Sanctions screening data

Processed data is saved to `/data/processed/` and ready for Neo4j ingestion.

## File Size Notes

⚠️ These files are **NOT** committed to git due to size:
- `globaltradesettlenet.csv` (~5-10 MB)
- `cross_border_customs.csv` (~10-20 MB)

Refer to `.gitignore` for excluded patterns.
