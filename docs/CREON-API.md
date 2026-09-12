\# CYBOS Plus (Creon) API 검증된 사양



출처: cybosplus.github.io (비공식 도움말 미러), money2.daishin.com 공식 Q\&A/자료실

확인일: 2026-09-12



\## 0. 환경



\- CYBOS Plus API 는 32비트로 개발됨. 32비트 Python 만 사용 가능 (대신증권 공식 답변)

\- 매일 재로그인 필요

\- 관리자 권한 실행 필요

\- 모듈: CpUtil.dll, cpdib.dll, cpsysdib.dll, CpTrade.dll



\## 1. 요청 제한 (공식)



대신증권 공식 답변: "조회는 15초 동안 60회를 초과해서는 안됩니다.

카운트가 0 이 되기 전에 반드시 시간 대기를 하셔야 합니다."



\### CpUtil.CpCybos



Property

&#x20; IsConnect                  -> 0 연결끊김 / 1 연결정상

&#x20; ServerType                 -> 0 끊김 / 1 cybosplus 서버 / 2 HTS 보통서버

&#x20; LimitRequestRemainTime     -> 요청개수 재계산까지 남은 시간 (millisecond)



Method

&#x20; GetLimitRemainCount(limitType) -> 제한까지 남은 요청개수

&#x20;     limitType: LT\_TRADE\_REQUEST=0, LT\_NONTRADE\_REQUEST=1, LT\_SUBSCRIBE=2



Event

&#x20; OnDisConnect  -> 이 이벤트 후에는 데이터 통신 불가. 안전 종료 필요.



\### 공식 자료실 샘플 (요청 제한 대기 패턴) — 검증됨



```python

import win32com.client, time



g\_objCpStatus = win32com.client.Dispatch("CpUtil.CpCybos")



class CpTimeChecker:

&#x20;   def \_\_init\_\_(self, checkType):

&#x20;       # 0: 주문관련, 1: 시세요청관련, 2: 실시간요청관련

&#x20;       self.chekcType = checkType



&#x20;   def checkRemainTime(self):

&#x20;       remainTime  = g\_objCpStatus.LimitRequestRemainTime

&#x20;       remainCount = g\_objCpStatus.GetLimitRemainCount(self.chekcType)

&#x20;       if remainCount <= 0:

&#x20;           while remainCount <= 0:

&#x20;               time.sleep(remainTime / 1000)

&#x20;               remainCount = g\_objCpStatus.GetLimitRemainCount(1)

&#x20;               remainTime  = g\_objCpStatus.LimitRequestRemainTime

```



주: 본 프로젝트는 위 패턴에 SAFETY\_MARGIN=8 및 클라이언트 슬라이딩 윈도(15s/52건)를

&#x20;   추가한 이중 방어를 사용한다 (설계서 3.3).



\## 2. CpUtil.CpCodeMgr  — 요청 비용 비소모 가정 (V-C12 실측 전 거버너 필수)



```

CodeToName(code)                -> 종목명

GetStockListByMarket(market)    -> 시장별 종목코드 배열  (1 거래소, 2 코스닥)

GetStockMarginRate(code)        -> 매수 증거금율

GetStockMemeMin(code)           -> 매매 거래단위 주식수   ★주문 수량 정규화에 필수

GetStockIndustryCode(code)      -> 증권전산업종코드

GetStockMarketKind(code)        -> 0 구분없음 / 1 거래소 / 2 코스닥 / 3 프리보드 / 4 KRX

GetStockControlKind(code)       -> 0 정상 / 1 주의 / 2 경고 / 3 위험예고 / 4 위험

GetStockSupervisionKind(code)   -> 0 일반종목 / 1 관리

GetStockStatusKind(code)        -> 0 정상 / 1 거래정지 / 2 거래중단

GetStockCapital(code)           -> 0 제외 / 1 대 / 2 중 / 3 소

GetStockFiscalMonth(code)       -> 결산기

GetStockGroupCode(code)         -> 그룹(계열사)코드    ★테마 클러스터링 보조

GetStockKospi200Kind(code)      -> KOSPI200 채용 구분

GetStockSectionKind(code)       -> 부 구분 (0 구분없음 / 1 주권 / 2 투자회사 / ...)

GetGroupCodeList(code)          -> 관심종목(700\~799)/업종코드의 종목배열

GetGroupName(code)              -> 관심종목명/업종코드명

GetIndustryList()               -> 증권전산업종 코드 리스트

GetIndustryName(code)           -> 업종명

GetKosdaqIndustry1List()        -> 코스닥 산업별 코드리스트

GetKosdaqIndustry2List()        -> 코스닥 지수업종 코드리스트

GetMarketStartTime()            -> 장 시작 시각 (9시면 9)

GetMarketEndTime()              -> 장 마감 시각 (오후3시면 15)

IsNxtTrdPsbl(code)              -> NXT 거래소 거래가능 여부

```



\### 검증된 사용 패턴 (관리종목 필터)



```python

g\_objCodeMgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")



for code in g\_objCodeMgr.GetStockListByMarket(1):

&#x20;   if g\_objCodeMgr.GetStockSupervisionKind(code) == 1:   # 관리종목

&#x20;       continue

&#x20;   if g\_objCodeMgr.GetStockStatusKind(code) != 0:        # 거래정지/중단

&#x20;       continue

&#x20;   if g\_objCodeMgr.GetStockSectionKind(code) != 1:       # 주권 아님

&#x20;       continue

&#x20;   ...

```



\## 3. CpSysDib.MarketEye  — 다종목 동시 조회 (핵심)



관련 CYBOS 화면: \[7059] MarketEye

통신종류: Request/Reply, 연속여부 X



\### 입력 (SetInputValue)



```

type 0 : (long or long array) 필드 또는 필드배열.  최대 64개 필드

type 1 : (string or string array) 종목코드 또는 배열.  최대 200종목

&#x20;        주의) 해외지수/환율은 심볼코드 (예: JP#NI225)

type 2 : (char) 체결비교방식.  '1' 체결가비교(default) / '2' 호가비교

```



\### 헤더 (GetHeaderValue)



```

0 : (long) 필드 개수

1 : (string array) 필드명 배열  ★요청한 필드값의 오름차순으로 정렬되어 있음

2 : (long) 종목 개수

```



\### 데이터 (GetDataValue(type, index))



```

type  : 요청한 필드의 index  ★필드는 요청 필드값 오름차순 정렬

index : 요청한 종목의 index

```



\### ★★★ INV-02 구현 패턴 (반드시 이대로)



```python

FIELDS = \[0, 4, 11, 5, 6, 7]          # 요청 순서는 무의미

sorted\_fields = sorted(FIELDS)         # \[0, 4, 5, 6, 7, 11]

fidx = {f: i for i, f in enumerate(sorted\_fields)}



obj.SetInputValue(0, sorted\_fields)

obj.SetInputValue(1, codes\[:200])

obj.BlockRequest()



n = obj.GetHeaderValue(2)

for i in range(n):

&#x20;   code  = obj.GetDataValue(fidx\[0],  i)

&#x20;   price = obj.GetDataValue(fidx\[4],  i)

&#x20;   value = obj.GetDataValue(fidx\[11], i)

```



\### 프로젝트 사용 필드 전체 목록 (원문 확인됨)



