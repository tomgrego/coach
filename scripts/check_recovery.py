import os
import pandas as pd
from garmindb.garmindb import GarminDb, Hrv
from garmindb import GarminConnectConfigManager

def check_recovery():
    config_dir = os.getcwd()
    config = GarminConnectConfigManager(config_dir)
    db_params = config.get_db_params()
    garmin_db = GarminDb(db_params)

    # Get latest HRV entries
    with garmin_db.managed_session() as session:
        latest_hrv = session.query(Hrv).order_by(Hrv.day.desc()).limit(7).all()
        
        if latest_hrv:
            print("\n--- Recovery Status (HRV) ---")
            data = []
            for entry in latest_hrv:
                data.append({
                    "Date": entry.day,
                    "HRV": entry.weekly_avg
                })
            df = pd.DataFrame(data)
            print(df)
        else:
            print("No HRV data found in GarminDB.")

if __name__ == "__main__":
    check_recovery()
