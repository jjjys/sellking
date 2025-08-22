import time, os, json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from openai import OpenAI

import pandas as pd
from utils.driver_call import driver_call
from utils.login import login_gov24, login_status_gov24

import logging
logger = logging.getLogger(__name__)


def debug_check(driver):
    """
    디버깅을 위해 현재 웹 페이지의 스크린샷과 HTML 소스를 저장하는 함수.
    """
    driver.save_screenshot("/app/debug_screenshot.png")
    with open("/app/page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

def openai_api(dong=None, num=None, gov24_dong_num=None, dong_or_num=None):
    """
    OpenAI API를 사용하여 입력된 동/호수 정보와 정부24 선택지 중 가장 적합한 값을 선택하는 함수.
    
    :param dong: 입력된 동 정보 (예: '101동')
    :param num: 입력된 호수 정보 (예: '101호')
    :param gov24_dong_num: 정부24 사이트에서 제공된 동/호수 선택지 리스트
    :param dong_or_num: 선택지가 동인지 호수인지 구분하는 문자열 ('동' 또는 '호수')
    :return: JSON 형식의 결과 (정답, 신뢰도, 추론이유 포함) 또는 에러 시 False
    """
    # 사전 작업
    load_dotenv()  # .env 읽기
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
    model="gpt-4.1",
    store=True,
    messages=[
        {"role": "user", "content": prompt}
    ]
    )
    logger.info(' ============= openai api result ============= ')
    #logger.info(f'input:{prompt}\n')
    logger.info(f'output:{completion01.choices[0].message.content}\n')

    result = completion01.choices[0].message.content

    # ai 출력 결과 검증
    try:
        result = json.loads(result)
        if isinstance(result, dict):
            return result
        else:
            logger.info(f'ai 응답이 json 형태가 아닙니다.')
            return False
    except:
        logger.info('ai 응답 json형태 미일치 오류')
        result = {
            "정답": "[ai 응답] json형태 미일치 오류",
            "신뢰도": "",
            "추론이유": ""
        }
        return result

def check_alert(driver=None):
    """
    Selenium 드라이버에서 경고창(alert)이 있는지 확인하고, 있으면 텍스트를 반환하는 함수.
    
    :param driver: Selenium 웹 드라이버 인스턴스
    :return: 경고창 텍스트 (존재 시), 없으면 False
    """
    try:
        # 경고창 확인 시도
        alert = driver.switch_to.alert
        logger.info("경고창이 확인됨.\n경고창 내용:", alert.text)
        return alert.text
    except NoAlertPresentException:
        logger.info("경고창이 없습니다.")
        return False

