import pandas as pd
import mysql.connector
from concurrent.futures import ThreadPoolExecutor
import sys
import time

# Reconfigure stdout to use UTF-8 to prevent UnicodeEncodeErrors on Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# --- Configuration ---
CHUNK_SIZE = 10000
MAX_WORKERS = 3 # Slightly lower concurrency to avoid deadlocks on small db instances

# Load DB credentials from secrets.toml if available to prevent hardcoding password in repository
def load_db_credentials():
    import os
    creds = {
        "host": "e-commerce-pipeline-bordockz-3737.c.aivencloud.com",
        "port": 14582,
        "user": "avnadmin",
        "password": "", # Loaded from secrets.toml
        "database": "ecommerce_analytics"
    }
    try:
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            with open(secrets_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            in_mysql = False
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line == "[mysql]":
                    in_mysql = True
                    continue
                if line.startswith("[") and in_mysql:
                    break
                if in_mysql and "=" in line:
                    k, v = line.split("=", 1)
                    creds[k.strip()] = v.strip().strip('"').strip("'")
    except Exception as e:
        print(f"Warning: Failed to load secrets.toml: {e}")
    return creds

DB_CREDS = load_db_credentials()

def upload_chunk(chunk_data, chunk_id):
    """Worker function to upload a single chunk of data in its own thread with retry logic."""
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        conn = None
        cursor = None
        try:
            # Each thread needs its own independent connection to the database (with fast C extension enabled)
            conn = mysql.connector.connect(
                use_pure=False,
                host=DB_CREDS.get("host"), 
                port=int(DB_CREDS.get("port")),                                       
                user=DB_CREDS.get("user"),
                password=DB_CREDS.get("password"),
                database=DB_CREDS.get("database"),
                connection_timeout=15
            )
            cursor = conn.cursor()
            
            # The SQL query for insertion
            sql = """
                INSERT INTO samplesuperstore 
                (OrderID, ProductID, ProductName, Quantity, OrderDate, Price, Sales, CustomerID, Region) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # executemany pushes the entire chunk of 10,000 rows in one massive query
            cursor.executemany(sql, chunk_data)
            conn.commit()
            
            # Success report for this chunk
            rows_uploaded = len(chunk_data)
            print(f"✅ Chunk {chunk_id}: Successfully uploaded {rows_uploaded} rows (Attempt {attempt}).")
            break # Success, exit retry loop
            
        except Exception as e:
            print(f"⚠️ Chunk {chunk_id} failed on attempt {attempt}/{max_retries} with error: {e}")
            if attempt < max_retries:
                time.sleep(2 * attempt) # Exponential backoff
            else:
                print(f"❌ Chunk {chunk_id}: Failed all {max_retries} attempts.")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


# 1. Load the full dataset
print("Loading dataset into memory...")
df = pd.read_csv('samplesuperstore.csv')

# 2. Clean data for SQL (Convert Pandas NaN to Python None)
df = df.where(pd.notnull(df), None)

# 3. Convert the DataFrame into a list of tuples
print("Formatting data for bulk insertion...")
records = df[['OrderID', 'ProductID', 'ProductName', 'Quantity', 'OrderDate', 'Price', 'Sales', 'CustomerID', 'Region']].values.tolist()
records = [tuple(row) for row in records]

# 4. Split the massive list into smaller chunks of 10,000
chunks = [records[i:i + CHUNK_SIZE] for i in range(0, len(records), CHUNK_SIZE)]
total_chunks = len(chunks)

# 5. Execute the parallel upload
print(f"Starting parallel upload across {MAX_WORKERS} threads. Total chunks to process: {total_chunks}")
print("-" * 50)

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit each chunk to the thread pool
    for i, chunk in enumerate(chunks, 1):
        executor.submit(upload_chunk, chunk, i)

print("-" * 50)
print("🚀 All parallel uploads complete!")