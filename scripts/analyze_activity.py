import os
import pandas as pd
from fitparse import FitFile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def semicircles_to_degrees(semicircles):
    if semicircles is None: return None
    return semicircles * (180.0 / 2**31)

class ActivityAnalyzer:
    def __init__(self, activities_dir="activities"):
        self.activities_dir = activities_dir
        self.summary_file = "activities_summary.csv"

    def analyze_file(self, file_path):
        """Analyzes a single FIT file and returns a summary dictionary."""
        try:
            fitfile = FitFile(file_path)
            
            # Extract basic session info
            session_msgs = list(fitfile.get_messages('session'))
            if not session_msgs:
                logger.warning(f"No session message found in {file_path}")
                return None
            
            sess = session_msgs[0]
            data = {
                "file_name": os.path.basename(file_path),
                "timestamp": sess.get_value('start_time'),
                "sport": sess.get_value('sport'),
                "sub_sport": sess.get_value('sub_sport'),
                "total_elapsed_time": sess.get_value('total_elapsed_time'),
                "total_distance": sess.get_value('total_distance'),
                "avg_heart_rate": sess.get_value('avg_heart_rate'),
                "max_heart_rate": sess.get_value('max_heart_rate'),
                "total_calories": sess.get_value('total_calories'),
            }

            # For climbing, try to get more details from laps/sets
            if data['sport'] in ['climbing', 'rock_climbing']:
                laps = list(fitfile.get_messages('lap'))
                data['climb_laps'] = len(laps)
                # You can add more climbing specific logic here if needed

            return data
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return None

    def update_summary(self):
        """Iterates through all files in activities_dir and updates the summary CSV."""
        all_data = []
        for file_name in os.listdir(self.activities_dir):
            if file_name.endswith(".fit"):
                file_path = os.path.join(self.activities_dir, file_name)
                # In a real scenario, we might want to check if the file is already in the summary
                data = self.analyze_file(file_path)
                if data:
                    all_data.append(data)
        
        if all_data:
            df = pd.DataFrame(all_data)
            df.to_csv(self.summary_file, index=False)
            logger.info(f"Summary updated with {len(all_data)} activities and saved to {self.summary_file}")
            return df
        else:
            logger.info("No activities found to summarize.")
            return None

if __name__ == "__main__":
    analyzer = ActivityAnalyzer()
    analyzer.update_summary()
