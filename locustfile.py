import csv
from locust import HttpUser, task, between

# Load users from CSV
with open("users.csv") as f:
    reader = csv.DictReader(f)
    users = list(reader)

class WebsiteUser(HttpUser):
    wait_time = between(60, 61)  # Each user logs in only once

    def on_start(self):
        # Assign a unique user to each simulated user
        self.user = users[self.environment.runner.user_count % len(users)]

    @task
    def login(self):
        self.client.post(
            "/api/auth/login/",
            json={
                "email": self.user["email"],
                "password": self.user["password"]
            },
            headers={"Content-Type": "application/json"}
        )
        self.environment.runner.quit()  # Stop after one login per user
