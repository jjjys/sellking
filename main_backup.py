import time, os, re, json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import SessionNotCreatedException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from openai import OpenAI

import pandas as pd
from utils.driver_call import driver_call
from utils.login import login_gov24


def openai_api(dong=None, num=None, gov24_dong_num=None, dong_or_num=None):
    '''
    설명:
    입력:동&호수 데이터, 정부24 동 혹은 호수 선택 리스트
    출력:정부24 동 혹은 호수 값 중 1개
    '''
    # 사전 작업
    load_dotenv()  # .env 읽기
    #OPENAI_API_KEY_TMP = os.getenv("OPENAI_API_KEY_TMP")
    #OPENAI_API_KEY_PRG = os.getenv("OPENAI_API_KEY_PRG")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key = OPENAI_API_KEY)

    # 프롬프트 작성
    prompt = f'''
당신은 대한민국 부동산에서 제공된 동(dong)과 호수(ho) 정보를 바탕으로 **주어진 선택지에서 가장 알맞은 단일 동 정보 또는 단일 호수 정보, 혹은 동과 호수를 조합한 정보를 반드시 선택해야 합니다.** 아래 내용을 참고하여 답변해 주세요.

# 동 정보  
{dong}  

# 호수 정보  
{num}  

# {dong_or_num} 선택지  
{gov24_dong_num}  

# 답변 형식  
{{
    "정답": "(선택지 중 택1)",
    "신뢰도": "(높음/중간/낮음)",
    "추론이유": "(선택지를 정답으로 선택한 이유)"
}}

# 지침
- 주어진 동과 호수 정보를 **종합적으로 판단**하여 선택지와 비교합니다.
- 동, 호수 선택지 중 동 정보만 있는 경우, 호수 정보만 있는 경우, 또는 동과 호수 정보가 모두 있는 경우를 모두 고려하여 가장 적합한 선택지를 선택합니다.
- **정확히 일치하는 경우**: 동과 호수 정보가 선택지와 **정확히 일치**하는 경우 해당 선택지를 선택합니다. (예: 입력 '101동', '101호' -> 선택지 '101동 101호')
- **가장 유사한 선택지**: 정확히 일치하는 선택지가 없을 경우, **주어진 선택지 중에서 가장 유사한 하나를 반드시 선택합니다.**
    - **유사성 판단 기준**:
        - **동과 호수 모두 포함된 선택지**: 입력된 동과 호수 정보가 모두 포함된 선택지를 최우선으로 고려합니다.
        - **동만 포함된 선택지**: 입력된 동 정보와 일치하는 동 선택지를 고려합니다.
        - **호수만 포함된 선택지**: 입력된 호수 정보와 일치하는 호수 선택지를 고려합니다.
        - 호수 번호의 숫자가 1~5 이내로 차이나는 경우를 "약간 다름"으로 간주합니다. (예: 101호와 102호, 101호와 105호)
- **신뢰도**는 선택한 답변의 정확성에 대한 확신을 나타내며, 다음과 같이 설정합니다:
    - **높음**: 동과 호수 정보가 선택지와 정확히 일치하거나, 단일 정보(동 또는 호수)가 정확히 일치하여 명확한 경우
    - **중간**: 동 또는 호수 중 하나는 일치하지만 다른 하나가 약간 다르거나, 선택지가 동 또는 호수 중 한 가지 정보만 포함하지만 일치하는 경우
    - **낮음**: 동과 호수 정보가 선택지와 크게 다르더라도, **가장 유사하다고 판단되는 선택지를 선택합니다.** (이 경우에도 신뢰도는 낮음으로 설정)
- 동 또는 호수 정보가 제공되지 않아 판단이 불가능한 경우에도 **가장 유사하다고 판단되는 선택지를 선택합니다.**
'''

    # api 호출
    completion01 = client.chat.completions.create(
    model="gpt-4o-mini",
    store=True,
    messages=[
        {"role": "user", "content": prompt}
    ]
    )
    print(' ============= openai api result ============= ')
    #print(f'input:{prompt}\n')
    print(f'output:{completion01.choices[0].message.content}\n')

    result = completion01.choices[0].message.content
    try:
        result = json.loads(result)
        if isinstance(result, dict):
            return result
        else:
            print(f'ai 응답이 json 형태가 아닙니다.')
            return False
    except:
        print('ai 응답 json형태 미일치 오류')
        result = {
            "정답": "ai 응답 json형태 미일치 오류",
            "신뢰도": "",
            "추론이유": ""
        }
        return result
    

