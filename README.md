# 부동산 중개인 정보 크롤러

## 개요
이 Python 스크립트는 네이버 블로그 검색 결과를 통해 부동산 중개인 정보를 수집합니다. 블로그 링크를 수집하고, 블로그 이름, 소개글, 사업자 정보 등을 추출하며, 이메일 주소를 식별합니다. 수집된 데이터는 엑셀 파일로 저장됩니다. Selenium과 undetected_chromedriver를 사용하여 봇 탐지를 회피하며, 이메일 알림 기능을 포함합니다.

## 기능
- **웹 스크래핑**: 지정된 키워드(예: "상가중개법인")로 네이버 블로그 검색 결과에서 블로그 URL을 수집합니다.
- **동적 스크롤링**: 페이지를 스크롤하여 모든 블로그 링크를 동적으로 로드합니다.
- **데이터 추출**: 개별 블로그 페이지에서 블로그 이름, 소개글, 사업자 정보를 추출합니다.
- **이메일 추출**: 정규식을 사용하여 사업자 정보 또는 소개글에서 이메일 주소를 식별합니다.
- **엑셀 출력**: 수집된 데이터를 `real_estate_agents_info_{keyword}.xlsx` 파일에 저장합니다.
- **이메일 알림**: Gmail SMTP를 통해 알림 이메일을 전송할 수 있습니다(현재 주석 처리됨).
- **봇 탐지 회피**: 랜덤 지연 시간과 `undetected_chromedriver`를 사용하여 사람의 행동을 모방합니다.
- **키워드 수정**: `main()` 함수에서 `keyword` 변수를 수정하여 원하는 검색 키워드로 데이터를 수집할 수 있습니다.

## 요구 사항
- Python 3.x
- 필요한 Python 패키지:
  ```
  pip install selenium undetected-chromedriver pandas openpyxl
  ```
- `undetected_chromedriver`와 호환되는 Chrome 브라우저 버전.
- (선택) 이메일 알림을 위해 Gmail 계정과 앱 비밀번호.

## 사용 방법
1. **설치**:
   - 위에 나열된 패키지를 설치합니다.
   - Chrome 브라우저가 설치되어 있고 `undetected_chromedriver`와 호환되는지 확인합니다.
   - 이메일 알림을 사용하려면 `main()` 함수에서 `sender_email`, `app_password`, `receiver_email`을 설정합니다.

2. **키워드 수정 및 데이터 수집**:
   - `scraper.py` 파일을 텍스트 편집기로 엽니다.
   - `main()` 함수에서 `keyword` 변수를 원하는 검색어로 수정합니다. 예:
     ```python
     keyword = '공인중개사'  # 원하는 키워드로 변경
     ```
   - 수정 후 파일을 저장합니다.

3. **스크립트 실행**:
   ```
   python scraper.py
   ```
   - 스크립트는 지정된 키워드로 네이버 블로그를 검색하여 데이터를 수집합니다.
   - 결과는 `real_estate_agents_info_{keyword}.xlsx` 파일에 저장됩니다 (예: `real_estate_agents_info_공인중개사.xlsx`).

4. **출력**:
   - 엑셀 파일에는 `블로그 링크`, `블로그 이름`, `소개`, `사업자 정보`, `이메일(추출)` 열이 포함됩니다.

## 코드 구조
- `send_email(sender_email, app_password, receiver_email, subject, body)`:
  Gmail SMTP를 사용하여 이메일을 전송합니다.
- `scroll_get_li_elements(driver)`:
  페이지를 스크롤하고 블로그 링크가 포함된 `<li>` 요소를 가져옵니다. 봇 탐지를 피하기 위해 랜덤 지연을 사용합니다.
- `scrape_hrefs(driver, url, output_file)`:
  검색 결과 페이지에서 블로그 URL을 수집하여 엑셀 파일에 저장합니다.
- `transform_url(url)`:
  블로그 URL을 사업자 정보 페이지 URL로 변환합니다.
- `get_bussiness_info(driver, url)`:
  변환된 URL에서 사업자 정보를 추출합니다.
- `scrape_real_estate_agents(driver, url)`:
  블로그 페이지에서 블로그 이름, 소개글, 사업자 정보를 수집합니다.
- `find_email(string1, string2)`:
  두 문자열에서 정규식을 사용하여 이메일 주소를 찾습니다.
- `main()`:
  URL 수집부터 데이터 추출 및 저장까지 전체 스크래핑 과정을 조정합니다.

## 참고 사항
- **오류 처리**: 요소 누락, 연결 문제 등의 오류를 처리하여 가능한 한 진행을 계속합니다.
- **속도 제한**: 봇 탐지를 피하기 위해 2~5초의 랜덤 지연을 사용합니다.
- **엑셀 업데이트**: 중단 시 데이터 보존을 위해 엑셀 파일을 점진적으로 업데이트합니다.
- **이메일 기능**: 기본적으로 주석 처리되어 있습니다. 유효한 자격 증명을 설정하여 활성화하세요.
- **제한 사항**: 네이버 페이지 구조 변경이나 봇 탐지로 인해 스크립트가 실패할 수 있습니다.

## 출력 예시
`real_estate_agents_info_공인중개사.xlsx` 파일 예시:
| 블로그 링크 | 블로그 이름 | 소개 | 사업자 정보 | 이메일(추출) |
|-------------|-------------|------|-------------|--------------|
| https://... | 예시 블로그 | 부동산 서비스... | 사업자명: ABC 부동산... | example@domain.com |

## 문제 해결
- **SessionNotCreatedException**: Chrome과 `undetected_chromedriver` 버전이 호환되는지 확인하세요.
- **요소 없음 오류**: 네이버 블로그 페이지 구조가 변경되었거나 키워드 검색 결과가 없는지 확인하세요.
- **이메일 오류**: Gmail 앱 비밀번호와 SMTP 설정을 확인하세요.