```

&#x20; 0 : 종목코드 (string)

&#x20; 1 : 시간 (ulong) hhmm

&#x20; 2 : 대비부호 (char)  '1'상한 '2'상승 '3'보합 '4'하한 '5'하락

&#x20; 3 : 전일대비        ※반드시 대비부호(2)와 같이 요청

&#x20; 4 : 현재가

&#x20; 5 : 시가

&#x20; 6 : 고가

&#x20; 7 : 저가

&#x20; 8 : 매도호가

&#x20; 9 : 매수호가

&#x20;10 : 거래량 (ulong)

&#x20;11 : 거래대금 (ulonglong) 단위:원

&#x20;12 : 장구분 (char)  '0'장전 '1'동시호가 '2'장중

&#x20;13 : 총매도호가잔량

&#x20;14 : 총매수호가잔량

&#x20;15 : 최우선매도호가잔량

&#x20;16 : 최우선매수호가잔량

&#x20;17 : 종목명 (string)

&#x20;20 : 총상장주식수 (ulonglong) 단위:주

&#x20;21 : 외국인보유비율 (float)

&#x20;22 : 전일거래량

&#x20;23 : 전일종가

&#x20;24 : 체결강도 (float)

&#x20;25 : 체결구분 (char) '1'매수체결 '2'매도체결

&#x20;28 : 예상체결가 (long)              ★코어 진입 지정가 산출

&#x20;29 : 예상체결가대비  ※부호(30)와 같이 요청

&#x20;30 : 예상체결가대비부호 (char)

&#x20;31 : 예상체결수량 (ulong)           ★수량 제약 산출

&#x20;32 : 19일종가합

&#x20;33 : 상한가

&#x20;34 : 하한가

&#x20;35 : 매매수량단위 (ushort)

&#x20;36 : 시간외단일대비부호 (char) '+' '-'

&#x20;37 : 시간외단일전일대비  ※부호(36)와 같이 요청

&#x20;38 : 시간외단일현재가

&#x20;39\~45 : 시간외단일 시/고/저/매도호가/매수호가/거래량/거래대금

&#x20;46\~51 : 시간외단일 잔량/체결강도/체결구분

&#x20;53\~57 : 시간외단일 예상체결 관련

&#x20;59\~61 : 시간외단일 기준가/상한가/하한가

&#x20;62 : 외국인순매매

&#x20;63 : 52주최고가

&#x20;64 : 52주최저가

&#x20;65 : 연중최고가

&#x20;66 : 연중최저가

&#x20;67 : PER (float)

&#x20;70 : EPS

&#x20;71 : 자본금 (단위 백만)

&#x20;72 : 액면가

&#x20;73 : 배당률

&#x20;74 : 배당수익률

&#x20;75 : 부채비율

&#x20;76 : 유보율

&#x20;77 : 자기자본이익률

&#x20;82 : VR (float)

&#x20;83 : 5일 회전율

&#x20;89 : BPS

&#x20;95 : 결산년월 (yyyymm)

116 : 프로그램순매수 (long)

117 : 당일외국인순매수잠정구분 (char) '1'확정 '2'잠정

118 : 당일외국인순매수 (long)

119 : 당일기관순매수잠정구분 (char)

120 : 당일기관순매수 (long)

121 : 전일외국인순매수

122 : 전일기관순매수

126 : 신용잔고율

127 : 공매도수량

128 : 공매도일자

```



================================================================

\[CREON-API] 4. StockChart 확정 사양 (V-C03 CLOSED)

출처: cybosplus.github.io/cpsysdib\_rtf\_1\_/stockchart.htm 원문

&#x20;     + 자료실 #16 공식 예제 대조, 2026-09-12 확인

모듈: cpsysdib.dll / CpSysDib.StockChart

통신: Request/Reply,  연속여부: X (★연속조회 미지원)

================================================================



4.1 종목코드 표기 (V-C01 부분 CLOSED)

&#x20; 주식 : "A" + 6자리   예) A003540, A005930

&#x20; 업종 : "U" + 3자리   예) U001  ← 원문에 명시됨

&#x20; ELW  : "J" + 6자리   예) J517016

&#x20; ※ U001(KOSPI종합)은 원문 확정. U201(KOSDAQ종합)은

&#x20;   CpCodeMgr.GetIndustryList/GetIndustryName 실측으로 최종 확인

&#x20;   → V-C01 잔여

&#x20; 코드 변환 규칙(INV-10):

&#x20;   Creon(A005930) ↔ Kiwoom(005930)

&#x20;   변환은 codec.py 단일 함수로만 수행. 문자열 조작 산재 금지.



4.2 SetInputValue type 전체 (원문)

&#x20; 0  종목코드(string)

&#x20; 1  요청구분(char)   '1'=기간요청 / '2'=개수요청

&#x20; 2  요청종료일(ulong) YYYYMMDD, 데이터의 가장 최근 날짜

&#x20;                      Default 0 = 최근 거래일

&#x20; 3  요청시작일(ulong) YYYYMMDD, 데이터의 가장 오래된 날짜

&#x20; 4  요청개수(ulong)

&#x20; 5  필드(long / long array)

&#x20; 6  차트구분(char)   'D'일 'W'주 'M'월 'm'분 'T'틱

&#x20; 7  주기(ushort)     Default 1

&#x20; 8  갭보정여부(char) '0'=갭무보정\[Default] / '1'=갭보정

&#x20; 9  수정주가(char)   '0'=무수정주가\[Default] / '1'=수정주가

&#x20; 10 거래량구분(char) ★★★

&#x20;      '1' 시간외거래량 모두 포함  \[Default]

&#x20;      '2' 장종료시간외거래량만 포함

&#x20;      '3' 시간외거래량 모두 제외

&#x20;      '4' 장전시간외거래량만 포함

&#x20; ※ char 계열은 pywin32에서 ord('1') 형태의 int로 전달한다.

&#x20;   공식 예제도 SetInputValue(1, ord('1')) 로 호출.



4.3 필드 번호 (원문 발췌, 우리가 쓰는 것만)

&#x20; 0  날짜(ulong YYYYMMDD)

&#x20; 1  시간(long hhmm)

&#x20; 2  시가   3 고가   4 저가   5 종가

&#x20; 6  전일대비  ※필드 37(대비부호)과 반드시 동시 요청

&#x20; 8  거래량(ulong/ulonglong)  ※원문 주석 "정밀도 만원 단위"

&#x20; 9  거래대금(ulonglong)      ★우리 핵심 지표

&#x20; 10 누적체결매도수량 / 11 누적체결매수수량

&#x20;      ※분·틱 요청에서만 제공. 체결강도 프록시로 활용 가능

&#x20; 12 상장주식수(ulonglong)

&#x20; 13 시가총액(ulonglong)      ★PIT 유니버스 재구성용

&#x20; 18 수정주가일자 / 19 수정주가비율

&#x20; 37 대비부호(char)



4.4 ★ 프로젝트 고정 필드셋 (임의 변경 금지 = INVARIANT-08)

&#x20; 일/주/월봉 : \[0, 2, 3, 4, 5, 8, 9, 12, 13]

&#x20;    정렬 후 GetDataValue 인덱스

&#x20;      0=날짜 1=시가 2=고가 3=저가 4=종가

&#x20;      5=거래량 6=거래대금 7=상장주식수 8=시가총액

&#x20; 분/틱봉   : \[0, 1, 2, 3, 4, 5, 8, 9]

&#x20;    정렬 후 GetDataValue 인덱스

&#x20;      0=날짜 1=시간 2=시가 3=고가 4=저가 5=종가

&#x20;      6=거래량 7=거래대금

&#x20; 분봉 확장(위성전략 옵션) : 위 + \[10, 11]

&#x20;    → 인덱스 8=누적체결매도수량 9=누적체결매수수량



4.5 ★ 프로젝트 고정 입력값 (INVARIANT-08)

&#x20; type 9  수정주가   = ord('1')   반드시 수정주가

&#x20; type 10 거래량구분 = ord('3')   반드시 시간외 전량 제외

&#x20; type 8  갭보정     = ord('0')   무보정 고정

&#x20; type 7  주기       = 1

&#x20; 근거: Default가 각각 무수정주가·시간외포함이므로

&#x20;       미지정 시 액면분할 왜곡 + 시간외 거래량 오염이 동시 발생.

&#x20; ※ 공식 예제 #16은 type 10을 지정하지 않는다(=Default '1').

&#x20;   예제를 그대로 복사하면 VR 지표가 전면 오염된다. 반드시 주입.



4.6 GetHeaderValue (원문)

&#x20; 0 종목코드  1 필드개수  2 필드명배열(요청필드 오름차순)

&#x20; 3 수신개수(long)        ← 루프 상한

&#x20; 4 마지막봉틱수(ushort)  ★장중 요청 시 마지막 봉은 미완성.

&#x20;                          분봉 수집 시 마지막 1봉은 버린다(누설 방지)

&#x20; 5 최근거래일  6 전일종가  7 현재가  8 대비부호  9 대비

&#x20; 10 거래량  11 매도호가  12 매수호가  13 시가 14 고가 15 저가

&#x20; 16 거래대금

&#x20; 17 종목상태(char) ★하드필터 직결

&#x20;    '0'정상 '1'투자위험 '2'관리 '3'거래정지 '4'불성실공시

&#x20;    '5'불성실+관리 '6'불성실+거래정지 '7'불성실+투자위험

&#x20;    '8'투자위험+거래정지 '9'관리+거래정지

&#x20;    'A'불성실+관리+거래정지 'B'불성실+투자위험+거래정지

&#x20;    'C'투자위험예고 'D'투자주의 'E'투자경고

&#x20;    'F'\~'N' 위 조합  'Z'ETF종목

&#x20;    → 운용 규칙: '0','D' 만 통과. 그 외 전량 배제.

&#x20;      'Z'(ETF)는 코어 전략 대상 아님 → 배제.

&#x20; 18 상장주식수 19 자본금\[백만원] 20 전일거래량

&#x20; 21 최근갱신시간(hhmm) 22 상한가 23 하한가