def close_other_windows(driver=None):
    # 현재 윈도우 핸들 저장
    current_handle = driver.current_window_handle
    # 열려 있는 모든 핸들 가져오기
    all_handles = driver.window_handles
    
    for handle in all_handles:
        if handle != current_handle:
            driver.switch_to.window(handle)
            driver.close()
    
    # 다시 현재 핸들로 전환
    driver.switch_to.window(current_handle)
    
def check_alert(driver=None):
    try:
        # 경고창 확인 시도
        alert = driver.switch_to.alert
        print("경고창이 존재합니다: ", alert.text)
        return True
    except NoAlertPresentException:
        print("경고창이 없습니다.")
        return False
    
def building_register_issuance_settings(driver=None):
    '''
    건축물대장 발급 전 세팅.
    1.발급/열람
    2.집합건물
    3.전유부
    '''
    
    # 건축물대장 발급/열람 페이지 이동
    #'발급 사이트로 바로 이동 불가 driver.get('https://www.gov.kr/mw/EgovPageLink.do?link=minwon/AA040_std_form')
    if driver.current_url != 'https://www.gov.kr/mw/EgovPageLink.do?link=minwon/AA040_std_form':
        try:
            driver.get('https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=15000000098&HighCtgCD=A02004002&tp_seq=01&Mcode=10205')
            issue_button = WebDriverWait(driver, timeout=T_DEFAULT).until(
                EC.element_to_be_clickable((By.LINK_TEXT, '발급하기'))
            )
            issue_button.click()

            # 사이트 업데이트로 추가. 로그인 성공 했음에도 로그인 인식 안되는 현상
            try:
                driver.find_element(By.LINK_TEXT, '회원 신청하기').click()
            except:
                pass
        except:
            print('발급 페이지 이동 에러')
            raise

    # 발급/열람 선택
    for _ in range(0,3): #최대 3번 시도
        issue_open_sate = WebDriverWait(driver, timeout=T_DEFAULT).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'li.active.visible'))
        )
        if not(issue_open_sate.text == '건축물대장(열람)'):
            print('현재 상태:발급')
            print('발급 -> 열람 전환 중...')
            WebDriverWait(driver, timeout=T_DEFAULT).until(
                EC.element_to_be_clickable((By.LINK_TEXT, '건축물대장(열람)'))
            ).click()
        else:
            print('현재 상태:열람')
            break

    # 검색 세팅(뷰포트 화면에 보이도록 설정)
    search_element = WebDriverWait(driver, timeout=T_DEFAULT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#주소검색'))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", search_element)
    time.sleep(2)

    # 집합건물, 전유부 선택(다른 선택 옵션)
    '''
    set_building = WebDriverWait(driver, timeout=T_DEFAULT).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '#main > div:nth-child(1) > div:nth-child(3) > div > div:nth-child(2)'))
    )
    junyuebu = WebDriverWait(driver, timeout=T_DEFAULT).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '#dis_2 > div > div:nth-child(3) > label'))
    )
    '''
    set_building = driver.find_element(By.CSS_SELECTOR, '#main > div:nth-child(1) > div:nth-child(3) > div > div:nth-child(2)')
    junyuebu = driver.find_element(By.CSS_SELECTOR, '#dis_2 > div > div:nth-child(3) > label')

    if '집합(아파트,연립주택 등)' == set_building.text:
        print('집합(아파트,연립주택 등) 선택')
        set_building.click()

    if '전유부' == junyuebu.text:
        junyuebu.click()
        print('전유부 선택')

    if True: # 열람,집합, 전유부 조건 시
        return True
    else:
        return False

def search_address(driver=None, address='주소'):
    '''
    desc:주소창 선택하기 팝업에서 입력받은 주소를 선택
    return: True/False, false_msg
    '''
    false_msg = ''
    # 현재 드라이버 핸들 저장 
    cur_drv_hnd = driver.current_window_handle # 안정화 작업
    new_drv_hnd = None # 새창 핸들 초기화 -> title로 찾기
    
    # 주소 검색 버튼 클릭으로 새 창 띄우기
    search_element = WebDriverWait(driver, timeout=T_DEFAULT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#주소검색'))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", search_element)
    search_element.click()

    # 새 창(주소검색창)으로 이동
    for i in range(0,5):
        if len(driver.window_handles) > 1:
            # 안정성 고려: and driver.title=='주소검색'
            print("새 창(주소) 확인!!")
            break
        print(f'새 창(주소) 탐색 중..({i+1}/5초)')
        time.sleep(1)
    driver.switch_to.window(driver.window_handles[1]) # 새 창 이동    
    new_drv_hnd = driver.current_window_handle

    # 주소값 입력
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, '#txtRoad').clear()
    driver.find_element(By.CSS_SELECTOR, '#txtRoad').send_keys(address) # address로 변경
    driver.find_element(By.CSS_SELECTOR, '#txtRoad').send_keys(Keys.ENTER)

    # 검색 결과 확인
    try:
        address_list = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'address-result-list'))
        ).find_elements(By.CSS_SELECTOR, ':scope > a')
    except Exception as e:
        false_msg = "주소 검색 결과 확인 불가"
        print(f'검색어:{address}')
        print(''' - 검색 결과 확인 불가.
              검색 결과가 없는 경우: asdf(이상한 값 입력)
              검색창의 입력값이 없는 경우: (공란)
              검색 범위가 넓은 경우: 서웉특별시''')
        driver.close()
        driver.switch_to.window(driver.window_handles[0]) # 기존 창으로 이동/finally 고려
        return False, false_msg
    if len(address_list) == 1: # 주소가 1개 나온 경우
        address_list[0].click()
    elif len(address_list) > 1: # 주소가 2개 이상 나온 경우
        '''
        예)
        "성미산로 20" 검색 시
        성미산로 20
        성미산로 20-1
        성미산로 200
        ... 결과가 나옴
        이 중 택해야하는게 필요한 경우 로직 추가
        '''
        address_list[0].click() # 가장 상위에 있는 주소 선택

    # 처리 행정기관 선택
    elem1 = WebDriverWait(driver, timeout=T_DEFAULT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '.address-result-list.land a:nth-child(2)'))
    )
    time.sleep(1)
    elem1.click()
    
    time.sleep(1)
    if len(driver.window_handles) > 1:
        false_msg = '행정처리기관 추가 선택 필요'
        print(false_msg)
        driver.close()
        return False, false_msg
    
    driver.switch_to.window(driver.window_handles[0]) # 기존 창으로 이동
    time.sleep(1)
    return True, false_msg

