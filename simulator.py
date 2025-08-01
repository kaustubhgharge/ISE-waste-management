import requests
import random
import time
import json

BIN_COUNT = 50
URL = "http://127.0.0.1:5000/update"

def load_bins():
    with open('bins_data.json', 'r') as f:
        return json.load(f)

def send_update(bins):
    update_data = {}
    for bin_id, data in bins.items():
        # Randomly increase fill_level by 0-10%
        new_fill = min(100, data['fill_level'] + random.randint(0, 10))
        # Increase last emptied days by 1 or reset if bin full
        new_days = data['last_emptied_days'] + 1 if new_fill < 100 else 0
        update_data[bin_id] = {
            "fill_level": new_fill,
            "last_emptied_days": new_days
        }
    response = requests.post(URL, json=update_data)
    if response.status_code == 200:
        print("Update sent successfully.")
        print("Optimized Route:", response.json().get('optimized_route'))
    else:
        print("Failed to send update", response.status_code)

def main():
    bins = load_bins()
    while True:
        send_update(bins)
        time.sleep(10)  # send every 10 seconds

if __name__ == "__main__":
    main()
