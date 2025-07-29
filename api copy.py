from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import time
from typing import Optional
from main import (
    building_register_issuance_settings,
    search_address,
    search_dong,
    search_num,
    get_building_register,
    T_DEFAULT
)
from utils.login import login_gov24
from utils.driver_call import driver_call
#import pdfkit
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Building Register API", description="API for issuing building register documents")

# 토큰 인증 설정
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_token = os.getenv("API_TOKEN")
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# 요청 데이터 모델 정의
class BuildingRegisterRequest(BaseModel):
    address: str
    dong: Optional[str] = None
    num: Optional[str] = None

# 응답 데이터 모델 정의
class BuildingRegisterResponse(BaseModel):
    success: bool
    message: str
    html_content: Optional[str] = None
    pdf_path: Optional[str] = None
    dong_result: Optional[dict] = None
    num_result: Optional[dict] = None

# .env 파일 로드
load_dotenv()
GOV24_ID = os.getenv("GOV24_ID")
GOV24_PW = os.getenv("GOV24_PW")
# 필수 환경 변수 확인
required_vars = ["GOV24_ID", "GOV24_PW", "OPENAI_API_KEY", "GEMINI_API_KEY", "API_TOKEN"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")

@app.on_event("startup")
async def startup_event():
    global driver
    driver = driver_call()
    logger.info("Initializing driver and logging in...")
    if not login_gov24(driver=driver, gov24_ID=GOV24_ID, gov24_PW=GOV24_PW):
        driver.quit()
        raise HTTPException(status_code=500, detail="Login to gov24 failed")

@app.on_event("shutdown")
async def shutdown_event():
    global driver
    if driver:
        driver.quit()
        logger.info("Driver closed")

@app.post("/building-register", response_model=BuildingRegisterResponse)
async def issue_building_register(request: BuildingRegisterRequest, token: str = Depends(verify_token)):
    """
    주소, 동, 호수를 받아 건축물대장을 발급하는 API
    """
    driver = None
    try:
        # 건축물대장 발급 페이지 세팅
        if not building_register_issuance_settings(driver=driver):
            raise HTTPException(status_code=500, detail="Failed to set up issuance page")

        # 주소 검색
        result_address = search_address(driver=driver, address=request.address)
        if not result_address['success']:
            return BuildingRegisterResponse(
                success=False,
                message=result_address['message'],
                html_content=None,
                pdf_path=None,
                dong_result=None,
                num_result=None
            )

        # 동 검색
        result_dong = search_dong(driver=driver, dong=request.dong, num=request.num)
        if not result_dong['success']:
            return BuildingRegisterResponse(
                success=False,
                message=f"동 검색 실패: {result_dong['dong_list']}",
                html_content=None,
                pdf_path=None,
                dong_result=result_dong,
                num_result=None
            )

        # 호수 검색
        result_num = search_num(driver=driver, dong=request.dong, num=request.num)
        if not result_num['success']:
            return BuildingRegisterResponse(
                success=False,
                message=f"호수 검색 실패: {result_num['num_list']}",
                html_content=None,
                pdf_path=None,
                dong_result=result_dong,
                num_result=result_num
            )

        # 건축물대장 발급
        html_content = get_building_register(driver=driver, address=request.address, dong=request.dong, num=request.num)

        # HTML을 PDF로 변환
        pdf_dir = os.path.join("data", "building_registers")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"건축물대장_{request.address}_{request.dong}_{request.num}.pdf")
        #pdfkit.from_string(html_content, pdf_path)

        return BuildingRegisterResponse(
            success=True,
            message="건축물대장 발급 성공",
            html_content=html_content,
            pdf_path=pdf_path,
            dong_result=result_dong,
            num_result=result_num
        )

    except Exception as e:
        return BuildingRegisterResponse(
            success=False,
            message=f"Error: {str(e)}",
            html_content=None,
            pdf_path=None,
            dong_result=None,
            num_result=None
        )
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)