4.7 GetDataValue(type, index)

&#x20; type  = 요청 필드의 "정렬된 위치 인덱스" (필드번호 아님)

&#x20; index = 수신 데이터의 행 인덱스 (0 .. GetHeaderValue(3)-1)

&#x20; ★INVARIANT-02의 공식 물증: 예제 #16이 \[0,2,3,4,5,8]을

&#x20;   요청하고 GetDataValue(0)\~(5)로 읽는다.



4.8 페이징 (연속여부 X 이므로 자체 구현)

&#x20; StockChart는 cont/next 개념이 없다.

&#x20; → 요청구분 '1'(기간) + type 2(요청종료일)를 과거로 밀며 반복.

&#x20;    루프: to = 목표최신일

&#x20;          while True:

&#x20;            req(from=목표최소일, to=to)

&#x20;            n = GetHeaderValue(3);  if n == 0: break

&#x20;            oldest = 수신 마지막 행의 날짜

&#x20;            if oldest <= 목표최소일: break

&#x20;            to = oldest - 1일(거래일 기준 감소)

&#x20;            if to <= 목표최소일: break

&#x20;            안전장치: 최대 반복 200회, 진척 없으면 즉시 중단

&#x20; 중복 제거 키: 일봉 (code, date) / 분봉 (code, date, hhmm)

&#x20; ※ 1회 최대 수신행수는 원문에 미기재 → V-C07(신규)로 실측 확정.

&#x20;   설계 기준값 2499행은 미검증 가정이므로 하드코딩 금지.

&#x20;   config: creon.stockchart.max\_rows\_per\_req (초기 2000, 보수적)



4.9 에러 처리 (원문 예제 패턴 + 우리 규칙)

&#x20; BlockRequest() 직후 반드시:

&#x20;    st  = obj.GetDibStatus()

&#x20;    msg = obj.GetDibMsg1()

&#x20;    st == 0 이면 정상. 그 외는 실패.

&#x20; ★예제는 실패 시 exit()로 프로세스를 죽인다 — 금지.

&#x20;  우리는 E\_COM/E\_EMPTY 에러코드로 RPC 응답 후 세션 유지.



4.10 공식 예제 #16에서 반드시 고칠 항목 (ADAPTED 체크리스트)

&#x20; (1) type 10 미지정        → ord('3') 주입           \[치명]

&#x20; (2) 필드 9(거래대금) 누락 → 4.4 고정 필드셋으로 교체 \[치명]

&#x20; (3) 실패 시 exit()        → 예외/에러코드 반환으로 교체\[치명]

&#x20; (4) RateGovernor 부재     → 모든 BlockRequest 전 경유 \[치명]

&#x20; (5) PyQt5 GUI 전제        → 전면 제거, 헤드리스 서버화

&#x20; (6) 변수명 len = 내장함수 섀도잉 → n 으로 개명

&#x20; (7) GetHeaderValue(17) 미사용 → 종목상태 하드필터 추가

&#x20; (8) 분봉 마지막 봉 미완성 미처리 → 장중 요청 시 마지막 행 폐기

&#x20; (9) writer.save() 는 현행 pandas에서 제거됨 → 엑셀 출력 미사용

&#x20; (10) 예제 기본코드 '00660'(5자리 오타) → 6자리 검증 강제



4.11 신규 VERIFY

&#x20; V-C07 StockChart 1회 최대 수신행수 (일봉/분봉 각각 실측)

&#x20; V-C08 필드 8 거래량 원문 주석 "정밀도 만원 단위"의 적용 범위

&#x20;       (업종 차트 한정 추정. 주식 일봉에서 실제 단위 실측 필요.

&#x20;        거래대금(9)과 거래량×종가 비교로 교차검증)

&#x20; V-C09 분봉에 수정주가('1')가 실제 적용되는지 여부

&#x20;       (액면분할 전후 분봉 확보 가능 구간으로 확인)

================================================================



\## 5. CpDib.StockCur — 실시간 시세 (Subscribe/Publish)



관련 CYBOS: \[7021 현재가] \[7024 시간대별체결] 등의 실시간 데이터

모듈 위치: cpdib.dll



\### 입력

```

0 : (string) 종목 코드

```



\### 헤더 (GetHeaderValue) — 이벤트 내에서 읽음

```

&#x20;0 : 종목코드 (string)

&#x20;1 : 종목명 (string)

&#x20;2 : 전일대비 (long)

&#x20;3 : 시간 (long)

&#x20;4 : 시가

&#x20;5 : 고가

&#x20;6 : 저가

&#x20;7 : 매도호가

&#x20;8 : 매수호가

&#x20;9 : 누적거래량   ★★단위 주의: 거래소/코스닥/프리보드=단주, 거래소지수=천주

10 : 누적거래대금 ★★단위 주의: 거래소=만원, 코스닥/프리보드=천원,

&#x20;                             거래소지수/코스닥지수=백만원

13 : 현재가

14 : 체결상태 (char) '1'매수 '2'매도

15 : 누적 매도체결수량 (체결가방식)

16 : 누적 매수체결수량 (체결가방식)

17 : 순간체결수량

18 : 시간 (초)

19 : 예상체결가 구분플래그 (char) '1'동시호가(예상체결가) '2'장중(체결)

20 : 장구분 플래그 (char)

&#x20;    '1' 장전예상체결

&#x20;    '2' 장중

&#x20;    '3' 장전시간외  ※주의: StockCur는 장전시간외 수신 안 됨. StockOutCur 사용

&#x20;    '4' 장후 시간외

&#x20;    '5' 장후 예상체결

21 : 장전시간외 거래량

22 : 대비부호 (char) '1'\~'9' (StockChart 헤더8과 동일)

23 : LP보유수량

24 : LP보유수량 대비

25 : LP보유율 (float)

26 : 체결상태 (호가방식)

27 : 누적 매도체결수량 (호가방식)

28 : 누적 매수체결수량 (호가방식)

```



\### Method

```

Subscribe()    : 입력 0에 저장된 종목코드로 수신 신청

Unsubscribe()  : 해지

Request()      : 사용하지 않음

BlockRequest() : 사용하지 않음

GetDataValue() : 사용하지 않음

```



\### Event

```

Received : 가입 종목의 변경 데이터 수신 시 발생

```



\### ★ 단위 함정

누적거래대금(10)은 거래소 '만원', 코스닥 '천원' 단위다.

MarketEye 필드 11(거래대금)은 '원' 단위다. 두 값을 섞어 쓰면 안 된다.

레이크 표준은 '원'으로 통일하고 StockCur 값은 시장별 승수를 곱해 정규화한다.



<ad\_stockchart.py 골격 (원문 대조 완료본)>



\# creon32/adapters/ad\_stockchart.py  구현 지침

\# 참조: docs/CREON-API.md §4 / docs/SAMPLES/creon\_official/16\_\*.py



FIELDS\_DWM = \[0, 2, 3, 4, 5, 8, 9, 12, 13]

FIELDS\_MT  = \[0, 1, 2, 3, 4, 5, 8, 9]



