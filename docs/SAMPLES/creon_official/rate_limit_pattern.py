# 출처: 대신증권 CYBOS Plus 사이보스플러스자료실 공식 샘플
# 검증 상태: 공식 배포 코드
# 용도: 요청 제한 대기 패턴의 원형. 프로젝트 RateGovernor 의 1차 방어 기반

import win32com.client
import time

g_objCpStatus = win32com.client.Dispatch("CpUtil.CpCybos")


class CpTimeChecker:
    def __init__(self, checkType):
        # 0: 주문 관련, 1: 시세 요청 관련, 2: 실시간 요청 관련
        self.chekcType = checkType

    def checkRemainTime(self):
        # 연속 요청 가능 여부 체크
        remainTime = g_objCpStatus.LimitRequestRemainTime
        remainCount = g_objCpStatus.GetLimitRemainCount(self.chekcType)
        print("남은 시간", remainTime, "남은 개수", remainCount)

        if remainCount <= 0:
            timeStart = time.time()
            while remainCount <= 0:
                time.sleep(remainTime / 1000)
                remainCount = g_objCpStatus.GetLimitRemainCount(1)
                remainTime = g_objCpStatus.LimitRequestRemainTime
                print(remainCount, remainTime)
            ellapsed = time.time() - timeStart
            print("시간 지연:", ellapsed,
                  "남은 시세 요청 개수:", remainCount, "시간:", remainTime)


# 프로젝트 확장 지침:
#   - SAFETY_MARGIN = 8 (0이 아니라 8에서 미리 대기)
#   - 클라이언트 슬라이딩 윈도(15000ms / 52건) 이중 방어 추가
#   - print 대신 구조화 로깅
#   - 우선순위 큐와 결합 (prio<=3 존재 시 prio=9 양보)
