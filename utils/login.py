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
import google.generativeai as genai
import base64

def captcha_solve_with_gemini(image_path):
    try:
        
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=GEMINI_API_KEY)

        # 이미지 파일 읽기 및 Base64 인코딩
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        #model = genai.GenerativeModel('gemini-1.5-pro')
        model = genai.GenerativeModel('gemini-1.5-flash')

        response = model.generate_content([
            "이 이미지에서 보이는 숫자만 답변해줘.",
            {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
        ])
        
        print("캡챠 분석 결과:")
        print(response.text)
        return response.text
    except Exception as e:
        print(f"캡챠 분석 중 오류 발생: {e}")

def captcha_img_save(driver=None):
    # 저장할 디렉토리 경로
    save_dir = r"data\captcha"

    # 현재 시간을 기반으로 파일명 생성 (예: captcha_20250702_135500.png)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"captcha_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)
    
    try:
        driver.find_element(By.CSS_SELECTOR, '.img-captcha').screenshot(filepath)
    except:
        driver.find_element(By.CSS_SELECTOR, '#cimg').screenshot(filepath) # 위 코드에서 태그 변경

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
        
        # 로그인 페이지 이동
        try:
            driver.get('https://plus.gov.kr/login/loginIdPwd')
            time.sleep(1)
            if driver.current_url != 'https://plus.gov.kr/login/loginIdPwd':
                driver.get('https://www.gov.kr/nlogin/loginById')
                time.sleep(1)
                if driver.current_url != 'https://www.gov.kr/nlogin/loginById':
                    driver.find_element(By.CSS_SELECTOR, '#loginMoTabpanel01 > div > div:nth-child(2) > div > a:nth-child(1)').click()
        except:
            print('로그인 페이지 에러') # 위 코드에서 태그 변경
            
        # 아이디 입력
        time.sleep(1)
        try:
            driver.find_element(By.CSS_SELECTOR, '#input_id').send_keys(gov24_ID)
        except:
            driver.find_element(By.CSS_SELECTOR, '#userId').send_keys(gov24_ID) # 위 코드에서 태그 변경
            time.sleep(1)
        try:
            driver.find_element(By.CSS_SELECTOR, ".btn.lg.btn-login").click()
        except:
            driver.find_element(By.CSS_SELECTOR, "#genLogin").click() # 위 코드에서 태그 변경
        time.sleep(1)

        # 비밀번호 입력
        try:
            driver.find_element(By.CSS_SELECTOR, '#input_pwd').send_keys(gov24_PW)
        except:
            driver.find_element(By.CSS_SELECTOR, '#pwd').send_keys(gov24_PW) # 위 코드에서 태그 변경

        # 캡챠 이미지 저장
        image_path = captcha_img_save(driver=driver)
        pred_captcha = captcha_solve_with_gemini(image_path)
        

        # 캡챠 이미지 ASCII Art로 출력
        image_to_ascii(image_path)

        # 캡챠 값 입력
        print("아래 예측값이 맞을 경우 그냥 엔터 입력")
        captcha_attempt = input(f'캡챠 입력 후 엔터(예측값:{pred_captcha}):')
        if captcha_attempt == '': # 입력값 없음
            try:
                driver.find_element(By.CSS_SELECTOR, '#label_05_01').send_keys(pred_captcha)
            except:
                driver.find_element(By.CSS_SELECTOR, '#answer').send_keys(pred_captcha) # 위 코드에서 태그 변경
        else:
            try:
                driver.find_element(By.CSS_SELECTOR, '#label_05_01').send_keys(captcha_attempt)
            except:
                driver.find_element(By.CSS_SELECTOR, '#answer').send_keys(captcha_attempt) # 위 코드에서 태그 변경
        
        login_pwd_url_1 = 'https://plus.gov.kr/login/loginIdPwdTo'
        login_pwd_url_2 = 'https://www.gov.kr/nlogin/loginByPswd'

        # 로그인 버튼 클릭
        if driver.current_url == login_pwd_url_1 or driver.current_url == login_pwd_url_2:
            try:
                driver.find_element(By.CSS_SELECTOR, ".btn.lg.btn-login").click()
            except:
                driver.find_element(By.CSS_SELECTOR, "#genLogin").click() # 위 코드에서 태그 변경
        
        for i in range(10):
            print(f'캡챠 로그인 성공 판단 중..({i+1}/10)')
            time.sleep(1)
            if driver.current_url != login_pwd_url_1 or\
                driver.current_url != login_pwd_url_2 and\
                ('로그아웃' in driver.find_element(By.CSS_SELECTOR, "div.log-after.on").text):
                print('로그인 성공!(캡챠 정답값 저장)')
                img_rename = image_path.replace('.png',f'_{captcha_attempt}.png')
                os.rename(image_path, img_rename)
                break
            

        # 로그인 후 화면 이동이 안되면 로그인 실패
        if driver.current_url == login_pwd_url_1 or driver.current_url == login_pwd_url_2:
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