def \_request(obj, gov, \*, code, mode, chart\_type,

&#x20;            to\_date=None, from\_date=None, count=None,

&#x20;            fields, period=1):

&#x20;   gov.acquire('nontrade')                  # INVARIANT-03

&#x20;   obj.SetInputValue(0, code)                # A+6자리

&#x20;   obj.SetInputValue(1, ord(mode))           # '1'기간 / '2'개수

&#x20;   if mode == '1':

&#x20;       obj.SetInputValue(2, to\_date)         # 최근일

&#x20;       obj.SetInputValue(3, from\_date)       # 과거일

&#x20;   else:

&#x20;       obj.SetInputValue(4, count)

&#x20;   obj.SetInputValue(5, fields)

&#x20;   obj.SetInputValue(6, ord(chart\_type))     # D W M m T

&#x20;   if chart\_type in ('m', 'T'):

&#x20;       obj.SetInputValue(7, period)

&#x20;   obj.SetInputValue(8, ord('0'))            # 갭무보정

&#x20;   obj.SetInputValue(9, ord('1'))            # 수정주가  ★

&#x20;   obj.SetInputValue(10, ord('3'))           # 시간외 전량 제외 ★★★

&#x20;   obj.BlockRequest()



&#x20;   st = obj.GetDibStatus()

&#x20;   if st != 0:

&#x20;       raise CreonComError(st, obj.GetDibMsg1())   # exit() 금지



&#x20;   n      = obj.GetHeaderValue(3)

&#x20;   status = obj.GetHeaderValue(17)     # 종목상태 하드필터

&#x20;   tail   = obj.GetHeaderValue(4)      # 마지막봉틱수

&#x20;   rows   = \[\[obj.GetDataValue(j, i) for j in range(len(fields))]

&#x20;             for i in range(n)]

&#x20;   return rows, status, tail



\# 장중 분봉 수집 시: 마지막 행(미완성 봉) 폐기 후 반환

\# 반환은 numpy 배열 + msgpack (32비트에 pyarrow/pandas 금지, INVARIANT-01)



================================================================

\[CREON-API] 5. MarketEye 확정 사양 (V-C04 CLOSED)

출처: cybosplus.github.io/cpsysdib\_rtf\_1\_/marketeye.htm 원문

&#x20;     + 자료실 #8, #24 공식 예제 대조, 2026-09-12 확인

모듈: cpsysdib.dll / ProgID "CpSysDib.MarketEye"

통신: Request/Reply,  연속여부: X

================================================================



5.1 SetInputValue

&#x20; 0 - (long or long array) 필드 또는 필드 배열. ★최대 64개

&#x20; 1 - (string or string array) 종목코드 또는 배열. ★최대 200종목

&#x20;     주의) 해외지수·환율은 심볼코드 입력 (예 JP#NI225)

&#x20; 2 - (char) 체결비교방식

&#x20;       '1' 체결가비교방식 \[default]

&#x20;       '2' 호가비교방식

&#x20;     → 프로젝트 고정값 '1'. 미지정(default) 허용.



5.2 GetHeaderValue  ★StockChart와 인덱스 의미가 다름

&#x20; 0 - (long) 필드 개수

&#x20; 1 - (string array) 필드명 배열 — 요청 필드값 오름차순 정렬

&#x20; 2 - (long) 종목 개수   ← ★루프 상한은 (2). StockChart는 (3)

&#x20; ※ 혼동 방지: StockChart 수신개수=GetHeaderValue(3),

&#x20;   MarketEye 종목개수=GetHeaderValue(2). 상수로 분리 정의할 것.



5.3 GetDataValue(type, index)

&#x20; type  = 요청 필드의 "오름차순 정렬된 위치 인덱스" (필드번호 아님)

&#x20; index = 종목 인덱스 (0 .. GetHeaderValue(2)-1)



5.4 ★★★ 공식 예제 #8의 실제 버그 (P-01 물증)

&#x20; 넘긴 필드 : \[0, 1, 2, 3, 4, 10, 17]

&#x20; 정렬 결과 : 0, 1, 2, 3, 4, 10, 17 (이미 오름차순)

&#x20; 올바른 인덱스 매핑

&#x20;    0=종목코드 1=시간 2=대비부호 3=전일대비

&#x20;    4=현재가   5=거래량 6=종목명

&#x20; 예제의 읽기 코드 (틀림)

&#x20;    GetDataValue(1)→rpName  ← 실제는 '시간'

&#x20;    GetDataValue(2)→rpTime  ← 실제는 '대비부호'

&#x20;    GetDataValue(3)→rpDiffFlag, (4)→rpDiff,

&#x20;    (5)→rpCur, (6)→rpVol   ← 전부 한 칸씩 밀림

&#x20; 원인: CpMarketEye.Request 내 주석의 \[0,17,1,2,3,4,10] 순서를

&#x20;       가정해 작성했으나, 어떤 순서로 넘겨도 오름차순 정렬된다.

&#x20; 교훈: 필드 배열을 하드코딩 리스트로 넘기고 인덱스를 손으로

&#x20;       세는 방식은 반드시 깨진다. 5.7 규약을 강제한다.



5.5 필드 번호 — 프로젝트 사용 항목 (원문 발췌)

&#x20; 0   종목코드(string)

&#x20; 1   시간(ulong, hhmm)

&#x20; 2   대비부호(char)  '1'상한 '2'상승 '3'보합 '4'하한 '5'하락

&#x20; 3   전일대비        ※반드시 필드 2와 동시 요청

&#x20; 4   현재가

&#x20; 5   시가   6 고가   7 저가

&#x20; 8   매도호가   9 매수호가

&#x20; 10  거래량(ulong)

&#x20; 11  거래대금(ulonglong)  ★단위: 원  (StockCur와 단위 다름)

&#x20; 12  장구분(char)  '0'장전 '1'동시호가 '2'장중

&#x20; 13  총매도호가잔량   14 총매수호가잔량

&#x20; 15  최우선매도호가잔량  16 최우선매수호가잔량

&#x20; 17  종목명(string)

&#x20; 20  총상장주식수(ulonglong) 단위:주  ★★5.8 천단위 함정

&#x20; 21  외국인보유비율(float)

&#x20; 22  전일거래량   23 전일종가

&#x20; 24  체결강도(float)

&#x20; 25  체결구분(char) '1'매수체결 '2'매도체결

&#x20; 28  예상체결가(long)        ★동시호가 종가베팅 핵심

&#x20; 29  예상체결가대비          ※필드 30과 동시 요청 필수

&#x20; 30  예상체결가대비부호(char)

&#x20; 31  예상체결수량(ulong)     ★

&#x20; 33  상한가   34 하한가      ★상한가 제외 필터

&#x20; 35  매매수량단위(ushort)

&#x20; 62  외국인순매매

&#x20; 63  52주최고가   64 52주최저가   ★신고가 돌파 필터

&#x20; 67  PER   70 EPS   71 자본금(백만)  89 BPS

&#x20; 82  VR(float)

&#x20; 83  5일 회전율(float)

&#x20; 116 프로그램순매수

&#x20; 117 당일외국인순매수잠정구분 / 118 당일외국인순매수

&#x20; 119 당일기관순매수잠정구분   / 120 당일기관순매수

&#x20; 121 전일외국인순매수  122 전일기관순매수

&#x20; 126 신용잔고율(float)

&#x20; 127 공매도수량   128 공매도일자

&#x20; ※ 시가총액 필드는 존재하지 않는다. 5.8 방식으로 산출.

&#x20; ※ 36\~61 시간외단일가 계열, 129\~146 ELW 계열은 사용 안 함.



5.6 ★ 프로젝트 고정 필드셋 (INVARIANT-08 확장)

&#x20; ME\_EOD (종가 스크리닝, 15:05\~15:30) — 26개

&#x20;   \[0,2,3,4,5,6,7,10,11,12,13,14,17,20,22,23,24,28,31,33,34,35,63,64,82,118]

&#x20; ME\_INTRADAY (위성 감시, 장중) — 14개

&#x20;   \[0,2,3,4,5,6,7,10,11,12,15,16,24,82]

&#x20; ME\_UNIVERSE (마스터 스냅샷, 1일 1회) — 8개

&#x20;   \[0,4,17,20,22,23,33,35]

&#x20; 세 세트 모두 64개 한도 내. 변경 시 config + 문서 동시 개정.



5.7 ★ 필드 접근 규약 (코드 작성 필수 규칙)

&#x20; 손으로 인덱스를 세지 말고 항상 정렬 후 dict를 생성한다.



&#x20;   def field\_index\_map(fields: list\[int]) -> dict\[int, int]:

&#x20;       """필드번호 -> GetDataValue 위치 인덱스"""

&#x20;       return {f: i for i, f in enumerate(sorted(set(fields)))}



&#x20;   FI = field\_index\_map(ME\_EOD)

&#x20;   price = obj.GetDataValue(FI\[4],  i)   # 현재가

&#x20;   amt   = obj.GetDataValue(FI\[11], i)   # 거래대금

&#x20;   name  = obj.GetDataValue(FI\[17], i)   # 종목명



&#x20; 추가 안전장치: 요청 직후 GetHeaderValue(1) 필드명 배열 길이가

&#x20; len(set(fields))와 일치하는지 assert. 불일치 시 E\_BADPARAM.

&#x20; 중복 필드 전달 금지(set으로 정규화 후 전송).



5.8 ★★★ 시가총액 산출과 천단위 함정 (신규 P-17)

&#x20; MarketEye에 시가총액 필드가 없으므로 계산한다.



&#x20;   listed = GetDataValue(FI\[20], i)      # 총상장주식수

&#x20;   price  = GetDataValue(FI\[4],  i)      # 현재가

&#x20;   mktcap = listed \* price

&#x20;   if g\_objCodeMgr.IsBigListingStock(code):

&#x20;       mktcap \*= 1000                    # ★필수



&#x20; 근거(대신증권 공식 안내): 상장주식수 20억 주 이상 종목은

&#x20; 필드 20이 천 단위로 제공된다. CpUtil.CpCodeMgr.IsBigListingStock(code)

&#x20; 가 해당 여부를 반환한다. (공식 예제 #24가 이 보정을 수행)

&#x20; 영향: 미보정 시 대형주 시총이 1/1000 → 시총 하한 필터에서

&#x20;       삼성전자·SK하이닉스 등이 전량 탈락. 조용히 실패하므로 위험.

&#x20; 교차검증(필수): StockChart 일봉 필드 13(시가총액)과 본 계산값을

&#x20;       전종목 대조. 불일치율 0%가 아니면 V-C10으로 원인 규명.

&#x20;       → 어느 쪽에 천단위 규칙이 적용되는지 확정 후 단일 소스 채택.



5.9 200종목 청크 루프 (공식 예제 #24 패턴 + 가드 주입)

&#x20;   codes = CodeMgr.GetStockListByMarket(1) \\

&#x20;         + CodeMgr.GetStockListByMarket(2)     # 1=거래소 2=코스닥

&#x20;   for chunk in chunked(codes, 200):

&#x20;       gov.acquire('nontrade')                  # ★예제에 없음

&#x20;       rows = marketeye(chunk, ME\_UNIVERSE)

&#x20;   ※ 예제의 for/continue 구조는 마지막 잔여 청크 처리를 별도

&#x20;     if문으로 빼고 있어 오류 유발 소지가 있다. chunked()로 단순화.

&#x20;   ※ 예산: 2,900종목 ÷ 200 = 15회 요청.

&#x20;     한도 60회/15초 기준 약 4초. 전종목 스냅샷은 병목이 아니다.



5.10 신규 VERIFY

&#x20; V-C10 MarketEye 필드20 기반 시총 vs StockChart 필드13 시총 정합성

&#x20; V-C11 [사양 CLOSED, 상세 10절] GetStockListByMarket 시장구분 상수 (1=거래소, 2=코스닥) 및

&#x20;       ETF/ETN/스팩/우선주 포함 여부. CpCodeMgr 보조 함수로 분리 확인

&#x20;       (GetStockSectionKind / GetStockSupervisionKind 등)

================================================================





================================================================

\[CREON-API] 6. StockCur 확정 사양 (실시간 체결)

출처: cybosplus.github.io/cpdib\_rtf\_1\_/stockcur.htm 원문

&#x20;     + 자료실 #8 공식 예제 대조, 2026-09-12 확인

모듈: cpdib.dll / ProgID "DsCbo1.StockCur"   ★모듈명≠ProgID

통신: Subscribe/Publish

================================================================



6.1 사용법

&#x20; SetInputValue(0, code) → Subscribe()  /  Unsubscribe()

&#x20; Request(), BlockRequest(), GetDataValue()는 사용하지 않음

&#x20; 수신은 Received 이벤트에서 GetHeaderValue로 읽는다



6.2 GetHeaderValue (원문)

&#x20; 0  종목코드(string)     1  종목명(string)

&#x20; 2  전일대비(long)       3  시간(long)

&#x20; 4  시가  5 고가  6 저가

&#x20; 7  매도호가  8 매수호가

&#x20; 9  누적거래량(long)   ★단위 주의 (6.3)

&#x20; 10 누적거래대금(long) ★단위 주의 (6.3)

&#x20; 13 현재가(long)

&#x20; 14 체결상태(char, 체결가방식) '1'매수 '2'매도

&#x20; 15 누적매도체결수량(체결가방식)  16 누적매수체결수량(체결가방식)

&#x20; 17 순간체결수량(long)

&#x20; 18 시간(초)

&#x20; 19 예상체결가 구분 플래그(char)

&#x20;      '1' 동시호가시간(예상체결)   '2' 장중(체결)

&#x20; 20 장구분 플래그(char)

&#x20;      '1' 장전예상체결  '2' 장중

&#x20;      '3' 장전시간외 \[주의] StockCur로는 수신되지 않음.

&#x20;                      필요 시 StockOutCur 사용

&#x20;      '4' 장후시간외   '5' 장후예상체결

&#x20; 21 장전시간외 거래량

&#x20; 22 대비부호(char) '1'상한 '2'상승 '3'보합 '4'하한 '5'하락

&#x20;                   '6'기세상한 '7'기세상승 '8'기세하한 '9'기세하락

&#x20; 23 LP보유수량  24 LP보유수량대비  25 LP보유율

&#x20; 26 체결상태(호가방식)

&#x20; 27 누적매도체결수량(호가방식)  28 누적매수체결수량(호가방식)



6.3 ★★★ 단위 정규화 (신규 P-18) — 원문 표

&#x20; 필드 9 누적거래량 기준 단위

&#x20;    거래소·코스닥·프리보드 ........ 단주

&#x20;    거래소 지수 ................... 천주

&#x20;    코스닥 지수·프리보드 지수 ..... 단주

&#x20; 필드 10 누적거래대금 기준 단위

&#x20;    거래소 ........................ 만원

&#x20;    코스닥·프리보드 ............... 천원

&#x20;    거래소 지수·코스닥 지수 ....... 백만원

&#x20;    프리보드 지수 ................. 천원

&#x20; 결론: 같은 필드인데 시장별로 단위가 10배 다르다.

&#x20; 정규화 규칙(필수) — 모든 값을 '원' 단위로 환산해 datahub에 적재

&#x20;    amount\_krw = raw \* 10\_000   (거래소/KOSPI 종목)

&#x20;    amount\_krw = raw \*  1\_000   (코스닥 종목)

&#x20;    amount\_krw = raw \* 1\_000\_000 (지수)

&#x20; 시장 판별은 CpCodeMgr.GetStockMarketKind(code)로 수행하며,

&#x20; 판별 불가 시 해당 틱을 폐기한다(추정 금지).

&#x20; 영향: 미정규화 시 코스닥 종목의 거래대금이 KOSPI 대비 1/10로

&#x20;       평가되어 VR 기반 위성 신호가 코스닥에서 발생하지 않는다.

&#x20; ※ MarketEye 필드 11은 '원' 단위이므로 환산 불필요.

&#x20;   두 소스를 혼용해 비율을 계산하는 코드는 금지(INVARIANT-12).



6.4 ★ 실체결/예상체결 분리 (신규 P-19)

&#x20; 필드 19 == ord('1') → 동시호가 예상체결. 실제 거래가 아님.

&#x20; 필드 19 == ord('2') → 장중 실체결.

&#x20; 위성 전략의 돌파·거래대금 판정은 19=='2' AND 20=='2' 인 틱만 사용.

&#x20; 공식 예제 #8은 예상체결도 동일하게 출력한다 → 그대로 쓰면

&#x20; 15:20\~15:30 동시호가의 예상체결이 돌파 신호로 오인된다.

&#x20; 종가 베팅의 동시호가 관찰은 MarketEye 필드 28/31(예상체결가·수량)을

&#x20; 사용하고, StockCur 예상체결 틱은 사용하지 않는다.



6.5 ★ 구독 관리 (신규 P-20, P-22)

&#x20; (1) WithEvents 핸들러를 지역변수로 두면 GC 대상이 되어 이벤트가

&#x20;     조용히 끊긴다. 공식 예제 #8의 CpStockCur.Subscribe()가

&#x20;     handler를 로컬에 두는 구조다 → 반드시 인스턴스 속성으로 보관.

&#x20;       self.\_handler = win32com.client.WithEvents(obj, CpEvent)

&#x20;     COM 객체와 핸들러를 dict\[code] = (obj, handler)로 동시 보관.

&#x20; (2) 구독 한도: CpCybos.GetLimitRemainCount(LT\_SUBSCRIBE)로 상시 감시.

&#x20;     예제는 200종목을 일괄 구독한다 → 프로젝트 상한은 50종목.

&#x20;     config: creon.subscribe.max\_codes = 50 (초기값 30 권장)

&#x20; (3) 재구독 전 반드시 기존 구독 해지. 예제의 StopSubscribe 패턴을

&#x20;     채택하되, 해지 실패도 로깅하고 계속 진행(부분 해지 누락 방지).

&#x20; (4) 연결 끊김(OnDisConnect) 시 구독은 전부 무효. 재연결 후

&#x20;     전량 재구독하며, 그 사이 수신 공백을 journal에 결측 구간으로 기록.

================================================================





================================================================

\[CREON-API] 7. CpSvrNew7043 상승률 상위 (준공식 / 예제 전용)

출처: 자료실 #8 공식 예제 (help 사이트에 문서 없음)

모듈: CpSysDib / ProgID "CpSysDib.CpSvrNew7043"

신뢰등급: SEMI-OFFICIAL — 예제에서 확인된 입력값만 사용. 확장 금지.

================================================================



7.1 예제에서 확인된 SetInputValue

&#x20; 0  시장구분(char)   '0' 거래소+코스닥

&#x20; 1  등락구분(char)   '2' 상승

&#x20; 2  기간(char)       '1' 당일

&#x20; 3  정렬기준(long)   21  전일대비 상위순

&#x20; 4  관리종목(char)   '1' 관리종목 제외

&#x20; 5  거래량조건(char) '0' 전체

&#x20; 6  표시항목(char)   '0' 시가대비

&#x20; 7  등락율 시작(long)  예: 0

&#x20; 8  등락율 끝(long)    예: 30

&#x20; ※ 위 값 이외의 코드값은 문서화되어 있지 않다. 추측해서 넣지 말 것.



7.2 GetHeaderValue / GetDataValue (예제 확인분)

&#x20; GetHeaderValue(0) 수신 개수

&#x20; GetHeaderValue(1) 전체 개수

&#x20; GetDataValue(0,i) 종목코드   (1,i) 종목명

&#x20; GetDataValue(3,i) 대비부호   (4,i) 대비   (6,i) 거래량

&#x20; ※ 이 서비스는 MarketEye와 달리 필드 오름차순 정렬 개념이 없고

&#x20;   고정 컬럼 구조다. 2,5 등 미확인 인덱스는 사용 금지.



7.3 ★ 연속조회 패턴 (Continue 속성) — 예제 정본

&#x20;   obj.BlockRequest()

&#x20;   ... 1페이지 처리 ...

&#x20;   while obj.Continue:            # ★Creon 연속조회는 .Continue

&#x20;       gov.acquire('nontrade')    # ★예제에 없음. 필수 주입

&#x20;       obj.BlockRequest()

&#x20;       ... 처리 ...

&#x20;       if len(result) >= LIMIT: break

&#x20; 안전장치(예제에 없음): 최대 반복 횟수 20회, 직전 페이지와 수신

&#x20; 개수·마지막 코드가 동일하면 진척 없음으로 판단하고 즉시 중단.



7.4 프로젝트 활용 방침

&#x20; 용도: 종가 스크리닝의 1차 축약 후보 추출(등락율 0\~30% 구간).

&#x20; 단독 사용 금지 — 다음 이유로 보조 수단에 한정한다.

&#x20;   (a) 문서화되지 않은 서비스로 사양 변경 시 무통보 파손 위험

&#x20;   (b) '관리종목 제외' 외 우리 하드필터(시총·ADV·경고)를 못 걸음

&#x20;   (c) 백테스트 시점에는 재현 불가 → 학습/실전 불일치(P-05) 유발

&#x20; ★백테스트 정합성 원칙: 실전 스크리닝은 반드시

&#x20;   MarketEye 전종목 스냅샷(15회 요청, 약 4초)을 정본으로 하고,

&#x20;   7043은 장중 모니터링 편의용으로만 쓴다.

&#x20;   백테스트와 실전이 동일 입력을 쓰지 않으면 G11(OOS/IS)이 무의미.

&#x20; ※ 예제의 200종목 상한은 MarketEye 1회 요청 한도에 맞춘 값이다.

================================================================





================================================================

\[CREON-API] 8. 기동 전 필수 점검 (공식 예제 #24 InitPlusCheck 채택)

================================================================

&#x20; (1) 관리자 권한 확인 — CYBOS Plus COM은 관리자 권한 필요

&#x20;       import ctypes

&#x20;       if not ctypes.windll.shell32.IsUserAnAdmin():

&#x20;           raise CreonEnvError('관리자 권한으로 실행하십시오')

&#x20; (2) 연결 확인 — CpUtil.CpCybos.IsConnect == 1

&#x20; (3) 서버 종류 확인 — ServerType == 1 (cybosplus 서버)

&#x20;       2(HTS 일반서버)면 일부 서비스가 동작하지 않는다 → 중단

&#x20; (4) 요청 잔량 확인 — GetLimitRemainCount(LT\_NONTRADE\_REQUEST)

&#x20; ★(5) 주문 초기화(CpTrade.CpTdUtil.TradeInit)는 절대 호출하지 않는다.

&#x20;      공식 예제 #24는 g\_objCpTrade를 Dispatch하지만 TradeInit은

&#x20;      주석처리해 두었다. 우리는 Dispatch 자체를 금지한다.

&#x20;      근거: INVARIANT-11 (주문은 키움 REST 단일 경로)

&#x20;      검증: T13 — creon32/ 전체에서 'CpTrade' grep 0건

================================================================





================================================================

\[PITFALLS] 신규 항목 P-17 \~ P-22

================================================================

P-17 상장주식수 천단위 미보정으로 대형주 전량 탈락

&#x20; 증상: 시총 1조 필터에 삼성전자가 걸러짐. 예외 없이 조용히 실패.

&#x20; 원인: MarketEye 필드 20은 20억주 이상 종목에서 천 단위 제공.

&#x20; 검출: T14 — 삼성전자(A005930) 시총이 300조 이상인지 단위 검사.

&#x20;       전종목 시총 상위 30개가 알려진 대형주와 일치하는지 확인.

&#x20; 예방: IsBigListingStock(code) 보정 강제. universe.py 단일 함수화.



P-18 StockCur 거래대금 시장별 단위 차이(만원/천원)

&#x20; 증상: 코스닥 종목에서 위성 돌파 신호가 거의 발생하지 않음.

&#x20; 원인: 거래소 만원 / 코스닥 천원. 10배 차이.

&#x20; 검출: T15 — 동일 종목을 StockCur와 MarketEye로 동시 조회해

&#x20;       '원' 환산 후 오차 1% 이내인지 검증(KOSPI·KOSDAQ 각 3종목).

&#x20; 예방: 수신 즉시 원 단위 정규화. 정규화 전 값은 datahub 진입 금지.



P-19 동시호가 예상체결을 실체결로 오인

&#x20; 증상: 15:20\~15:30에 위성 돌파 신호 폭증, 익일 재현 불가.

&#x20; 원인: StockCur 필드 19='1'(예상체결)을 필터링하지 않음.

&#x20; 검출: T16 — 15:20 이후 생성 신호 수가 장중 시간대 평균의

&#x20;       3배를 넘으면 FAIL.

&#x20; 예방: 19=='2' AND 20=='2' 틱만 사용.



P-20 WithEvents 핸들러 GC로 실시간 수신 무음 중단

&#x20; 증상: 수십 분 후 이벤트가 조용히 끊김. 예외 없음.

&#x20; 원인: 핸들러를 지역변수로 보관.

&#x20; 검출: T17 — 구독 종목의 최종 수신 시각을 30초 주기로 감시,

&#x20;       장중 5분 무수신이면 ALERT.

&#x20; 예방: dict\[code] = (com\_obj, handler) 로 강참조 유지.



P-21 GetHeaderValue 인덱스 의미의 서비스별 불일치

&#x20; 증상: 루프가 0회 또는 잘못된 횟수로 돌아 데이터 유실.

&#x20; 원인: MarketEye 종목개수=(2), StockChart 수신개수=(3),

&#x20;       7043 수신개수=(0)/전체개수=(1).

&#x20; 예방: 어댑터별 상수로 분리 정의하고 매직넘버 직접 사용 금지.



P-22 대량 구독으로 LT\_SUBSCRIBE 소진

&#x20; 증상: 일정 종목 수 이후 Subscribe가 조용히 실패.

&#x20; 원인: 공식 예제 #8처럼 200종목 일괄 구독.

&#x20; 검출: T18 — 구독 후 GetLimitRemainCount(LT\_SUBSCRIBE) 잔량이

&#x20;       전체의 30% 미만이면 FAIL.

&#x20; 예방: 구독 상한 50(권장 30), 교체 시 선해지 후 등록.

================================================================





================================================================

\[CLAUDE.md] INVARIANT 추가

================================================================

INVARIANT-12  단위·소스 혼용 금지

&#x20; 거래대금/거래량/시가총액은 datahub 진입 시점에

&#x20; '원' 및 '주' 단위로 정규화된 값만 저장한다.

&#x20; 서로 다른 소스(MarketEye / StockCur / StockChart)의 원시값을

&#x20; 직접 나누거나 비교하는 연산을 금지한다.

&#x20; 모든 비율 지표(VR, 거래대금배수)는 동일 소스·동일 단위 계열

&#x20; 내에서만 계산한다.

&#x20; 검증: T15, T19(소스 교차 정합성 리포트)



INVARIANT-13  필드 인덱스 수동 계산 금지

&#x20; MarketEye/StockChart 응답 접근은 field\_index\_map()이 만든

&#x20; dict를 경유해야 한다. GetDataValue에 정수 리터럴을 직접

&#x20; 넣는 코드는 리뷰에서 반드시 거부한다.

&#x20; 근거: 공식 예제 #8에 실제 정렬 버그 존재.

&#x20; 검증: T20 — 어댑터 소스에서 GetDataValue(<숫자리터럴> 패턴

&#x20;       grep 결과 0건이면 PASS (CI 포함)

================================================================





\## 6. DsCbo1.StockMst — 단일 종목 현재가 (공식 샘플 검증됨)



```python

objStockMst = win32com.client.Dispatch("DsCbo1.StockMst")

objStockMst.SetInputValue(0, code)

objStockMst.BlockRequest()



if objStockMst.GetDibStatus() != 0:

&#x20;   print("통신상태", objStockMst.GetDibStatus(), objStockMst.GetDibMsg1())

&#x20;   return False



cur       = objStockMst.GetHeaderValue(11)  # 종가(현재가)

diff      = objStockMst.GetHeaderValue(12)  # 전일대비

baseprice = objStockMst.GetHeaderValue(27)  # 기준가

exFlag    = objStockMst.GetHeaderValue(58)  # 예상플래그

viBase    = objStockMst.GetHeaderValue(80)  # 정적VI 발동 예상기준가

viexUp    = objStockMst.GetHeaderValue(81)  # 정적VI 발동 예상상승가

viexDown  = objStockMst.GetHeaderValue(82)  # 정적VI 발동 예상하락가



for i in range(10):                          # 10차 호가

&#x20;   offer    = objStockMst.GetDataValue(0, i)  # 매도호가

&#x20;   bid      = objStockMst.GetDataValue(1, i)  # 매수호가

&#x20;   offervol = objStockMst.GetDataValue(2, i)  # 매도호가 잔량

&#x20;   bidvol   = objStockMst.GetDataValue(3, i)  # 매수호가 잔량

```



주: 본 프로젝트는 다종목 효율 때문에 MarketEye 를 주로 쓰고,

&#x20;   StockMst 는 10차 호가/VI 기준가가 필요한 위성 전략 보조로만 쓴다.



\## 7. 에러 처리 공통 패턴



모든 RQ 객체는 GetDibStatus() / GetDibMsg1() 을 제공한다.

BlockRequest() 직후 반드시 확인한다.



```python

ret = obj.BlockRequest()

if obj.GetDibStatus() != 0:

&#x20;   raise CreonError(f"status={obj.GetDibStatus()} msg={obj.GetDibMsg1()}")

```



\## 8. VERIFY 목록 (구현 첫날 실환경 확인)



V-C01  업종 지수 코드: 코스피 'U001', 코스닥 'U201' 추정. GetIndustryList() 로 실제 확인

V-C02  Creon 자동 로그인 커맨드라인 인자 형식 (설치본 버전별 상이)

V-C03  거래량구분 '3' 설정 시 일봉 거래대금이 HTS \[7400]과 일치하는지 1종목 대조

V-C04  Python 3.11 32-bit + pywin32 COM 안정성 (3.12는 미검증)

V-C05  StockCur 누적거래대금 시장별 승수 실측 확인

V-C06  GetLimitRemainCount 가 15초 윈도 내에서 실제로 60에서 감소하는지 계측

================================================================
[CREON-API] 9. 종목코드 규칙 (V-C01 부분 CLOSED)
출처: 대신증권 Plus Q&A 공식 답변 (money2.creontrade.com,
      boardseq=60 seq=20267 / seq=22690), 2019-03-04
      + marketeye.htm / stockchart.htm 원문 교차확인
================================================================
  주식    A + 6자리   예) A003540, A005930   CYBOS tr7021/7024
  ETN     Q + 6자리   예) Q500001, Q530031   CYBOS 7021/7024
  업종    U + 3자리   예) U001               CYBOS tr7035/7036/7041/7042
  ELW     J + 6자리   예) J506633, J517016   CYBOS tr7714/8971
  선물옵션 CYBOS와 동일 표기
  ※ ETN은 CpStockCode로는 조회되지 않는다. CpCodeMgr로 전체 코드를
    받은 뒤 'Q' 접두어로 식별하라는 것이 공식 답변이다.
  ※ V-C01 잔여: U201(KOSDAQ종합)은 GetIndustryList/GetIndustryName
    실측으로 확정. U + 3자리 규칙 자체는 공식 확정됨.

  9.1 codec.py 단일 책임 (INV-10 확장)
    creon_to_kiwoom(c): 'A005930' -> '005930'  (A 접두어만 허용)
    kiwoom_to_creon(c): '005930'  -> 'A005930'
    assert_stock(c): 문자열이며 ASCII 'A' + 숫자 6자리 전체 일치, 아니면 예외
    kiwoom_to_creon도 ASCII 숫자 6자리 전체 일치만 허용(빈값·공백 거부)
    ★주식 외 상품(Q/J/U)이 주식 경로에 유입되면 즉시 예외.
      키움 주문 경로에는 어떤 경우에도 Q/J/U가 도달할 수 없다.
    공식 예제 #5는 요청 배열에 Q530031(ETN)을 섞는다. 시연 목적이며
    우리 유니버스에는 A 접두어 주식만 허용한다.
