import requests
import json
from datetime import datetime, timedelta

def get_slots_url():
    date_field = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    center = "grove-wellbeing-centre"
    # center = "ballysillan-leisure-centre"
    duration = "badminton-40min"
    # duration = "badminton-60min"
    start = "18:20"
    end = "19:00"
    # start = "10:30"
    # end = "11:30"
    slots_url = f"https://better-admin.org.uk/api/activities/venue/{center}/activity/{duration}/slots?date={date_field}&start_time={start}&end_time={end}"

    print(f"slots_url {slots_url}")
    return slots_url

def get_available_slots(slots_url, attempts):
    slots_response = requests.get(slots_url, headers=headers)
    print(f"{attempts+1} {datetime.now()}")
    
    if is_json(slots_response.text) == False:
        print("Response is not json.")
        return None
    slots_data = slots_response.json()

    if slots_response.status_code != 200 or not slots_data.get("data"):
        print(f"No available slots in the response -> {slots_response.text}")
        return None

    return slots_data["data"]

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True
    
# Step 1: Login and get token

login_url = "https://better-admin.org.uk/api/auth/customer/login"
login_payload = {"username": "dawnkottaram@gmail.com", "password": "Belfast@111"}

headers = {
    "Content-Type": "application/json",  # Add this header
    "origin": "https://bookings.better.org.uk"
}

login_response = requests.post(login_url, json=login_payload, headers=headers)

# Check if the request was successful (status code 200)
if login_response.status_code != 200:
    print(f"Login failed with status code: {login_response.status_code}")
    exit()

login_data = login_response.json()

if "token" not in login_data:
    print("Login failed.")
    exit()

token = login_data["token"]
print("token received.")

# Step 2: Get User details to read user membership id
user_details_url = "https://better-admin.org.uk/api/auth/user"
additional_headers = {
    "Authorization": f"Bearer {token}",
    "authority": "better-admin.org.uk",
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,bg;q=0.7",
    "sec-ch-ua-mobile": "?0",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site"
}
headers.update(additional_headers)

user_details_response = requests.get(user_details_url, headers=headers)
user_details_data = user_details_response.json()

if user_details_response.status_code != 200 or "data" not in user_details_data:
    print("Failed to get user details.")
    exit()

membership_user_id = user_details_data["data"]["membership_user"]["id"]
print("membership_user_id collected.")

# Step 3: Get slots to play - Repeat upto max_attempts until data contains elements
max_attempts = 100  # Set the maximum number of attempts
attempts = 0

# Step 3: Get slots to play
slots_url = get_slots_url()

while attempts < max_attempts:
    slots_data = get_available_slots(slots_url, attempts)
    if slots_data:
        break  # Break the loop if slots are available
    else:
        attempts += 1

if attempts == max_attempts:
    print("Max attempts reached. Exiting.")
    exit()

# Capture attributes from the first element in the slots data
slot_id = slots_data[0]["id"]
pricing_option_id = slots_data[0]["pricing_option_id"]
print("slot_id and pricing_option_id found.")

# Step 4: Add the slot to the cart
add_to_cart_url = "https://better-admin.org.uk/api/activities/cart/add"
add_to_cart_payload = {
    "items": [
        {
            "id": slot_id,
            "type": "activity",
            "pricing_option_id": pricing_option_id,
            "apply_benefit": True,
            "activity_restriction_ids": [],
        }
    ],
    "membership_user_id": membership_user_id,
    "selected_user_id": None,
}

add_to_cart_response = requests.post(add_to_cart_url, json=add_to_cart_payload, headers=headers)

if add_to_cart_response.status_code != 200:
    print("Failed to add slot to the cart.")
    exit()

print("added slot to cart.")

# Step 5: Complete the cart to make the booking
complete_cart_url = "https://better-admin.org.uk/api/checkout/complete"
complete_cart_payload = {"completed_waivers": [], "payments": [], "selected_user_id": None, "source": "activity-booking", "terms": [1]}

complete_cart_response = requests.post(complete_cart_url, json=complete_cart_payload, headers=headers)

if complete_cart_response.status_code == 200:
    print("Booking successful!")
else:
    print("Failed to complete the booking.")
