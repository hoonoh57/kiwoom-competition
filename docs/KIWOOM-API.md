\# 키움증권 REST API 검증된 사양



출처: openapi.kiwoom.com 공식 가이드 및 공지사항

확인일: 2026-09-12



\## 0. 도메인



```

운영 REST      : https://api.kiwoom.com

모의투자 REST  : https://mockapi.kiwoom.com

운영 WebSocket : wss://api.kiwoom.com:10000/api/dostk/websocket

```



\## 1. 유량 정책 (공식 공지 2026.07.02 기준)



```

\- 계좌별(토큰별) 1초당 전체 호출 한도: 50회

\- 특정 중분류(예: 차트)는 1초당 20회로 별도 제한

\- 조건검색 관련은 1분당 5회

```



★ 본 프로젝트는 조건검색 API(ka10171/10172/10173)를 의도적으로 사용하지 않는다.

&#x20;  스크리닝은 전부 Creon MarketEye 로 수행한다 (설계서 5절).

&#x20;  프로젝트 리미터 설정: per\_sec = 40 (공식 50의 80%)



주: 유량 정책은 변경될 수 있다. 구현 시점에

&#x20;   https://openapi.kiwoom.com/m/board/Board0101View?seqid=49 재확인.



\## 2. 접근토큰 발급 (au10001) — 공식 샘플 검증됨



```

Method       : POST

URL          : /oauth2/token

Content-Type : application/json;charset=UTF-8

```



Request Body

```

grant\_type : "client\_credentials"  (필수)

appkey     : 앱키                  (필수)

secretkey  : 시크릿키              (필수)

```



Response Body

```

expires\_dt  : 만료일 (예: "20241107083713")

token\_type  : "bearer"

token       : 접근토큰

return\_code : 0 = 정상

return\_msg  : "정상적으로 처리되었습니다"

```



공식 Python 샘플

```python

import requests, json



def fn\_au10001(data):

&#x20;   host = 'https://api.kiwoom.com'          # 모의: https://mockapi.kiwoom.com

&#x20;   endpoint = '/oauth2/token'

&#x20;   url = host + endpoint

&#x20;   headers = {'Content-Type': 'application/json;charset=UTF-8'}

&#x20;   response = requests.post(url, headers=headers, json=data)

&#x20;   print('Code:', response.status\_code)

&#x20;   print('Header:', json.dumps(

&#x20;       {k: response.headers.get(k) for k in \['next-key', 'cont-yn', 'api-id']},

&#x20;       indent=4, ensure\_ascii=False))

&#x20;   print('Body:', json.dumps(response.json(), indent=4, ensure\_ascii=False))



if \_\_name\_\_ == '\_\_main\_\_':

&#x20;   params = {

&#x20;       'grant\_type': 'client\_credentials',

&#x20;       'appkey':    'AxserEsdcredca.....',

&#x20;       'secretkey': 'SEefdcwcforehDre2fdvc....',

&#x20;   }

&#x20;   fn\_au10001(data=params)

```



토큰 운영 규칙 (프로젝트)

\- 만료 10분 전 자동 갱신

\- 갱신 실패 시 신규 주문 차단, 청산 전용 모드 전환

\- 토큰 캐시 파일: secrets/kiwoom\_token\_{prod|mock}.json

\- IP 화이트리스트 등록 필요 (미등록 시 401/403)



\## 3. 공통 호출 규약



```

헤더

&#x20; Authorization : Bearer {token}

&#x20; api-id        : {API\_ID}              ★TR 구분은 URL이 아니라 이 헤더

&#x20; Content-Type  : application/json;charset=UTF-8



응답 헤더

&#x20; api-id   : 에코

&#x20; cont-yn  : 연속조회 여부 ('Y'/'N')

&#x20; next-key : 연속조회 키

```



연속조회는 응답의 cont-yn='Y' 일 때 next-key 를 요청 헤더에 넣어 재호출한다.



\## 4. API ID 목록 (프로젝트 사용분)



