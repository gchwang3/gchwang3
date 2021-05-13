import time
import pyupbit
import datetime

access = "your-access"
secret = "your-secret"

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

# 키값 로드

with  open("upbit.txt", 'r') as f:
    access = f.readline().strip()
    secret = f.readline().strip()


# 로그인 
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
time.sleep(1)


buy_list = "KRW-DOGE" # KRW-BTC
buy_name = "DOGE"

# 잔고조회
get_bals = upbit.get_balances()
#print(get_bals)
for bal in get_bals:
    print(bal['currency'], float(bal['balance']) * float(bal['avg_buy_price']), end=' ')    
    if int(bal['avg_buy_price']) !=0 :
        bal_val = float(pyupbit.get_current_price(bal['unit_currency']+'-'+ bal['currency']))
    else:
        bal_val = 0
    bal_val2 = float(bal['balance']) 
#    print('평가금액', bal_val, bal_val2, bal_val*bal_val2)
    print('평가금액',  bal_val*bal_val2)
#print(upbit.get_balances())
#quit() 


target_price = get_target_price(buy_list, 0.25)
ma15 = get_ma15(buy_list)
current_price = get_current_price(buy_list)
print("#tar : ", target_price, "cur: ", current_price, "ma15: ", ma15)   
start_time = get_start_time(buy_list)
end_time = start_time + datetime.timedelta(days=1)
print("tiem - start: ", start_time, "end:", end_time)


# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(buy_list)
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price(buy_list, 0.25)
            ma15 = get_ma15(buy_list)
            current_price = get_current_price(buy_list)

            if target_price < current_price and ma15 < current_price:
                krw = get_balance("KRW")                
                if krw > 5000:
                    buy_ret = upbit.buy_market_order(buy_list, krw*0.9995) # 시장가 매수 ( 종목 , 매수 금액)
                    print('buy_ret:', buy_ret, 'name', buy_list, 'KRW', krw*0.9995)
                # else:
                #     #print("krw low")
        else:
            btc = get_balance(buy_name) # "BTC"
            print("sell")
            if btc > 0.00008:
                sell_ret = upbit.sell_market_order(buy_list, btc*0.9995) # 시장가 매도 ( 종목, 수량)
                print('sell_ret', sell_ret , 'name', buy_list, 'KRW', btc*0.9995)                           
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)