================================================================


================================================================
[CREON-API] 10. CpCodeMgr 확정 사양 (V-C11 CLOSED)
출처: cybosplus.github.io/cputil_rtf_1_/cpcodemgr.htm 원문
모듈: CpUtil.dll / ProgID "CpUtil.CpCodeMgr"
성격: 로컬 마스터 조회(서버 통신 아님)
================================================================

10.1 ★ 요청 한도 비소모 (설계상 매우 중요)
  CpCodeMgr는 로그인 시 내려받은 로컬 마스터를 읽는다.
  따라서 60회/15초(LT_NONTRADE_REQUEST) 한도를 소모하지 않는다고
  판단한다 → 종목당 반복 호출이 자유롭다.
  ※ V-C12로 실측 검증: 전종목(약 2,900) 루프 전후로
    GetLimitRemainCount(LT_NONTRADE_REQUEST) 값을 비교해
    감소가 0이면 확정. 감소가 있으면 RateGovernor 경유로 전환.
  ★검증 전에는 '비소모 가정'에 의존하는 코드를 작성하지 말 것.

10.2 시장구분 CPE_MARKET_KIND
  0 구분없음 / 1 거래소(KOSPI) / 2 코스닥 / 3 프리보드 / 4 KRX
  GetStockListByMarket(1) + GetStockListByMarket(2) = 우리 유니버스 원천
  GetStockMarketKind(code) → 해당 종목의 소속부 반환
  ★정정: 이전 문서의 'GetMarketKind'는 오기.
    정확한 함수명은 GetStockMarketKind(code) 이다.
    P-18 단위 정규화의 시장 판별은 이 함수를 사용한다.

