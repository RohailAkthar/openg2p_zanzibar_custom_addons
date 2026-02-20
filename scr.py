import pandas as pd
import glob
import os

def parse_payment_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    header_idx = -1
    for i, line in enumerate(lines):
        if 'JINA LA MZEE' in line.upper():
            header_idx = i
            break
            
    if header_idx == -1:
        raise ValueError(f"Could not find valid header in {file_path}")
        

    df = pd.read_csv(file_path, skiprows=header_idx, dtype=str)
    df.columns = [str(col).strip().upper() for col in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
    
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

    df = df.dropna(subset=['Beneficiary_Name'])
    
    df['Source_File'] = os.path.basename(file_path)
    
    return df


all_files = glob.glob("*.csv")
dataframes = []

for file in all_files:
    try:
        clean_df = parse_payment_file(file)
        dataframes.append(clean_df)
        print(f"Successfully processed: {file}")
    except Exception as e:
        print(f"Error processing {file}: {e}")

if dataframes:
    master_database = pd.concat(dataframes, ignore_index=True)
    
    print("\n--- Data Preview ---")
    print(master_database[['Beneficiary_Name', 'Zone_Region', 'District', 'Woreda_Ward', 'Account_Number']].head())