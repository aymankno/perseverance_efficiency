import json
import math
import csv
with open("mars_rover_waypoints.json", "r") as f: data = json.load(f)
features=data['features']
with open("mars_rover_data.csv","w",newline='') as csvfile:
    writer = csv.writer(csvfile)

    #column headings 
    writer.writerow([
        "sol",
        "easting",
        "northing",
        "dist_m",
        "tilt",
        "final",
        "straight_line"
    ])
    previous_easting=None
    previous_northing=None
    for point in features:
        props=point['properties']
        sol=props['sol']
        easting=props['easting']
        northing=props['northing']
        dist_m=props['dist_m']
        tilt=props['tilt']
        final=props['final']

        if previous_easting is None:
            straight_line=0
        else:
            dx=easting-previous_easting
            dy=northing-previous_northing
            straight_line=math.sqrt(dx*dx+dy*dy)
        
        writer.writerow([
            sol,
            easting,
            northing,
            dist_m,
            tilt,
            final,
            straight_line
        ])
        previous_easting=easting
        previous_northing=northing
        
print("CSV file created successfully!")