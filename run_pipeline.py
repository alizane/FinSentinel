from sqlalchemy import create_engine, text
import time

# --- DATABASE CONFIGURATION ---
DB_USER = 'postgres'
DB_PASSWORD = 'Hiking%40786'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'fraud_detection_db'

# --- The SQL command to refresh our two enriched profile tables ---
REFRESH_COMMAND = """
    REFRESH MATERIALIZED VIEW profile_customer_beneficiary;
    REFRESH MATERIALIZED VIEW profile_customer_location;
"""

def run_pipeline():
    """Connects to the database and refreshes all materialized views."""
    print("Starting data pipeline refresh...")
    start_time = time.time()
    
    try:
        engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
        
        with engine.connect() as connection:
            print("   -> Connected to database. Refreshing views...")
            connection.execute(text(REFRESH_COMMAND))
            connection.commit()
            
        end_time = time.time()
        print(f"Pipeline refresh completed successfully in {end_time - start_time:.2f} seconds.")

    except Exception as e:
        print(f"An error occurred during the pipeline refresh: {e}")

if __name__ == "__main__":
    run_pipeline()