from .driver_call import driver_call
from dotenv import load_dotenv
import os,time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import google.generativeai as genai
import base64
import logging
logger = logging.getLogger(__name__)

def captcha_solve_with_gemini(image_path):
    """Gemini AI를 사용하여 캡챠 이미지를 분석하고 숫자 값을 추출하는 함수."""
    try:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=GEMINI_API_KEY)

        # 이미지 파일 읽기 및 Base64 인코딩
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        #model = genai.GenerativeModel('gemini-1.5-pro')
        model = genai.GenerativeModel('gemini-2.5-flash')

        response = model.generate_content([
            "이 이미지에서 보이는 숫자만 답변해줘.",
            {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
        ])
        
        logger.info(f"캡챠 분석 결과:{response.text}")
        return response.text
    except Exception as e:
        logger.info(f"캡챠 분석 중 오류 발생: {e}")

def captcha_img_save(driver=None):
    """Selenium 드라이버에서 캡챠 이미지를 캡처하여 파일로 저장하는 함수."""
    try:
        # 저장할 디렉토리 경로
        save_dir = os.path.join("data", "captcha")
        os.makedirs(save_dir, exist_ok=True) # 디렉토리가 존재하지 않으면 생성

        # 현재 시간을 기반으로 파일명 생성 (예: captcha_20250702_135500.png)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captcha_{timestamp}.png"
        filepath = os.path.join(save_dir, filename)
        
        try:
            driver.find_element(By.CSS_SELECTOR, '.img-captcha').screenshot(filepath)
        except:
            driver.find_element(By.CSS_SELECTOR, '#cimg').screenshot(filepath) # 위 코드에서 태그 변경

        # 완료 메시지
        logger.info(f"캡차 이미지 저장 완료: {filepath}")
        return filepath
    except:
        logger.info('캡챠 이미지 저장 실패')
        return False

def login_gov24(driver=None, gov24_ID='', gov24_PW=''):
    """정부24 사이트에 로그인하는 함수. 캡챠를 처리하고 여러 번 시도."""
    for _ in range(0,3): # 3번 시도
        try:
            # 로그인 페이지 이동
            try:
                '''
                정부24 로그인 페이지 랜덤으로 변경됨.
                로그인이 계속 안되는 경우 아래
                페이지1,2,3 중에 다른 하나로 driver.get() 수정필요
                '''
                login_page_1 = 'https://plus.gov.kr/login/loginIdPwd'
                login_page_2 = 'https://www.gov.kr/nlogin/loginById'
                login_page_3 = 'https://plus.gov.kr/login?awqf=!2f'
                driver.get(login_page_2) # 안되는 경우 페이지 1,2,3 중에 하나로 변경
                time.sleep(1)
                if '간단히 로그인' in driver.page_source:
                    # 간단히 로그인 버튼 클릭
                    driver.find_element(By.CSS_SELECTOR, '#loginMoTabpanel01 > div > div:nth-child(2) > div > a:nth-child(1)').click()
                    time.sleep(1)
            except:
                logger.info('로그인 페이지 에러, html 태그 변경 필요') # 위 코드에서 태그 변경
                
            # 아이디 입력
            time.sleep(1)
            try:
                logger.info('아이디 값 입력(태그1)')
                driver.find_element(By.CSS_SELECTOR, '#input_id').send_keys(gov24_ID)
            except:
                logger.info('아이디 값 입력(태그2)')
                driver.find_element(By.CSS_SELECTOR, '#userId').send_keys(gov24_ID) # 위 코드에서 태그 변경
            time.sleep(1)
            try:
                logger.info('아이디 다음 버튼 클릭(태그1)')
                driver.find_element(By.CSS_SELECTOR, ".btn.lg.btn-login").click()
            except:
                logger.info('아이디 다음 버튼 클릭(태그2)')
                driver.find_element(By.CSS_SELECTOR, "#genLogin").click() # 위 코드에서 태그 변경
            time.sleep(1)

            # 비밀번호 입력
            try:
                logger.info('비밀번호 값 입력(태그1)')
                driver.find_element(By.CSS_SELECTOR, '#input_pwd').send_keys(gov24_PW)
            except:
                logger.info('비밀번호 값 입력(태그2)')
                driver.find_element(By.CSS_SELECTOR, '#pwd').send_keys(gov24_PW) # 위 코드에서 태그 변경

            # 캡챠 이미지 저장
            image_path = captcha_img_save(driver=driver)
            pred_captcha = captcha_solve_with_gemini(image_path)
            
            try:
                driver.find_element(By.CSS_SELECTOR, '#label_05_01').send_keys(pred_captcha)
                logger.info('캡챠 정답 값 입력(태그1)')
            except:
                driver.find_element(By.CSS_SELECTOR, '#answer').send_keys(pred_captcha) # 위 코드에서 태그 변경
                logger.info('캡챠 정답 값 입력(태그2)')
            
            login_pwd_url_1 = 'https://plus.gov.kr/login/loginIdPwdTo'
            login_pwd_url_2 = 'https://www.gov.kr/nlogin/loginByPswd'

            # 로그인 버튼 클릭
            if driver.current_url == login_pwd_url_1 or driver.current_url == login_pwd_url_2:
                try:
                    driver.find_element(By.CSS_SELECTOR, ".btn.lg.btn-login").click()
                    logger.info('로그인 버튼 클릭 (태그1)')
                except:
                    driver.find_element(By.CSS_SELECTOR, "#genLogin").click() # 위 코드에서 태그 변경
                    logger.info('로그인 버튼 클릭 (태그2)')
            
            for i in range(3):
                logger.info(f'캡챠 로그인 성공 판단 중..({i+1}/3)')
                time.sleep(1)
                if (driver.current_url != login_pwd_url_1 or driver.current_url != login_pwd_url_2) and\
                    not('입력확인 문자를 정확히 입력해 주세요.' in driver.page_source):
                    logger.info('로그인 성공!(캡챠 정답값 저장)')
                    img_rename = image_path.replace('.png',f'_{pred_captcha}.png')
                    os.rename(image_path, img_rename)
                    return True
                
            # 로그인 후 화면 이동이 안되면 로그인 실패
            if (driver.current_url == login_pwd_url_1 or driver.current_url == login_pwd_url_2):
                logger.info(f'로그인 실패!({_+1}/3)')
            time.sleep(3)
        except:
            logger.info('로그인 시도 중 에러 발생!')
            break
    return False

def login_status_gov24(driver):
    """정부24 사이트의 현재 로그인 상태를 확인하는 함수."""
    try:
        driver.get('https://plus.gov.kr/')
        elem_selector = '#iw_header > div.header-in > div > div.header-top > div > div.bottom'
        WebDriverWait(driver, timeout=10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, elem_selector))
                )
        time.sleep(1)
        if '로그아웃' in driver.find_element(By.CSS_SELECTOR, elem_selector).text:
            logger.info('현재 상태:로그인')
            return True
        else:
            logger.info('현재 상태:로그아웃')
            return False
    except Exception as e:
        logger.info(f'로그인 상태 체크 에러\n{e}')
        return False

    

if __name__ == '__main__': 
    
    load_dotenv()  # .env 읽기
    GOV24_ID = os.getenv("GOV24_ID")
    GOV24_PW = os.getenv("GOV24_PW")
    driver = driver_call()
    for _ in range(0,10):
        logger.info(f'{_+1} 번째 실행')
        login_status_gov24(driver)
        login_gov24(driver=driver, gov24_ID=GOV24_ID, gov24_PW=GOV24_PW)
        login_status_gov24(driver)