def search_dong(driver=None, dong=None, num=None):
    '''
    desc:동 선책. 2개 이상일 경우 LLM 이용
    parm:drv, dong
    return: True/False, list
    '''
    
    # 주소 검색 버튼 클릭으로 새 창 띄우기
    search_element = WebDriverWait(driver, timeout=T_DEFAULT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#동명검색'))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", search_element)
    search_element.click()
    

    # 새 창(동 선택창)으로 이동
    for i in range(0,10):
        if len(driver.window_handles) > 1:
            print("새 창(동 선택 창) 확인!!")
            break
        elif (i > 4) and check_alert(driver=driver):
            '''
            n초 대기. 늦게 새 창 나오는 것 고려.
            # 동 검색 결과 안나오는 경우
            WebDriverWait(driver, 10).until(EC.alert_is_present()).text
            WebDriverWait(driver, 10).until(EC.alert_is_present()).dismiss()
            return False, None
            '''
            print(f'경고창 확인됨.\n{WebDriverWait(driver, 10).until(EC.alert_is_present()).text}')
            WebDriverWait(driver, 10).until(EC.alert_is_present()).dismiss()
            driver.switch_to.window(driver.window_handles[0]) # 기존 창으로 이동/finally 고려
            res = {
                "정답": "동 검색 결과 없음",
                "신뢰도": "",
                "추론이유": ""
            }
            return None, res
        print(f'새 창(동) 탐색 중..({i+1}/5초)')
        time.sleep(1)
    driver.switch_to.window(driver.window_handles[1]) # 새 창 이동    
    new_drv_hnd = driver.current_window_handle

    # 동 검색 결과 확인 
    time.sleep(1)
    dong_list = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".tbl_list.border"))
    ).find_elements(By.CSS_SELECTOR, ' table tbody tr a')
    print(f'동 출력 결과 개수: {len(dong_list)}개')
    dong_list_text = ''
    if len(dong_list) < 2: # 동수가 1개 나온 경우
        dong_list_text = dong_list[0].text
        #print(f'{dong_list_text}')
        dong_list[0].click()
        # 드라이버 핸들 돌려 놓기
        driver.switch_to.window(driver.window_handles[0])
        res = {
            "정답": dong_list_text,
            "신뢰도": "100%",
            "추론이유": "선택지가 1개"
        }
        time.sleep(1)
        return dong_list_text, res
    else: # 동수가  2개 이상 나온 경우
        for idx, itm in enumerate(dong_list):
            #print(f'{itm.text}')
            dong_list_text = f'{dong_list_text}\n{itm.text}'
        #print(dong_list_text)
        ai_res = openai_api(dong=dong, num=num, gov24_dong_num=dong_list_text, dong_or_num='동')
        target_dong = ai_res['정답'].strip()
        if ai_res['정답'] == "ai 응답 json형태 미일치 오류":
            # 드라이버 핸들 돌려 놓기
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
            #return dong_list_text[1:].split('\n'), target_dong
            return dong_list_text, ai_res
        print(f'동 입력값:{dong}')
        print(f'동 예측값:{target_dong}')
        # 예측값 클릭
        for idx, itm in enumerate(dong_list):
            if target_dong == itm.text.strip():
                print("예측값과 일치하는 항목 클릭")
                dong_list[idx].click()
                time.sleep(1)
                break
        if len(driver.window_handles) > 1:
            print('ai 응답 오류:정확히 일치하는 값을 응답하지 않음')
            print('선택지 클릭 불가')
            ai_res['정답'] = f'ai 응답 오류:정확히 일치하는 값을 응답하지 않음\n{ai_res["정답"]}'
            # 드라이버 핸들 돌려 놓기
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
            return dong_list_text[1:], ai_res
        
        # 드라이버 핸들 돌려 놓기
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)
        #return dong_list_text[1:].split('\n'), target_dong
        return dong_list_text[1:], ai_res

