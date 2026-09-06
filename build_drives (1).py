"""
Mars rover drive-level aggregation.

Input : mars_rover_data.csv  (one row per waypoint, from Saamiya)
Output: rover_drives.csv     (one row per drive)

Waypoint file structure (verified against the data, not assumed):
  - `final` is 'y' at the last waypoint of a drive; 'm' and 'i' are
    intermediate position records inside a drive. 'i' means NASA estimated
    the position rather than measuring it.
  - `dist_m` is the TOTAL driven distance for the whole drive, recorded on
    the terminating 'y' row. Intermediate rows carry 0. (One exception at
    row 674, flagged below.)
  - `straight_line` is the straight-line distance from the PREVIOUS row to
    this one, i.e. one segment.
  - A drive starts where the previous drive ended, so the previous 'y' row
    is this drive's starting point.
"""

import math
import pandas as pd

SHORT_DRIVE_M = 5.0  # straight-line displacement below this is flagged, not dropped

df = pd.read_csv("mars_rover_data.csv")

# --- assign drive ids: a drive closes on each 'y' row -----------------------
drive_id, current = [], 0
for tag in df["final"]:
    drive_id.append(current)
    if tag == "y":
        current += 1
df["drive_id"] = drive_id

# drop anything after the final 'y' (an unterminated partial drive)
df = df[df["drive_id"] < current]

rows = []
prev_end = None  # (easting, northing) of the previous drive's last waypoint

for did, drive in df.groupby("drive_id", sort=True):
    end = drive.iloc[-1]

    # The first drive has no preceding 'y' row to start from, so it starts
    # at its own first waypoint. Its displacement is 0 by construction.
    start = prev_end if prev_end is not None else (drive.iloc[0]["easting"],
                                                   drive.iloc[0]["northing"])

    path_m = drive["dist_m"].sum()                 # zeros elsewhere, so this is the 'y' value
    seg_straight_sum = drive["straight_line"].sum()  # polyline through the intermediate points
    straight_m = math.dist(start, (end["easting"], end["northing"]))

    n_segments = len(drive)
    n_i = int((drive["final"] == "i").sum())
    n_m = int((drive["final"] == "m").sum())

    rows.append({
        "drive_id": did,
        "sol_start": int(drive.iloc[0]["sol"]),
        "sol_end": int(end["sol"]),
        "n_segments": n_segments,
        "n_intermediate": n_segments - 1,
        "path_m": path_m,
        "straight_m": straight_m,
        "seg_straight_sum_m": seg_straight_sum,
        "excess_m": path_m - straight_m,
        # ratios are undefined for zero-displacement drives -> left blank
        "detour_ratio": path_m / straight_m if straight_m > 0 else None,
        "wander_ratio": seg_straight_sum / straight_m if straight_m > 0 else None,
        "tilt_mean": drive["tilt"].mean(),
        "tilt_max": drive["tilt"].max(),
        "n_i_rows": n_i,
        "n_m_rows": n_m,
        "frac_i": n_i / n_segments,
        # --- flags: nothing is deleted, filter downstream as needed ---
        "flag_zero_distance": path_m == 0,
        "flag_short_drive": straight_m < SHORT_DRIVE_M,
        "flag_single_segment": n_segments == 1,   # wander_ratio is forced to 1.0 here
        "flag_dist_anomaly": bool(((drive["final"] != "y") & (drive["dist_m"] != 0)).any()),
        # driven distance cannot be shorter than the polyline through the
        # waypoints the rover actually occupied; if it is, the record is bad
        "flag_impossible": path_m < seg_straight_sum - 0.01,
    })

    prev_end = (end["easting"], end["northing"])

out = pd.DataFrame(rows)
out.to_csv("rover_drives.csv", index=False)

# --- console summary --------------------------------------------------------
usable = out[~out.flag_zero_distance & ~out.flag_single_segment & ~out.flag_short_drive & ~out.flag_impossible]
print(f"drives written          : {len(out)}")
print(f"  single-segment        : {out.flag_single_segment.sum()}  (wander_ratio pinned at 1.0)")
print(f"  zero distance         : {out.flag_zero_distance.sum()}")
print(f"  short (<{SHORT_DRIVE_M}m)         : {out.flag_short_drive.sum()}")
print(f"  dist_m anomaly        : {out.flag_dist_anomaly.sum()}")
print(f"  physically impossible : {out.flag_impossible.sum()}")
print(f"usable for whole-vs-pieces: {len(usable)}")
print()
print(usable[["path_m", "straight_m", "detour_ratio", "wander_ratio",
              "tilt_max"]].describe().round(3).to_string())