10.3 ★ 하드필터 함수군 (MarketEye 조회 불필요)
  GetStockSupervisionKind(code)  관리구분
      0 일반종목 / 1 관리          → 1이면 배제
  GetStockStatusKind(code)       주식상태
      0 정상 / 1 거래정지 / 2 거래중단  → 0만 통과
  GetStockControlKind(code)      감리구분
      0 정상 / 1 주의 / 2 경고 / 3 위험예고 / 4 위험
      → 운용 규칙: 0, 1(주의)만 통과. 2,3,4 전량 배제.
  GetStockSectionKind(code)      부 구분
      1 주권 / 2 투자회사 / 3 부동산투자회사 / 4 선박투자회사
      5 사회간접자본투융자회사 / 6 주식예탁증서(DR)
      7 신주인수권증권 / 8 신주인수권증서 / 9 ELW
      10 ETF / 11 수익증권 / 12 해외ETF / 13 외국주권
      14 선물 / 15 옵션
      → ★운용 규칙: 1(주권)만 통과. 나머지 전량 배제.
        Q 접두어 차단과 함께 비주권 상품을 배제한다. 스팩 자동 배제는
        이 enum만으로 보장하지 않으므로 기존 스팩·기업인수 명칭 필터를 유지한다.
  GetStockListedDate(code)       상장일(long YYYYMMDD)
      → 상장 후 60거래일 미만 종목 배제(신규상장 필터)
  GetStockLacKind(code)          락구분
      0 없음 / 1 권리락 / 2 배당락 / 3 분배락 / 4 권배락
      5 중간배당락 / 6 권리중간배당락 / 99 기타
      → ★0이 아닌 날은 코어 전략 진입 금지(가격 불연속)
  GetStockParPriceChageType(code) 액면정보
      0 해당없음 / 1 액면분할 / 2 액면병합 / 99 기타
      → 수정주가 적용 검증(V-C09)의 대상 종목 선별에 사용
  IsStockCreditEnable(code)      신용가능 여부(BOOL)
      → 참고용. 우리는 레버리지 미사용(INVARIANT-07)

