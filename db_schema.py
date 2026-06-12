import mysql.connector
import time
import sys
import pandas as pd

def log(msg):
    print(msg)
    sys.stdout.flush()

# Load DB credentials from secrets.toml if available to prevent hardcoding password in repository
def load_db_credentials():
    import os
    creds = {
        "host": "e-commerce-pipeline-bordockz-3737.c.aivencloud.com",
        "port": 14582,
        "user": "avnadmin",
        "password": "", # Loaded from secrets.toml
        "database": "ecommerce_analytics",
        "connection_timeout": 5
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
            if "port" in creds:
                creds["port"] = int(creds["port"])
    except Exception as e:
        print(f"Warning: Failed to load secrets.toml: {e}")
    return creds

secrets = load_db_credentials()

log("Connecting to database...")
try:
    conn = mysql.connector.connect(**secrets)
    cursor = conn.cursor()
    
    log("Fetching CREATE TABLE info...")
    cursor.execute("SHOW CREATE TABLE samplesuperstore")
    create_table = cursor.fetchone()
    log(f"CREATE TABLE:\n{create_table[1]}\n")
    
    log("Fetching table indexes...")
    cursor.execute("SHOW INDEX FROM samplesuperstore")
    indexes = cursor.fetchall()
    log("Indexes:")
    for idx in indexes:
        log(f" - Key_name: {idx[2]}, Column_name: {idx[4]}, Non_unique: {idx[1]}")
        
    log("Running EXPLAIN SELECT COUNT(*) FROM samplesuperstore...")
    cursor.execute("EXPLAIN SELECT COUNT(*) FROM samplesuperstore")
    explain = cursor.fetchall()
    log(f"Explain output: {explain}")
    
    cursor.close()
    conn.close()
except Exception as e:
    log(f"Database Error: {e}")

# Check local CSV row count
try:
    log("Reading local samplesuperstore.csv shape...")
    df = pd.read_csv("samplesuperstore.csv")
    log(f"Local CSV shape: {df.shape}")
except Exception as e:
    log(f"CSV Error: {e}")
