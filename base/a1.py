import requests
from bs4 import BeautifulSoup
from PIL import Image
import matplotlib.pyplot as plt
import base64

# Step 1: Fetch the page
url = "https://verify.bmdc.org.bd/"
session = requests.Session()
response = session.get(url)

# Check if the request was successful
if response.status_code != 200:
    print("Failed to fetch the page. Status code:", response.status_code)
    exit()

# Step 2: Parse the HTML to extract the CAPTCHA image URL, CSRF token, and action_key
soup = BeautifulSoup(response.content, "html.parser")

# Extract the CAPTCHA image URL
captcha_image_tag = soup.find("img", {"alt": " "})
if not captcha_image_tag:
    print("CAPTCHA image not found. Check the HTML structure.")
    exit()

# Use the src attribute directly (it should already contain the full URL)
captcha_image_url = captcha_image_tag["src"]
print("CAPTCHA image URL:", captcha_image_url)

# Extract the CSRF token
csrf_token = soup.find("input", {"name": "bmdckyc_csrf_token"})["value"]
print("CSRF Token:", csrf_token)

# Extract the action_key
action_key_input = soup.find("input", {"name": "action_key"})
if not action_key_input:
    print("Action key not found. Check the HTML structure.")
    exit()

action_key = action_key_input["value"]
print("Action Key:", action_key)

# Step 3: Download and process the CAPTCHA image
captcha_image_response = session.get(captcha_image_url)
if captcha_image_response.status_code != 200:
    print(
        "Failed to download CAPTCHA image. Status code:",
        captcha_image_response.status_code,
    )
    exit()

# Save the CAPTCHA image locally for debugging
with open("captcha_image.jpg", "wb") as f:
    f.write(captcha_image_response.content)
print("CAPTCHA image saved as 'captcha_image.jpg'.")

# Open the CAPTCHA image using PIL
captcha_image = Image.open("captcha_image.jpg")

# Display the CAPTCHA image for debugging
print("Displaying CAPTCHA image...")
plt.imshow(captcha_image)
plt.axis("off")  # Hide axes
plt.show()

# Prompt the user to input the CAPTCHA text
captcha_text = input("Enter the CAPTCHA text: ")
print("You entered:", captcha_text)

# Step 4: Submit the form with the doctor's registration number and CAPTCHA
doctor_registration_number = input(
    "Enter Doctor registration Number : "
)  # Replace with the actual registration number
form_data = {
    "bmdckyc_csrf_token": csrf_token,
    "reg_ful_no": doctor_registration_number,
    "reg_student": "1",  # 1 for MBBS, 2 for BDS
    "captcha_code": captcha_text,
    "action_key": action_key,  # Use the dynamically extracted action_key
    "action_flag": "1",
}

response = session.post("https://verify.bmdc.org.bd/regfind", data=form_data)

# Step 5: Extract the doctor's information and image
soup = BeautifulSoup(response.content, "html.parser")
doctor_info = soup.find("div", {"class": "form-items"})

if not doctor_info:
    print("Doctor information not found. Check the registration number or CAPTCHA.")
    exit()

# Extract doctor's name and full registration number
doctor_full_reg_num = doctor_info.find(
    "h3",
    {
        "class": "badge badge-pill badge-success mt-1 mb-3 font-weight-bold d-block text-center text-white"
    },
).text.strip()
doctor_name = doctor_info.find(
    "h3", {"class": "mb-4 font-weight-bold text-center"}
).text.strip()
doctor_image_tag = doctor_info.find("img", {"class": "rounded img-responsive mb-2"})

if not doctor_image_tag:
    print("Doctor image not found.")
    exit()

doctor_image_url = doctor_image_tag["src"]
print("Doctor Name:", doctor_name)
print("Doctor Full Registration Number:", doctor_full_reg_num)

# Extract additional information: Reg. Year, Reg. Valid Till, and Portable Card No
additional_info = doctor_info.find("div", {"class": "form-group row text-center"})
if additional_info:
    reg_year = additional_info.find_all("div", {"class": "col-md-4"})[0].find("span").text.strip()
    reg_valid_till = additional_info.find_all("div", {"class": "col-md-4"})[1].find("span").text.strip()
    portable_card_no = additional_info.find_all("div", {"class": "col-md-4"})[2].find("span").text.strip()

    print("Reg. Year:", reg_year)
    print("Reg. Valid Till:", reg_valid_till)
    print("Portable Card No:", portable_card_no)
else:
    print("Additional information not found.")

# Extract Date of Birth and Blood Group
dob_blood_group = doctor_info.find_all("div", {"class": "form-group row mb-0", "data-html2canvas-ignore": "true"})
if dob_blood_group and len(dob_blood_group) > 0:
    # First div with these classes contains Date of Birth and Blood Group
    dob = dob_blood_group[0].find_all("div", {"class": "col-md-6"})[0].find("h6").text.strip()
    blood_group = dob_blood_group[0].find_all("div", {"class": "col-md-6"})[1].find("h6").text.strip()

    print("Date of Birth:", dob)
    print("Blood Group:", blood_group)
else:
    print("Date of Birth and Blood Group not found.")

# Extract Father's Name
if dob_blood_group and len(dob_blood_group) > 1:
    # Second div with these classes contains Father's Name
    father_name = dob_blood_group[1].find("h6").text.strip()
    print("Father's Name:", father_name)
else:
    print("Father's Name not found.")

# Extract Mother's Name
if dob_blood_group and len(dob_blood_group) > 2:
    # Third div with these classes contains Mother's Name
    mother_name = dob_blood_group[2].find("h6").text.strip()
    print("Mother's Name:", mother_name)
else:
    print("Mother's Name not found.")

# Extract Registration Status
registration_status_div = doctor_info.find("div", {"class": "form-group row mb-0"})
registration_status=registration_status_div.find_all_next('span', {'class': 'font-weight-bold'})[0].text.strip()
print("Registration Status:", registration_status)
           

# Step 6: Download the doctor's image
if doctor_image_url.startswith("data:image/jpg;base64,"):
    # Extract the base64 data
    base64_data = doctor_image_url.split(",")[1]
    image_data = base64.b64decode(base64_data)

    # Save the image locally
    with open("doctor_image.jpg", "wb") as f:
        f.write(image_data)
    print("Doctor image saved as 'doctor_image.jpg'.")
    # Open the image using PIL
    doctor_image = Image.open("doctor_image.jpg")
    plt.imshow(doctor_image)
    plt.axis("off")  # Hide axes
    plt.show()
else:
    # Handle the case where the image URL is a regular HTTP/HTTPS URL
    doctor_image_response = session.get(doctor_image_url)
    if doctor_image_response.status_code == 200:
        with open("doctor_image.jpg", "wb") as f:
            f.write(doctor_image_response.content)
        print("Doctor image saved as 'doctor_image.jpg'.")
    else:
        print(
            "Failed to download the doctor's image. Status code:",
            doctor_image_response.status_code,
        )
    