def building_register_issuance_settings(driver=None):
    """
    건축물대장 발급을 위한 사전 페이지 세팅 함수 (발급/열람, 집합건물, 전유부 선택).
    
    :param driver: Selenium 웹 드라이버 인스턴스
    :return: 세팅 성공 시 True, 실패 시 False (예외 발생 시)
    """
    try:
        # 로그인 상태 체크 후 필요 시 로그인
        if not login_status_gov24(driver):
            load_dotenv()  # .env 읽기
            GOV24_ID = os.getenv("GOV24_ID")
            GOV24_PW = os.getenv("GOV24_PW")
            login_gov24(driver=driver,
                gov24_ID=GOV24_ID,
                gov24_PW=GOV24_PW)

        # Navigate to issuance page
        driver.get('https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=15000000098&HighCtgCD=A02004002&tp_seq=01&Mcode=10205')
        time.sleep(2)  # Allow page to load
        logger.info('발급 페이지 이동 완료')

        # Click "발급하기" button
        try:
            issue_button = WebDriverWait(driver, timeout=10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, '발급하기'))
            )
            driver.execute_script("arguments[0].click();", issue_button)  # JavaScript click to avoid interactability issues
            logger.info('발급하기 버튼 클릭')
        except Exception as e:
            logger.info(f"Error clicking '발급하기': {str(e)}")
            raise

        # 간혹 나오는 화면 처리.
        try:
            issue_button = WebDriverWait(driver, timeout=10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, '회원 신청하기'))
            )
            driver.execute_script("arguments[0].click();", issue_button)
            logger.info('회원 신청하기 버튼 클릭')
        except Exception as e:
            # 간혹 나오는 화면이 없는 경우
            #logger.info(f"Error clicking '회원 신청하기 버튼': {str(e)}")
            pass

        # Select "건축물대장(열람)"
        for _ in range(10):
            try:
                issue_open_state = WebDriverWait(driver, timeout=10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'li.active.visible'))
                )
                if issue_open_state.text != '건축물대장(열람)':
                    logger.info(f'건축물대장(열람)으로 전환 중...({_+1}/10)')
                    WebDriverWait(driver, timeout=10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".mw_sel_list li.visible"))
                    )
                    chk_list = driver.find_elements(By.CSS_SELECTOR, ".mw_sel_list li.visible")
                    for idx, elem in enumerate(chk_list):
                        if elem.text=='건축물대장(열람)':
                            elem.click()
                            break
                    time.sleep(1)
                else:
                    logger.info('Already in 열람 state')
                    break

            except Exception as e:
                logger.info(f"Error selecting 열람: {str(e)}")
                raise

        # Scroll to address search button
        try:
            search_element = WebDriverWait(driver, timeout=10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#주소검색'))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", search_element)
            time.sleep(1)
        except Exception as e:
            logger.info(f"Error finding address search button: {str(e)}")
            raise

        # Select 집합건물 and 전유부
        set_building = driver.find_element(By.CSS_SELECTOR, '#main > div:nth-child(1) > div:nth-child(3) > div > div:nth-child(2)')
        junyuebu = driver.find_element(By.CSS_SELECTOR, '#dis_2 > div > div:nth-child(3) > label')
        try:
            if '집합(아파트,연립주택 등)' in set_building.text:
                logger.info('Selecting 집합건물...')
                set_building.click()
                #driver.execute_script("arguments[0].click();", set_building)
            else:
                logger.info('집합건물 not found in expected element')

            if '전유부' in junyuebu.text:
                logger.info('Selecting 전유부...')
                junyuebu.click()
                #driver.execute_script("arguments[0].click();", junyuebu)
            else:
                logger.info('전유부 not found in expected element')
        except Exception as e:
            logger.info(f"Error selecting 집합건물 or 전유부: {str(e)}")
            raise

        return True
    except Exception as e:
        logger.info(f"Error in building_register_issuance_settings: {str(e)}")
        return False
    
def search_address(driver=None, address='주소'):
    """
    정부24 사이트에서 주소를 검색하고 결과를 반환하는 함수.
    
    :param driver: Selenium 웹 드라이버 인스턴스
    :param address: 검색할 주소 문자열
    :return: 검색 성공 여부와 메시지를 포함한 딕셔너리
    """
    fail_msg = ''
    
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
            logger.info("새 창(주소) 확인되었습니다.")
            break
        logger.info(f'새 창(주소) 탐색 중..({i+1}/5초)')
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
        fail_msg = "[주소]주소 검색 결과 확인 불가"
        logger.info(f'검색어:{address}')
        logger.info(''' - 검색 결과 확인 불가.
              검색 결과가 없는 경우: asdf(이상한 값 입력)
              검색창의 입력값이 없는 경우: (공란)
              검색 범위가 넓은 경우: 서웉특별시''')
        driver.close()
        driver.switch_to.window(driver.window_handles[0]) # 기존 창으로 이동/finally 고려
        return {"success": False, "message": fail_msg}
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
        fail_msg = '[주소]행정처리기관 추가 선택 필요'
        logger.info(fail_msg)
        driver.close()
        driver.switch_to.window(driver.window_handles[0]) # 기존 창으로 이동
        return {"success": False, "message": fail_msg}
    
    driver.switch_to.window(driver.window_handles[0]) # 기존 창으로 이동(인터넷 환경에서 안되는 경우 있어서 안정적으로 추가)
    time.sleep(1)
    return {"success": True, "message": fail_msg}

def search_dong(driver=None, dong=None, num=None):
    """
    정부24 사이트에서 동 정보를 검색하고 AI로 적합한 동을 선택하는 함수.
    
    :param driver: Selenium 웹 드라이버 인스턴스
    :param dong: 검색할 동 정보
    :param num: 호수 정보 (AI 판단에 사용)
    :return: 동 리스트, AI 선택 결과, 성공 여부를 포함한 딕셔너리
    """
    
    # 동 검색 버튼 클릭으로 새 창 띄우기
    search_element = WebDriverWait(driver, timeout=T_DEFAULT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#동명검색'))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", search_element)
    search_element.click()
    
    # 새 창(동 선택창)으로 이동
    for i in range(0, 6):
        alert_msg = check_alert(driver=driver)
        if len(driver.window_handles) > 1:
            logger.info("새 창(동 선택 창) 확인되었습니다.")
            driver.switch_to.window(driver.window_handles[1])  # 새 창 이동 
            break
        # 동 검색결과 없음
        elif (i > 4) or alert_msg:
            if alert_msg:
                # 경고창 닫기
                WebDriverWait(driver, 10).until(EC.alert_is_present()).dismiss()
                alert_msg = f'[동 경고창]{alert_msg}'
            else:
                alert_msg = '확인되는 동 경고창이 없습니다.'
            # 기존 창으로 이동
            driver.switch_to.window(driver.window_handles[0])
            res = {
                "정답": "",
                "신뢰도": "",
                "추론이유": ""
            }
            # 1.동 검색결과 없음(경고창 알림)
            return {
                "success": False,
                "dong_list": alert_msg,
                "selected_dong": "",
                "ai_response": res
            }
        logger.info(f'새 창(동 선택 창) 탐색 중..({i+1}/5초)')
        time.sleep(1)
       

    # 동 검색 결과 확인 
    time.sleep(1)
    dong_list = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".tbl_list.border"))
    ).find_elements(By.CSS_SELECTOR, 'table tbody tr a')
    logger.info(f'동 출력 결과 개수: {len(dong_list)}개')
    dong_1st = dong_list[0].text # 클릭 시 팝업 창 꺼지기 때문에 데이터 저장해놓고 사용.
    
    if len(dong_list) < 2:  # 동수가 1개 나온 경우
        dong_list[0].click()
        driver.switch_to.window(driver.window_handles[0])
        res = {
            "정답": dong_1st,
            "신뢰도": "100%",
            "추론이유": "선택지가 1개"
        }
        time.sleep(1)
        # 2.동 검색결과 선택지 1개
        return {
            "success": True,
            "dong_list": dong_1st,
            "selected_dong": dong_1st,
            "ai_response": res
        }
    else:  # 동수가 2개 이상 나온 경우
        dong_list_text = [itm.text.strip() for itm in dong_list]
        dong_list_text = '\n'.join(dong_list_text)
        ai_res = openai_api(dong=dong, num=num, gov24_dong_num=dong_list_text, dong_or_num='동')
        ai_res['정답'] = ai_res['정답'].strip()
        
        # ai 응답이 확률적으로 json 형태가 아닌 경우
        if ai_res['정답'] == "ai 응답 json형태 미일치 오류":
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
            #3.동 검색결과 선택지 2개 이상(AI로 예측 진행) > 3.정해진 답변 형식(json)으로 답변하지 않는 경우
            return {
                "success": False,
                "dong_list": dong_list_text,
                "selected_dong": ai_res['정답'],
                "ai_response": ai_res
            }
        
        # 입력값과 예측값 일치하는 경우 > 클릭
        for idx, itm in enumerate(dong_list):
            if ai_res['정답'] == itm.text.strip():
                logger.info("예측값과 일치하는 항목 클릭")
                dong_list[idx].click()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)
                #3.동 검색결과 선택지 2개 이상(AI로 예측 진행) > 2.동 선택지에 있는 값으로 예측하는 경우
                return {
                    "success": True,
                    "dong_list": dong_list_text,
                    "selected_dong": ai_res['정답'],
                    "ai_response": ai_res
                }
            
        logger.info(f'동 입력값:{dong}')
        logger.info(f'동 예측값:{ai_res["정답"]}')
        time.sleep(1)

        # 입력값과 예측값 일치하지 않는 경우 > ai 응답 오류
        if len(driver.window_handles) > 1:
            logger.info('ai 응답 오류: 정확히 일치하는 값을 응답하지 않음')
            logger.info('선택지 클릭 불가')
            ai_res['정답'] = f'ai 응답 오류: 정확히 일치하는 값을 응답하지 않음\n예측값:{ai_res["정답"]}'
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            #3.동 검색결과 선택지 2개 이상(AI로 예측 진행) > 1.동 선택지에 없는 값으로 예측하는 경우
            return {
                "success": False,
                "dong_list": dong_list_text,
                "selected_dong": ai_res['정답'],
                "ai_response": ai_res
            }
        