def search_num(driver=None, dong=None, num=None): 
    '''
    desc:호수 선책. 2개 이상일 경우 LLM 이용
    parm:drv, num
    return: True/False, list
    '''
    
    # 주소 검색 버튼 클릭으로 새 창 띄우기
    search_element = WebDriverWait(driver, timeout=T_DEFAULT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#호명검색'))
    )
    search_element.click()

    # 새 창(호수 선택 창)으로 이동
    for i in range(0,5):
        if len(driver.window_handles) > 1:
            print("새 창(호수 선택 창) 확인!!")
            break
        print(f'새 창(호수 선택 창) 탐색 중..({i+1}/5초)')
        time.sleep(1)
    driver.switch_to.window(driver.window_handles[1]) # 새 창 이동    
    new_drv_hnd = driver.current_window_handle

    # 호수 검색 결과 확인 
    time.sleep(1)
    num_list = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".tbl_list.border"))
    ).find_elements(By.CSS_SELECTOR, ' table tbody tr a')
    print(f'호수 출력 결과 개수: {len(num_list)}개')
    num_list_text = ''
    if len(num_list) < 2: # 호수가 1개 나온 경우
        num_list_text = num_list[0].text
        #print(f'{num_list_text}')
        num_list[0].click()
        # 드라이버 핸들 돌려 놓기
        driver.switch_to.window(driver.window_handles[0])
        res = {
            "정답": num_list_text,
            "신뢰도": "100%",
            "추론이유": "선택지가 1개"
        }
        time.sleep(1)
        return num_list_text, res
    else: # 호수가  2개 이상 나온 경우
        for idx, itm in enumerate(num_list):
            #print(f'{itm.text}')
            num_list_text = f'{num_list_text}\n{itm.text}'
        #print(num_list_text)
        ai_res = openai_api(dong=dong, num=num, gov24_dong_num=num_list_text, dong_or_num='호수')
        target_num = ai_res['정답'].strip()
        if ai_res['정답'] == "ai 응답 json형태 미일치 오류":
            # 드라이버 핸들 돌려 놓기
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
            #return dong_list_text[1:].split('\n'), target_dong
            return num_list_text, ai_res
        print(f'호수 입력값:{num}')
        print(f'호수 예측값:{target_num}')
        # 예측값 클릭
        for idx, itm in enumerate(num_list):
            if target_num == itm.text.strip():
                print("예측값과 일치하는 항목 클릭")
                num_list[idx].click()
                time.sleep(1)
                break
        if len(driver.window_handles) > 1:
            print('ai 응답 오류:정확히 일치하는 값을 응답하지 않음')
            print('선택지 클릭 불가')
            ai_res['정답'] = f'ai 응답 오류:정확히 일치하는 값을 응답하지 않음\n{ai_res["정답"]}'
            # 드라이버 핸들 돌려 놓기
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
            return num_list_text[1:], ai_res
    
        # 드라이버 핸들 돌려 놓기
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)
        return num_list_text[1:], ai_res
    