10.4 주문·체결 관련
  GetStockMemeMin(code)    매매 거래단위 주식수
      → ★주문 수량은 반드시 이 배수로 산출. 미준수 시 주문 거부.
  GetStockMarginRate(code) 매수 증거금율  (참고용)
  GetStockMaxPrice(code)   상한가 / GetStockMinPrice(code) 하한가
      → 지정가 상한 클램프. 상한가 종목 배제 판정에도 사용
  GetStockStdPrice(code)   권리락 등 기준가
  GetStockParPrice(code)   액면가
  GetStockYdOpenPrice / YdHighPrice / YdLowPrice / YdClosePrice
      → 전일 시/고/저/종가. 갭 계산을 차트 조회 없이 즉시 수행 가능.
        ★단, '현재 마스터' 기준이므로 백테스트에는 사용 금지(10.7)

10.5 ★ 테마 클러스터링 대체 경로 (theme.py 설계 변경)
  GetStockIndustryCode(code)   증권전산업종코드
  GetIndustryList()            증권전산업종 코드 리스트
  GetIndustryName(code)        업종명
  GetKosdaqIndustry1List()     코스닥 산업별 코드 리스트
  GetKosdaqIndustry2List()     코스닥 지수업종 코드 리스트
  GetGroupCodeList(code)       관심종목(700~799) 및 업종코드의 종목배열
                               예) GetGroupCodeList(24) = 증권업
  GetGroupName(code)           그룹/업종 명칭
  GetStockGroupCode(code)      그룹(계열사) 코드
  → 설계 변경: 기존 '뉴스·공시 키워드 + 5분봉 상관계수' 기반
    테마 클러스터링을 1차적으로 '증권전산업종코드 동일 그룹'으로
    대체한다. 결정론적·재현가능·무비용이며 LLM 의존이 없다.
    "동일 업종 내 3종목 이상이 일정 조건 동반 상승" 규칙을
    그대로 적용할 수 있다.
    뉴스 기반 클러스터링은 G1~G12 게이트 통과 후의 확장 항목으로
    후순위 이동. (업종코드는 우리 테마 개념보다 거칠다는 한계는 인정)
  대장주 판별: 동일 업종 클러스터 내
    시가총액 · 거래대금 · 등락률 가중점수 1위 = leader
    (뉴스 키워드 없이 산출 가능)

