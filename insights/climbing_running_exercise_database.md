# **Biomechanical Strength Training Database and Garmin Connect FIT SDK Mapping for Hybrid Climbing-Running Athletes**

## **Biomechanical Demands of the Hybrid Climbing-Running Athlete**

The hybrid climbing-running athlete represents a highly complex biomechanical profile that requires the simultaneous development of divergent physiological adaptations. Running is an exercise in high-frequency, cyclical, linear impact-loading, requiring structural stiffness in the lower extremities to optimize elastic energy return. The kinetic demands of running rely heavily on the rate of force development (![][image1]) in the plantar flexors, quadriceps, and hamstrings, which can be mathematically defined as:  
![][image2]  
A high ![][image1] minimizes ground contact time, reducing the metabolic cost of transport. During the stance phase of running, the lower extremities must absorb and redirect peak ground reaction forces (![][image3]) that can reach three to four times the athlete’s body weight:  
![][image4]  
where ![][image5] represents body mass, ![][image6] is gravitational acceleration, and ![][image7] is the vertical deceleration of the center of mass upon landing. Consequently, runners benefit from a highly rigid, spring-like tendon architecture, particularly in the Achilles tendon and plantar fascia, to store and release elastic strain energy.  
Conversely, rock climbing requires multi-planar, non-cyclical, isometric, and eccentric motor control. It prioritizes maximum upper-body pulling power, isometric finger flexor recruitment, and lateral hip mobility. The physical demands of climbing are characterized by slow, controlled contractions or explosive dynamic movements. While running demands high-frequency sagittal-plane dominance, steep-wall climbing requires extreme hip abduction and external rotation to keep the center of mass close to the vertical wall.  
Additionally, the repetitive concentric pulling action of climbing often leads to overdeveloped internal rotators (e.g., latissimus dorsi, teres major, pectoralis major), causing a protective anterior shoulder migration, often referred to as "climber’s slouch." To prevent shoulder impingement and maximize reach, the athlete must cultivate antagonist thoracic extension and scapular retractor strength.  
During dynamic climbing movements, such as flagging or preventing a "barndoor" (i.e., rotating off the wall when contact points are lost), the core must resist rotational torque. This rotational torque (![][image8]) about the remaining handhold can be calculated as:  
![][image9]  
where ![][image10] is the distance from the pivot point to the center of mass, ![][image11] is the gravitational force, and ![][image12] is the angle of body tilt relative to the line of gravity. To neutralize this torque, the lateral and anterior core must generate equal and opposite isometric tension.  
Integrating these two disciplines introduces significant physical stress. Unmanaged running volume can lead to posterior chain tightness that restricts the hip mobility needed for high-stepping and flagging. At the same time, the upper-body mass required for climbing pull power can increase the energy cost of running. Strength programming must therefore target multi-planar stability, eccentric deceleration capacity, finger tendon resilience, and upper-body muscular balance. This database translates these specific physical targets into a machine-readable format compatible with the Garmin Connect ecosystem and the FIT SDK schema.

## **Garmin Connect API and FIT SDK Integration Architecture**

Executing strength training programs within the Garmin ecosystem requires strict adherence to the Flexible and Interoperable Data Transfer (FIT) SDK standards.1 The FIT file format is a compact, binary protocol designed for local device storage and seamless cloud transfer to Garmin Connect.2 Within a strength-focused FIT file, activities and workouts are represented via a hierarchical array of messages, primarily the WorkoutStepMessage and the SetMessage.4  
A recurring challenge for third-party developers syncing strength data to Garmin is the "Go" display bug.4 When a custom strength workout is pushed to a Garmin wearable (e.g., Fēnix, Forerunner, or Epix), the device often fails to display custom workout step names, reverting to a generic "Go" prompt.4 This occurs because the Garmin watch does not read arbitrary strings directly from the standard wkt\_step\_name field.4 Instead, the firmware expects an exact match against pre-compiled exercise database enums stored locally.4  
To bypass this limitation and render custom exercise names on the wrist, the developer must inject an undocumented record known as the ExerciseTitleMessage (Message ID 264\) directly into the FIT byte stream.4 This message acts as a relational lookup table.4 The device maps the exercise\_category and a unique exercise\_name integer (assigned sequentially, starting at 0\) from the WorkoutStepMessage to the corresponding string inside the ExerciseTitleMessage.4 Crucially, to force the watch to override its pre-compiled database and display the custom string, the developer must set the exercise\_category field to the value 65534 (the enum representation of UNKNOWN).4  
However, utilizing the UNKNOWN category disables Garmin Connect’s native muscle activation visualization.6 To preserve this visual feedback—which tracks cumulative workload across primary and secondary muscle groups—the FIT file must utilize Garmin's pre-defined exercise categories and exact uppercase exerciseName string constants.6  
When writing strength training activity files, developers often find that the rest time is saved as zero on Garmin Connect.6 This occurs because Garmin Connect expects a specific sequence of messages: a SetMessage of type ACTIVE containing the active reps and weights, immediately followed by a SetMessage of type REST.6 Without this explicit REST set message, the platform fails to separate work from rest, skewing volume and pacing metrics.6  
Furthermore, Garmin workouts have a strict 40-step limit on most devices.8 This introduces a programming trade-off: representing every single set as an individual step vs. compressing entire exercises into single steps.8 If every set is an individual step (including warmups), a comprehensive workout will quickly exceed the limit.8  
To solve the duplicate activity issue common with third-party sync integrations, advanced sync pipelines use "merge mode".10 Many athletes use a Garmin watch to record heart rate at 1-second intervals during strength workouts.10 When syncing a completed workout from apps like Hevy or Liftosaur, creating a new activity results in duplicate logs and ignores the watch's training effect, EPOC, and recovery metrics.8 "Merge mode" checks for temporal overlap (typically requiring at least 70% overlap within a 20-minute window) between the watch-recorded Strength Training activity and the logged workout.10 It then injects the exercise, set, rep, and weight metadata directly into the existing watch activity, preserving the detailed physiological metrics and adding the correct muscle activation map.8  
The table below outlines the core schema variables required to configure these steps within the FIT file 4:

| FIT Message Field | Required | Data Type | Operational Function in Strength Workouts |
| :---- | :---- | :---- | :---- |
| sport | Yes | Enum | Set to TRAINING to categorize the workout as non-endurance.5 |
| sub\_sport | Yes | Enum | Set to STRENGTH\_TRAINING to activate strength-specific data screens.5 |
| exercise\_category | Yes | Enum (uint16) | Standard Garmin Category (e.g., PULL\_UP, SQUAT, CORE).4 |
| exercise\_name | Yes | Enum (uint16) | Standard Subcategory identifying the specific movement pattern.4 |
| duration\_type | Yes | Enum | Set to REPS for repetition counting, or TIME for isometric holds.4 |
| duration\_value | Yes | uint32 | Total reps (count) or duration in milliseconds.4 |

## **Exercise Database Mapping to Garmin Connect API and FIT SDK Schema**

The following database maps climbing- and running-specific strength movements directly to the Garmin Connect API and FIT SDK schema.9 By utilizing these exact uppercase strings, developers and athletes can ensure that their workouts register correct muscle maps, load profiles, and kinematic metrics upon upload.6

| Garmin Category | Exact Garmin exerciseName | Biomechanical Target | Climbing-Specific Utility | Running-Specific Utility |
| :---- | :---- | :---- | :---- | :---- |
| PULL\_UP | PULL\_UP | Vertical pulling power, scapular depression, humeral adduction.9 | Primary driver for vertical ascension; pulling past holds; lock-off strength. | Postural support; counteracts chest compression during deep fatigue. |
| ROW | FACE\_PULL | Humeral external rotation, scapular retraction, posterior deltoid activation.13 | Antagonist training; stabilizes shoulder complex on sidepulls and compression features. | Corrects forward-shoulder roll, optimizing lung expansion and breathing. |
| SHOULDER\_STABILITY | Y\_RAISE | Lower trapezius recruitment, scapular upward rotation.9 | Enhances overhead reach stability; supports shoulder safety on high handholds. | Stabilizes the upper spine, reducing lateral torso sway on uneven terrain. |
| DEADLIFT | BARBELL\_DEADLIFT | Hip-dominant pulling, posterior chain overload (gluteus, hamstrings).8 | Creates maximum body tension; drives power for aggressive heel-hooks. | Builds terminal hip extension power; protects hamstrings during speed work. |
| SQUAT | BARBELL\_SQUAT | Knee-dominant pushing, quadriceps and gluteal concentric power.8 | Enhances raw push power for dynamic jump-starts and high-step placements. | Primary builder of stride power; strengthens knee extensors for downhill running. |
| LUNGE | BARBELL\_LUNGE | Unilateral hip and knee extension, eccentric quadriceps control.14 | Mimics deep flagging movements, building stability on steep walls. | Builds eccentric quadriceps strength, reducing muscle damage on descents. |
| PLANK | PLANK | Isometric anterior core bracing, anti-extension abdominal control.9 | Develops base torso rigidity; transfers lower-body power to the hands on the wall. | Minimizes vertical pelvic oscillation, preserving running economy. |
| CORE | HANGING\_KNEE\_RAISE | Abdominal compression, hip flexor endurance. | Enables high-stepping and undercling positioning; assists in putting feet back on holds. | Supports hip flexion drive during rapid hill ascents and high-cadence strides. |
| SLED | SLED\_PUSH | Multi-joint concentric drive, ankle-hip integration, horizontal force application.9 | Establishes linear lower-body push capacity without eccentric soreness. | Highly specific builder of acceleration mechanics and stride power. |
| CORE | HOLLOW\_ROCK | Anti-extension core control, deep abdominal compression.9 | Establishes total body tension, keeping feet on steep overhanging walls. | Restricts excessive pelvis tilt, optimizing stride transfer efficiency. |
| CORE | MODIFIED\_FRONT\_LEVER | Advanced anti-extension abdominal control, latissimus static tension.9 | Directly supports core-to-toe tension on roof climbs and steep bouldering. | Minimizes trunk collapse and posture breakdown during late-stage fatigue. |
| CORE | HALF\_TURKISH\_GET\_UP | Multi-planar core bracing, dynamic shoulder stability.9 | Stabilizes complex shoulder angles during dynamic, multi-directional lunges. | Integrates cross-lateral torso coordination, stabilizing the running stride. |
| CARRY | DEAD\_HANG | Isometric finger flexor overload, grip endurance, forearm tension.9 | Fundamental climbing exercise; builds finger pull-force and skin tolerance. | Decompresses the spine, counteracting impact loading from high running mileage. |
| CARRY | FARMERS\_WALK | Unilateral carriage stability, deep grip activation, traps.9 | Enhances overall hand/forearm work capacity and core endurance. | Promotes dynamic lateral hip stability, reducing pelvic drop on trails. |