def search_num(driver=None, dong=None, num=None): 
    """
    정부24 사이트에서 호수 정보를 검색하고 AI로 적합한 호수를 선택하는 함수.
    
    :param driver: Selenium 웹 드라이버 인스턴스
    :param dong: 동 정보 (AI 판단에 사용)
    :param num: 검색할 호수 정보
    :return: 호수 리스트, AI 선택 결과, 성공 여부를 포함한 딕셔너리
    """
    
    # 호수 검색 버튼 클릭으로 새 창 띄우기
    search_element = WebDriverWait(driver, timeout=T_DEFAULT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#호명검색'))
    )
    search_element.click()

    # 새 창(호수 선택 창)으로 이동
    for i in range(0, 6):
        alert_msg = check_alert(driver=driver)
        if len(driver.window_handles) > 1:
            logger.info("새 창(호수 선택 창) 확인되었습니다.")
            driver.switch_to.window(driver.window_handles[1])  # 새 창 이동    
            break
        # 호수 검색 클릭 안되는 경우
        elif (i > 4) or alert_msg:
            if alert_msg:
                # 경고창 닫기
                WebDriverWait(driver, 10).until(EC.alert_is_present()).dismiss()
                alert_msg = f'[호수 경고창]{alert_msg}'
            else:
                alert_msg = '확인되는 호수 경고창이 없습니다.'
            # 기존 창으로 이동
            driver.switch_to.window(driver.window_handles[0])
            res = {
                "정답": "",
                "신뢰도": "",
                "추론이유": ""
            }
            # 1.동 검색결과 없음(경고창 알림)
            return {
                "success": False,
                "num_list": alert_msg,
                "selected_num": "",
                "ai_response": res
            }
        logger.info(f'새 창(호수 선택 창) 탐색 중..({i+1}/5초)')
        time.sleep(1)    

    # 호수 검색 결과 확인 
    time.sleep(1)
    num_list = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".tbl_list.border"))
    ).find_elements(By.CSS_SELECTOR, 'table tbody tr a')
    logger.info(f'호수 출력 결과 개수: {len(num_list)}개')
    num_1st = num_list[0].text # 클릭 시 팝업 창 꺼지기 때문에 데이터 저장해놓고 사용.
    if len(num_list) < 2:  # 호수가 1개 나온 경우
        num_list[0].click()
        driver.switch_to.window(driver.window_handles[0])
        ai_response = {
            "정답": num_1st,
            "신뢰도": "100%",
            "추론이유": "선택지가 1개"
        }
        time.sleep(1)
        return {
            "success": True,
            "num_list": num_1st,
            "selected_num": num_1st,
            "ai_response": ai_response
        }
    else:  # 호수가 2개 이상 나온 경우
        num_list_text = [itm.text for itm in num_list]
        num_list_text = '\n'.join(num_list_text)
        ai_res = openai_api(dong=dong, num=num, gov24_dong_num=num_list_text, dong_or_num='호수')
        ai_res['정답'] = ai_res['정답'].strip()

        if ai_res['정답'] == "ai 응답 json형태 미일치 오류":
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
            return {
                "success": False,
                "num_list": num_list_text,
                "selected_num": ai_res['정답'],
                "ai_response": ai_res
            }
    
        # 입력값과 예측값 일치하는 경우 > 클릭
        for idx, itm in enumerate(num_list):
            if ai_res['정답'] == itm.text.strip():
                logger.info("예측값과 일치하는 항목 클릭")
                num_list[idx].click()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)
                return {
                    "success": True,
                    "num_list": num_list_text,
                    "selected_num": ai_res['정답'],
                    "ai_response": ai_res
                }
                
        logger.info(f'호수 입력값:{num}')
        logger.info(f'호수 예측값:{ai_res["정답"]}')
        time.sleep(1)
        
        
        if len(driver.window_handles) > 1:
            logger.info('ai 응답 오류: 정확히 일치하는 값을 응답하지 않음')
            logger.info('선택지 클릭 불가')
            ai_res['정답'] = f'ai 응답 오류: 정확히 일치하는 값을 응답하지 않음\n예측값:{ai_res["정답"]}'
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
            return {
                "success": False,
                "num_list": num_list_text,
                "selected_num": ai_res['정답'],
                "ai_response": ai_res
            }

