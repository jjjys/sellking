from selenium.common.exceptions import SessionNotCreatedException
import re
import undetected_chromedriver as uc
import logging
logger = logging.getLogger(__name__)

def get_chrome_options():
    """ChromeOptions 설정을 반환하는 함수"""
    options = uc.ChromeOptions()
    options.add_argument('--incognito')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")  # 일반 Chrome UA
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--headless')
    options.binary_location = "/usr/bin/google-chrome"  # Docker에서 Chrome 경로
    
    return options

def initialize_driver(version_main=None):
    """Chrome 드라이버를 초기화하는 함수"""
    options = get_chrome_options()
    return uc.Chrome(options=options, version_main=version_main)


def driver_call():
    """Chrome 드라이버, 웹브라우저 버전 오류 제거 함수"""
    try:
        # 처음 시도: version_main 없이 드라이버 생성
        driver = initialize_driver()
    except SessionNotCreatedException as e:
        # 에러 메시지에서 현재 Chrome 브라우저 버전 추출
        match = re.search(r'Current browser version is (\d+)', str(e))
        if match:
            current_version = int(match.group(1))
            logger.info(f"Detected current Chrome browser version: {current_version}")
            logger.info(f"Retrying with version_main={current_version}...")
            # 현재 브라우저 버전에 맞는 드라이버로 재시도
            driver = initialize_driver(version_main=current_version)
        else:
            # 버전 정보를 추출할 수 없는 경우 예외를 다시 던짐
            raise
    return driver 

if __name__ == '__main__': 
    #driver = initialize_driver()
    driver = driver_call()

    pass
    driver.quit()