## **Biomechanical Progressions and Regressions Hierarchy**

To allow for structured athletic adaptation, strength programming must arrange movements along logical progression-regression lines. These hierarchies are designed to adjust load, reduce or increase stability requirements, alter ranges of motion, and target specific climbing and running kinematics.

### **1\. Vertical Pulling Progression Series**

This pathway moves from high-stability latissimus isolating work, through bodyweight vertical pulling, to maximum pulling overload.13

| Progression Level | Garmin Category | Garmin exerciseName | Biomechanical Pivot | Climbing Utility | Running Utility |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Regression** | PULL\_UP | CLOSE\_GRIP\_LAT\_PULLDOWN | External load adjustment; isolates the pull action without requiring the athlete to lift their entire body weight.13 | Allows precise latissimus and forearm isolation, preventing compensatory movement patterns in fatiguing muscles.13 | Postural control; isolates upper-body pulling mechanics without lower-body fatigue. |
| **Baseline** | PULL\_UP | PULL\_UP | Closed kinetic chain integration; requires full-body coordination and active scapular depression.9 | Develops standard lock-off capability, pull power, and upper-body coordinate control. | Counteracts chest compression and slouching under aerobic fatigue. |
| **Progression** | PULL\_UP | PULL\_UP | Supra-maximal overload of vertical pull pathways; increases motor unit recruitment.13 | Translates directly to dynamic, explosive bouldering and high-demand climbing moves. | Enhances structural integrity and absolute power of the latissimus-torso connection. |

### **2\. Horizontal Pulling Progression Series**

This pathway targets horizontal scapular retraction, correcting running posture and climbing side-pull mechanics.8

| Progression Level | Garmin Category | Garmin exerciseName | Biomechanical Pivot | Climbing Utility | Running Utility |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Regression** | ROW | SEATED\_CABLE\_ROW | Seated, braced, bilateral pull; isolates thoracic retractors with minimal lumbar loading.8 | Safely strengthens the middle trapezius and rhomboids, counteracting chest tightness. | Corrects forward-shoulder roll, optimizing thoracic capacity and respiratory efficiency. |
| **Baseline** | ROW | DUMBBELL\_ROW | Unilateral, semi-supported, free-weight row; requires rotational core control to prevent trunk rotation.9 | Mimics single-arm pull positions on the wall; corrects arm-drive asymmetry in runners. | Balances the unilateral arm-swing drive required during trail ascents. |
| **Progression** | ROW | RENEGADE\_ROW | Unilateral row executed from a full push-up plank; highly unstable base of support. | Combines horizontal pulling power with extreme anti-rotational core stability, preventing wall rotation. | Integrates core and shoulder girdles under high unilateral tension. |

### **3\. Vertical Pressing Progression Series**

This series targets antagonist upper-body pushing strength, ensuring shoulder health and overhead stability.9

| Progression Level | Garmin Category | Garmin exerciseName | Biomechanical Pivot | Climbing Utility | Running Utility |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Regression** | SHOULDER\_PRESS | DUMBBELL\_SHOULDER\_PRESS | Unconstrained glenohumeral path; allows independent arm movement, reducing joint strain. | Safely addresses pressing imbalances without forcing the shoulder joints into restrictive paths. | Promotes shoulder relaxation and posture control during high-impact running. |
| **Baseline** | SHOULDER\_PRESS | BARBELL\_SHOULDER\_PRESS | Bilateral barbell press; demands significant anterior core activation to prevent lumbar hyper-extension. | Establishes a rigid trunk and stable overhead lockout, protecting shoulders during long climbs. | Enhances spinal alignment and load-bearing capacity under high dynamic stress. |
| **Progression** | CORE | HALF\_TURKISH\_GET\_UP | Unilateral, multi-planar overhead stability under dynamic, shifting torso angles.9 | Stabilizes complex shoulder angles during dynamic, multi-directional lunges. | Integrates cross-lateral torso coordination, stabilizing the running stride. |

### **4\. Knee-Dominant Pushing Progression Series**

This series develops the concentric power needed for ascending steep terrain and the eccentric control required for downhill landing stability.8

| Progression Level | Garmin Category | Garmin exerciseName | Biomechanical Pivot | Climbing Utility | Running Utility |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Regression** | SQUAT | GOBLET\_SQUAT | Anterior weight distribution; encourages a vertical torso, deep knee flexion, and active core bracing. | Safely develops deep quadriceps mobility, improving pelvic alignment and knee tracking. | Promotes safe, loaded knee-flexion patterns to protect the patella. |
| **Baseline** | SQUAT | BARBELL\_SQUAT | Posterior axial loading; maximizes mechanical tension across the quadriceps, glutes, and spine.8 | Strengthens major lower-body muscle groups, improving stride power and steep trail ascents. | Primary builder of quadriceps and gluteal drive for flat and uphill running. |
| **Progression** | SQUAT | SINGLE\_LEG\_SQUAT | Unilateral base of support; shifts balance demands to the lateral hip and foot stabilizers.8 | Directly replicates the unilateral landing impact of running and the single-leg lock-offs used in climbing. | Crucial for single-leg landing stability and preventing knee valgus collapse on downhills. |