def main():
    global T_DEFAULT
    T_DEFAULT = 10
    load_dotenv()  # .env 읽기
    GOV24_ID = os.getenv("GOV24_ID")
    GOV24_PW = os.getenv("GOV24_PW")

    # 매도왕 수집 데이터 읽기
    file_path = r"C:\Users\User\Desktop\sellking\data\adress_info.xlsx"
    df = pd.read_excel(file_path, engine="openpyxl")
    output_file_path = r"C:\Users\User\Desktop\sellking\data\adress_info_updated.xlsx"

    # 새로운 열을 추가하기 위해 DataFrame에 빈 열 생성
    df['gov24_dong_list'] = ''
    df['gov24_dong_tratget'] = ''
    df['gov24_dong_신뢰도'] = ''
    df['gov24_dong_추론이유'] = ''
    df['gov24_num_list'] = ''
    df['gov24_num_tratget'] = ''
    df['gov24_num_신뢰도'] = ''
    df['gov24_num_추론이유'] = ''

    # 웹사이트 접속 및 로그인
    driver = driver_call()
    login_gov24(driver=driver,
                gov24_ID=GOV24_ID,
                gov24_PW=GOV24_PW)
    
    # 각 행 반복
    for index, row in df.iloc[:].iterrows():
        # 각 행의 데이터 접근 (열 이름으로 접근 가능)
        address = row[df.columns[0]]  # 주소
        dong = row[df.columns[1]]     # 동
        num = row[df.columns[2]]      # 호수

        # 주소, 동, 호수 전체 값 확인
        print('\n'*3)
        print('='*20)
        print('='*20)
        print(f"행 {index + 1}:")
        print(f"address:{address}")
        print(f"dong:{dong}")
        print(f"num:{num}")
        print("=" * 20,'\n') 

        if '인천광역시' in address or '경기도 평택시' in address: # 경기도 평택시 송일로5번길 37
            print(f"행 {index + 1}: 인천광역시 포함 주소입니다. 건너뜁니다.")
            continue  # pass 대신 continue를 사용하여 다음 행으로 이동
        
        # 건축물대장 열람페이지 이동 및 세팅
        if index%10==0: # 로그인 연장 팝업 문제로 페이지 임시 이동
            time.sleep(1)
            driver.get('https://www.gov.kr/')
        building_register_issuance_settings(driver=driver)
        
        
        

        if not(search_address(driver=driver, address=address)):
            print('주소 검색결과 확인되지 않음.')
            error_msg = '주소 검색결과 확인되지 않음.'
            gov24_dong_list = error_msg
            df.at[index, 'gov24_dong_list'] = gov24_dong_list
            df.to_excel(output_file_path, index=False, engine="openpyxl")
            continue
        try:
            gov24_dong_list, ai_res = search_dong(driver=driver, dong=dong, num=num)
            gov24_dong_tratget = ai_res['정답']
            gov24_dong_confidence = ai_res['신뢰도']
            gov24_dong_reasoning = ai_res['추론이유']
            
            gov24_num_list, ai_res = search_num(driver=driver, dong=dong, num=num)
            gov24_num_tratget = ai_res['정답']
            gov24_num_confidence = ai_res['신뢰도']
            gov24_num_reasoning = ai_res['추론이유']

        except:
            print('동 검색 결과는 경우, 호수 검색x 다음 진행')
            continue
            print('예외로 안들어가겎므!')
            error_msg = '동 검색 결과가 없거나 ai 응답 에러로 확인 요망'
            gov24_dong_list = error_msg
            gov24_dong_tratget = error_msg
            gov24_dong_confidence = error_msg
            gov24_dong_reasoning = error_msg
            
            gov24_num_list = error_msg
            gov24_num_tratget = error_msg
            gov24_num_confidence = error_msg
            gov24_num_reasoning = error_msg

        df.at[index, 'gov24_dong_list'] = gov24_dong_list
        df.at[index, 'gov24_dong_tratget'] = gov24_dong_tratget
        df.at[index, 'gov24_dong_신뢰도'] = gov24_dong_confidence
        df.at[index, 'gov24_dong_추론이유'] = gov24_dong_reasoning

        df.at[index, 'gov24_num_list'] = gov24_num_list
        df.at[index, 'gov24_num_tratget'] = gov24_num_tratget
        df.at[index, 'gov24_num_신뢰도'] = gov24_num_confidence
        df.at[index, 'gov24_num_추론이유'] = gov24_num_reasoning
        df.to_excel(output_file_path, index=False, engine="openpyxl")

    # 수정된 DataFrame을 엑셀 파일로 저장
    #output_file_path = r"C:\Users\User\Desktop\sellking\data\adress_info_updated.xlsx"
    #df.to_excel(output_file_path, index=False, engine="openpyxl")
    print(f"수정된 파일이 {output_file_path}에 저장되었습니다.")