```

인증

&#x20; au10001  접근토큰 발급

&#x20; au10002  접근토큰 폐기



주문  ★프로젝트 핵심

&#x20; kt10000  주식 매수주문

&#x20; kt10001  주식 매도주문

&#x20; kt10002  주식 정정주문

&#x20; kt10003  주식 취소주문



계좌

&#x20; kt00004  계좌평가현황요청 (계열)

&#x20; kt00005  체결잔고요청 (계열)

&#x20; ka10075  미체결요청

&#x20; ka10076  체결요청



시세 (보조. 주 데이터는 Creon)

&#x20; ka10001  주식기본정보요청

&#x20; ka10004  주식호가요청

&#x20; ka10080  주식분봉차트조회

&#x20; ka10081  주식일봉차트조회



실시간 (WebSocket type)

&#x20; 00  주문체결

&#x20; 04  잔고

&#x20; 0B  주식체결      ★프로젝트 사용

&#x20; 0D  주식호가잔량  ★프로젝트 사용

&#x20; 0H  주식시간외호가

&#x20; 1h  VI발동/해제



조건검색 (프로젝트 미사용)

&#x20; ka10171  조건검색 목록조회

&#x20; ka10172  조건검색 요청 일반

&#x20; ka10173  조건검색 실시간

```



================================================================

\[KIWOOM-API] 5. 국내주식 주문 API 확정 사양 (V-K01 CLOSED)

출처: github.com/Kiwoom-Securities/Kiwoom-REST-API (공식)

&#x20;     examples/국내주식/주문/\*.py 원문 대조, 2026-09-12 확인

================================================================



5.0 공통

&#x20; 운영 도메인   : https://api.kiwoom.com

&#x20; 모의 도메인   : https://mockapi.kiwoom.com

&#x20; 주문 엔드포인트: POST /api/dostk/ordr   (4종 모두 동일)

&#x20; 조회 엔드포인트: POST /api/dostk/acnt   (미체결/잔고 등, 주문과 다름)

&#x20; 요청 헤더:

&#x20;    Content-Type : application/json;charset=UTF-8

&#x20;    authorization: Bearer {token}

&#x20;    api-id       : kt10000 | kt10001 | kt10002 | kt10003

&#x20;    cont-yn      : (연속조회 시) 이전 응답의 cont-yn

&#x20;    next-key     : (연속조회 시) 이전 응답의 next-key

&#x20; 응답 헤더: cont-yn, next-key, api-id

&#x20; 응답 공통 body: return\_code(정상 0), return\_msg

&#x20; 판정 규칙: HTTP 200이어도 성공이 아님. 반드시 return\_code로 판정.

&#x20; 타입 규칙: 수량/단가 등 모든 값은 문자열(str)로 전송. 종목코드는 6자리

&#x20;           (예: "005930", 앞자리 0 생략 금지).



5.1 kt10000 주식 매수주문

&#x20; 요청 body:

&#x20;    dmst\_stex\_tp  (필수) 국내거래소구분 : KRX | NXT | SOR

&#x20;    stk\_cd        (필수) 종목코드

&#x20;    ord\_qty       (필수) 주문수량 (단위 1주)

&#x20;    trde\_tp       (필수) 매매구분 (5.5 코드표)

&#x20;    ord\_uv        (선택) 주문단가 (원). 시장가는 "" 로 비움

&#x20;    cond\_uv       (선택) 조건단가 (원). 미해당 시 ""

&#x20; 응답 body:

&#x20;    ord\_no             주문번호 (7자리)

&#x20;    dmst\_stex\_tp       국내거래소구분

&#x20; 공식 예제 호출값:

&#x20;    dmst\_stex\_tp='KRX', stk\_cd='005930', ord\_qty='1',

&#x20;    trde\_tp='3', ord\_uv='', cond\_uv=''



5.2 kt10001 주식 매도주문

&#x20; 요청/응답 필드는 kt10000과 완전히 동일. api-id만 kt10001.



