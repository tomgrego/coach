import os
import pandas as pd
from garmindb.garmindb import GarminDb, RestingHeartRate, DailySummary
from garmindb import GarminConnectConfigManager

def check_health():
    config_dir = os.getcwd()
    config = GarminConnectConfigManager(config_dir)
    db_params = config.get_db_params()
    garmin_db = GarminDb(db_params)

    with garmin_db.managed_session() as session:
        # Get RHR
        rhr_entries = session.query(RestingHeartRate).order_by(RestingHeartRate.day.desc()).limit(7).all()
        # Get Daily Summary for Stress
        summary_entries = session.query(DailySummary).order_by(DailySummary.day.desc()).limit(7).all()
        
        print("\n--- Health Metrics ---")
        health_data = {}
        for entry in rhr_entries:
            health_data[entry.day] = {"RHR": entry.resting_heart_rate}
        
        for entry in summary_entries:
            if entry.day in health_data:
                health_data[entry.day]["Stress"] = entry.stress_avg
            else:
                health_data[entry.day] = {"Stress": entry.stress_avg}
        
        df = pd.DataFrame.from_dict(health_data, orient='index').sort_index(ascending=False)
        print(df)

if __name__ == "__main__":
    check_health()
