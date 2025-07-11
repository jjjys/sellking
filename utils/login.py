from .driver_call import driver_call
from dotenv import load_dotenv
import os,time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import numpy as np


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
    return filepath

def image_to_ascii(image_path, width=100):
    try:
        # Load image
        img = Image.open(image_path)
        if img.mode != 'L':  # Convert to grayscale only if needed
            img = img.convert('L')
        img = img.resize((width, int((img.height / img.width) * width * 0.55)))

        # Define ASCII characters
        ascii_chars = '@%#*+=-:. '
        pixels = np.array(img)
        ascii_image = np.array([ascii_chars[p // 32] for p in pixels.ravel()]).reshape(pixels.shape)

        # Print ASCII art
        for row in ascii_image:
            print(''.join(row))
            
    except FileNotFoundError:
        print(f"Error: File {image_path} not found.")
    except Exception as e:
        print(f"Error: {str(e)}")

def login_gov24(driver=None, gov24_ID='', gov24_PW=''):
    try:
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

        # 캡챠 이미지 저장
        image_path = captcha_img_save(driver=driver)

        # 캡챠 이미지 ASCII Art로 출력
        image_to_ascii(image_path)

        # 캡챠 값 입력
        captcha_attempt = input('캡챠 입력 후 엔터:')
        driver.find_element(By.CSS_SELECTOR, '#label_05_01').send_keys(captcha_attempt)

        # 로그인 버튼 클릭
        if driver.current_url == 'https://plus.gov.kr/login/loginIdPwdTo':
            driver.find_element(By.CSS_SELECTOR, ".btn.lg.btn-login").click()
        
        for i in range(10):
            if driver.current_url != 'https://plus.gov.kr/login/loginIdPwdTo' and ('로그아웃' in driver.find_element(By.CSS_SELECTOR, "div.log-after.on").text):
                print('로그인 성공!(캡챠 정답값 저장)')
                img_rename = image_path.replace('.png',f'_{captcha_attempt}.png')
                os.rename(image_path, img_rename)
                break
            print(f'캡챠 로그인 성공 판단 중..({i+1}/10)')
            time.sleep(1)

        # 로그인 성공으로 캡챠 정답값 이름 다시 저장하기.
        if driver.current_url == 'https://plus.gov.kr/login/loginIdPwdTo':
            print('로그인 실패!')
            return False
        time.sleep(3)
        return  True
    except:
        print('로그인 시도 중 에러 발생!')
        return False

if __name__ == '__main__': 
    
    load_dotenv()  # .env 읽기
    GOV24_ID = os.getenv("GOV24_ID")
    GOV24_PW = os.getenv("GOV24_PW")
    #print(GOV24_ID)  
    #print(GOV24_PW) 
    drv = driver_call()
    for _ in range(0,10):
        print(f'{_+1} 번째 실행')
        login_gov24(driver=drv, gov24_ID=GOV24_ID, gov24_PW=GOV24_PW)