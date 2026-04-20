from fastapi import FastAPI, Request, Response, Query, HTTPException, UploadFile, File, Depends, Cookie
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

async def verify_consent(consent_cookie: Optional[str] = Cookie(None, alias="user_consent")):
    """
    Dependency that checks if the 'user_consent' cookie exists and is 'accepted'.
    """
    if consent_cookie != "accepted":
        raise HTTPException(
            status_code=403, 
            detail="Consent required. Please accept cookies to use this feature."
        )
    return True

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    consent = request.cookies.get("user_consent")
    print(consent)
    show_banner = True if not consent else False

    return templates.TemplateResponse(
        request = request, 
        name = "index.html", 
        context = {"message": "viola!", "show_banner": show_banner}
    )

@app.post("/get-recommendations")
async def upload_and_recommend(file: UploadFile = File(...), consent: bool = Depends(verify_consent)):
    """
    This endpoint only runs if verify_consent passes.
    """
    # Logic to process the file and generate recommendations
    return {
        "filename": file.filename,
        "recommendations": ["Item A", "Item B", "Item C"],
        "status": "Success"
    }

@app.post("/set-consent")
async def set_cookie_consent(response: Response, choice: str = Query(...)):
    if choice == "accept":
        # Set a long-term cookie for accepted consent
        response.set_cookie(
            key="user_consent",
            value="granted",
            max_age=31536000,  # 1 year
            httponly=True,
            samesite="lax"
        )
        return {"status": "accepted"}
    
    # no cookie should be set as consent was denied
    response.delete_cookie(key="user_consent")
    # Set a session cookie or a 'denied' flag
    # response.set_cookie(
    #     key="user_consent",
    #     value="denied",
    #     httponly=True
    # )
    return {"status": "rejected"}