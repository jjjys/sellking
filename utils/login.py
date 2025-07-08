from .driver_call import driver_call
from dotenv import load_dotenv
import os,time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def captcha_img_save(driver=None):
    # 저장할 디렉토리 경로
    save_dir = r"C:\Users\User\Desktop\sellking\data\captcha"

    # 현재 시간을 기반으로 파일명 생성 (예: captcha_20250702_135500.png)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"captcha_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)
    
    driver.find_element(By.CSS_SELECTOR, '.img-captcha').screenshot(filepath)

    # 완료 메시지
    print(f"캡차 이미지 저장 완료: {filepath}")
    return True

def login_gov24(driver=None, gov24_ID='', gov24_PW=''):
    if driver==None:
        driver = driver_call()
    
    driver.get('https://plus.gov.kr/login/loginIdPwd')
    # 아이디 입력
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, '#input_id').send_keys(gov24_ID)
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, ".btn.lg.btn-login").click()
    time.sleep(1)

    # 비밀번호 입력
    driver.find_element(By.CSS_SELECTOR, '#input_pwd').send_keys(gov24_PW)

    # 캡챠 입력
    #캡챠 입력 코드 작성
    captcha_img_save(driver=driver)
    input('캡챠 입력 후 엔터')
    if driver.current_url == 'https://plus.gov.kr/login/loginIdPwdTo':
        driver.find_element(By.CSS_SELECTOR, ".btn.lg.btn-login").click()
    
    for i in range(10):
        if driver.current_url != 'https://plus.gov.kr/login/loginIdPwdTo':
            break
        time.sleep(1)
    time.sleep(1)
    return  True

if __name__ == '__main__': 
    
    load_dotenv()  # .env 읽기
    GOV24_ID = os.getenv("GOV24_ID")
    GOV24_PW = os.getenv("GOV24_PW")
    print(GOV24_ID)  
    print(GOV24_PW)  

    login_gov24(GOV24_ID, GOV24_PW)