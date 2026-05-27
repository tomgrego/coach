import os
import json
import logging
import subprocess
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_config():
    load_dotenv()
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    
    if not email or not password:
        logger.error("GARMIN_EMAIL or GARMIN_PASSWORD not found in .env")
        return False

    config = {
        "credentials": {
            "user": email,
            "password": password
        },
        "directories": {
            "base_dir": os.path.join(os.getcwd(), "GarminDB"),
            "relative_to_home": False
        },
        "db": {
            "type": "sqlite"
        },
        "data": {
            "download_latest_activities": 25,
            "download_all_activities": 100,
            "download_days_overlap": 3
        },
        "settings": {
            "metric": True
        }
    }
    
    config_path = os.path.join(os.getcwd(), "GarminConnectConfig.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    logger.info(f"Config created at {config_path}")
    return True

def run_garmindb():
    if not setup_config():
        return

    logger.info("Syncing data with GarminDB...")
    try:
        # GarminDB expects a directory path for the config, and looks for GarminConnectConfig.json inside it.
        # We need to specify the modes: download (-d), import (-i), and analyze (--analyze).
        config_dir = os.getcwd()
        subprocess.run(["garmindb_cli.py", "-f", config_dir, "--download", "--import", "--analyze", "--latest", "--all"], check=True)
        logger.info("GarminDB sync complete.")
    except Exception as e:
        logger.error(f"Error running GarminDB: {e}")

if __name__ == "__main__":
    run_garmindb()
