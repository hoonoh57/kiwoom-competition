\# 검증된 참조 코드 저장소



여기에는 "실제로 동작이 확인된" 코드만 넣는다.

추정으로 쓴 코드는 넣지 않는다.



\## 수집 지침 (구현 첫날 수행)



1\. Creon 도움말 원문 저장

&#x20;  https://cybosplus.github.io/cpsysdib\_rtf\_1\_/marketeye.htm

&#x20;  https://cybosplus.github.io/cpsysdib\_rtf\_1\_/stockchart.htm

&#x20;  https://cybosplus.github.io/cpdib\_rtf\_1\_/stockcur.htm

&#x20;  https://cybosplus.github.io/cputil\_rtf\_1\_/cpcybos.htm

&#x20;  https://cybosplus.github.io/cputil\_rtf\_1\_/cpcodemgr.htm

&#x20;  → docs/SAMPLES/creon\_help/\*.md 로 저장



================================================================

\[SAMPLES] 2. Creon 공식 파이썬 예제 (대신증권 CYBOS Plus 자료실)

접근 경로: CYBOS Plus 실행 → 도움말/공지사항 창 → 좌측 \[자료실]

&#x20;         필터: 상품=전체(65), 언어=파이썬(45)

&#x20;         ※ 상품=주식(32) ∩ 파이썬 = 28건

웹 게시판 동일 경로(로그인 필요):

&#x20; money2.daishin.com/e5/mboard/ptype\_basic/plusPDS/

&#x20;   DW\_Basic\_Read.aspx?boardseq=299\&seq={게시글번호}

&#x20; (확인된 예: seq=58 → 5분 차트 MACD 신호)

================================================================



2.1 저장 규칙

&#x20; docs/SAMPLES/creon\_official/<번호2자리>\_<slug>.py

&#x20;   예) 16\_stockchart\_all\_periods.py

&#x20;       24\_all\_stocks\_marketcap.py

&#x20;       08\_top200\_gainers\_realtime.py

&#x20;       04\_multi\_subscribe\_unsubscribe.py

&#x20;       02\_daily\_paging\_next.py

&#x20;       21\_realtime\_minute\_bar\_build.py

&#x20; 각 파일 최상단에 아래 헤더를 붙여 원문성을 보존한다.

&#x20;   # SOURCE : CYBOS Plus 자료실 #<번호> "<원제목>"

&#x20;   # DATE   : <작성일>  / RETRIEVED: <수집일>

&#x20;   # STATUS : VERBATIM (원문 무수정) | ADAPTED (GUI제거/가드주입)

&#x20;   # NOTE   : 원문은 요청제한 가드 없음 → RateGovernor 필수

&#x20; VERBATIM 원본은 절대 수정하지 않는다. 수정이 필요하면

&#x20; creon\_official/adapted/ 에 사본을 만들어 작업한다.



2.2 P0 (어댑터 구현 착수 전 필수 확보)

&#x20; #16 주식차트 조회(일간/주간/월간/분간/틱)   → ad\_stockchart 정본

&#x20; #24 전종목 시가총액 구하기                  → universe + 200청크 루프

&#x20; #08 당일 상승률 상위 200종목 실시간 통신     → MarketEye+StockCur 결합

&#x20; #05 복수종목 조회/실시간                    → ad\_marketeye 기본형

&#x20; #04 복수종목 실시간 등록/해지               → LT\_SUBSCRIBE 관리

&#x20; #02 주식 일자별 조회(다음)                  → 연속조회 정본

&#x20; + \[공통] 탭 12건 전량 (로그인/연결/요청제한/코드관리)  ★P0



2.3 P1 (설계 참고 전용 — 코드 이식 금지)

&#x20; #28 매수 주문 에러 처리   → 에러처리 패턴만 발췌

&#x20; #14 미체결+취소/일괄취소  → order\_fsm 상태기계 참고

&#x20; #10 주문 체결 실시간      → 체결 이벤트 처리 참고

&#x20; #17 분할 주문             → ADV 0.5% 분할 참고

&#x20; #19 잔고 일괄 매도        → 킬스위치 참고

&#x20; ※ INVARIANT-11: Creon 주문/계좌 API 호출 전면 금지.

&#x20;   위 예제는 '읽고 배우되 이식하지 않는다'.



2.4 P2 (전략·로깅 보강)

&#x20; #21 실시간 분차트 생성 / #11 VI 발동 감시 / #26 5분MACD

&#x20; #23 지표계산 / #22 당일손익 / #25 투자자별 / #15·#13 10차호가



2.5 첨부파일 존재 항목

&#x20; #15, #13 (우측 첨부 아이콘) → 다운로드 후

&#x20; docs/SAMPLES/creon\_official/attachments/ 에 원본 보관



2.6 추가 수집 대상 탭

&#x20; 공통(12)     ★P0  로그인/연결/제한/코드관리 추정

&#x20; 차트(3)            차트 조회 보강

&#x20; 종목검색(4)  ★P1  CssStgList 계열.

&#x20;                    키움 조건검색(5회/분) 봉인의 대체 후보로 평가

&#x20; 투자정보(4)        수급/재무 피처 후보



2.7 LLM 프롬프트 사용 규칙

&#x20; 어댑터 코드를 요청할 때 해당 P0 예제 파일을 반드시 첨부하고

&#x20; 다음 문장을 고정 포함한다.

&#x20;   "첨부된 공식 예제의 COM 객체명, 메서드명, SetInputValue

&#x20;    type 번호, 필드 번호를 그대로 복사하라. 추론·보정 금지.

&#x20;    예제에 없는 값이 필요하면 코드를 쓰지 말고 질문하라."

&#x20; 또한 예제 원문에 없는 다음 사항은 우리 규칙으로 덮어쓴다.

&#x20;   - RateGovernor 경유 호출 (INVARIANT-03)

&#x20;   - STA 단일 스레드 (INVARIANT-04)

&#x20;   - MarketEye 필드 오름차순 정렬 (INVARIANT-02)

&#x20;   - GUI(PyQt) 전면 제거



2.8 잔여 VERIFY 연계

&#x20; V-C02(자동로그인 인자)  → \[공통] 탭 수집 후 재판정

&#x20; V-C03(거래량구분 '3')   → #16 수집 후 재판정

&#x20; V-C01(U001/U201)        → \[공통]/\[차트] 탭 수집 후 재판정

================================================================



3\. 키움 공식 API 가이드의 Python 샘플 (★V-K01 해소용)

&#x20;  https://openapi.kiwoom.com/guide/apiguide

&#x20;  해당 API 페이지의 Python 탭 코드를 그대로 복사

&#x20;  → docs/SAMPLES/kiwoom\_official/{api\_id}.py

&#x20;  최소 필요: au10001, kt10000, kt10001, kt10002, kt10003,

&#x20;             ka10075, ka10076, WebSocket 예제



\## 이미 확보된 검증 코드



\- creon\_official/rate\_limit\_pattern.py  (CpTimeChecker, 공식 자료실)

\- creon\_official/stockmst\_currentprice.py (10차호가+VI, 공식 자료실)

\- kiwoom\_official/au10001\_token.py      (공식 가이드)



\## 사용 규칙



LLM 에게 코드 작성을 지시할 때, 해당 API 의 샘플이 이 디렉터리에 있으면

"docs/SAMPLES/xxx 를 기반으로 작성하라"고 명시한다.

샘플이 없는 API 는 추측 구현을 금지하고 먼저 샘플을 수집한다.