def get_building_register(driver=None, address='주소', dong=None, num=None):
    """
    정부24 사이트에서 건축물대장을 발급하고 HTML 형식으로 반환하는 함수.
    
    :param driver: Selenium 웹 드라이버 인스턴스
    :param address: 건물 주소
    :param dong: 동 정보
    :param num: 호수 정보
    :return: 건축물대장 HTML 문자열
    """
    try:
        # 저장할 디렉토리 경로
        save_dir = os.path.join("data", "building_registers")
        os.makedirs(save_dir, exist_ok=True)  # 디렉토리가 없으면 생성

        # 신청하기 버튼 클릭
        driver.find_element(By.CSS_SELECTOR, "#btn_end").click()

        # 열람/발급 페이지 이동
        if driver.current_url != 'https://plus.gov.kr/mypage/mbrAplySrvcList':
            for _ in range(0,60):
                logger.info(f'열람/발급 페이지 이동 확인 중...({_+1}/60)초. 현재 페이지:{driver.current_url}')
                time.sleep(1)
                if 'https://plus.gov.kr/mypage/mbrAplySrvcList' in driver.current_url:
                    logger.info('열람/발급 페이지 확인되었습니다.')
                    break
        
        # 열람/발급 문서 클릭
        WebDriverWait(driver, timeout=T_DEFAULT).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="iw_container"]/div[1]/div[2]/div[5]/div[1]/div[2]/div[1]/table/tbody/tr/td[4]/span[2]/button'))
            ).click()
        

        # 새 창에서 html 전처리 작업 후 저장
        for _ in range(0,180):
            logger.info(f'열람/발급 창 확인 중...({_+1}/180)초')
            time.sleep(1)
            if len(driver.window_handles) > 1:
                logger.info(f'열람/발급 창 확인되었습니다.')
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(1)
                break
        building_register_html = driver.find_element(By.CLASS_NAME, 'minwon-preview').get_attribute('outerHTML').replace('euc-kr','UTF-8')
        building_register_html = f"<html><head></head><body>{building_register_html}</body></html>"
        building_register_html = building_register_html.replace('style="background : url(/img/confirm/bgtest04.gif)"','')

        # 파일 경로 생성
        file_path = os.path.join(save_dir, f"건축물대장_{address}_{dong}_{num}.html")

        # 파일 쓰기
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(building_register_html)
        
        # 기존 창으로 돌아가기
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        # 반환값.
        return building_register_html
    except Exception as e:
        logger.info(f"건축물대장 발급 오류: {str(e)}")
        return ""

