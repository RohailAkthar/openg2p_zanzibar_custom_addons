import pandas as pd
import glob
import os

def parse_payment_file(file_path):
    # 1. Dynamically find the header row
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    header_idx = -1
    for i, line in enumerate(lines):
        # We know the header row always contains 'JINA LA MZEE' (Elder's Name)
        if 'JINA LA MZEE' in line.upper():
            header_idx = i
            break
            
    if header_idx == -1:
        raise ValueError(f"Could not find valid header in {file_path}")
        
    # Read CSV starting exactly at the header. 
    # Force all types to string to preserve leading zeros in Bank Accounts and IDs.
    df = pd.read_csv(file_path, skiprows=header_idx, dtype=str)
    
    # 2. Clean up column names and drop empty "ghost" columns (fixes the Kusini anomaly)
    df.columns = [str(col).strip().upper() for col in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
    
    # 3. Standardize Column Names (Map all variations to a single standard)
    rename_map = {
        'SR': 'Serial_Number',
        'JINA LA MZEE': 'Beneficiary_Name',
        'ZANZIBAR ID': 'National_ID',
        'ACCOUNT NO': 'Account_Number',
        'ACCOUNT NUMBER': 'Account_Number',
        'AKAUNTI': 'Account_Number',
        'JINA LA MTU WA KARIBU': 'Next_Of_Kin',
        'IDADI': 'Amount',
        'KIASI': 'Amount',
        'SHEHIA': 'Woreda_Ward',
        'WILAYA': 'District',
        'ENEO': 'Zone_Region'
    }
    df.rename(columns=rename_map, inplace=True)
    
    # 4. Fix Data Misplacement (The "Pemba" anomaly)
    # If the Zone_Region column doesn't exist, create it
    if 'Zone_Region' not in df.columns:
        df['Zone_Region'] = 'UNKNOWN'
        
    if 'District' in df.columns:
        # Check if "PEMBA" was accidentally put in the District column
        pemba_mask = df['District'].str.strip().str.upper() == 'PEMBA'
        if pemba_mask.any():
            # Move "PEMBA" to the correct Zone_Region column
            df.loc[pemba_mask, 'Zone_Region'] = 'PEMBA'
            
            # Deduce the actual District from the file name
            file_name = os.path.basename(file_path).upper()
            if 'CHAKE CHAKE' in file_name:
                df.loc[pemba_mask, 'District'] = 'CHAKE CHAKE'
            elif 'MICHEWENI' in file_name:
                df.loc[pemba_mask, 'District'] = 'MICHEWENI'

    # 5. Final Cleanup: Drop rows that are completely empty or footer summaries
    df = df.dropna(subset=['Beneficiary_Name'])
    
    # Add a source file column for auditing purposes
    df['Source_File'] = os.path.basename(file_path)
    
    return df

# --- Execution ---
# Get all csv files in your directory
all_files = glob.glob("*.csv")
dataframes = []

for file in all_files:
    try:
        clean_df = parse_payment_file(file)
        dataframes.append(clean_df)
        print(f"Successfully processed: {file}")
    except Exception as e:
        print(f"Error processing {file}: {e}")

# Combine everything into one master database-ready dataset
if dataframes:
    master_database = pd.concat(dataframes, ignore_index=True)
    
    # Preview the perfectly mapped data
    print("\n--- Data Preview ---")
    print(master_database[['Beneficiary_Name', 'Zone_Region', 'District', 'Woreda_Ward', 'Account_Number']].head())