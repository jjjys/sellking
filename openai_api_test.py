'''
프롬프트 수정할 때 임시 사용 파일

'''


import os, json
from dotenv import load_dotenv
from openai import OpenAI


def openai_api(dong=None, num=None, gov24_dong_num=None):
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
당신은 대한민국 부동산에서 제공된 동(dong)과 호수(ho) 정보를 바탕으로 선택지에서 가장 알맞은 답변을 선택해야 합니다. 아래 내용을 참고하여 답변해 주세요.

# 동 정보  
{dong}  

# 호수 정보  
{num}  

# 선택지  
{gov24_dong_num}  

# 답변 형식  
{{
    "정답": "(선택지 중 택1)",
    "신뢰도": "(높음/중간/낮음)",
    "추론이유": "(선택지를 정답으로 선택한 이유)"
}}

# 지침  
- 주어진 동과 호수 정보를 선택지와 비교하여 **정확히 일치하는 경우** 해당 선택지를 선택합니다.  
- 정확히 일치하는 선택지가 없을 경우, **가장 유사한 선택지**를 선택합니다.  
- **신뢰도**는 선택한 답변의 정확성에 대한 확신을 나타내며, 다음과 같이 설정합니다:  
  - **높음**: 동과 호수가 선택지와 정확히 일치할 때  
  - **중간**: 동은 일치하지만 호수가 약간 다르거나, 그 반대의 경우  
  - **낮음**: 동과 호수가 선택지와 크게 다르거나 불확실한 경우
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
    print(f'input:{prompt}\n')
    print(f'output:{completion01.choices[0].message.content}\n')

    result = completion01.choices[0].message.content
    result = json.loads(result)
    if isinstance(result, dict):
        return result
    return False



def main():
    global T_DEFAULT
    T_DEFAULT = 10
    load_dotenv()  # .env 읽기
    GOV24_ID = os.getenv("GOV24_ID")
    GOV24_PW = os.getenv("GOV24_PW")

    dong = '101'
    num = '1203'
    gov24_dong_num = '''\n내대지마을 죽전이편한세상 101동(공동주택(아파트) : 9663.09)\n내대지마을 죽전이편한세상 102동(공동주택(아파트) : 5458.03)
'''

    result = openai_api(dong,num,gov24_dong_num)
    

    input()

    

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

if __name__ == '__main__':
    main()