5.3 kt10002 주식 정정주문

&#x20; 요청 body:

&#x20;    dmst\_stex\_tp  (필수) KRX | NXT | SOR

&#x20;    orig\_ord\_no   (필수) 원주문번호

&#x20;                  - 매수/매도 주문 응답으로 받은 7자리 주문번호

&#x20;    stk\_cd        (필수) 종목코드

&#x20;    mdfy\_qty      (필수) 정정수량 (단위 1주, "0" = 잔량 전부 정정)

&#x20;    mdfy\_uv       (필수) 정정단가 (원)

&#x20;    mdfy\_cond\_uv  (선택) 정정조건단가 (원)

&#x20; 응답 body:

&#x20;    ord\_no             주문번호 (정정으로 새로 생성된 번호)

&#x20;    base\_orig\_ord\_no   모주문번호

&#x20;    mdfy\_qty           정정수량

&#x20;    dmst\_stex\_tp       국내거래소구분

&#x20; 공식 예제 호출값:

&#x20;    orig\_ord\_no='0000139', mdfy\_qty='1', mdfy\_uv='199700'



5.4 kt10003 주식 취소주문

&#x20; 요청 body:

&#x20;    dmst\_stex\_tp  (필수) KRX | NXT | SOR

&#x20;    orig\_ord\_no   (필수) 원주문번호 (7자리)

&#x20;    stk\_cd        (필수) 종목코드

&#x20;    cncl\_qty      (필수) 취소수량 (단위 1주, "0" = 잔량 전부 취소)

&#x20; 응답 body:

&#x20;    ord\_no             주문번호

&#x20;    base\_orig\_ord\_no   모주문번호

&#x20;    cncl\_qty           취소수량

&#x20; 공식 예제 호출값:

&#x20;    orig\_ord\_no='0000140', cncl\_qty='1'



5.5 trde\_tp (매매구분) 코드표 - 공식 docstring 원문

&#x20;    0  보통(지정가)        3  시장가

&#x20;    5  조건부지정가        81 장마감후시간외

&#x20;    61 장시작전시간외      62 시간외단일가

&#x20;    6  최유리지정가        7  최우선지정가

&#x20;    10 보통(IOC)          13 시장가(IOC)

&#x20;    16 최유리(IOC)        20 보통(FOK)

&#x20;    23 시장가(FOK)        26 최유리(FOK)

&#x20;    28 스톱지정가         29 중간가

&#x20;    30 중간가(IOC)        31 중간가(FOK)

&#x20; 본 프로젝트 사용 범위:

&#x20;    코어(종가 진입)   : 0 (지정가, 상한 +0.5% 슬리피지 캡)

&#x20;    코어(익일 청산)   : 3 (시장가) 또는 0

&#x20;    위성(돌파)        : 0 (지정가 +0.3%)

&#x20;    사용 금지         : 28/29/30/31 (검증 전), 61/62/81 (설계 범위 외)



5.6 주문 상태 확인 - ka10075 미체결요청

&#x20; POST /api/dostk/acnt  (주문 엔드포인트가 아님에 주의)

&#x20; 요청 body:

&#x20;    all\_stk\_tp  0:전체, 1:종목

&#x20;    trde\_tp     0:전체, 1:매도, 2:매수

&#x20;    stex\_tp     0:통합, 1:KRX, 2:NXT

&#x20;    stk\_cd      (종목 지정 시)

&#x20; 응답: oso\[] 리스트

&#x20;    ord\_stt   주문상태

&#x20;    ord\_qty   주문수량

&#x20;    oso\_qty   미체결수량 (0이면 전량 체결)

&#x20;    cntr\_qty  체결량

&#x20;    stk\_nm    종목명

&#x20; 주의: 미체결 0건이면 oso 키 자체가 없음.

&#x20;       반드시 .get("oso", \[]) 로 받아 KeyError 방지.



5.7 ka10088 미체결 분할주문 상세

&#x20; POST /api/dostk/acnt, api-id: ka10088

