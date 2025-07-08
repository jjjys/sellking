'''

1.웹사이트 로그인

2.ai 새 창으로 띄워서 질의응답
로그인 캡챠(모델 개발x) & 동호수 검색 시 이용

3.메인
3.1.로그인
3.2.엑셀 읽기
3.3.새 창에서 처리 * 최대3번
3.4.엑셀 데이터 기록
3.5.건축물대장 있는 경우 -> html 파일로 저장.


'''

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import SessionNotCreatedException
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys

import pandas as pd
from utils.driver_call import driver_call



if __name__ == '__main__': 

    driver = driver_call()


    


    # Excel 파일 읽기

    # 첫 번째 행(헤더)을 제외하고 각 행 반복
    for index, row in df.iloc[1:].iterrows():
        # 각 행의 데이터 접근 (열 이름으로 접근 가능)
        print('='*20)
        print(f"행 {index + 1}:")
        address = row[df.columns[0]] # 주소

        # '동' text 미포함 시 끝에 '동'추가
        dong = row[df.columns[1]] # 동
        # '호' text 미포함 시 끝에 '호'추가
        num = row[df.columns[2]] # 호수

        print(f"address:{address}")
        print(f"dong:{dong}")
        print(f"num:{num}")
        print("-" * 20)  # 구분선
        



'''
driver.window_handles
driver.current_window_handle
driver.switch_to.window(driver.window_handles[0])
'''