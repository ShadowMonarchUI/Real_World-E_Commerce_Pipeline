import pandas as pd
import numpy as np
import sys
import time

# Reconfigure stdout to use UTF-8 to prevent UnicodeEncodeErrors on Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

def run_cleaning_pipeline(input_path, output_path):
    log_start = time.time()
    print("🚀 Starting optimized data cleaning pipeline...")
    
    # 1. Load raw data with optimized datatypes and specific columns to save memory
    dtypes = {
        'InvoiceNo': str,
        'StockCode': str,
        'Description': str,
        'Quantity': 'int32',
        'InvoiceDate': str,
        'UnitPrice': 'float32',
        'CustomerID': str,
        'Country': str
    }
    
    print("  Loading CSV dataset...")
    df = pd.read_csv(input_path, encoding='unicode_escape', dtype=dtypes)
    
    # 2. Filter valid sales first to reduce rows before string manipulation (saves CPU cycles)
    print("  Filtering transactions...")
    is_valid_sales = (df['Quantity'] > 0) & (df['UnitPrice'] > 0) & (~df['InvoiceNo'].str.startswith('C', na=False))
    clean_sales = df[is_valid_sales].copy()
    
    # 3. Clean text column anomalies only on filtered records
    print("  Cleaning descriptions & customer records...")
    clean_sales['Description'] = clean_sales['Description'].str.strip().str.upper()
    clean_sales['CustomerID'] = clean_sales['CustomerID'].fillna('GUEST_CHECKOUT')
    
    # 4. Feature Engineering: Create clean financial metrics matching required schema
    clean_sales['Sales'] = clean_sales['Quantity'] * clean_sales['UnitPrice']
    
    # Map raw columns to your standardized analytics schema
    final_schema = clean_sales.rename(columns={
        'InvoiceNo': 'OrderID',
        'StockCode': 'ProductID',
        'Description': 'ProductName',
        'Quantity': 'Quantity',
        'InvoiceDate': 'OrderDate',
        'UnitPrice': 'Price',
        'CustomerID': 'CustomerID',
        'Country': 'Region'
    })
    
    # 5. Export to the target filename
    print("  Saving clean dataset...")
    final_schema.to_csv(output_path, index=False)
    
    elapsed = time.time() - log_start
    print(f"✨ Pipeline complete in {elapsed:.2f}s! Clean file saved to: {output_path}")

if __name__ == "__main__":
    run_cleaning_pipeline('raw_online_retail.csv', 'samplesuperstore.csv')