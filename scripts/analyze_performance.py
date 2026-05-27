import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from garmindb.garmindb import (
    ActivitiesDb, Activities, ActivityRecords, ActivityLaps, 
    GarminDb, RestingHeartRate, Hrv, DailySummary, ActivitySplits
)
from garmindb import GarminConnectConfigManager

class PerformanceCoach:
    def __init__(self):
        config_dir = os.getcwd()
        self.config = GarminConnectConfigManager(config_dir)
        self.db_params = self.config.get_db_params()
        self.act_db = ActivitiesDb(self.db_params)
        self.garmin_db = GarminDb(self.db_params)
        self.alerts = []

    def _to_seconds(self, duration):
        if duration is None: return 0
        if isinstance(duration, (int, float)): return duration
        if hasattr(duration, 'hour'):
            return duration.hour * 3600 + duration.minute * 60 + duration.second
        return 0

    def check_health_trends(self):
        warnings = []
        with self.garmin_db.managed_session() as session:
            rhr_entries = session.query(RestingHeartRate).order_by(RestingHeartRate.day.desc()).limit(14).all()
            hrv_entries = session.query(Hrv).order_by(Hrv.day.desc()).limit(14).all()
            
            # Check RHR baseline
            if len(rhr_entries) > 1:
                current_rhr = rhr_entries[0].resting_heart_rate
                baseline_entries = rhr_entries[1:8]
                if baseline_entries:
                    baseline_rhr = sum(e.resting_heart_rate for e in baseline_entries) / len(baseline_entries)
                    rhr_increase = current_rhr - baseline_rhr
                    if rhr_increase >= 5.0:
                        warn = f"🚨 HARD STOP: Resting Heart Rate spiked +{rhr_increase:.1f} bpm over baseline (Current: {current_rhr:.1f} bpm, Baseline: {baseline_rhr:.1f} bpm). High-intensity work is prohibited today."
                        warnings.append(warn)
                        self.alerts.append(warn)
            
            # Check HRV
            if hrv_entries:
                latest = hrv_entries[0]
                if latest.last_night_avg and latest.baseline_low and latest.last_night_avg < latest.baseline_low:
                    warn = f"⚠️ HRV UNBALANCED: Last night's HRV was {latest.last_night_avg} ms, below baseline low of {latest.baseline_low} ms. Recovery is compromised."
                    warnings.append(warn)
                    self.alerts.append(warn)
                
                if len(hrv_entries) > 7:
                    old_weekly = hrv_entries[7].weekly_avg
                    if latest.weekly_avg and old_weekly and latest.weekly_avg - old_weekly <= -3:
                        warn = f"⚠️ HRV DOWNWARD TREND: 7-day HRV average dropped from {old_weekly} ms to {latest.weekly_avg} ms. Cumulative fatigue is building."
                        warnings.append(warn)
                        self.alerts.append(warn)
        return warnings

    def get_coach_scorecard(self, limit=1):
        """Generates a high-fidelity narrative analysis for recent activities."""
        activities = Activities.get_latest(self.act_db, limit)
        if not activities:
            print("No data found for scorecard.")
            return

        for act in activities:
            print(f"\n{'='*60}")
            print(f"COACH'S SCORECARD: {act.sport.upper()} - {act.start_time}")
            print(f"{'='*60}")

            if act.sport == 'running':
                self._analyze_run_deep(act)
            elif act.sport in ['rock_climbing', 'mountaineering']:
                if act.sub_sport == 'bouldering' or (act.name and 'bouldering' in act.name.lower()):
                    self._analyze_bouldering_deep(act)
                else:
                    self._analyze_climb_deep(act)
            elif act.sport == 'strength_training' or act.sport == 'fitness_equipment':
                self._analyze_strength_deep(act)
            
            print(f"\n--- Recovery & Macro Context ---")
            print(f"Weekly Load Contribution: {self._fmt(act.training_load, 1) if act.training_load else 'TBD'}")
            print(f"Target: Refer to plan.md and goals.md for alignment.")

    def _fmt(self, value, decimals=0, default="TBD"):
        if value is None: return default
        return round(value, decimals)

    def _fmt_pace(self, speed_kmh):
        if not speed_kmh or speed_kmh <= 0:
            return "TBD"
        pace_mins = 60 / speed_kmh
        m = int(pace_mins)
        s = int(round((pace_mins - m) * 60))
        if s == 60:
            m += 1
            s = 0
        return f"{m}:{s:02d}"

    def _analyze_run_deep(self, act):
        # 1. The Numbers
        print(f"\n### The Session Scorecard")
        print(f"* Total Distance: {self._fmt(act.distance, 2)} km")
        print(f"* Avg Pace: {self._fmt_pace(act.avg_speed) if act.avg_speed else 'TBD'} min/km")
        print(f"* Avg Heart Rate: {self._fmt(act.avg_hr)} bpm")
        
        avg_cadence_spm = act.avg_cadence * 2 if act.avg_cadence else None
        if avg_cadence_spm:
            print(f"* Avg Cadence: {avg_cadence_spm} spm")
            if avg_cadence_spm < 165:
                warn = f"⚠️ CADENCE WARNING: Run on {act.start_time.strftime('%Y-%m-%d')} had average cadence of {avg_cadence_spm} spm (below knee-safe 165 spm)."
                print(f"  {warn}")
                self.alerts.append(warn)
            elif 170 <= avg_cadence_spm <= 172:
                print(f"  ✅ CADENCE OPTIMAL: {avg_cadence_spm} spm (Target 170-172 spm achieved). Excellent joint alignment!")
        else:
            print("* Avg Cadence: TBD")

        # 2. Zone 2 Adherence (122-147 bpm)
        with self.act_db.managed_session() as session:
            records = session.query(ActivityRecords).filter(ActivityRecords.activity_id == act.activity_id).all()
            if records:
                hr_vals = [r.hr for r in records if r.hr is not None]
                if hr_vals:
                    z2_sec = sum(1 for hr in hr_vals if 122 <= hr <= 147)
                    z2_pct = (z2_sec / len(hr_vals)) * 100
                    compliance = "✅ OPTIMAL" if z2_pct >= 80 else "⚠️ INTENSITY LEAK"
                    print(f"\n### Heart Rate & Zone 2 Adherence")
                    print(f"Adherence: {z2_pct:.1f}% in Zone 2 ({compliance})")
                    print(f"Target: >80% in Zone 2 (122-147 bpm) for base runs. Staying in this range builds mitochondrial density for the 10k.")
                    if z2_pct < 80:
                        warn = f"⚠️ RUN INTENSITY LEAK: Run on {act.start_time.strftime('%Y-%m-%d')} had only {z2_pct:.1f}% Zone 2 adherence (Target: >80%)."
                        self.alerts.append(warn)

        # 3. Lap Breakdown (Programmatic 1km Reconstructed Laps)
        if records:
            print(f"\n### Reconstructed Lap Breakdown (1 km Splits)")
            laps = []
            prev_dist = 0.0
            prev_time = records[0].timestamp
            lap_hr = []
            lap_num = 1
            current_target = 1.0
            
            for r in records:
                dist = r.distance if r.distance is not None else 0.0
                if r.hr is not None:
                    lap_hr.append(r.hr)
                    
                if dist >= current_target:
                    split_dist = dist - prev_dist
                    split_dur = (r.timestamp - prev_time).total_seconds()
                    
                    if split_dist > 0:
                        pace_decimal = (split_dur / 60) / split_dist
                        pace_min = int(pace_decimal)
                        pace_sec = int(round((pace_decimal - pace_min) * 60))
                        if pace_sec == 60:
                            pace_min += 1
                            pace_sec = 0
                        pace_str = f"{pace_min}:{pace_sec:02d}"
                    else:
                        pace_str = "N/A"
                        
                    avg_hr = sum(lap_hr) / len(lap_hr) if lap_hr else None
                    max_hr = max(lap_hr) if lap_hr else None
                    
                    laps.append({
                        "Lap": lap_num,
                        "Dist (km)": round(split_dist, 2),
                        "Pace": pace_str,
                        "Avg HR": round(avg_hr) if avg_hr else "TBD",
                        "Max HR": max_hr if max_hr else "TBD"
                    })
                    
                    prev_dist = dist
                    prev_time = r.timestamp
                    lap_hr = []
                    lap_num += 1
                    current_target += 1.0
                    
            # Final lap
            final_dist = records[-1].distance if records[-1].distance is not None else 0.0
            if final_dist > prev_dist:
                split_dist = final_dist - prev_dist
                split_dur = (records[-1].timestamp - prev_time).total_seconds()
                if split_dist > 0.01:
                    pace_decimal = (split_dur / 60) / split_dist
                    pace_min = int(pace_decimal)
                    pace_sec = int(round((pace_decimal - pace_min) * 60))
                    if pace_sec == 60:
                        pace_min += 1
                        pace_sec = 0
                    pace_str = f"{pace_min}:{pace_sec:02d}"
                    
                    avg_hr = sum(lap_hr) / len(lap_hr) if lap_hr else None
                    max_hr = max(lap_hr) if lap_hr else None
                    
                    laps.append({
                        "Lap": lap_num,
                        "Dist (km)": round(split_dist, 2),
                        "Pace": pace_str,
                        "Avg HR": round(avg_hr) if avg_hr else "TBD",
                        "Max HR": max_hr if max_hr else "TBD"
                    })
            
            df = pd.DataFrame(laps)
            print(df.to_string(index=False))

        # 4. Decoupling (runs > 45 mins)
        duration_sec = self._to_seconds(act.elapsed_time)
        if duration_sec > 2700 and records:
            rec_df = pd.DataFrame([{'hr': r.hr, 'speed': r.speed} for r in records if r.hr and r.speed])
            if len(rec_df) > 100:
                mid = len(rec_df) // 2
                ef1 = rec_df.iloc[:mid]['speed'].mean() / rec_df.iloc[:mid]['hr'].mean()
                ef2 = rec_df.iloc[mid:]['speed'].mean() / rec_df.iloc[mid:]['hr'].mean()
                drift = ((ef1 - ef2) / ef1) * 100
                print(f"\n### Aerobic Stability (Cardiac Drift)")
                print(f"Decoupling: {drift:.2f}% | {'✅ STABLE' if drift < 5 else '⚠️ DECOUPLED'}")
                if drift >= 5:
                    warn = f"⚠️ AEROBIC DECOUPLING HIGH: Run on {act.start_time.strftime('%Y-%m-%d')} decoupled by {drift:.2f}% (Target: <5%)."
                    print("  Analysis: Decoupling > 5% indicates Aerobic Deficiency Syndrome (ADS) or heat stress/dehydration.")
                    self.alerts.append(warn)
        else:
            print(f"\n### Aerobic Stability (Cardiac Drift)")
            print(f"Decoupling: Not calculated. Run duration ({duration_sec/60:.1f} mins) is <= 45 minutes.")

    def _analyze_climb_deep(self, act):
        print(f"\n### Technical Analysis: {act.name if act.name else 'Lead Climbing Session'}")
        print(f"* Peak Intensity: {self._fmt(act.max_hr)} bpm")
        
        # Economy Score (Z1/Z2 Ratio)
        z1 = self._to_seconds(act.hrz_1_time)
        z2 = self._to_seconds(act.hrz_2_time)
        z3 = self._to_seconds(act.hrz_3_time)
        z4 = self._to_seconds(act.hrz_4_time)
        z5 = self._to_seconds(act.hrz_5_time)
        total = z1 + z2 + z3 + z4 + z5

        if total > 0:
            climbing_economy = ((z1 + z2) / total) * 100
            compliance = "✅ OPTIMAL" if climbing_economy >= 80 else "⚠️ INTENSITY LEAK"
            print(f"* Climbing Economy Score (Z1/Z2 Flow Time): {climbing_economy:.1f}% ({compliance})")
            print(f"  * Z1 (Flow/Recovery): {z1/total*100:.1f}%")
            print(f"  * Z5 (Anaerobic Limit): {z5/total*100:.1f}%")
            if climbing_economy < 80:
                warn = f"⚠️ CLIMB ECONOMY LEAK: climbing economy was {climbing_economy:.1f}% on {act.start_time.strftime('%Y-%m-%d')} (Target: >80% for volume)."
                self.alerts.append(warn)
            
        if act.avg_hr and act.max_hr:
            intensity = (act.avg_hr / act.max_hr) * 100
            print(f"* Intensity Score: {intensity:.1f}% | Target: <70% for volume, >85% for redpoint")
            
        # Route-level grade checks
        with self.act_db.managed_session() as session:
            splits = session.query(ActivitySplits).filter(ActivitySplits.activity_id == act.activity_id).all()
            if splits:
                print("\n### Route-Level Movement Economy")
                economy_warnings = []
                for s in splits:
                    grade = s.grade
                    def is_easy_grade(grade_str):
                        if not grade_str: return False
                        grade_str = grade_str.strip().lower()
                        if grade_str[0].isdigit():
                            try:
                                return int(grade_str[0]) < 6
                            except ValueError:
                                pass
                        return False
                    
                    if is_easy_grade(grade) and s.avg_hr and s.avg_hr > 160:
                        warn = f"⚠️ MOVEMENT ECONOMY ALERT: Route split {s.split} (Grade {grade}) averaged {s.avg_hr} bpm (>160 bpm on easy grade)."
                        print(f"  {warn}")
                        economy_warnings.append(s)
                        self.alerts.append(warn)
                if not economy_warnings:
                    print("✅ All easy-grade routes (< 6a) completed with controlled heart rate (< 160 bpm). Excellent movement economy!")

    def _analyze_bouldering_deep(self, act):
        print(f"\n### Bouldering Performance Analysis: {act.name if act.name else 'Indoor Power Session'}")
        
        # Peak HR freshness check
        max_hr = act.max_hr
        if max_hr:
            print(f"* Peak HR Reached: {max_hr} bpm")
            if max_hr >= 185:
                print("  ✅ PEAK RECRUITMENT OPTIMAL: HR hit 185+ bpm, indicating high central nervous system (CNS) freshness.")
            elif max_hr < 170:
                warn = f"🚨 CNS FATIGUE ALERT: Peak HR was only {max_hr} bpm (below 170 bpm) on bouldering session {act.start_time.strftime('%Y-%m-%d')}, suggesting systemic overtraining."
                print(f"  {warn}")
                self.alerts.append(warn)
        
        with self.act_db.managed_session() as session:
            records = session.query(ActivityRecords).filter(ActivityRecords.activity_id == act.activity_id).order_by(ActivityRecords.timestamp).all()
            if records:
                records_list = [{'hr': r.hr, 'timestamp': r.timestamp} for r in records if r.hr is not None]
                if len(records_list) > 30:
                    peaks = []
                    # Peak detection (effort spikes)
                    for i in range(15, len(records_list) - 15):
                        hr_val = records_list[i]['hr']
                        if hr_val >= 130:
                            window = [r['hr'] for r in records_list[i-15:i+16]]
                            if hr_val == max(window):
                                if not peaks or (records_list[i]['timestamp'] - peaks[-1]['timestamp']).total_seconds() > 60:
                                    peaks.append({
                                        'index': i,
                                        'timestamp': records_list[i]['timestamp'],
                                        'peak_hr': hr_val
                                    })
                                    
                    print(f"\n### Detected Bouldering Sets & Recovery Curve")
                    for idx, p in enumerate(peaks):
                        peak_time = p['timestamp']
                        peak_idx = p['index']
                        
                        # Recovery time (drop below 120 bpm)
                        recovery_dur = None
                        for j in range(peak_idx, len(records_list)):
                            if records_list[j]['hr'] < 120:
                                recovery_dur = (records_list[j]['timestamp'] - peak_time).total_seconds()
                                break
                                
                        # Rest to next set (ATP recovery check)
                        rest_to_next = None
                        rest_warning = ""
                        if idx < len(peaks) - 1:
                            rest_to_next = (peaks[idx+1]['timestamp'] - peak_time).total_seconds()
                            if rest_to_next < 180:
                                rest_warning = "⚠️ SHORT REST"
                                warn = f"⚠️ ATP REST COMPROMISED: Rest between set {idx+1} and {idx+2} was only {int(rest_to_next)}s (Target: >3 mins)."
                                self.alerts.append(warn)
                                
                        rec_str = f"{int(recovery_dur)}s" if recovery_dur is not None else "N/A"
                        rest_str = f"{int(rest_to_next)}s {rest_warning}" if rest_to_next is not None else "N/A"
                        print(f"* Set {idx+1:2d} | Peak HR: {p['peak_hr']:3d} bpm | Recovery to <120 bpm: {rec_str:5s} | Rest to next: {rest_str}")
                        
                        if recovery_dur is not None and recovery_dur > 90:
                            warn = f"⚠️ SLOW BOULDER RECOVERY: Set {idx+1} took {int(recovery_dur)}s to drop below 120 bpm (Target: <90s)."
                            self.alerts.append(warn)
                            
                    if any(p.get('recovery_sec', 0) > 90 for p in peaks if 'recovery_sec' in p):
                        print("\n⚠️ Note: Recovery times > 90s indicate accumulating cardiovascular fatigue. Increase rest intervals.")

    def _analyze_strength_deep(self, act):
        print(f"\n### Strength Session Analysis: {act.name if act.name else '7a Workout'}")
        duration_mins = self._to_seconds(act.elapsed_time) / 60
        print(f"* Total Duration: {self._fmt(duration_mins, 1) if duration_mins else 'TBD'} mins")
        print(f"* Avg Heart Rate: {self._fmt(act.avg_hr)} bpm")

        json_path = os.path.join(os.getcwd(), f"GarminDB/FitFiles/Activities/activity_{act.activity_id}.json")
        parsed_from_json = False
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                sets_summary = data.get('summarizedExerciseSets', [])
                if sets_summary:
                    print(f"\n### Exercise Breakdown (Parsed from Garmin Connect JSON)")
                    parsed_from_json = True
                    deadlift_found = False
                    frenchies_found = False
                    
                    for ex in sets_summary:
                        cat = ex.get('category', '').upper()
                        sub_cat = ex.get('subCategory', '').upper()
                        sets = ex.get('sets', 0)
                        duration_ms = ex.get('duration', 0.0)
                        max_w_g = ex.get('maxWeight', 0.0)
                        reps = ex.get('reps', 0)
                        
                        dur_sec = duration_ms / 1000.0
                        avg_tut = dur_sec / sets if sets > 0 else 0
                        max_w_kg = max_w_g / 1000.0
                        
                        if cat == 'DEADLIFT':
                            deadlift_found = True
                            load_pct = (max_w_kg / 28.0) * 100
                            compliance = "✅ OPTIMAL LOAD" if max_w_kg >= 23 else "⚠️ WORK IN PROGRESS"
                            print(f"\n* **Finger pulls (Deadlift Substitute):**")
                            print(f"  * Sets: {sets}")
                            print(f"  * Max Load: {max_w_kg:.1f} kg ({load_pct:.1f}% of 28kg base max) - {compliance}")
                            print(f"  * Average TUT: {avg_tut:.1f}s per set (Target: 6s recruitment lifts)")
                            if max_w_kg < 23:
                                warn = f"⚠️ STRENGTH LOAD LOW: Recruitment load was {max_w_kg:.1f} kg on {act.start_time.strftime('%Y-%m-%d')} (Build target: >=23 kg)."
                                self.alerts.append(warn)
                        elif cat == 'PULL_UP' or sub_cat == 'DEAD_HANG_BICEPS_CURL' or 'CURL' in cat or 'HANG' in sub_cat:
                            frenchies_found = True
                            compliance = "✅ OPTIMAL TUT (20-30s)" if 20 <= avg_tut <= 30 else ("⚠️ LOW TUT" if avg_tut < 20 else "✅ HIGH TUT (Optimal for recruitment/endurance)")
                            print(f"\n* **Frenchies / Lock-offs ({cat.title()} / {sub_cat.title() if sub_cat else 'None'}):**")
                            print(f"  * Sets: {sets} | Reps: {reps}")
                            print(f"  * Average TUT: {avg_tut:.1f}s per set - {compliance}")
                            if avg_tut < 20:
                                warn = f"⚠️ FRENCHIE TUT LOW: Average TUT was {avg_tut:.1f}s on {act.start_time.strftime('%Y-%m-%d')} (Target: 20-30s)."
                                self.alerts.append(warn)
                        else:
                            print(f"\n* **{cat.title()} ({sub_cat.title() if sub_cat else 'None'}):**")
                            print(f"  * Sets: {sets} | Reps: {reps} | Avg TUT: {avg_tut:.1f}s | Max Weight: {max_w_kg:.1f} kg")
                            
                    if not deadlift_found:
                        print("\n⚠️ No Finger Lifts (Deadlift) found. Remember to log your quad block sets as Deadlift in Garmin Connect!")
                    if not frenchies_found:
                        print("⚠️ No Frenchies (Pull-Up/Dead Hang) found. Log them in Garmin Connect to track lock-off Time Under Tension.")
                    
                    print("\n* **Path to 7a Alignment:**")
                    print("  This builds the 'Chassis'. Ensure you maintain 3 minutes rest between recruitment sets for ATP-CP replenishment.")
            except Exception as e:
                print(f"Warning: Could not parse strength JSON: {e}")
                
        if not parsed_from_json:
            # Fallback to sqlite laps
            with self.act_db.managed_session() as session:
                laps = ActivityLaps.s_get_activity(session, act.activity_id)
                if laps:
                    print(f"\n### Set Breakdown (Time Under Tension)")
                    data = []
                    for lap in laps:
                        duration_sec = self._to_seconds(lap.elapsed_time)
                        data.append({
                            "Set": lap.lap,
                            "TUT (s)": duration_sec,
                            "Avg HR": lap.avg_hr,
                            "Max HR": lap.max_hr
                        })
                    df = pd.DataFrame(data)
                    print(df.to_string(index=False))
                    
                    avg_tut = df['TUT (s)'].mean()
                    print(f"\n### Recruitment Stimulus")
                    print(f"* Average TUT: {avg_tut:.1f}s")
                    if avg_tut < 20:
                        print("⚠️ Analysis: Low Time Under Tension. Ensure you are holding Frenchies for the full 5s per position.")
                        warn = f"⚠️ FRENCHIE TUT LOW: Average TUT was {avg_tut:.1f}s on fallback query."
                        self.alerts.append(warn)
                    else:
                        print("✅ Analysis: High TUT detected. This is optimal for end-range recruitment.")

    def run_full_diagnostic(self, limit=3):
        print("\n" + "="*60)
        print("   AI COACH DEEP PERFORMANCE DIAGNOSTIC")
        print("="*60)
        
        self.alerts = []
        # Run health checks to populate alerts first
        self.check_health_trends()
        
        # Run the scorecard (appends scorecard metrics warnings)
        self.get_coach_scorecard(limit=limit)
        
        # Run weekly load trend
        self.weekly_load_trend()

        # Display health warnings / hard stops consolidated at the bottom
        if self.alerts:
            print("\n" + "!"*60)
            print("🚨🚨🚨 CONSOLIDATED ACTIVE COACH WARNINGS & ALERTS 🚨🚨🚨")
            print("!"*60)
            for alert in self.alerts:
                print(f" - {alert}")
            print("!"*60)
        else:
            print("\n" + "="*60)
            print("✅ ALL SYSTEMS NOMINAL: No health, cadence, or intensity red flags detected.")
            print("="*60)

    def weekly_load_trend(self):
        with self.act_db.managed_session() as session:
            activities = Activities.get_latest(self.act_db, 20)
            df = pd.DataFrame([{
                'date': a.start_time,
                'load': a.training_load if a.training_load else 0
            } for a in activities])
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                weekly_load = df['load'].resample('W').sum()
                print(f"\n{'='*60}")
                print("WEEKLY TRAINING LOAD TREND")
                print(f"{'='*60}")
                print(weekly_load.tail(4))
                
                loads = weekly_load.tail(2).values
                if len(loads) == 2:
                    if loads[1] <= loads[0] * 0.5:
                        print("\n✅ DELOAD STATUS: Deload week completed with >50% load reduction. Optimal recovery achieved.")
                    elif loads[1] > loads[0]:
                        print("\n⚠️ INTENSIFICATION STATUS: Weekly load is rising. Monitor HRV/RHR for signs of CNS fatigue.")
                    else:
                        load_reduction_pct = ((loads[0] - loads[1]) / loads[0]) * 100
                        warn = f"⚠️ DELOAD VOLUME HIGH: Load reduction was only {load_reduction_pct:.1f}% (Target: >50% load reduction for deload)."
                        print(f"\n{warn}")
                        self.alerts.append(warn)

if __name__ == "__main__":
    coach = PerformanceCoach()
    coach.run_full_diagnostic()
