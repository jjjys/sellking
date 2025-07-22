import time,random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import SessionNotCreatedException
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys

import pandas as pd
from utils.driver_call import driver_call

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def send_email(sender_email, app_password, receiver_email, subject, body):
    # 이메일 메시지 설정
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # 이메일 본문 추가
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Gmail SMTP 서버 연결
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # TLS 보안 연결 시작
        server.login(sender_email, app_password)  # App Password로 로그인

        # 이메일 전송
        server.send_message(msg)
        print("이메일이 성공적으로 전송되었습니다!")
        
    except Exception as e:
        print(f"이메일 전송 중 오류 발생: {e}")
        
    finally:
        server.quit()  # 서버 연결 종료



def scroll_get_li_elements(driver):
    # Scroll to the bottom of the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    # Random delay to mimic human behavior (2-5 seconds)
    rand_time = random.uniform(2, 5)
    print(f'wait for {rand_time} seconds for avoiding bot detection')
    time.sleep(rand_time)

    ul_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "list__Osep4"))
    )
    
    # Find all li elements within ul
    li_elements = ul_element.find_elements(By.TAG_NAME, "li")

    return li_elements, ul_element.get_attribute("outerHTML") # 정규식으로 링크 파싱하는 방법 테스트
    

def scrape_hrefs(driver, url, output_file=None):
    # Navigate to the target URL
    driver.get(url)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    # Initialize list to store hrefs
    hrefs = []
    last_count = 0
    
    while True:
        # Find the ul element
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            li_elements, li_contained_html = scroll_get_li_elements(driver)
            # Check if new li elements have loaded
            current_count = len(li_elements)
            if current_count == last_count:
                for i in range(0,5):
                    print('try more')
                    li_elements, li_contained_html = scroll_get_li_elements(driver)
                    # Check if new li elements have loaded
                    current_count = len(li_elements)
                if current_count == last_count:
                    # 최대 4000개 링크 테스트
                    #href_pattern = r'href=["\'](.*?)["\']'
                    #hrefs_li_contained_html = re.findall(href_pattern, li_contained_html)
                    print('list elements are no longer found')
                    break  # Exit loop if no new elements are loaded
            last_count = current_count
            print(f"{len(li_elements)} hrefs found")
            # Extract hrefs from a tags within li elements
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # driver.save_screenshot('scr.png') # len(li_elements) 4000개 이후 안되는거 확인.
            for li in li_elements:
                try:
                    a_tag = li.find_element(By.TAG_NAME, "a")
                    href = a_tag.get_attribute("href")
                    if href not in hrefs:  # Avoid duplicates
                        hrefs.append(href)

                        # Save hrefs to Excel
                        df = pd.DataFrame(hrefs, columns=["블로그 링크"])
                        df.to_excel(output_file, index=False)
                        print(f"Saved ({len(hrefs)}/{len(li_elements)}) hrefs to {output_file}")
                        #print(f"Saved ({len(hrefs)}/{len(last_count)}) hrefs to {output_file}")
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                except:
                    print('에러 발생')
                    continue  # Skip if no a tag or href found
                
        except Exception as e:
            print(f"Error finding ul or li elements: {e}")
            break
    
    return hrefs

def transform_url(url):
    # URL 파싱
    parsed_url = urlparse(url)
    
    # 경로 수정: 'PostList'를 'Business'로 변경
    new_path = parsed_url.path.replace('PostList', 'Business')
    
    # 쿼리 파라미터에서 blogId만 유지
    query_params = parse_qs(parsed_url.query)
    new_query = {'blogId': query_params.get('blogId', [''])[0]}
    
    # 새로운 URL 생성
    new_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        new_path,
        parsed_url.params,
        urlencode(new_query),
        parsed_url.fragment
    ))
    
    return new_url

def get_bussiness_info(driver, url):
    res = ''
    try:
        driver.get(transform_url(url))
        tr_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr"))
        )
        tr_elements = tr_elements[:-1]
        for tr in tr_elements:
            if tr.text == '\n':
                pass
            res = f"{res}\n{tr.text}"
        res = res.strip()
        return res
    except:
        if '일시적인 오류로 서비스에 접속할 수 없습니다.' in driver.page_source:
            print('사업자 정보 확인 불가')
            return '사업자 정보 확인 불가'
        else:
            print('일시적인 오류로 서비스에 접속할 수 없습니다. 외 페이지')
            return '에러, 확인 요망'

