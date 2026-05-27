import os
import logging
import pandas as pd
from dotenv import load_dotenv
from garmindb.garmindb import ActivitiesDb, Activities
from garmindb import GarminConnectConfigManager
from analyze_performance import PerformanceCoach

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    
    # 1. Sync data from Garmin (Optional if user wants to run it separately)
    # logger.info("To sync data, run: uv run scripts/sync_garmindb.py")

    # 2. Access GarminDB
    logger.info("Accessing GarminDB for coaching review...")
    try:
        config_dir = os.getcwd()
        if not os.path.exists(os.path.join(config_dir, "GarminConnectConfig.json")):
            logger.warning("GarminConnectConfig.json not found. Please run scripts/sync_garmindb.py first.")
            return

        # Initialize the Deep Performance Coach
        coach = PerformanceCoach()
        
        # 3. Perform Deep Diagnostic
        coach.run_full_diagnostic(limit=2) # Analyze last 2 sessions in depth

        print(f"\n{'='*60}")
        print("   QUICK PROGRESS OVERVIEW")
        print(f"{'='*60}")
        
        # Quick table view
        act_db = coach.act_db
        latest_activities = Activities.get_latest(act_db, 5)

        if latest_activities:
            data = []
            for act in latest_activities:
                data.append({
                    "Date": act.start_time,
                    "Sport": act.sport,
                    "Name": act.name if act.name else "N/A",
                    "Dist (km)": round(act.distance, 2) if act.distance else 0,
                    "Avg HR": act.avg_hr
                })
            df = pd.DataFrame(data)
            print(df)
            
            print(f"\n{'-'*60}")
            print("Next Steps: Review plan.md and goals.md for upcoming targets.")
            print(f"{'-'*60}")
        else:
            logger.info("No activities found in GarminDB. Run scripts/sync_garmindb.py to import your data.")

    except Exception as e:
        logger.error(f"Error accessing GarminDB: {e}")

if __name__ == "__main__":
    main()
