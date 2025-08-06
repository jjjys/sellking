from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os
import logging
from utils.driver_call import driver_call
from utils.login import login_gov24
from main import building_register_issuance_settings, search_address, search_dong, search_num, get_building_register
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Building Register API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080","https://.*\\.ngrok-free\\.app"],
    #allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Token authentication
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_token = os.getenv("API_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_TOKEN environment variable not set",
        )
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# Request model
class AddressRequest(BaseModel):
    address: str
    dong: Optional[str] = None
    num: Optional[str] = None
    #output_format: str = "html"

# Load environment variables
load_dotenv()
required_vars = ["GOV24_ID", "GOV24_PW", "API_TOKEN"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")

# Global driver
driver = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global driver
    try:
        logger.info("Initializing driver and logging in...")
        driver = driver_call()  # 드라이버 초기화
        if not login_gov24(driver=driver, gov24_ID=os.getenv("GOV24_ID"), gov24_PW=os.getenv("GOV24_PW")):
            driver.quit()
            raise HTTPException(status_code=500, detail="Login to gov24 failed")
        yield
    finally:
        if driver is not None:
            driver.quit()
            logger.info("Driver closed")
            driver = None  # 전역 변수 초기화

app = FastAPI(lifespan=lifespan)

@app.post("/get_building_register")
async def get_building_register_endpoint(request: AddressRequest, token: str = Depends(verify_token)):
    try:
        logger.info(f"Processing request: {request}")
        
        # Set up issuance page
        logger.info("Running building_register_issuance_settings...")
        if not building_register_issuance_settings(driver=driver):
            raise HTTPException(status_code=500, detail="Failed to set up issuance page")

        # Search address
        logger.info("Running search_address...")
        address_result = search_address(driver=driver, address=request.address)
        if not address_result["success"]:
            logger.error(f"Address search failed: {address_result['message']}")
            raise HTTPException(status_code=400, detail=address_result["message"])

        # Search dong
        logger.info("Running search_dong...")
        dong_result = {"success": True, "selected_dong": request.dong, "ai_response": {"정답": request.dong}}
        if request.dong:
            dong_result = search_dong(driver=driver, dong=request.dong, num=request.num)
            if not dong_result["success"]:
                logger.error(f"Dong search failed: {dong_result['dong_list']}")
                raise HTTPException(status_code=400, detail=f"Dong search failed: {dong_result['dong_list']}")

        # Search num
        logger.info("Running search_num...")
        num_result = {"success": True, "selected_num": request.num, "ai_response": {"정답": request.num}}
        if request.num and dong_result["success"]:
            num_result = search_num(driver=driver, dong=request.dong, num=request.num)
            if not num_result["success"]:
                logger.error(f"Num search failed: {num_result['num_list']}")
                raise HTTPException(status_code=400, detail=f"Num search failed: {num_result['num_list']}")

        # Get building register
        logger.info("Running get_building_register...")
        if dong_result["success"] and num_result["success"]:
            building_register_html = get_building_register(
                driver=driver,
                address=request.address,
                dong=request.dong or "",
                num=request.num or ""
            )
            # if request.output_format.lower() == "pdf":
            #     raise HTTPException(status_code=501, detail="PDF conversion not implemented yet")
            # Return HTML directly
            logger.info("Returning HTML response")
            return HTMLResponse(content=building_register_html, status_code=200)
        else:
            logger.error("Failed to retrieve building register due to dong or num search failure")
            raise HTTPException(status_code=400, detail="Failed to retrieve building register")
    except Exception as e:
        logger.error(f"Error in get_building_register_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)