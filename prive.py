import struct
import win32com.client

# 0) 32비트 파이썬인지 확인 (크레온은 32비트만 됩니다)
if struct.calcsize("P") * 8 != 32:
    print("[중단] 32비트 파이썬이 필요합니다. 지금은 64비트입니다.")
    raise SystemExit

# 1) 크레온 연결 확인
cybos = win32com.client.Dispatch("CpUtil.CpCybos")
if cybos.IsConnect == 0:
    print("[중단] 크레온에 연결되지 않았습니다. 크레온을 켜고 로그인하세요.")
    raise SystemExit

# 2) 삼성전자 시세 요청
stock = win32com.client.Dispatch("DsCbo1.StockMst")
stock.SetInputValue(0, "A005930")   # A005930 = 삼성전자
stock.BlockRequest()

if stock.GetDibStatus() != 0:
    print("[실패]", stock.GetDibMsg1())
    raise SystemExit

# 3) 결과 출력
name  = stock.GetHeaderValue(1)    # 종목명
price = stock.GetHeaderValue(11)   # 현재가
print(f"{name} 현재가: {price:,}원")
