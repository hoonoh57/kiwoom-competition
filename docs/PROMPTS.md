\# 세션 시작 프롬프트 템플릿



\## 표준 시작 프롬프트 (복사해서 사용)



```

프로젝트 루트의 CLAUDE.md 를 먼저 읽고 INVARIANTS 를 확인해줘.

그 다음 docs/SDD-QT-001.txt 의 \[해당 절 번호] 을 읽어줘.



작업: \[모듈명] 구현

참조 필수: docs/CREON-API.md \[해당 절] / docs/KIWOOM-API.md \[해당 절]

확인 필수: docs/PITFALLS.md 의 P-\[번호]

기반 코드: docs/SAMPLES/\[파일] (있으면)



문서에 확정값이 있는 항목은 추론하지 말고 그대로 써줘.

문서에 없는 API 사양은 지어내지 말고 VERIFY 목록에 추가하고 나에게 물어봐.

```



\## 모듈별 참조 매핑



rate\_governor.py     → SDD 3.3  / CREON 1절     / P-06 / SAMPLES rate\_limit\_pattern.py

com\_session.py       → SDD 3.1,3.2 / CREON 0,1절 / P-07

ad\_marketeye.py      → SDD 3.6  / CREON 3절     / P-01

ad\_stockchart.py     → SDD 3.7  / CREON 4절     / P-03, P-13

ad\_codemgr.py        → SDD 3.5  / CREON 2절     / P-15

ad\_stockcur.py       → SDD 3.2  / CREON 5절     / P-05

server.py            → SDD 3.4,3.9 / CREON 7절  / P-09

datahub.py           → SDD 4.2  / -             / P-10, INV-10

universe.py          → SDD 4.4.2 / CREON 2절    / P-15

regime.py            → SDD 4.3  / -             / P-14

theme.py             → SDD 4.4.4 / CREON 2절(GetStockGroupCode)

strategy\_core.py     → SDD 4.4  / -             / P-04, P-11

strategy\_sat.py      → SDD 4.5  / -             / P-05

risk.py              → SDD 6절  / -             / INV-06, INV-07

router.py            → SDD 4.4.6 / KIWOOM 6절   / P-08, P-11

kiwoom\_rest.py       → SDD 5절  / KIWOOM 2,3,4,6절 / P-08

kiwoom\_ws.py         → SDD 5절  / KIWOOM 5절

bt/engine.py         → SDD 7절  / -             / P-04, P-14, P-15, P-16

bt/costs.py          → SDD 7.2  / -             / P-16



\## 세션 종료 시 프롬프트



```

이번 세션에서 확정한 사항과 새로 발견한 VERIFY 항목,

그리고 PITFALLS 에 추가할 항목이 있으면 정리해줘.

CLAUDE.md 의 "현재 진행 상태" 체크박스도 갱신해줘.

```



\## 설계 변경 요청이 올 때 (LLM 자신에게)



CLAUDE.md 의 "금지 사항" 에 해당하면 거부하고 근거 절을 인용한다.

해당하지 않는 변경이면 SDD 를 먼저 수정하고 그 다음 코드를 수정한다.

코드만 바꾸고 문서를 방치하면 다음 세션에서 문서가 거짓이 된다.



