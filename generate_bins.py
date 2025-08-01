import json
import random

locations = [
    "Market Square", "Central Park", "Train Station", "City Library", "Town Hall",
    "Museum", "University Campus", "Sports Arena", "Shopping Center", "Hospital",
    "Post Office", "Fire Station", "Police Station", "Community Center", "Cinema",
    "Bus Station", "Parking Lot", "City Square", "Railway Crossing", "Main Street"
]

# Rough lat/lon around Lemgo for variety
base_lat, base_lon = 52.0280, 8.8980

bins = []
for i in range(20):
    fill_level = random.choices(
        population=[random.randint(0, 60), random.randint(80, 94), random.randint(95, 100)],
        weights=[60, 25, 15],  # More chance for low/mid fill, some for nearly full and full
        k=1
    )[0]
    last_emptied = random.randint(0, 10)  # 0 to 10 days for more inactive possibility

    bin_data = {
        "id": i + 1,
        "location": locations[i],
        "type": random.choice(["General", "Recycling", "Organic"]),
        "lat": base_lat + random.uniform(-0.004, 0.004),
        "lon": base_lon + random.uniform(-0.004, 0.004),
        "fill": fill_level,
        "last_emptied_days_ago": last_emptied
    }
    bins.append(bin_data)

with open("bins.json", "w") as f:
    json.dump(bins, f, indent=2)

print("bins.json generated with random values.")
