import requests
from PIL import Image
from io import BytesIO
import base64

BASE_URL = "http://localhost:8000"

def test_flow():
    # Initialize session
    init_response = requests.get(f"{BASE_URL}/init-session")
    if init_response.status_code != 200:
        print("Failed to initialize session")
        return

    session_data = init_response.json()
    print("Session ID:", session_data["session_id"])

    # Show CAPTCHA
    captcha_bytes = base64.b64decode(session_data["captcha_image"])
    img = Image.open(BytesIO(captcha_bytes))
    img.show()

    # Get input
    reg_number = input("Enter registration number: ")
    captcha_text = input("Enter CAPTCHA text: ")

    # Verify doctor
    verify_data = {
        "session_id": session_data["session_id"],
        "registration_number": reg_number,
        "captcha_text": captcha_text
    }
    
    verify_response = requests.post(
        f"{BASE_URL}/verify-doctor",
        json=verify_data  # Send as JSON
    )
    
    if verify_response.status_code == 200:
        print("\nVerification Successful!")
        print("Doctor Details:")
        for key, value in verify_response.json().items():
            print(f"{key.upper():<20}: {value}")
    else:
        print(f"\nVerification Failed ({verify_response.status_code}):")
        print(verify_response.json().get("detail", "Unknown error"))

if __name__ == "__main__":
    test_flow()