10.6 기타
  CodeToName(code)         종목명
  GetMarketStartTime()     장 시작 시각 (9시면 9 반환)
  GetMarketEndTime()       장 마감 시각 (오후 3시면 15 반환)
    → ★반일장·임시 변경 대응에 활용. 다만 '분' 단위가 없으므로
      15:20/15:30 등 세부 시각은 자체 캘린더로 관리(P-12).
  GetMemberList() / GetMemberName(code)  거래원(회원사)
  GetStockCapital(code)    자본금규모 0제외/1대/2중/3소
  GetStockFiscalMonth(code) 결산기
  GetStockKospi200Kind(code) KOSPI200 채용 구분
    (2011-04-01 이후 enum: 1건설기계 2조선운송 3철강소재
     4에너지화학 5정보통신 6금융 7필수소비재 8자유소비재)

10.7 ★★★ 백테스트 사용 금지 (신규 P-23)
  CpCodeMgr의 모든 반환값은 '현재 시점' 마스터다. 과거 시점의
  관리종목 여부·업종·상장주식수·전일종가를 알려주지 않는다.
  → 백테스트에서 CpCodeMgr 호출은 전면 금지(INVARIANT-14).
    과거 하드필터는 해당 시점까지 관측·저장된 PIT 마스터로만 판정한다.
    StockChart 필드 12/13은 일자별 데이터로 별도 적재한다.
    GetHeaderValue(17)은 봉별 필드가 아닌 응답 헤더이며 과거 상태 복원은
    보장되지 않는다(V-C-PIT01 OPEN). 과거 모든 봉에 이 값을 복제하지 않는다.
    PIT 필수 속성이 없으면 현재값으로 대체하지 않고 해당 평가를 중단한다.
  → 운영 절차: 매 거래일 장 종료 후 CpCodeMgr 전종목 스냅샷을
    lake/master_daily/asof=YYYYMMDD/ 로 적재한다. 이 일별 스냅샷의
    누적이 곧 미래의 PIT 마스터가 된다. 오늘부터 쌓지 않으면
    영구히 복원 불가하므로 스프린트 1주차에 최우선 구축한다.
  영향: 미준수 시 생존편향(P-15)이 백테스트 전체를 무효화한다.

10.8 ★ 문서 미기재 함수 (준공식)
  IsBigListingStock(code)  상장주식수 20억주 이상 여부
    → 공식 help 페이지의 CpCodeMgr 함수 목록에 없다.
      출처는 대신증권 자료실 #24 예제 및 안내문(공식)이다.
    신뢰등급 SEMI-OFFICIAL. 사용은 하되 반드시 방어한다.
      if not hasattr(mgr, 'IsBigListingStock'): raise CreonEnvError
    P-17 보정에 필수이므로 부재 시 기동을 중단한다(조용한 오류 방지).
================================================================


================================================================
[CREON-API] 11. 하드필터 구현 정본 (universe.py)
================================================================
  통과 조건 (전부 AND)
    1. 코드 접두어 'A'                      codec.assert_stock
    2. GetStockSectionKind == 1 (주권)
    3. GetStockSupervisionKind == 0
    4. GetStockStatusKind == 0
    5. GetStockControlKind in (0, 1)
    6. GetStockLacKind == 0
    7. 상장 경과일 >= 60 거래일            GetStockListedDate
    8. 시가총액 >= 임계값   ← MarketEye 필드20 × 필드4
                              + IsBigListingStock 보정 (P-17)
    9. adv20 >= 임계값      ← StockChart 일봉 필드 9(거래대금)
   10. 주가 범위 1,000 ~ 200,000원
   11. 당일 등락률 4 ~ 18%, 상한가 제외 (필드 33 대조)
   12. 전일 대비 갭 < 6%
  ※ 1~7은 CpCodeMgr(무통신), 8~12는 MarketEye/StockChart(통신).
    저비용 조건을 먼저 적용해 통신 대상을 최소화한다.
  ※ 백테스트에서는 1~7을 PIT 마스터 테이블로 치환한다(10.7).
================================================================

### 반영 시 정합성 보완 (2026-09-13)

- 위 11절은 공통 필터이며 SDD 4.4.2의 스팩·우선주·시간외·VI 등 추가 배제 조건도 유지한다.
- V-C11 CLOSED는 함수와 enum 사양 범위다. 실제 상품 포함 분포와 스팩 분류 보장은 별도 실측한다.
- V-C12 OPEN: 다른 조회를 차단하고 리셋 경계를 기록해 측정한다. 전후 잔량만 같아도 중간 리셋이 있으면 비소모 확정 불가. 검증 전에는 RateGovernor를 경유한다.
- V-C-PIT01 OPEN: StockChart 헤더 17의 과거 요청 시점 의미 및 과거 상태 재현성 검증. 확인 전 PIT 상태 소스로 사용 금지.
- 장 종료 스냅샷은 수집 완료 시각 이후에만 사용한다. 같은 날 15:10 판정에 장 종료 자료를 사용하지 않는다.
- 도움말 대조: [CpCodeMgr](https://cybosplus.github.io/cputil_rtf_1_/cpcodemgr.htm), [StockChart](https://cybosplus.github.io/cpsysdib_rtf_1_/stockchart.htm). 헤더 17의 과거 복원 보장은 문서에서 확인되지 않았다.

## 2026-09-13 CpCybos 개정 사양

- 시세 RQ 한도는 15초당 60건이며 초과 시 오류가 아닌 내부 블로킹이다. 따라서 `RateGovernor`는 지연 폭주 방어를 위해 필수다.
- `GetLimitRemainTime(limitType)`은 `LimitRequestRemainTime` 프로퍼티와 별개이며, 두 값을 혼동하지 않는다. 모든 RQ는 `BlockRequest2(1)`을 우선 사용하고 반환값과 `GetDibStatus()`를 함께 검사한다(V-C15).
- SB 공식 상한은 400건이나 프로젝트 구독 상한은 50종목이다. `SubscribeLatest()`를 사용하며, `StockCur` 틱 누적값은 거래대금 게이트에 사용하지 않는다.
- 위성 거래대금은 MarketEye 필드 11·10의 5초 폴링 누적으로 산출한다. 틱 누락률은 V-C14/T28로 실측한다.
- V-C02만 미해결 VERIFY로 유지한다. V-C07, V-C09, V-C10, V-C13~V-C16은 실환경 검증 대상으로 명시한다.

