import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load the variables from .env
load_dotenv()

def get_engine():
    """Returns a SQLAlchemy engine using variables from .env"""
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    
    # Constructing the connection string
    # We use f-strings to plug in the variables
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    
    return create_engine(db_url)

def get_db_config():
    """Returns the raw connection string if needed for other tools"""
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"