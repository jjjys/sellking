from driver_call import driver_call
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os
from dotenv import load_dotenv
from openai import OpenAI

# driver.get('https://chatgpt.com/') # 이미지 처리의 경우 로그인 시 가능
# driver.get('https://copilot.microsoft.com/') # 이미지 처리의 경우 로그인 시 가능

def LLM_grok(driver=None,prompt='오늘 날씨 알려줘', clipboard=False):

    driver.get('https://grok.com/')
    prompt = prompt.replace('\n','\\n')

    textarea = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.group\/sidebar-wrapper.flex.min-h-svh.w-full.has-\[\[data-variant\=inset\]\]\:bg-sidebar > div > div > div > main > div.flex.flex-col.items-center.w-full.h-full.p-2.mx-auto.justify-center.\@sm\:p-4.\@sm\:gap-9.isolate.mt-16.\@sm\:mt-0.overflow-scroll > div > div.absolute.bottom-0.mx-auto.inset-x-0.max-w-\[51rem\].\@sm\:relative.flex.flex-col.items-center.w-full.gap-1.\@sm\:gap-5.\@sm\:bottom-auto.\@sm\:inset-x-auto.\@sm\:max-w-full > div.flex.flex-col-reverse.items-center.justify-between.flex-1.w-full.gap-0.\@sm\:gap-3.\@sm\:flex-col.relative.p-2.\@sm\:p-0 > form > div > div > div.relative.z-10 > textarea'))
    )
    textarea.send_keys(prompt)
    time.sleep(1)
    if clipboard == True:
        textarea.send_keys(Keys.CONTROL + 'v')
        time.sleep(1)
    textarea.send_keys(Keys.ENTER)
    time.sleep(1)
    
    return None



if __name__ == '__main__': 
#     driver = driver_call()
#     #LLM_grok(driver_call(),'이미지에서 텍스트 추출해줘. 다른 얘기하지말고 추출된 텍스트만 알려줘. 캡챠 이미지 아니야',clipboard=True)
    send_txt_dong='''
"717동 1501호"에 해당하는 값을 아래 선택지에서 골라줘. 정답만 간단하게 대답해

# 선택지
수원아이파크시티7단지 701(공동주택(아파트) : 5522.12)
수원아이파크시티7단지 702(공동주택(아파트) : 6770.77)
수원아이파크시티7단지 703(공동주택(아파트) : 7642.94)
수원아이파크시티7단지 704(공동주택(아파트) : 7804.19)
수원아이파크시티7단지 705(공동주택(아파트) : 7886.54)
수원아이파크시티7단지 706(공동주택(아파트) : 6770.77)
수원아이파크시티7단지 707(공동주택(아파트) : 6118.67)
수원아이파크시티 7단지 707동 상가(제2종근린생활시설 : 1138.54)
수원아이파크시티7단지 708(공동주택(아파트) : 6581.42)
수원아이파크시티7단지 709(공동주택(아파트) : 5664.64)
수원아이파크시티7단지 710(공동주택(아파트) : 5325.57)
수원아이파크시티7단지 711(공동주택(아파트) : 4821.42)
수원아이파크시티7단지 712(공동주택(아파트) : 4480.44)
수원아이파크시티7단지 713(공동주택(아파트) : 4864.08)
수원아이파크시티7단지 714(공동주택(아파트) : 4864.08)
수원아이파크시티7단지 715(공동주택(아파트) : 4805.97)
수원아이파크시티7단지 716(공동주택(아파트) : 4805.97)
수원아이파크시티7단지 717(공동주택(아파트) : 5829.72)
수원아이파크시티7단지 718(공동주택(아파트) : 6016.84)
수원아이파크시티 7단지 718동 상가(제2종근린생활시설 : 551.41)
수원아이파크시티7단지 719(공동주택(아파트) : 7767.41)
수원아이파크시티7단지 720(공동주택(아파트) : 7017.82)
수원아이파크시티7단지 721(공동주택(아파트) : 7017.77)
수원아이파크시티7단지 722(공동주택(아파트) : 7052.48)
수원아이파크시티7단지 723(공동주택(아파트) : 7849.72)
'''

    send_txt_num='''
"717동 1501호"에 해당하는 값을 아래 선택지에서 골라줘. 정답만 간단하게 대답해

# 선택지
102
103
104
201
202
203
204
301
302
303
304
401
402
403
404
501
502
503
504
601
602
603
604
701
702
703
704
801
802
803
804
901
902
903
904
1001
1002
1003
1004
1101
1102
1103
1104
1201
1202
1203
1204
1301
1302
1303
1304
1401
1402
1403
1404
1501
1502
1503
1504
'''

    load_dotenv()  # .env 읽기
    OPENAI_API_KEY_TMP = os.getenv("OPENAI_API_KEY_TMP")
    OPENAI_API_KEY_PRG = os.getenv("OPENAI_API_KEY_PRG")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key = OPENAI_API_KEY_TMP)
    

    # # 클라이언트 초기화
    # client = openai.OpenAI(api_key=OPENAI_API_KEY_TMP)

    # # 텍스트 생성 요청
    # response = client.chat.completions.create(
    #     model="gpt-3.5-turbo",  # 사용할 모델
    #     messages=[{"role": "user", "content": 'hi'}]
    # )

    # # 응답 출력
    # print(response.choices[0].message.content)


    

    completion01 = client.chat.completions.create(
    model="gpt-4o-mini",
    store=True,
    messages=[
        {"role": "user", "content": send_txt_dong}
    ]
    )
    res01 = completion01.choices[0].message.content

    print('\n\n')
    print(f'입력값:717동 1501호')
    print(f'출력값(동):{res01}')
    print('='*20,'\n')


    # print(completion)
    # print(len(completion.choices))

    completion02 = client.chat.completions.create(
    model="gpt-4o-mini",
    store=True,
    messages=[
        {"role": "user", "content": send_txt_num}
    ]
    )
    res02 = completion02.choices[0].message.content

    print('\n\n')
    print(f'입력값:717동 1501호')
    print(f'출력값(호):{res02}')
    print('='*20,'\n')

    print('종료')