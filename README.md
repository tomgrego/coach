# AI Training & Nutrition Coach

This project is your automated training assistant, designed to help you reach a **7a climbing grade** and a **50-minute 10k run** by the end of 2026.

## Structure

- `scripts/coach_dashboard.py`: The central orchestrator.
- `scripts/sync_garmindb.py`: Automates GarminDB setup and data synchronization.
- `scripts/analyze_performance.py`: Deep dive into metrics (Decoupling, Cadence, TRIMP).
- `scripts/check_health.py`: Quick view of RHR and Stress levels.
- `scripts/check_recovery.py`: Quick view of HRV trends.
- `GarminDB/`: Local SQLite database and raw data storage (managed by GarminDB).
- `GarminConnectConfig.json`: Project-local configuration for GarminDB.
- `goals.md`: Persists your long-term goals and physical profile.
- `plan.md`: Your current training schedule and nutritional guidelines.

## Setup

1.  **Dependencies:** Managed by `uv`. Run `uv sync` to ensure everything is installed.
2.  **Credentials:** Copy `.env.example` to `.env` and enter your Garmin credentials.
    ```bash
    cp .env.example .env
    ```
3.  **Sync Data:** Run the GarminDB sync script.
    ```bash
    uv run scripts/sync_garmindb.py
    ```
4.  **Coach Analysis:** Run the coach dashboard or specific analysis scripts.
    ```bash
    uv run scripts/coach_dashboard.py
    uv run scripts/analyze_performance.py
    ```

## Deep Analysis Workflow

The coach performs a multi-layered diagnostic for every activity synced from GarminDB. Below are the specific technical mandates for the analysis:

### 🏃 Running (Aerobic Base & 10k Goal)
The primary objective is building a "Floor" (Aerobic Base) without compromising the "Ceiling" (VO2 Max).
*   **Key Metrics:**
    *   **Aerobic Decoupling (Pa:Hr):** Comparing the Efficiency Factor (Avg Speed / Avg HR) of the first half vs. the second half of the run. Target: **< 5%**.
    *   **Cadence:** Monitored strictly for MCL safety. Target: **170-172 spm**.
    *   **Time in Zone 2:** Percentage of run spent between **122-147 bpm**. Target: **> 80%** for Base runs.
*   **Red Flags:**
    *   Decoupling > 5% indicates "Aerobic Deficiency" or dehydration/heat stress.
    *   Cadence < 165 spm indicates over-striding and high impact on the knee.
*   **Helpful Visualizations:** Dual-axis line charts (Pace vs. HR) to see where drift begins.

### 🧗 Indoor Lead Climbing (Economy & Volume)
Focuses on technical volume and reducing the metabolic cost of moves.
*   **Key Metrics:**
    *   **Zone Distribution:** Analyzing the ratio of Z1/Z2 (Economy) vs. Z4/Z5 (Intensity).
    *   **Intensity Score:** (Avg HR / Max HR) * 100. Target: **< 70%** for volume sessions.
    *   **Recovery Rate:** How quickly HR drops during mid-route "shakes" or between routes.
*   **Red Flags:**
    *   Average HR > 160 bpm on grades < 6a suggests poor movement economy or "Flash Pump."
    *   Lack of HR drop during shakes suggests high CNS fatigue.
*   **Helpful Visualizations:** HR distribution pie charts and session "heart rate timelines."

### 🧗 Bouldering (Power & Intensity)
Focuses on maximum recruitment and power-endurance intervals (4x4s).
*   **Key Metrics:**
    *   **Peak HR:** Verification of true maximums during limit moves.
    *   **Inter-set Recovery:** Time taken for HR to drop below 120 bpm after a hard burn.
    *   **Work-to-Rest Ratio:** Monitoring the 3-minute rest rule for ATP replenishment.
*   **Red Flags:**
    *   Inability to reach high HR peaks (sign of systemic fatigue).
    *   "Finger open" failure (muscular failure despite aerobic readiness).

### ⛰️ Outdoor / Mountaineering
Focuses on approach durability and multi-pitch stamina.
*   **Key Metrics:**
    *   **Ascent Rate (m/h):** Efficiency on approaches.
    *   **Cardiac Drift on Approach:** Tracking drift over 2+ hours of steady movement.
*   **Red Flags:** Approach HR > 150 bpm (stealing energy from the climb).

### 🏋️ Workout & Strength (The 7a Chassis)
Supplemental training to build the specific recruitment and stability needed for Grade 7.
*   **Key Metrics:**
    *   **Time Under Tension (TUT):** Mandatorily tracked for Frenchies and Hanging Core. Target: **> 20s** per set for recruitment.
    *   **Rest Intervals:** Enforce the **3-minute ATP rule** for power moves; **90s** for stability moves.
    *   **Volume Adherence:** Percentage of planned sets/reps completed.
*   **Red Flags:**
    *   Significant drop in TUT across sets suggests CNS fatigue or poor recruitment.
    *   Isolating triceps/biceps over hybrid "Climber" movements (shoulders/lats/core).
*   **Helpful Visualizations:** Set-by-set duration bar charts and weekly recruitment volume (total kg lifted for finger work).

### 📊 Health & Recovery (The Macro View)
The coach monitors the "Battery" to adjust future sessions.
*   **Key Metrics:**
    *   **HRV (7-day Average):** Downward trends indicate the need for a deload.
    *   **RHR Spike:** A rise of **+5 bpm** over baseline is a hard stop for high-intensity work.
    *   **Weekly Training Load (ATL):** Ensuring the 3:1 periodization (Build vs. Deload) is enforced.
*   **Helpful Visualizations:** Multi-week training load bar charts and HRV/RHR trend lines.

---

## Roadmap

- [x] Initial environment setup with `uv`.
- [x] GarminDB integration for structured health and activity data.
- [x] Automated Garmin data extraction and database syncing.
- [ ] Advanced analysis (HRV trends, Power-to-weight estimation).
- [ ] Automated updates to `plan.md` based on performance.
