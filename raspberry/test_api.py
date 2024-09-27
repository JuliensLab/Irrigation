import requests

# URL of the API you want to test
url = "https://irrigationmars.com/api/test.php"

# Send the GET request to the API
try:
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the response if allowed
        print("Success:", response.json())
    elif response.status_code == 403:
        # If the IP is not allowed
        print("Access Denied:", response.json())
    else:
        # Handle other status codes
        print(f"Unexpected status code: {response.status_code}")
        print("Response:", response.text)
except requests.exceptions.RequestException as e:
    # Handle request exceptions
    print("Request failed:", e)
