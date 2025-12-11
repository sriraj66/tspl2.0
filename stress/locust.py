from locust import HttpUser, task, between

# Filtered URLs to test
URLS = [
    "https://tntenniscricket.in/",
    "https://tntenniscricket.in/blog/vgallery",
    "https://tntenniscricket.in/blog/who-can-register/",
    "https://tntenniscricket.in/blog/gallery",
    "https://tntenniscricket.in/points/table.view",
    "https://tntenniscricket.in/newsevents/",
    "https://tntenniscricket.in/blog/tspl-t10-action/",
    "https://tntenniscricket.in/blog/own-a-tspl-franchise-team/",
    "https://tntenniscricket.in/privacy-policy",
    "https://tntenniscricket.in/sitemap.xml",
    "https://tntenniscricket.in/commite-team",
    "https://tntenniscricket.in/about-us/",
]

# 50 fake test users
TEST_USERS = [f"user{i}@example.com" for i in range(1, 200)]


class TNTSPLUser(HttpUser):
    wait_time = between(1, 3)  # simulated delay

    def on_start(self):
        """Random user assigned per locust instance"""
        self.username = TEST_USERS[self.environment.runner.user_count % len(TEST_USERS)]

    @task(5)
    def browse_pages(self):
        """Hit all TNTSPL main URLs"""
        for url in URLS:
            self.client.get(url, name=url.replace("https://tntenniscricket.in", ""))

    @task(1)
    def login_page(self):
        """Hits the login page but does NOT post credentials"""
        self.client.get("https://tntenniscricket.in/accounts/login/", name="/login")
