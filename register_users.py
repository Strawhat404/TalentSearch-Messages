import csv
import requests

url = "http://localhost:8000/api/auth/register/"

with open("users.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        data = {
            "email": row["email"],
            "password": row["password"],
            "name": row["email"].split("@")[0]  # or any name you want
        }
        response = requests.post(url, json=data)
        print(f"{row['email']}: {response.status_code} {response.text}")