### **5\. Hip-Dominant Pulling Progression Series**

This series builds a strong posterior chain, generating lower-body power and protecting the hamstrings during rapid leg turnover.8

| Progression Level | Garmin Category | Garmin exerciseName | Biomechanical Pivot | Climbing Utility | Running Utility |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Regression** | DEADLIFT | ROMANIAN\_DEADLIFT | Focuses on eccentric hamstring loading; starts from an upright stance, reducing initial spinal shear.9 | Builds hamstring elasticity, reducing muscle strains during downhill running. | Promotes posterior chain flexibility and active hamstring control. |
| **Baseline** | DEADLIFT | BARBELL\_DEADLIFT | Concentric pull from a dead stop; maximizes posterior chain recruitment and spinal loading.8 | Strengthens hamstrings and glutes for heel-hooking; improves overall lower-back durability. | Generates powerful terminal hip extension to drive running stride velocity. |
| **Progression** | DEADLIFT | SINGLE\_LEG\_DEADLIFT | Unilateral hip hinge; demands significant lateral ankle, knee, and hip stabilization.9 | Builds ankle stability and lateral hip control, helping to prevent rolls and sprains on uneven trails. | Corrects hamstring strength imbalances; builds lateral stability for trail running. |

### **6\. Core Stability Progression Series**

This pathway moves from basic horizontal bracing to advanced anti-extension work, helping keep the feet pinned to steep walls.9

| Progression Level | Garmin Category | Garmin exerciseName | Biomechanical Pivot | Climbing Utility | Running Utility |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Regression** | PLANK | PLANK | Static, four-point bridge posture; basic anti-extension loading.9 | Teaches basic abdominal bracing and maintains core alignment. | Stabilizes the lumbar spine, minimizing energy loss during distance running. |
| **Baseline** | CORE | HOLLOW\_ROCK | Dynamic, two-point posterior pelvic tilt rocker; highly active abdominal compression.9 | Replicates the full-body tension required to keep the toes on steep rock walls. | Optimizes pelvic alignment, preventing hyper-lordosis during long runs. |
| **Progression** | CORE | MODIFIED\_FRONT\_LEVER | Advanced suspension; requires the latissimus dorsi and core to support the pelvis horizontally.9 | Essential for steep roof climbing, allowing the athlete to place their feet back on holds. | Develops exceptional core-to-limb force transfer, stabilizing the torso. |

## **Systemic Programming and File Compilation Protocols**

To program these workouts effectively, the athlete’s strength sessions must be structured into a machine-readable format using the Garmin FIT SDK.1 Developers can compile these workouts into .fit binary files and sideload them via the NewFiles folder on a compatible device.12

### **Programmatic Setup Structure**

A strength training session must follow a specific sequence of messages to ensure proper parsing by Garmin Connect and target wearable devices 12:

\+-------------------------------------------------------------+  
| 1\. File ID Message                                          |  
|    \[manufacturer: 1 (Garmin), product: 2480 (Edge), etc.\]   | \[15\]  
\+-------------------------------------------------------------+  
                              |  
                              v  
\+-------------------------------------------------------------+  
| 2\. Workout Message                                          |  
|    \[sport: training, sub\_sport: strength\_training\]          |   
\+-------------------------------------------------------------+  
                              |  
                              v  
\+-------------------------------------------------------------+  
| 3\. Workout Step Messages (1...N)                            |  
|    \[category, exercise\_name, duration\_type, reps/time\]      |   
\+-------------------------------------------------------------+  
                              |  
                              v  
\+-------------------------------------------------------------+  
| 4\. Exercise Title Messages (Optional, for custom names)     |  
|       |   
\+-------------------------------------------------------------+

### **Workout Configuration and Sideloading**

During FIT file creation, developers must configure each workout step with the correct duration and target fields 4:

1. **Isometric Finger Holds:** Use WorkoutStepDuration.TIME to track holds in milliseconds.4 This triggers a countdown timer on the device, which is ideal for isometric finger training (e.g., a 10-second hang on a 20mm edge).4  
2. **Concentric/Eccentric Reps:** Use WorkoutStepDuration.REPS to track repetitions.4 This activates the watch's internal accelerometer to auto-count reps during movements like squats and shoulder presses.4  
3. **Active Rest Intervals:** To track rest periods accurately, write a SetMessage or WorkoutStepMessage with intensity set to REST immediately after each active set.5 This ensures the watch displays a rest timer instead of registering a blank interval.6  
4. **Sideloading Path:** Once the FIT file is generated, connect the Garmin device via USB and transfer the compiled binary to the /Garmin/NewFiles directory.12 Upon disconnecting, the watch parses the file and saves it to the custom strength training directory.12

This system ensures that the hybrid athlete's training is fully integrated, tracking both climbing and running adaptations within a unified fitness ecosystem.7

#### **Citovaná díla**

