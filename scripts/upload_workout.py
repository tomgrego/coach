#!/usr/bin/env python3
import os
import sys
import json
import argparse
import logging
from garminconnect import Garmin

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def pace_to_speed(pace_str: str) -> float:
    """Converts a pace string (MM:SS) to speed in meters per second (m/s)."""
    try:
        parts = pace_str.split(":")
        minutes = int(parts[0])
        seconds = int(parts[1])
        total_seconds = minutes * 60 + seconds
        if total_seconds <= 0:
            raise ValueError
        return 1000.0 / total_seconds
    except Exception:
        raise ValueError(f"Invalid pace format '{pace_str}'. Use MM:SS (e.g., 4:45).")

def speed_to_pace_str(speed: float) -> str:
    """Converts speed in m/s to a pace string (MM:SS)."""
    if speed <= 0:
        return "0:00"
    total_seconds = int(round(1000.0 / speed))
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"

def customize_monday_workout(workout: dict, weight: float) -> dict:
    """Updates the weight and description for Monday finger lifts."""
    workout["workoutName"] = f"Build 1 W22 - Monday Max Strength & structural hardening ({weight}kg)"
    
    # Traverse segment steps to find deadlift
    steps_updated = 0
    for segment in workout.get("workoutSegments", []):
        for step in segment.get("workoutSteps", []):
            # Check if it's a repeat group or executable step
            if step.get("type") == "RepeatGroupDTO":
                for child in step.get("workoutSteps", []):
                    if child.get("category") == "DEADLIFT":
                        child["weightValue"] = weight
                        child["description"] = f"Max Strength Finger Lift: Pull {weight}kg on quad block, hold 6s. Active shoulders."
                        steps_updated += 1
            elif step.get("category") == "DEADLIFT":
                step["weightValue"] = weight
                step["description"] = f"Max Strength Finger Lift: Pull {weight}kg on quad block, hold 6s. Active shoulders."
                steps_updated += 1
                
    logger.info(f"Updated Monday workout with weight: {weight}kg ({steps_updated} steps modified)")
    return workout

def customize_tuesday_workout(workout: dict, pace_str: str) -> dict:
    """Updates the pace target and descriptions for Tuesday running intervals."""
    # Convert base pace to seconds
    parts = pace_str.split(":")
    minutes = int(parts[0])
    seconds = int(parts[1])
    base_seconds = minutes * 60 + seconds
    
    # Calculate range: base_pace +/- 5 seconds
    faster_seconds = base_seconds - 5
    slower_seconds = base_seconds + 5
    
    faster_pace_str = f"{faster_seconds // 60}:{faster_seconds % 60:02d}"
    slower_pace_str = f"{slower_seconds // 60}:{slower_seconds % 60:02d}"
    
    speed_faster = 1000.0 / faster_seconds  # targetValueOne (faster speed)
    speed_slower = 1000.0 / slower_seconds  # targetValueTwo (slower speed)
    
    workout["workoutName"] = f"Build 1 W22 - Tuesday VO2 Max Intervals (4x1km) @ {pace_str}"
    
    steps_updated = 0
    for segment in workout.get("workoutSegments", []):
        for step in segment.get("workoutSteps", []):
            if step.get("type") == "RepeatGroupDTO":
                for child in step.get("workoutSteps", []):
                    if child.get("stepType", {}).get("stepTypeKey") == "interval":
                        child["targetValueOne"] = round(speed_faster, 4)
                        child["targetValueTwo"] = round(speed_slower, 4)
                        child["description"] = f"1km interval @ {pace_str} min/km pace target (Range: {faster_pace_str}-{slower_pace_str})"
                        steps_updated += 1
            elif step.get("stepType", {}).get("stepTypeKey") == "interval":
                step["targetValueOne"] = round(speed_faster, 4)
                step["targetValueTwo"] = round(speed_slower, 4)
                step["description"] = f"1km interval @ {pace_str} min/km pace target (Range: {faster_pace_str}-{slower_pace_str})"
                steps_updated += 1
                
    logger.info(f"Updated Tuesday workout with pace: {pace_str} min/km (Range: {faster_pace_str}-{slower_pace_str})")
    return workout