def main():
    try:
        global T_DEFAULT
        T_DEFAULT = 10
        load_dotenv()  # .env 읽기
        GOV24_ID = os.getenv("GOV24_ID")
        GOV24_PW = os.getenv("GOV24_PW")

        # 웹사이트 접속 및 로그인
        driver = driver_call()
        login_gov24(driver=driver,
                    gov24_ID=GOV24_ID,
                    gov24_PW=GOV24_PW)

        #########################################################
        ### [ 작업을 위한 데이터 읽기 ] ############################
        #########################################################
        # 매도왕 수집 데이터 읽기
        file_path = r"data\adress_info.xlsx"
        df = pd.read_excel(file_path, engine="openpyxl")
        output_file_path = r"data\adress_info_updated.xlsx"

        # 새로운 열을 추가하기 위해 DataFrame에 빈 열 생성
        required_columns = ['gov24_dong_list', 'gov24_dong_tratget', 'gov24_dong_신뢰도', 'gov24_dong_추론이유',
                            'gov24_num_list','gov24_num_tratget','gov24_num_신뢰도','gov24_num_추론이유']
        # 각 열이 DataFrame에 없는 경우에만 추가
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''

        # 각 행 반복
        for index, row in df.iloc[:].iterrows():
            # 각 행의 데이터 접근 (열 이름으로 접근 가능)
            address = row[df.columns[0]]  # 주소
            dong = row[df.columns[1]]     # 동
            num = row[df.columns[2]]      # 호수

            # 주소, 동, 호수 전체 값 확인
            logger.info('\n'*3)
            logger.info('='*20)
            logger.info('='*20)
            logger.info(f"행 {index + 1}:")
            logger.info(f"address:{address}")
            logger.info(f"dong:{dong}")
            logger.info(f"num:{num}")
            logger.info("=" * 20,'\n') 

            # if '인천광역시' in address or '경기도 평택시' in address: # 경기도 평택시 송일로5번길 37
            #     logger.info(f"행 {index + 1}: 인천광역시 포함 주소입니다. 건너뜁니다.")
            #     continue  # pass 대신 continue를 사용하여 다음 행으로 이동
            
            
            #########################################################
            ### [ 작업 시작 ] ########################################
            #########################################################
        
            # 건축물대장 열람페이지 이동 및 세팅
            if index%10==0: # 로그인 연장 팝업 문제로 페이지 임시 이동
                time.sleep(1)
                driver.get('https://www.gov.kr/')
            building_register_issuance_settings(driver=driver)
                    
            # 주소 검색
            result_address = search_address(driver=driver, address=address)
            if result_address['success'] == False:
                logger.info(result_address['message'])
                df.at[index, 'gov24_dong_list'] = result_address['message']
                df.to_excel(output_file_path, index=False, engine="openpyxl")
                continue

            # 동 검색
            result_dong = search_dong(driver=driver, dong=dong, num=num)
            df.at[index, 'gov24_dong_list'] = result_dong["dong_list"]
            df.at[index, 'gov24_dong_tratget'] = result_dong["ai_response"]['정답']
            df.at[index, 'gov24_dong_신뢰도'] = result_dong["ai_response"]['신뢰도']
            df.at[index, 'gov24_dong_추론이유'] = result_dong["ai_response"]['추론이유']

            # 호수 검색    
            if result_dong['success']:
                result_num = search_num(driver=driver, dong=dong, num=num)
                df.at[index, 'gov24_num_list'] = result_num["num_list"]
                df.at[index, 'gov24_num_tratget'] = result_num["ai_response"]['정답']
                df.at[index, 'gov24_num_신뢰도'] = result_num["ai_response"]['신뢰도']
                df.at[index, 'gov24_num_추론이유'] = result_num["ai_response"]['추론이유']

                # 건축물 대장 발급 신청(주소,동,호수 문제 없는 경우)
                if result_num['success']:
                    logger.info('\n건축물 대장 발급 진행\n')
                    building_register_html = get_building_register(driver=driver, address=address, dong=dong, num=num)
            
            # 수정된 DataFrame을 엑셀 파일로 저장
            df.to_excel(output_file_path, index=False, engine="openpyxl")
            logger.info(f"수정된 파일이 {output_file_path}에 저장되었습니다.")
    except:
        logger.info("main error")
    
    finally:
        driver.quit()

T_DEFAULT = 10 # 전역변수 대기 시간

if __name__ == '__main__':
    main()
