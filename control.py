import os
import requests
import dotenv

dotenv.load_dotenv()

host = "https://miutech.cloud:8991/api"
# host = "http://localhost:8000/api"
username = os.environ["ADMIN_USERNAME"]
password = os.environ["ADMIN_PASSWORD"]


def get_token():
    url = f"{host}/login"
    response = requests.post(
        url, json={"username": username, "password": password})
    print(response.json())
    if response.status_code == 200:
        return response.json()["access_token"]

    url = f"{host}/signup"
    response = requests.post(url, json={
                             "username": username, "password": password, "email": "daniel.bb0321@miutech.cloud", "name": "Daniel"})
    print(response.json())
    if response.status_code == 200:
        return response.json()["access_token"]

    return None


def initialize_problem():
    token = get_token()
    if not token:
        print("no permission")
        return

    url = f"{host}/initialize_problem"
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code == 200:
        print("initialize problem success")
    else:
        print(f"error: {response.status_code} {response.text}")

def initialize_word():
    token = get_token()
    if not token:
        print("no permission")
        return

    url = f"{host}/initialize_word"
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code == 200:
        print("initialize_word success")
    else:
        print(response.json())
        print("initialize_word failed")


if __name__ == "__main__":
    # initialize_problem()
    initialize_word()
