from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os
import logging
from contextlib import asynccontextmanager

# main.py 함수들 가져오기
from main import (
    building_register_issuance_settings,
    search_address,
    search_dong,
    search_num,
    get_building_register
)
from utils.driver_call import driver_call
from utils.login import login_gov24

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

driver = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global driver
    load_dotenv()
    GOV24_ID = os.getenv("GOV24_ID")
    GOV24_PW = os.getenv("GOV24_PW")

    logger.info("서버 시작: Selenium 드라이버 초기화 및 정부24 로그인")
    try:
        driver = driver_call()
        if not login_gov24(driver=driver, gov24_ID=GOV24_ID, gov24_PW=GOV24_PW):
            raise RuntimeError("정부24 로그인 실패. ID/PW 확인 필요")
        logger.info("정부24 로그인 성공")
        yield
    finally:
        if driver:
            driver.quit()
            logger.info("서버 종료: Selenium 드라이버 종료")

app = FastAPI(title="Building Register API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 (form.html 제공)
app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_token = os.getenv("API_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=500, detail="API_TOKEN not set")
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return credentials.credentials

class AddressRequest(BaseModel):
    address: str
    dong: Optional[str] = None
    num: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("static/form.html")

@app.post("/render_building_register", response_class=HTMLResponse)
async def render_building_register(request: AddressRequest, token: str = Depends(verify_token)):
    global driver
    if not driver:
        raise HTTPException(status_code=503, detail="Selenium 드라이버 준비 안 됨")

    try:
        logger.info(f"요청: {request.address}_{request.dong}_{request.num}")

        if not building_register_issuance_settings(driver=driver):
            raise HTTPException(status_code=500, detail="발급 설정 실패")

        address_result = search_address(driver=driver, address=request.address)
        if not address_result["success"]:
            raise HTTPException(status_code=400, detail=f"주소 검색 실패: {address_result['message']}")

        if request.dong:
            dong_result = search_dong(driver=driver, dong=request.dong, num=request.num)
            if not dong_result["success"]:
                raise HTTPException(status_code=400, detail=f"동 검색 실패: {dong_result['dong_list']}")

        if request.num:
            num_result = search_num(driver=driver, dong=request.dong, num=request.num)
            if not num_result["success"]:
                raise HTTPException(status_code=400, detail=f"호수 검색 실패: {num_result['num_list']}")

        building_register_html = get_building_register(
            driver=driver,
            address=request.address,
            dong=request.dong or "",
            num=request.num or ""
        )

        return HTMLResponse(content=building_register_html, status_code=200)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=8000)