def scrape_real_estate_agents(driver, url):
    # URL로 이동
    driver.get(url)
    
    try:
        # 블로그 이름(h2 > a) 수집
        try:
            title = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2 > a"))
            ).text.strip()
            print(f"수집 데이터(블로그 이름):\n{title}\n")
        except:
            title = ""
        # 소개글(.desc__Sxw5t) 수집
        try:
            desc = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".desc__Sxw5t"))
            ).text.strip()
            print(f"수집 데이터(소개글):\n{desc}\n")
        except:
            desc = ""  # 소개글이 없는 경우 빈 문자열
        # 사업자정보 수집
        try:
            bussiness_info = get_bussiness_info(driver, url)
            print(f"수집 데이터(사업자정보):\n{bussiness_info}\n")
        except:
            bussiness_info = "" 
        
        # DataFrame 생성
        data = {
            "블로그 이름": title,  # pandas 저장을 위해 단일 값을 리스트로
            "소개": desc,
            "사업자 정보": bussiness_info
        }

        return data
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        
    finally:
        # 드라이버 종료는 호출자가 관리
        pass

def find_email(string1, string2):
    # 이메일 패턴 정규식: 일반적인 이메일 형식 (username@domain.com 등)
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # 문자열1에서 이메일 검색
    email1 = re.search(email_pattern, string1)
    if email1:
        return email1.group()
    
    # 문자열1에 없으면 문자열2에서 검색
    email2 = re.search(email_pattern, string2)
    if email2:
        return email2.group()
    
    # 둘 다 없으면 None 반환
    return None

def main():
    try:
        # 키워드(네이버 블로그 검색 키워드) 설정
        keyword = '상가중개법인'#'공인중개사'
        file_path = rf"real_estate_agents_info_{keyword}.xlsx"

        driver = driver_call()
        url = f"https://m.blog.naver.com/SectionBlogSearch.naver?orderType=sim&pageAccess=direct&periodType=all&searchValue={keyword}"
        #url = f"https://m.blog.naver.com/SectionBlogSearch.naver?orderType=sim&pageAccess=tab&periodType=all&searchValue={keyword}"
        
        scrape_hrefs(driver,url,output_file=file_path)
        
        ### [ 블로그 내부 정보 추출(이메일 정보 포함) ] ###
        df = pd.read_excel(file_path, engine="openpyxl")

        # 열 추가를 위한 빈 df 생성
        # # 필요한 열 목록
        required_columns = ['블로그 링크', '블로그 이름', '소개', '사업자 정보', '이메일(추출)']
        # 각 열이 DataFrame에 없는 경우에만 추가
        for col in required_columns:
            if col not in df.columns:
                print(f"{col}열이 없어서 추가.")
                df[col] = ''

        for index, row in df.iloc[:].iterrows():
            # 각 행의 데이터 접근 (열 이름으로 접근 가능)
            url = row[df.columns[0]]  # url
            
            # 이전에 했단 행은 넘어감.
            if not(pd.isna(row[df.columns[1]]) or row[df.columns[1]].strip() == ''):
                print(f"값 존재:{row[df.columns[1]]}\n다음 행({index+2}) 진행\n\n")
                continue

            # 주소, 동, 호수 전체 값 확인
            print('\n'*3)
            print('='*20)
            print('='*20)
            print(f"행 {index + 1}:")
            print(f"url:{url}")
            print("=" * 20,'\n') 
            result = scrape_real_estate_agents(driver, url)
            df.at[index, '블로그 이름'] = result['블로그 이름']
            df.at[index, '소개'] = result['소개']
            df.at[index, '사업자 정보'] = result['사업자 정보']
            df.at[index, '이메일(추출)'] = find_email(result['사업자 정보'], result['소개'])
            df.to_excel(file_path, index=False, engine="openpyxl")
    finally:
        driver.quit()
      
    # # 구글 이메일 전송 테스트
    # # 참고: https://kincoding.com/entry/Google-Gmail-SMTP-%EC%82%AC%EC%9A%A9%EC%9D%84-%EC%9C%84%ED%95%9C-%EC%84%B8%ED%8C%85-2025%EB%85%84-%EB%B2%84%EC%A0%84
    # sender_email = "realestate250625@gmail.com"  # 발신자 Gmail 주소
    # app_password = ""     # Google에서 생성한 App Password -> 수정함.
    # receiver_email = "realestate250625@gmail.com"  # 수신자 이메일 주소
    # subject = "테스트 이메일"  # 이메일 제목
    # body = "이것은 Python을 사용한 테스트 이메일입니다."  # 이메일 본문
    # send_email(sender_email, app_password, receiver_email, subject, body)
    
    
if __name__ == '__main__':
    main() 