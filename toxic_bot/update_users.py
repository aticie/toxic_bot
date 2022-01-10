import os
import time
import json
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

users_file = os.path.join("Users", "user_properties.json")

while True:

    with open(users_file, "r") as f:
        users = json.load(f)

    for k,v in users.items():

        if not v["tournament_ping_preference"]:
            print(f"Skipping {v['osu_username']} because they don\'t want to be pinged.")
            continue

        update_date = datetime.strptime(v["last_updated"], "%m/%d/%Y, %H:%M:%S")
        time_diff = datetime.now() - update_date

        if not time_diff > timedelta(days=1):
            print(f"Skipping {v['osu_username']} because already updated less than a day ago.")
            continue

        osu_username = v["osu_username"]
        r = requests.get(f"https://osu.ppy.sh/users/{osu_username}")

        soup = BeautifulSoup(r.text, 'html.parser')
        try:
            json_user = soup.find(id="json-user").string
            json_achievements = soup.find(id="json-achievements").string
        except:
            continue
        
        user_dict = json.loads(json_user)

        users[k]["osu_rank"] = user_dict["statistics"]["rank"]["global"]
        users[k]["osu_badges"] = len(user_dict["badges"])
        users[k]["last_updated"] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        print(f"Successfully updated {v['osu_username']}!")

        with open(os.path.join("Users", "user_properties.json"), "w") as f:
            json.dump(users, f, indent=2)

        time.sleep(600)
        break