&#x20; 요청 body: ord\_no (주문번호 7자리)

&#x20; 응답: osop\[] 리스트 → stk\_cd, stk\_nm, osop\_qty(미체결수량), cntr\_qty



5.8 au10001 접근토큰 발급 (재확인)

&#x20; POST /oauth2/token  (Content-Type: application/json;charset=UTF-8)

&#x20; 요청 body: grant\_type="client\_credentials", appkey, secretkey

&#x20; 응답 body: token, token\_type("bearer"),

&#x20;            expires\_dt(문자열 YYYYMMDDHHMMSS 예 "20241107083713"),

&#x20;            return\_code, return\_msg

&#x20; au10002 = 접근토큰 폐기(revoke)



5.9 order\_fsm.py 구현 필수 규칙 (INVARIANT 연계)

&#x20; (1) ord\_no는 7자리 문자열. 발급 즉시 journal에 영구 기록.

&#x20;     프로세스가 죽어 번호를 잃으면 ka10075로 재탐색해야 하므로

&#x20;     intent\_id ↔ ord\_no 매핑을 파일/DB에 동기 커밋 후 다음 단계 진행.

&#x20; (2) 정정은 시간우선순위를 상실(정정 시점으로 재배치)한다.

&#x20;     따라서 코어 전략은 정정을 사용하지 않고 '취소 후 재주문'으로 통일.

&#x20;     위성 전략만 1회 정정 허용.

&#x20; (3) "0" 시맨틱 주의: mdfy\_qty="0" = 잔량 전부 정정,

&#x20;     cncl\_qty="0" = 잔량 전부 취소. 부분 처리 시 실수량 명시.

&#x20; (4) 이미 전량 체결된 주문에 정정/취소를 보내면 return\_code != 0.

&#x20;     예외가 아닌 정상 분기로 처리(상태 재동기화 후 종료).

&#x20; (5) 시장가(trde\_tp=3)는 ord\_uv를 반드시 ""로 비운다.

&#x20;     값이 있으면 정합성 오류. 또한 금액 상한 검사는

&#x20;     '내가 정한 price\_cap × qty'로 사전 수행(체결가 미지).

&#x20; (6) 지정가는 호가가격단위에 맞춰 반올림 후 전송.

&#x20; (7) 중복주문 방지: 재시도(429/5xx) 전 ka10075로 기존 주문 존재 여부

&#x20;     확인. 키움은 X-Idempotency-Key를 공식 지원하지 않으므로

&#x20;     멱등성은 클라이언트 측 intent\_id + 사전조회로 보장한다.

&#x20;     (※ 블로그 예제의 X-Idempotency-Key 헤더는 비공식이므로 신뢰 금지)



5.10 공식 예제 저장소 (신규 확정 - SAMPLES 섹션에 추가)

&#x20; github.com/Kiwoom-Securities/Kiwoom-REST-API

&#x20;   examples/OAuth 인증/

&#x20;   examples/국내주식/주문/      ← kt10000\~kt10003, 금현물 kt5000x

&#x20;   examples/국내주식/계좌/      ← kt00004, kt00005, ka10075, ka10088

&#x20;   examples/국내주식/시세/      ← ka10001, ka10004, ka10080, ka10081

&#x20;   examples/국내주식/순위정보/, 관심종목/, 기관\_외국인/, 공매도/,

&#x20;            대차거래/, ELW/, ETF/

&#x20;   examples/미국주식/

&#x20; raw 다운로드 패턴:

&#x20;   https://raw.githubusercontent.com/Kiwoom-Securities/

&#x20;     Kiwoom-REST-API/main/examples/<카테고리>/<파일>.py

&#x20; 운영 규칙: 프로젝트 초기에 이 저장소를 git clone 하여

&#x20;   docs/SAMPLES/kiwoom\_official/ 에 고정(pin)한다.

&#x20;   LLM에게 주문/조회 코드를 요청할 때는 반드시 해당 파일을