def delete_existing_workout_by_name(client: Garmin, name: str):
    """Deletes existing workouts with the same name to prevent duplicates."""
    try:
        workouts = client.get_workouts()
        deleted_count = 0
        for w in workouts:
            if w.get("workoutName") == name:
                workout_id = w.get("workoutId")
                logger.info(f"Found existing workout '{name}' with ID {workout_id}. Deleting...")
                client.delete_workout(workout_id)
                deleted_count += 1
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} duplicate workout(s).")
    except Exception as e:
        logger.warning(f"Could not check or delete duplicate workouts: {e}")

def main():
    parser = argparse.ArgumentParser(description="Upload customized workouts to Garmin Connect.")
    parser.add_argument("--file", help="Path to a custom workout JSON template to upload directly.")
    parser.add_argument("--monday", action="store_true", help="Upload Monday Max Strength workout.")
    parser.add_argument("--tuesday", action="store_true", help="Upload Tuesday VO2 Max Intervals workout.")
    parser.add_argument("--weight", type=float, default=23.0, help="Finger lift weight override in kg (Monday workout, default: 23.0).")
    parser.add_argument("--pace", default="4:45", help="Target interval pace override as MM:SS (Tuesday workout, default: 4:45).")
    parser.add_argument("--dry-run", action="store_true", help="Print the workout JSON without uploading it.")
    parser.add_argument("--token-path", default="garmin_tokens.json", help="Path to the Garmin tokens file (default: garmin_tokens.json).")
    
    args = parser.parse_args()
    
    if not (args.file or args.monday or args.tuesday):
        parser.print_help()
        sys.exit(1)
        
    # Determine which file to load
    workout_file = None
    if args.file:
        workout_file = args.file
    elif args.monday:
        workout_file = "workouts/monday_strength.json"
    elif args.tuesday:
        workout_file = "workouts/tuesday_intervals.json"
        
    if not os.path.exists(workout_file):
        logger.error(f"Workout file '{workout_file}' not found.")
        sys.exit(1)
        
    try:
        with open(workout_file, "r") as f:
            workout = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read JSON from '{workout_file}': {e}")
        sys.exit(1)
        
    # Perform customizations
    if args.monday:
        workout = customize_monday_workout(workout, args.weight)
    elif args.tuesday:
        workout = customize_tuesday_workout(workout, args.pace)
        
    # If dry-run, just output and exit
    if args.dry_run:
        logger.info("Dry-run mode: Printing generated workout JSON payload.")
        print(json.dumps(workout, indent=2))
        sys.exit(0)
        
    # Login using garmin_tokens.json
    if not os.path.exists(args.token_path):
        logger.error(f"Garmin tokens file '{args.token_path}' not found. Cannot authenticate.")
        sys.exit(1)
        
    logger.info("Authenticating with Garmin Connect using token file...")
    try:
        client = Garmin()
        client.client.load(args.token_path)
        if not client.client.is_authenticated:
            logger.error("Authentication failed. Stored tokens might be invalid or expired.")
            sys.exit(1)
        logger.info("Successfully authenticated!")
    except Exception as e:
        logger.error(f"Failed to authenticate: {e}")
        sys.exit(1)
        
    # Delete duplicate workout before uploading
    workout_name = workout.get("workoutName")
    if workout_name:
        delete_existing_workout_by_name(client, workout_name)
        
    # Upload workout
    logger.info(f"Uploading workout '{workout_name}'...")
    try:
        response = client.upload_workout(workout)
        workout_id = response.get("workoutId")
        logger.info(f"Workout uploaded successfully! Workout ID: {workout_id}")
        logger.info("You can now find this workout in Garmin Connect under 'Training & Planning' -> 'Workouts' and sync it to your watch.")
    except Exception as e:
        logger.error(f"Failed to upload workout: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
