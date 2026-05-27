import os
import logging
from datetime import date, timedelta
from dotenv import load_dotenv
from garminconnect import Garmin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_garmin_data():
    load_dotenv()
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not email or not password:
        logger.error("GARMIN_EMAIL or GARMIN_PASSWORD not found in .env file")
        return

    try:
        # Initialize Garmin client
        client = Garmin(email, password)
        client.login()
        logger.info("Successfully logged into Garmin Connect")

        # Define date range for activities (e.g., last 7 days)
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        activities = client.get_activities_by_date(
            start_date.isoformat(), end_date.isoformat()
        )
        logger.info(f"Found {len(activities)} activities")

        # Create activities directory if it doesn't exist
        os.makedirs("activities", exist_ok=True)

        for activity in activities:
            activity_id = activity["activityId"]
            activity_date = activity["startTimeLocal"].split(" ")[0]
            activity_name = activity["activityName"].replace(" ", "_")
            file_name = f"{activity_date}_{activity_id}_{activity_name}.fit"
            file_path = os.path.join("activities", file_name)

            if not os.path.exists(file_path):
                logger.info(f"Downloading activity {activity_id}...")
                data = client.download_activity(activity_id, dl_fmt=client.ActivityDownloadFormat.ORIGINAL)
                with open(file_path, "wb") as f:
                    f.write(data)
                logger.info(f"Saved to {file_path}")
            else:
                logger.info(f"Activity {activity_id} already exists locally")

        # Fetch health stats (optional but useful)
        stats = client.get_stats(end_date.isoformat())
        logger.info(f"Daily stats fetched: {stats}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    fetch_garmin_data()