&#x20;   첨부하고 "필드명을 이 파일에서 그대로 복사, 추론 금지"를 지시한다.

&#x20; 예제 코드 공통 구조(모든 파일 동일):

&#x20;   - 파일 상단 주석 블록에 api\_id / api\_name / api\_url / menu\_path

&#x20;   - COLUMNS dict = 응답 필드명 → 한글명 (응답 스펙의 사실상 정본)

&#x20;   - 필수 파라미터 ValueError 검증 → body 구성 → client.fetch\_page()

&#x20;   - cont\_yn / next\_key 기반 연속조회 루프 (MAX\_PAGES=10,

&#x20;     REQUEST\_DELAY\_SECONDS=0.2)

&#x20;   주의: 예제는 `from kiwoom import get\_client` 라는 자체 래퍼를

&#x20;   전제한다. 우리 프로젝트는 gw64/kiwoom\_rest.py 로 대체하되

&#x20;   body 구성부와 COLUMNS만 발췌 이식한다.

================================================================



\## 6. 주문 구현 규칙 (프로젝트)



\### 6.1 멱등성 ★INV-09

```

\- 모든 주문에 client 생성 intent\_id 부여 (날짜+종목+전략+uuid8)

\- 동일 intent\_id 재제출은 로컬에서 차단

\- 429/5xx/타임아웃 재시도 전에 반드시 미체결(ka10075)/체결(ka10076) 조회로

&#x20; 실재 여부 확인. 조회 없는 재시도는 중복 체결을 만든다.

```



\### 6.2 주문 상태기계

```

INTENT -> SUBMITTED -> ACKED -> (PARTIAL) -> FILLED | CANCELED | REJECTED | ORPHAN



ORPHAN : 제출했으나 응답 미수신. reconcile() 이 계좌조회로 해소.

```



\### 6.3 재시도 정책

```

429, 500, 502, 503, 504 -> 지수 백오프 (2s, 4s, 8s), 최대 3회

401, 403                -> 토큰 갱신 1회 후 재시도. 실패 시 청산 전용 모드

그 외 4xx               -> 즉시 실패. 버그로 기록

```



\### 6.4 트러블슈팅 표

```

증상          원인                      해결

\------------- ------------------------- ----------------------------------

중복 체결     멱등키 미적용             intent\_id 필수, 재시도 전 조회

401/403       토큰 만료 / IP 미등록     만료 10분 전 갱신, 화이트리스트 점검

429/5xx       레이트 제한 / 간헐 장애   지수 백오프, 서킷브레이커, 큐잉

갭 과열 체결  갭 가드 미적용            F10 필터(시초가 갭 6%) 적용

체결 누락     체결 이벤트 레이스        체결 감지 후 200\~400ms 지연 후 처리

반일장 오동작 거래 캘린더 미반영        KRX 캘린더 체크, 타임존 KST 고정

```



\## 7. VERIFY 목록



V-K01  kt10000/10001/10002/10003 의 정확한 endpoint path 와 요청 body 필드명

&#x20;      (계좌번호, 종목코드, 수량, 가격, 거래소구분 dmst\_stex\_tp, 매매구분 등)

&#x20;      → openapi.kiwoom.com/guide/apiguide 의 해당 API 페이지에서 공식 샘플 복사

V-K02  주문 시 신용/미수 구분 필드명 (사용하지 않기 위해 무엇을 비워야 하는지 확인)

V-K03  유량 정책 최신 공지 (Board0101View?seqid=49)

V-K04  0B/0D 실시간 응답의 필드 키 이름과 타입

V-K05  모의투자 도메인에서 주문 API 동작 여부 및 실전과의 차이



★ V-K01 은 반드시 공식 페이지의 Python 샘플을 그대로 가져와 docs/SAMPLES/ 에

&#x20; 저장한 뒤 구현한다. 블로그 코드의 endpoint(/uapi/domestic-stock/...)는

&#x20; 타 증권사 형식과 혼동된 것으로 보이므로 신뢰하지 않는다.



