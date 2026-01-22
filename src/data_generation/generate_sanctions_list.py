"""
Generate synthetic sanctions lists (OFAC, UN, EU format)
Based on real sanctions list structures but with fake entities

Usage:
    python src/data_generation/generate_sanctions_list.py
    
Output:
    - data/processed/sanctions_ofac.csv
    - data/processed/sanctions_un.csv
    - data/processed/sanctions_eu.csv
    - data/processed/sanctions_all.csv
"""

import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker()
Faker.seed(42)  # Reproducible results
random.seed(42)

def generate_sanctions_list(num_entities=200):
    """Generate synthetic sanctions entities"""
    
    sanctions = []
    high_risk_countries = ['Iran', 'North Korea', 'Syria', 'Russia', 'Venezuela', 
                          'Cuba', 'Myanmar', 'Belarus', 'Libya', 'Sudan']
    
    programs = {
        'OFAC_SDN': ['IRAN', 'DPRK', 'SYRIA', 'UKRAINE-RUSSIA', 'VENEZUELA', 'CUBA'],
        'UN_SC': ['DPRK', 'LIBYA', 'IRAN', 'SOMALIA', 'TALIBAN'],
        'EU_FSF': ['RUSSIA', 'BELARUS', 'IRAN', 'SYRIA', 'MYANMAR']
    }
    
    for i in range(num_entities):
        list_type = random.choice(['OFAC_SDN', 'UN_SC', 'EU_FSF'])
        country = random.choice(high_risk_countries)
        entity_type = random.choice(['Company', 'Individual', 'Vessel', 'Aircraft'])
        
        # Generate realistic names based on entity type
        if entity_type == 'Company':
            name = fake.company()
            aliases = [
                name.replace('Ltd', 'Limited'),
                name.replace(' ', '_'),
                f"{name} Trading"
            ]
        elif entity_type == 'Individual':
            name = fake.name()
            # Create alternative spellings
            aliases = [name, name.replace(' ', '-')]
        elif entity_type == 'Vessel':
            name = f"MV {fake.word().title()} {random.randint(1,99)}"
            aliases = [name.replace('MV', 'M/V'), name.replace(' ', '_')]
        else:  # Aircraft
            name = f"{fake.word().upper()}-{random.randint(1000,9999)}"
            aliases = [name]
        
        entity = {
            'sanction_id': f"{list_type.split('_')[0]}_{10000 + i}",
            'name': name,
            'aliases': '|'.join(aliases[:2]),  # Store as pipe-separated
            'list_type': list_type,
            'country': country,
            'program': random.choice(programs[list_type]),
            'entity_type': entity_type,
            'added_date': fake.date_between(start_date='-5y', end_date='today'),
            'id_number': f"ID-{random.randint(100000,999999)}",
            'remarks': fake.sentence(nb_words=10)
        }
        sanctions.append(entity)
    
    return pd.DataFrame(sanctions)

if __name__ == "__main__":
    print("🔄 Generating synthetic sanctions lists...")
    
    # Create output directory if it doesn't exist
    os.makedirs('data/processed', exist_ok=True)
    
    # Generate all sanctions lists
    df_all = generate_sanctions_list(200)
    
    # Split by list type
    df_ofac = df_all[df_all['list_type'] == 'OFAC_SDN']
    df_un = df_all[df_all['list_type'] == 'UN_SC']
    df_eu = df_all[df_all['list_type'] == 'EU_FSF']
    
    # Save to processed folder
    df_ofac.to_csv('data/processed/sanctions_ofac.csv', index=False)
    df_un.to_csv('data/processed/sanctions_un.csv', index=False)
    df_eu.to_csv('data/processed/sanctions_eu.csv', index=False)
    df_all.to_csv('data/processed/sanctions_all.csv', index=False)
    
    print(f"\n✅ Generated {len(df_all)} sanctions entities")
    print(f"   - OFAC SDN: {len(df_ofac)} entities")
    print(f"   - UN SC: {len(df_un)} entities")
    print(f"   - EU FSF: {len(df_eu)} entities")
    print(f"\n📁 Saved to data/processed/")
    print(f"   - sanctions_ofac.csv")
    print(f"   - sanctions_un.csv")
    print(f"   - sanctions_eu.csv")
    print(f"   - sanctions_all.csv")
    
    # Display sample
    print("\n📊 Sample sanctions entities:")
    print(df_all[['name', 'entity_type', 'list_type', 'country', 'program']].head(10))
