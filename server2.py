from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import uuid
import base64
from typing import Dict, Any
from pydantic import BaseModel


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
sessions: Dict[str, Dict[str, Any]] = {}


class VerifyRequest(BaseModel):
    session_id: str
    registration_number: str
    captcha_text: str
    reg_student: int = 1


@app.get("/init-session")
async def init_session():
    try:
        session_id = str(uuid.uuid4())
        session = requests.Session()
        url = "https://verify.bmdc.org.bd/"

        response = session.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to initialize session")

        soup = BeautifulSoup(response.content, "html.parser")
        csrf_token = soup.find("input", {"name": "bmdckyc_csrf_token"})["value"]
        action_key = soup.find("input", {"name": "action_key"})["value"]

        captcha_image_tag = soup.find("img", {"alt": " "})
        captcha_image_url = captcha_image_tag["src"]
        captcha_response = session.get(captcha_image_url)

        if captcha_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch CAPTCHA")

        # Save CAPTCHA image to file
        with open("captcha_image.jpg", "wb") as f:
            f.write(captcha_response.content)

        sessions[session_id] = {
            "session": session,
            "csrf_token": csrf_token,
            "action_key": action_key,
        }

        return JSONResponse(
            {
                "session_id": session_id,
                "captcha_image": base64.b64encode(captcha_response.content).decode(
                    "utf-8"
                ),
                "csrf_token": csrf_token,
                "action_key": action_key,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify-doctor")
async def verify_doctor(request: VerifyRequest):
    try:
        session_data = sessions.get(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session expired")

        session = session_data["session"]
        form_data = {
            "bmdckyc_csrf_token": session_data["csrf_token"],
            "reg_ful_no": request.registration_number,
            "reg_student": str(request.reg_student),
            "captcha_code": request.captcha_text,
            "action_key": session_data["action_key"],
            "action_flag": "1",
        }

        response = session.post("https://verify.bmdc.org.bd/regfind", data=form_data)
        soup = BeautifulSoup(response.content, "html.parser")
        doctor_info = soup.find("div", {"class": "form-items"})

        if not doctor_info:
            raise HTTPException(
                status_code=400, detail="Invalid CAPTCHA or registration number"
            )

        # Extract and process doctor's image
        doctor_image_tag = doctor_info.find(
            "img", {"class": "rounded img-responsive mb-2"}
        )
        if not doctor_image_tag:
            raise HTTPException(status_code=404, detail="Doctor image not found")

        doctor_image_url = doctor_image_tag["src"]
        image_bytes = b""

        if doctor_image_url.startswith("data:image/jpg;base64,"):
            base64_data = doctor_image_url.split(",", 1)[1]
            image_bytes = base64.b64decode(base64_data)
        else:
            image_response = session.get(doctor_image_url)
            image_response.raise_for_status()
            image_bytes = image_response.content

        # Save doctor image to file
        with open("doctor_image.jpg", "wb") as f:
            f.write(image_bytes)

        registration_status_div = doctor_info.find("div", {"class": "form-group row mb-0"})
        registration_status=registration_status_div.find_all_next('span', {'class': 'font-weight-bold'})[0].text.strip()
        # Build result with image and data
        result = {
            "doctor_image_base64": base64.b64encode(image_bytes).decode("utf-8"),
            "name": doctor_info.find(
                "h3", {"class": "mb-4 font-weight-bold text-center"}
            ).text.strip(),
            "registration_number": doctor_info.find(
                "h3",
                {
                    "class": "badge badge-pill badge-success mt-1 mb-3 font-weight-bold d-block text-center text-white"
                },
            ).text.strip(),
            "status": registration_status,
            # "status": "Valid" if "Valid" in response.text else "Invalid",
        }

        # Additional information
        additional_info = doctor_info.find(
            "div", {"class": "form-group row text-center"}
        )
        if additional_info:
            fields = additional_info.find_all("div", {"class": "col-md-4"})
            result.update(
                {
                    "reg_year": fields[0].find("span").text.strip(),
                    "valid_till": fields[1].find("span").text.strip(),
                    "card_number": fields[2].find("span").text.strip(),
                }
            )

        # Personal details
        personal_info = doctor_info.find_all("div", {"class": "form-group row mb-0"})
        if personal_info:
            result.update(
                {
                    "dob": personal_info[0].find_all("h6")[0].text.strip(),
                    "blood_group": personal_info[0].find_all("h6")[1].text.strip(),
                    "father_name": personal_info[1].find("h6").text.strip(),
                    "mother_name": personal_info[2].find("h6").text.strip(),
                }
            )

        return JSONResponse(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
