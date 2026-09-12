\# 프로젝트: 코어-위성 오버나이트 트레이딩 시스템 (QT)



\## 세션 시작 시 필수 동작



이 파일을 읽은 즉시 아래를 수행한다.



1\. `docs/SDD-QT-001.txt` (설계서) 를 읽는다. 모든 상수/스키마의 단일 진실 원천이다.

2\. 작업 대상이 Creon 관련이면 `docs/CREON-API.md` 를 읽는다.

3\. 작업 대상이 키움 주문/실시간이면 `docs/KIWOOM-API.md` 를 읽는다.

4\. 코드 작성 전 `docs/PITFALLS.md` 의 해당 항목을 확인한다.

5\. `docs/SAMPLES/` 에 검증된 참조 코드가 있으면 그것을 기반으로 한다.



문서에 확정값이 적혀 있는 항목은 절대 추론하지 말고 그대로 옮긴다.

문서에 없는 API 사양은 "모른다"고 말하고 VERIFY 목록에 추가한다. 지어내지 않는다.



\## 절대 위반 불가 규칙 (INVARIANTS)



INV-01  P1(32bit)에서 pyarrow / pandas / duckdb 를 import 하지 않는다.

&#x20;       허용 패키지: pywin32, pyzmq, msgpack, numpy 만.

&#x20;       Windows 32-bit 휠이 없어 반드시 실패한다.



INV-02  MarketEye / StockChart 응답 필드는 "요청 필드번호 오름차순"으로 정렬된다.

&#x20;       요청 배열 순서가 아니다. 반드시 sorted(fields) 기반 인덱스 맵을 쓴다.

&#x20;       이 규칙 위반은 예외 없이 값만 조용히 섞이는 최악 버그다.



INV-03  Creon 시세 요청은 15초당 60건. 모든 COM 호출은 RateGovernor 를 통과한다.

&#x20;       governor 없는 직접 호출 코드는 작성 금지.



INV-04  COM 객체는 단일 스레드에서만 생성/사용. 진입 시 pythoncom.CoInitialize().

&#x20;       멀티스레드 COM 접근 코드 작성 금지.



INV-05  백테스트는 모드 A(확정값)와 모드 B(15:10 시점값)를 항상 동시 산출한다.

&#x20;       공식 성과는 B. B/A < 0.70 이면 전략 폐기.

&#x20;       전략 모듈은 실전/백테스트가 동일 코드 경로를 타야 한다.



INV-06  risk.authorize() 가 반환한 AuthToken 없이 router.submit() 호출 불가.

&#x20;       타입 시그니처로 강제한다. 우회 경로 작성 금지.



INV-07  레버리지(신용/미수) 사용 코드 작성 금지. 주문구분에 신용 코드 미사용.



INV-08  StockChart 일반 조회 입력은 아래 5개를 고정한다.

```python
SetInputValue(9,  ord('1'))   # 수정주가
SetInputValue(10, ord('3'))   # 시간외 거래량 모두 제외
SetInputValue(11, ord('N'))   # 09:00 기준 분봉 주기
SetInputValue(12, ord('A'))   # 거래소구분 = KRX+NXT 전체
SetInputValue(13, ord('2'))   # KRX조회구분 = 정규장만
```

    12번 미지정 시 기본값 'K'(KRX only)로 NXT 체결분이 누락된다.
    NXT는 거래대금 기준 약 37%이므로 F08의 절대문턱 100억이 직접 깨진다.

    13번 미지정 시 기본값 '1'(애프터마켓 포함)이며 2026-09-14부터
    일봉 종가·고가·저가·거래량에 16:00~20:00 4시간이 혼입된다.
    RP·UW 등 당일 고저 기반 지표 정의가 무너진다.

    F11 애프터종가 조회만 krx_query_kind_afterhours='1'을 사용한다(SDD 3.6).
    다음 일반 조회는 krx_query_kind='2'로 복원한다.
    신규 설정 네 키 누락 시 기동 중단. 기본값 폴백 금지(SDD 3.7, T31).

    출처: boardseq=284&seq=102


INV-09  모든 주문에 client 생성 intent\_id(멱등키) 부여.

&#x20;       네트워크 타임아웃 시 재시도 전에 반드시 계좌조회로 실재 확인.



INV-10  Creon 종목코드는 'A005930', 키움은 '005930'.

&#x20;       변환은 datahub 경계의 단일 함수에서만. 레이크 표준은 접두 없는 6자리.



INV-17  2026-09-14 를 구조적 단절일로 고정한다.
        KRX 애프터마켓(16:00~20:00) 개설 및 시간외단일가 폐지로
        오버나이트 갭 분포가 변경된다. 이전 구간 갭 통계의 외삽 금지.
        G2 / G10 / G11 은 2026-09-13 이전 데이터만으로 최종 통과 판정하지
        않는다. TBD-F11 재추정 완료 전까지 코어 포지션 50% 제한
        (core.f11_transition.sizing_mult = 0.50).

