'''
아래 테스트를 위한 임시 사용 파일
1.프롬프트 수정
2.LLM 모델 수정
'''

import os, json
from dotenv import load_dotenv
from openai import OpenAI


def openai_api(dong=None, num=None, gov24_dong_num=None):
    # 사전 작업
    load_dotenv()  # .env 읽기
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
    model="o1",
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

    

if __name__ == '__main__':
    main()