1. Official Garmin FIT SDK Tools · GitHub, použito května 25, 2026, [https://github.com/garmin/fit-sdk-tools](https://github.com/garmin/fit-sdk-tools)  
2. Flexible and Interoperable Data Transfer (FIT) SDK \- Garmin Developers, použito května 25, 2026, [https://developer.garmin.com/fit/](https://developer.garmin.com/fit/)  
3. fit\_sdk \- Dart API docs \- Pub.dev, použito května 25, 2026, [https://pub.dev/documentation/fit\_sdk/latest/](https://pub.dev/documentation/fit_sdk/latest/)  
4. Custom Workout FIT File \- Step Names Not Showing \- Discussion \- Garmin Forums, použito května 25, 2026, [https://forums.garmin.com/developer/fit-sdk/f/discussion/357803/custom-workout-fit-file---step-names-not-showing](https://forums.garmin.com/developer/fit-sdk/f/discussion/357803/custom-workout-fit-file---step-names-not-showing)  
5. Workout File \- File Types | FIT SDK | Garmin Developers, použito května 25, 2026, [https://developer.garmin.com/fit/file-types/workout/](https://developer.garmin.com/fit/file-types/workout/)  
6. Examples for encoding strength training activity files \- Discussion \- FIT SDK \- Garmin Forums, použito května 25, 2026, [https://forums.garmin.com/developer/fit-sdk/f/discussion/270009/examples-for-encoding-strength-training-activity-files](https://forums.garmin.com/developer/fit-sdk/f/discussion/270009/examples-for-encoding-strength-training-activity-files)  
7. Getting Started With Strength Training on a Garmin Watch, použito května 25, 2026, [https://support.garmin.com/en-US/?faq=LcYGZd4EOZ9PkTY5YRvin5](https://support.garmin.com/en-US/?faq=LcYGZd4EOZ9PkTY5YRvin5)  
8. liftosaur2garmin can sync your Liftosaur workouts to Garmin Connect \- Reddit, použito května 25, 2026, [https://www.reddit.com/r/liftosaur/comments/1sgqzgd/liftosaur2garmin\_can\_sync\_your\_liftosaur\_workouts/](https://www.reddit.com/r/liftosaur/comments/1sgqzgd/liftosaur2garmin_can_sync_your_liftosaur_workouts/)  
9. Uploading to Strava \- Strava Developers, použito května 25, 2026, [https://developers.strava.com/docs/uploads/](https://developers.strava.com/docs/uploads/)  
10. drkostas/hevy2garmin: Sync Hevy gym workouts to Garmin Connect with exercise names, sets, reps, weights, HR overlay, and calorie estimation \- GitHub, použito května 25, 2026, [https://github.com/drkostas/hevy2garmin](https://github.com/drkostas/hevy2garmin)  
11. I built a tool that syncs Hevy workouts to Garmin connect with exercise names and heart rate, použito května 25, 2026, [https://www.reddit.com/r/Hevy/comments/1sfu9id/i\_built\_a\_tool\_that\_syncs\_hevy\_workouts\_to\_garmin/](https://www.reddit.com/r/Hevy/comments/1sfu9id/i_built_a_tool_that_syncs_hevy_workouts_to_garmin/)  
12. Encoding FIT Workout Files \- Cookbook | FIT SDK | Garmin Developers, použito května 25, 2026, [https://developer.garmin.com/fit/cookbook/encoding-workout-files/](https://developer.garmin.com/fit/cookbook/encoding-workout-files/)  
13. \[FEATURE\] Track Strength Workouts · Issue \#189 · arpanghosh8453, použito května 25, 2026, [https://github.com/arpanghosh8453/garmin-grafana/issues/189](https://github.com/arpanghosh8453/garmin-grafana/issues/189)  
14. Strength workout \- list of exercises available part 2 \- Garmin Connect Web, použito května 25, 2026, [https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/403586/strength-workout---list-of-exercises-available-part-2](https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/403586/strength-workout---list-of-exercises-available-part-2)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAZCAYAAABKM8wfAAAB1klEQVR4Xu2VMShHQRzHf8Ig/mUTC4UkISmbRQyKRWGTURZFkUlYTMRA2QyyGE0mZVXKwmBAKIQFhcL329393f/evffoz0DvU5/h/7/73X3fvXd3IgkJATrhaojLsBcWpnt/UgEXJVjjugQrv9A/aq4M/lzgIlgD9+GFthGWwmo4C69EPZhNPiyBC/AdDoiqMXV0BD7C7pD+dg3n3IDXsE1iYOgdeKrlAIY8uAlvYJ31v2FCVACG8jEIR63fdn+3JgeOwzvY5LRlEBWYrEl4KF/glDZX1MpNW21RgQnfwqGo1eZi0QBRgb+7wlylOS3HKYY9uo3EBWb9OryFtdoAJrD7DZfDKXgu4d+VCWC+xy64p3XfFIkLTOw36u1jAj9r+YTcuVuiNlxHumcQE2BbVM0uPNH+emD3k+DrmYT3Er4J3E+iQD6PqmwCv8F2bYB/E5hwUE7AiXy4gQk3GeWGc4kLbLLwpOCJQQNEBeaFwQn41D58gaOIC9wKn+CY22ATFbhZ1G3FzZSCLVpzVP1k4AZ4DFdE3YxehuClqEGM/D2v21nIAV7hMJzR9sMD+KJrHuCZqPF81Etmf95mlDWU5/wR7BN14WQFN1+ZqBWp0iYkJCQkZM8HNk66QBaUdTQAAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAA8CAYAAADbhOb7AAAExUlEQVR4Xu3dW6hmYxgH8EcOkcOQGjmUGYlkijJImRpKjQsuRA6jXLjgwtWkFEWSMlw4U2ImFzJJ3BBJ+aSkKKW4UBI5hFIu5gKZ8TzzrjXf+tb+tmbM7G2X36/+7bXetda3b5/eYwQAAAAAAAAAAAAAAAAAAAAAAAAAAAAA8J84ctwAAMDKcUFmZ2bTqP2YzNmZTzPnZU7OXJTZ1l0DALBMHs/cmXk7c9ToWRVtk5gt0A6PVsABALAMDsls6K5/j1a0DY0Ltge7v+d3f6vAuynzXObErm1j5trMuswtXVs5NPNM5olo/7dUD97D0Xr5+jYAAAaqqKoes/Jy5q/Bs9IXbNWjdlpm+8zTiPcyV2YOy3yYWR9taLWGUZ/OvJ45KbMq81b394ZoRV0VaPV9/e4X0Qo/AAAGzs08P7ivwu2VmPa4lXEP26PTR3FO5q7B/VWZXd11tZ/QXfe/8W5339sSraCr3rl3Mt+EuXEAAHtV79bWzBWj9irWqmjre93GBds13d9Sw5jjgm13d13t9W2pHravMi919716p34DAIA5zsy8EAsXGdR9zWW7pLsfF2xDazN3D+43R1ttWoYFW20Z8mbmg+6+HJ25OnPpoO3YaPPcAABI30XrDVssVbTdnvmhu/8589meL2fdk/k42rDmY9EKsR2ZP6J9W79Rqkfv+u69R2Lag1fz2t7PvBbThQwAAEuiJt5XMdKnVkNeN3h+fOah0Tt9LuzeGbdXzoqVv3qyiq8a9twXq2Pa89arez1rAMCymMTsxPlaOflLtMn9veqtGs77Kk92f+u7+n5Y0Jye+TLabwEAcIAmsXClYxVoNRl/eN8XbDV8WL1TVbDVPK95BVu5I6ZzygAAOACTzPfR9iyrnrH7MpcPX4hWsD0QrTj7JGZXSS5WsNU7kzntdV/fLBYAAEYm0Sbr1/YVb2R+mnnaVMFWhVrNT/stDqxgq33Q6kSBxbLS574BACy7ScwOidZQ6Hi+2nBI9LLMmumjRQu22v6ihkUPlur9W8kBAFgyk5gt2Grl6It7nza7Y2ER15tXsPWnD9TxTWM3Zr79hxwxfRUAgDKJ2YKthjJrs9jaELY/IWB/C7b7o+2BBgDAEjklZleJrmS/xvyjompIdrw/XJ9a3Vrq5AQAAJZQ9epV799T4wfRhnU3ResBrHfqAPiNmW3RDnjvzwrd181zAQDYT3V+aJ0rWsO2u2J2dWkVclWg9cZDuvPm1gEAcJBV79m9mVWZjzLrBs9qyLOff1fGBduazMXRthGp47eq+Kvr9ZmbM1uiFYB1xFZdH7fnq6berWHVWwdtAADMUYex971qVbSNj9MaGhdsvdtiuthiEu1A+FI9cFtj+vs/Zs6INvQ66dpOzWzurgEAGKlernFxVkVZncYwz2IFWy2sGBZs/XYm1TbsodsZbWFDzXn7OloP2/aY/5sAAP97tcfbs+PGdHu0wmyef1OwDVfJ9gXbJPPqoL3OVQUAYGRD5vNYuFXHjsyfmbXTV/c6WAVbbRVSQ6+9mvcGAMAKtDoWHsUFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAsPL8DYOj0fimP+5hAAAAAElFTkSuQmCC>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACsAAAAbCAYAAADlJ3ZtAAAB9klEQVR4Xu2WTygFURTGj6T8zd+UImUjopQsLGRjY4HCzo5EyQJJsbERVjaipERZkPwprISyVNgoxUpY2FuwwPe553rz5iE03ng1X/3qvjkz03nnfmfOFQkUKEIdytw34H2+KmaSjQPZSj14BFMgz0ENOFUWzWP+qw08gzp3AGpWhtyBaIvVJQvgBuTr9XiQpusGhX/IV2Uqx2AHJOr1StCr63KlRH/7JiZFHsCkGJ8yqU352BK+qkuhXzfEdP0RuANFjvt8l/Wq26+s7oyELOGlMsAEGJQfvj8HnCtOvxbI31qAtqPNUt2BrxRTydrGIsOu2F/qV8naxvpsGFCcbuvKARgT4+d+kACSwIjC2DhI1xi9yetLoEKhbLJs4EOwD4o1FiFOo2vwBF6Ue3AGSh33WdnP27aYQcFEVsW8p1tMsxCKg4NFYNUGxDRrFZhV2NQ2WRaoU8wA8kw2WefWcfQSnhf4fSatCr/TTIp/hgmywrsKn+e7rsScN1rEY7mTZSLTYio4KqHEKVad1awGa2JsYp8ljRrjugxsgcK3Jz2STfYStIvZelaU3iTLSo+YraeVmABt0ySmefeUPjAPbnW9Ai7EnPo8kbOyWSAlPPyuZAn3H9c8d3AnoiJuIw805ATUhof/l2IqWW5lrsLG4WwPFCiaegU2ZHA13bl7AgAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAxCAYAAABnGvUlAAADn0lEQVR4Xu3dS6itYxgH8EcoQojILZdckqQopQwMFEkUGcjAKUrKwGVwXIojyaWQy0hKlBSJkkjKLqUwQZkzYKAwoVAuz3Pe9fk+r22ftc9ae5+96/erf/u7rbW+4b/3ck4EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwlZySeTrz/Cqpe9vRtZkD+oub5PbMfv1FAIBFHJQ5PvN95sLMcZmTMw9kLpg8t12clHmnv7iJXs5c1V8EAFhUFbN7J+cHZg7NHDm5tl18mrm4v7gOD0UrrXvr6Mwn/UUAgEXdkLl0dlzTeSdGG3nbV9OKvcszOzIHZ67MnBftPatY3TL7O/gyc+zkvNSz9ZkqplVE1zJvYds/c2Pm9GgFd1C/9crkHABgYVUwXsycH62oVAmpsrZeR2XO6i92quQcE+13VktftAb3ZJ7KvBqtdH2XeTTzWObWzBfjo7ES/y1l9bkHM09m/uju9eYpbIdnXos2dVxr/ao0Tk1HKwEAFlYF6JfJ+R2T4/WokvRWf3EJqlBWGfxscu2nGKc9d3b3Xpocl4tiLFQ1kvj1eGu3I6KVv2GjRY3Q1QjZcH7m+Og/fov2XaW+u6ZBp+qd+tIIALDXqnD8OTm/eva3RtmqzFSGEbf6e0mMmxFqgX8VmipVQ2Gr52uEqkrWstTv/Tg5/yrGkvRe5pnJvb6w3RltOrTUSOKeNiTMM8L2Q+bsGEcn+6ljhQ0AWKoqP/9XYoby83C0UvRctDJT06e1zu2czGWZt2MsbLuirTVbphdifMcqatMpyHr/mmY9dXb+Ueaw8fbu9W/1mSpXNTK2pw0J8xS24TeujzY6eVf8e0dtvS8AwMJqHVYVrb8yv0dbD9YbCtuOzAcxlpnKCZnXM9fFWNjqmSozVeaWaSVz2+y4itG0HH2eebw7P21yXhsC6r3ejTYdWu+9lnkK25uZRzJ3R/vuWh83bDw4JPP+7BgAYMN9E21RfxW3KnhPRCs0N0f7t8ZWMvdlPs7cn/k2c0Xm18wbsW9cE+MuzXMzH86Oa0PDTbPjtdTGiemuz/WqYrmrvwgAsFGqqPXlpdaxDWva+ntbQb3Ts7PjWr/2c7T1ZjUqtuyp2tXU79QULQDAhqupwzNie/5vB6WmJjfbViywAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABF/A1WRb9gaJx/OAAAAAElFTkSuQmCC>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAAbCAYAAABxwd+fAAABEUlEQVR4Xu3Sr0vDQRzG8Y+oKPhrgmVYRAQRkyiDgWGCwQX9B7SYDCKI0WoWQexi1mozrJsFYQhLigj6L/h+9n1Oz+UFw/eBF+Pus93n7nYRZcr0L2s4RNUG0cCpPzWexB5ObCF6soxzHOHZbrGFFbRxgSssYdtesBhZtMB6FN2/rObaOFp4wJTnVu0Tm57rZgIjuMO1Dbg2jzfseqzs2KvrfzKLDg4sRR31Ax1JUQMdUe4x6vmf9G0h3dF7/J4/Rff2iGmPU0NRwzlsuNaN/s4nzJiibup6mb5Emvgw7XIf9aweN1FsV1tPF6331IniYlP0VNRQznCMoaweYxjOJ6JYUEfSY8yjnUqlZ75Mmf+Tb/+KMSZN/aM2AAAAAElFTkSuQmCC>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAcCAYAAAC3f0UFAAAA0ElEQVR4Xu3QMQsBYRzH8UcMFEkpmQwsJorVCzAoycArsBjkJSiDF6AMssliMdgMSlmsBovBYvQa/H7u5zx3gzJZ7luf4Z7733PPnTFB/6oAPShDQsL2QAj6soA8zOAhlc/oj8M1uAiPwRpwlYzWTARWsBZesyFsJaq111N8mjeJ8VhLGItbFm7GeS2xNJyhLm5x2ENLuGsX7lAUT1U4CM+4gROkxNNPw/74UXP/IhvAyLpOwhE61prbDiaQk6lxdo3ZQ+/465rQlpJx/kjQ1550iCplAq+IbgAAAABJRU5ErkJggg==>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAdCAYAAAB8I5agAAAArklEQVR4Xu3QvwpBYRzG8Vco/4pBJguzcg+iDDLZ2F2CktElKINSdmWyKcpkMrkDi7vw/TnPeRULi0HnW5/lPb869TgX9evS0kYHWWTkrY+P89jKAA1csRJfAnPMJIYkNhiLr4YbmmIVcX55ezR0wS/LYtVxQVV8Xx2PcEBOrD6OqEhL766LvXse2zI7F6xgq5heeGwf15jIAlOcsJRSeGzFXbCAsdmsAlIS9RfdAX2lHWwdaAurAAAAAElFTkSuQmCC>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAeCAYAAAD6t+QOAAAAdklEQVR4XmNgGAWDFjADsTEUh2DBujCFPEC8Coj/Y8F/obgDiBlBinOBOBTKAWE/IA4ASWADJCnmZoBaAQUtQGyKxMcKBKF4HRDLoMlhAFhobAFiXjQ5DJAOxUsZUJ2FFZCkeCEUl6NLYAOgUAFhVnSJUTBcAAAcmhTH8gHwkgAAAABJRU5ErkJggg==>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAxCAYAAABnGvUlAAADRUlEQVR4Xu3cT6ilYxwH8EcoGpI/NQ3K350kNFbKRkKRsFCUlb9ZEWp2koUizSRFhI1oZqGEksUtJWVtqSgSms3ERvnz+3rf9973vHPvce65547FfD717b7vc55zTjOrb8/zPqc1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAxVxaOVh5Y5KM5bVlXdlnETdU3q+cNRq7qfJJ5a7+PnNerJy+PgMA4CRxRuXCyi+tK0X7KpdUfq1cP5q3Xd/2WcSH7fjv+qxyTuWrymWVUyrPVZ4aTwIAOFmkLB3or/e0bhXrlcq56zN2Twrj/aP7FLNX28Zq20+VO/rrzP2ovwYAWLkUkWzv3TvK1TMzlpOC9XDrStaNrVsh264Uppv76+crF1dur5y2PuO/ZfXrtbZRrvLvu69yZuW2/v78ygNtdqv08so1o/uspv0wuv+zde8fDMUSAGClUqZeqvw9yh+Vl8eTeilcW2X8jNfgmco9la8rj7ZuezErUYtKkXy7cl3rvuODtr33x7WV8yqnVt7sx76ofN+6wvZQ67ZYU+qy3fpj5ap+3rRkpjz+VbmickvlWJstdHe3zf8fAAB25OzWlZlsPb7Xtl+I5skKW0rP8AxYCtjU0crn08Fe3vf76H5YadvMx60rUFMpbCmg+Y4UtMhKWwpbpGCt9deR8WElLn/HBWytcqS/vqhyaOOlf2X+MquIAAALeaLywnRwBZ5t8583e6vy2HSw90jrVrQG2bbcSj4jn7WZdyo/t+6EaVYUd1LYhm3PO9vxhxEUNgBgV+XU5P7p4A7tbYufxpy6oPJN61bOdiKFcVjZW2vdytiihS2FLM/MDXLgIJ+Xbd4vR+ODJ9tqVygBAGZ817oys0opPMsUtvxkRn7KY3ieLr9xtqynK69XHqw83rry9lvrPju/p5bilcMD+ZtDBxnP65HSmC3dQZ5Xy7xP22yRGwzPyAEAcALlN9fmbcUObq28Ox0EAGD3ZYUuz9LNkxXBw23jdCkAACdYTtHmNO1W5r0GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA8P/7B6Rga0KgeSZlAAAAAElFTkSuQmCC>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAeCAYAAAAVdY8wAAAAgklEQVR4XmNgGAV0B4xA7ArEflDMAcQOQBwMxdwwhZZAnAfEG6F4GxCHAvEqKE6HKcwEYj0g3gPFDUCsD8QvoRhkG2kKeYFYDohvQLENVBzkVhBGASDJq1AsjSaHAkAO3grFGKYggzlA3ArFeAFRCnmAeD8DIsDxApDPmaF4FAwpAADTahscLVZWngAAAABJRU5ErkJggg==>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAcCAYAAABoMT8aAAAA30lEQVR4XmNgGAXoIBmKZxGBQepQACMQC0OxJxD/BOJ+IJZEwrZQfB6IF0K0YQfRQPwPiF3QJaAgCIjL0QVBAOQKEJ4PxE+AWAYqzgzEvDBFQODLALEEAwhC8Wkg3grEHFBxYyDOhSkCAl0g1kTiwwFIIQh/BeJOBoi/QQo3MOD2Dgqg2IB0KAYF4HoGSHQdBuJnQKyEpA4rgAUeegCCXDGNAREeOIEIEF+FYuQAlGUg0vkwv4NwFZocUQDmd3wJCCsApapHQPwLiP9D8SsgvgDEWkjqcAKKDRgFo2DgAQCAUzRkN3ZDPAAAAABJRU5ErkJggg==>

[image12]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAfCAYAAADeKVyVAAAA3UlEQVR4Xu3RPwtBURgG8FcMhAyUlMmgzMpkErJYZFAsJh/BZPQFxAdgMsjkT8kgFh/AajDIZrN73nufezGoa6M89at73vN0bp0j8pvJwQqWlHzdFsnQFEJQoT64rFJAzFNUibMybbhvxHGxBgeKcGYVTxDTgQcm0CMrbdpBUAcJuMCAUlCELc3B+1ExDzd5/KoKTThTV0uaOhwhSpo0XEkPMqKnrMFPmhbsSS/fiOOiDofWAvHBAhpkJwsjMe9TFWAm5mvYL6LRxRg6pN/x58Jz3BAm/X4bx8V/vi138pwzEdLR4ogAAAAASUVORK5CYII=>