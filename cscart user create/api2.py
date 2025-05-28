import requests
import json

# --- Configuration ---
# Replace with your CS-Cart store URL (e.g., "http://yourstore.com" or "https://yourstore.com")
CSKART_URL = "http://teszt22.arsuna.hu"

# Replace with your CS-Cart admin email address
ADMIN_EMAIL = "it@arsuna.hu"

# Replace with your CS-Cart admin user's API key
# You can find/generate this in your CS-Cart admin panel, usually under Customers > Administrators > [Your Admin Account] > API access
API_KEY = "8B0e0En12gW5wD250NAo0kW33F78Zd3T"

# --- New User Details ---
# Modify these details for the new user you want to create
new_user_data = {
    "email": "palfijuci@gmail.com",
    "password": "SecurePassword123!",
    "user_type": "C",  # 'C' for Customer, 'A' for Admin, 'V' for Vendor
    "status": "A",     # 'A' for Active, 'D' for Disabled, 'H' for Hidden
    "company_id": "1", # Typically "1" for the main storefront.
                       # For CS-Cart Multi-Vendor, this might be different.
                       # For individual customers not tied to a specific company context, "0" might be used.
                       # Please verify this from your CS-Cart setup if unsure.
    "lastname": "Thurzó-Pálfi Judit",
    "phone": "+36302409473",
}

def create_cscart_user():
    """
    Creates a new user in CS-Cart via the API.
    """
    if CSKART_URL == "YOUR_CSKART_STORE_URL" or \
       ADMIN_EMAIL == "YOUR_ADMIN_EMAIL" or \
       API_KEY == "YOUR_API_KEY":
        print("ERROR: Please update the placeholder values for CSKART_URL, ADMIN_EMAIL, and API_KEY in the script.")
        return

    # Construct the API endpoint URL
    # Note: CS-Cart API can sometimes be /api.php?_d=users or /api/v1/users depending on version and setup.
    # /api/users/ is common for RESTful API.
    api_url = f"{CSKART_URL.rstrip('/')}/api/2.0/users/"

    print(f"Attempting to create user at: {api_url}")
    print(f"User data: {json.dumps(new_user_data, indent=2)}")

    try:
        # Make the POST request with Basic Authentication
        response = requests.post(
            api_url,
            auth=(ADMIN_EMAIL, API_KEY), # Basic Auth: username=admin_email, password=api_key
            json=new_user_data,          # Send data as JSON payload
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json" # Request JSON response
            }
        )

        # Print the HTTP status code
        print(f"\nResponse Status Code: {response.status_code}")

        # Try to parse the JSON response
        try:
            response_data = response.json()
            print("Response JSON:")
            print(json.dumps(response_data, indent=2))

            if response.status_code == 201: # 201 Created usually indicates success
                print("\nUser created successfully!")
                if "user_id" in response_data:
                    print(f"New User ID: {response_data['user_id']}")
            else:
                print("\nFailed to create user. API returned an error.")
                if "message" in response_data:
                    print(f"Error Message: {response_data['message']}")
                if "errors" in response_data:
                    print(f"Details: {response_data['errors']}")

        except ValueError: # If response is not JSON
            print("Response content (not JSON):")
            print(response.text)
            if response.status_code == 201:
                 print("\nUser likely created successfully (Status 201), but response was not standard JSON.")
            else:
                print("\nFailed to create user. Response was not JSON.")


    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred during the HTTP request: {e}")

if __name__ == "__main__":
    create_cscart_user()