INV-18  주문 전 세션을 판정하고, 애프터마켓 구간에서는 시장가
        (키움 trde_tp='3') 전송을 코드 레벨에서 차단한다.
        애프터마켓은 지정가·최우선지정가·최유리지정가만 허용된다.
        세션 경계를 하드코딩하지 않고 매 거래일
        CpCodeMgr.GetNewMarketEndTime(code) 로 조회한다.
        공식 도움말에 수능일 16:30 등 예외가 명기되어 고정 시각은 오작동한다.
        출처: boardseq=284&seq=11

\## 코드 스타일



\- Python 3.12 (P2/P3), Python 3.11 32-bit (P1)

\- 타입힌트 필수. dataclass / TypedDict 사용

\- 설정값 하드코딩 금지. 전부 config/system.yaml 참조

\- 모든 COM 호출과 REST 호출은 try/except 로 감싸고 구조화 로깅

\- 테스트는 tests/t01\~t23 번호 규칙 유지



\## 현재 진행 상태



\- \[ ] 1주차: P1 골격 (com\_session, rate\_governor, ad\_codemgr, health.status) + T01 + 매 거래일 장 종료 master_daily 스냅샷(P2 적재)

\- \[ ] 2주차: 데이터 파이프라인 (ad\_marketeye, ad\_stockchart, creon\_client, datahub) + T02\~T05

\- \[ ] 3\~4주차: 백테스트 + 코어 전략 (regime, theme, strategy\_core, bt/engine) + T06\~T09

\- \[ ] 5주차: 주문 게이트웨이 + 리스크 (kiwoom\_rest, order\_fsm, risk, router) + T10\~T12

\- \[ ] 6주차+: 위성 전략, ops UI, 단계적 롤아웃



게이트 미통과 시 다음 주차로 넘어가지 않는다.



\## 금지 사항 (설계 재협상 금지)



\- "스캘핑도 추가하자" → 거부. 왕복비용 0.35\~0.50%로 구조적 불가 (설계서 7.2)

\- "레버리지로 수익률 올리자" → 거부. G5 리스크오브루인 문턱 위반

\- "키움 조건검색 쓰자" → 거부. 분당 5회 제약. 의도적 미사용 (설계서 5절)

\- "백테스트 모드 A만 쓰자" → 거부. INV-05 위반





## 2026-09-13 추가 규칙

INVARIANT-14  백테스트는 PIT 데이터만 사용
  bt/ 이하 모든 코드에서 CpCodeMgr 및 실시간 조회 호출을 금지한다.
  과거 시점 판정은 lake/master_daily 스냅샷과 StockChart 일봉에
  적재된 값으로만 수행한다.
  검증: T21 (CI 포함)

INVARIANT-15  유니버스는 주권(SectionKind==1)만 포함
  ETF(10)·해외ETF(12)·ETN(Q접두어)·ELW(9)·DR(6)·리츠(3)·
  투자회사(2)·선박투자회사(4)·수익증권(11)·외국주권(13)을
  코어/위성 전략 대상에서 전면 배제한다.
  검증: T23 — 유니버스 표본 500종목의 SectionKind가 전부 1

- INV-10 확장: codec.py에서 A + ASCII 숫자 6자리만 주식 변환에 허용한다. Q/J/U는 주문 경로 진입 전에 예외 처리한다. 기존 INV-09는 주문 멱등성으로 유지한다.
- INV-03 유지: CpCodeMgr도 V-C12 비소모 실측 완료 전 RateGovernor를 경유한다.
- INVARIANT-14 보완: StockChart 헤더 17로 과거 상태를 복원하지 않는다(V-C-PIT01 OPEN). PIT 결측은 현재 마스터로 보충하지 않는다. 스냅샷 수집 완료 시각 이후에만 사용한다.
- INVARIANT-15 보완: SectionKind==1만으로 스팩 제외를 보장하지 않는다. SDD의 스팩·우선주 추가 필터를 유지한다.
- T21~T23은 구현할 수락 테스트이며, 문서 등록은 실행·통과를 의미하지 않는다.

- INVARIANT-03 개정: Creon 시세 RQ는 `rate_governor.acquire('nontrade')`와 `BlockRequest2(1)`을 거친다. 한도 초과는 내부 블로킹으로 처리되므로 우회 금지.
- INVARIANT-16: 거래대금·거래량 게이트는 MarketEye 누적값 차분만 사용한다. StockCur 틱 누적은 사용하지 않으며 `SubscribeLatest()`를 사용한다.
- T28~T30과 V-C14~V-C16은 실환경 검증 항목이다. 구현 전까지 틱 기반 게이트와 미검증 BlockRequest2 지원을 전제로 하지 않는다.
