import os, requests, time

CLIENT_ID = "client-id"
CLIENT_SECRET = "client-secret"
TOKEN_URL = "https://22d05079trial.authentication.us10.hana.ondemand.com/oauth/token"

def access_token():
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    res = requests.post(TOKEN_URL, data=data)
    print("fetching token")
    token = res.json().get("access_token")
    if token:
        print("Token:",token)
        print("✅ Token retrieved successfully")

if __name__=="__main__":
    access_token()