''' # 아래는 테스트 부분
    for i in range(0,10):
        # 주소 검색
        #search_address(driver=driver, address='서울특별시 동대문구 장한로28가길 17')
        search_address(driver=driver, address='경기도 수원시 권선구 덕영대로1190번길 100')
        #search_address(driver=driver, address='성미산로20')
        # 동 검색
        if search_dong(driver=driver, dong='717동 1501호'):
            # 호수 검색
            search_num(driver=driver, num='717동 1501호')

    
search_address(driver=driver, address='경기도 남양주시 별내1로 6')
search_dong(driver=driver, dong='상가1층 137호'):
search_num(driver=driver, num='상가1층 137호')
# 동
힐스테이트 별내역 101동(숙박시설(생활숙박시설) : 25577.4216)
힐스테이트 별내역 102동(숙박시설(생활숙박시설) : 31496.3486)	
힐스테이트 별내역 103동(숙박시설(생활숙박시설) : 27088.4654)	
*힐스테이트 별내역 판매시설동(판매시설 : 6533.8245)
# 호수
137호

search_address(driver=driver, address='서울특별시 구로구 디지털로26길 43')
search_dong(driver=driver, dong='L 7층 전체')
search_num(driver=driver, num='L 7층 전체')
# 동
1개
# 호수
L701

search_address(driver=driver, address='서울특별시 구로구 가마산로 97')
search_dong(driver=driver, dong='현대로얄아파트 4층')
search_num(driver=driver, num='현대로얄아파트 4층')
# 동
1개
# 호수
4층 10호


search_address(driver=driver, address='경기도 의정부시 민락로 195')
search_dong(driver=driver, dong='H동 302')
search_num(driver=driver, num='H동 302')
# 동
1개
# 호수
106

search_address(driver=driver, address='서울특별시 금천구 가산디지털2로 169-23')
search_dong(driver=driver, dong='기숙사 302')
search_num(driver=driver, num='기숙사 302')
# 동
기숙사
# 호수
302

    '''

    # 발급하고 저장하기(html, pdf)

    #driver.quit()

if __name__ == '__main__':
    main()
