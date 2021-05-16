import pyupbit
import time
from collections import deque
import datetime
printlog_filename = 'coin_'+datetime.datetime.now().strftime('%Y_%m%d_%H_%M_%S')+'.log'

coin_test = False #True

def printlog(message, *args):
    """인자로 받은 문자열을 파이썬 셸에 출력한다."""
    print(datetime.datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args)
    with open(printlog_filename, 'a') as out:
        out.flush()                 
        # print( message, *args, file=out)
        print(datetime.datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args, file=out)                
        out.flush()         


class Realcoin(pyupbit.Upbit):
    def __init__(self, key0, key1):
        super().__init__(key0, key1)

    def get_current_price(self, ticker):
        while True:
            price = pyupbit.get_current_price(ticker)
            if price != None:
                return price
            else:
                printlog("get_current_price wait")
                time.sleep(0.3)

    def buy_market_order(self, ticker, cash):
        while True:
            order = super().buy_market_order(ticker, cash)
            if order == None or 'error' in order:
                printlog("buy_market_order wait", ticker, cash, order)
                time.sleep(0.3)
                continue
            else:
                return order

    def get_order_detail(self, uuid):
        while True:
            order = super().get_order(uuid)
            if order != None and len(order['trades']) > 0:
                return order
            else:
                printlog("get_order_detail wait", uuid)
                time.sleep(0.3)

    def get_outstanding_order(self, ticker):
        while True:
            order = super().get_order(ticker)
            if order != None and len(order) == 0:
                return order
            else:
                printlog("get_outstanding_order wait", ticker)
                time.sleep(0.3)

    def get_balance(self, ticker="KRW"):
        while True:
            volume = super().get_balance(ticker)
            if volume != None:
                return volume
            else:
                printlog("get_balance wait", ticker)
                time.sleep(0.3)

    def sell_limit_order(self, ticker, price, volume):
        price = pyupbit.get_tick_size(price)
        while True:
            order = super().sell_limit_order(ticker, price, volume)
            if order != None and "uuid" in order:
                return order
            else:
                printlog("sell_limit_order wait", ticker, price, volume, order)
                time.sleep(0.3)

class Real1Percent(Realcoin):
    def __init__(self, key0, key1, ticker, cash):
        super().__init__(key0, key1)
        self.ticker = ticker

        self.ma15 = deque(maxlen=15)
        self.ma50 = deque(maxlen=50)
        self.ma120 = deque(maxlen=120)

        df = pyupbit.get_ohlcv(self.ticker, interval="minute1")
        self.ma15.extend(df['close'])
        self.ma50.extend(df['close'])
        self.ma120.extend(df['close'])

        self.price_curr = None
        self.hold_flag = False
        self.wait_flag = False
        self.remain_flag = False        
        self.remain_price = 0                
        self.remain_volume = 0                        
        self.cash = cash
        self.uuid = None
#        self.cash = 10000

    def update(self, price_open, price_curr):
        if self.price_curr != None:
            self.ma15.append(price_curr)
            self.ma50.append(price_curr)
            self.ma120.append(price_curr)

        self.curr_ma15 = sum(self.ma15) / len(self.ma15)
        self.curr_ma50 = sum(self.ma50) / len(self.ma50)
        self.curr_ma120 = sum(self.ma120) / len(self.ma120)

        if self.hold_flag == False:
            if coin_test:
                # 손절가 테스트 
                self.price_buy  = price_open * 0.99   
                self.price_sell = price_open * 1.10
            else:
                self.price_buy  = price_open * 1.01
                self.price_sell = price_open * 1.02

        self.wait_flag  = False

    def can_i_buy(self, price):
        # return self.wait_flag == False
        if coin_test:
            # 손절가 테스트 
            return self.hold_flag == False and self.wait_flag == False and \
                price >= self.price_buy
        else:
            return self.hold_flag == False and self.wait_flag == False and \
            price >= self.price_buy and self.curr_ma15 >= self.curr_ma50 and \
            self.curr_ma15 <= self.curr_ma50 * 1.03 and self.curr_ma120 <= self.curr_ma50

    def can_i_sell(self):
        return self.hold_flag == True

    def can_i_sell_by_market(self, price):
        return price <= (self.price_sell *0.98)


    def make_order(self):
        ret = self.buy_market_order(self.ticker, self.cash * 0.9995)
        order = ret                
        printlog("매수 주문",order['created_at'][11:-6],order['market'],'매수/매도',order['side'], order['state'],'금액',order['price'], '잔량',order['remaining_volume'])                                        

        time.sleep(3)
        #order = self.get_order(self.ticker)  # 호출시 error 발생하여, 현재 함수 탈출함. 
        # printlog('order',order)
        #printlog('주문정보',order['created_at'][0:-6],order['market'],order['side'], order['state'],order['price'], order['remaining_volume'])                                
        volume = self.get_balance(self.ticker)
        ret = self.sell_limit_order(self.ticker, self.price_sell, volume)
        order = ret                
        printlog("매도 주문",order['created_at'][11:-6],order['market'],'매수/매도',order['side'], order['state'],order['price'], '잔량',order['remaining_volume'])                                        
        # self.uuid = ret['uuid']
        self.hold_flag = True

    def make_sell_cancel_order(self):
        orders = self.get_order(self.ticker)        
        for order in orders:    
            if order['side'] == 'ask':            
                ret = self.cancel_order(order['uuid'])
                if ret == None or 'error' in ret:
                    printlog("매도 취소 에러",ret)
                    time.sleep(0.5)
                else:
                    printlog("매도 취소")

        orders = self.get_order(self.ticker)                            
        for order in orders:    
            if order['side'] == 'ask':            
                printlog('cancel wait')
                time.sleep(0.5)                                

    def make_sell_market_order(self):
        volume = self.get_balance(self.ticker)
        while True:        
            ret = self.sell_market_order(self.ticker, volume)
            time.sleep(0.5)                        
            if ret == None or 'error' in ret:
                printlog("시장가 매도 주문 에러", ret)
                time.sleep(0.5)
            else:
                order = ret
                printlog("시장가 매도주문",order['created_at'][11:-6],order['market'],'매수/매도',order['side'], order['state'],'금액',order['price'], '잔량',order['remaining_volume'])                                                        
                break

        orders = self.get_order(self.ticker)                            
        for order in orders:    
            if order['side'] == 'ask':            
                printlog('market ask wait')
                time.sleep(0.5)          
        remain_cash = self.get_balance()
        printlog("잔고 : ", remain_cash)
        self.hold_flag = False
        self.wait_flag = True
        self.remain_flag = False            
        self.remain_price = 0
        self.remain_volume = 0



    def take_order(self):
        # ticker 가 입력될 경우, 미체결시 주문이 있을 경우 리턴함. 
        uncomp = self.get_order(self.ticker) 
        printlog(uncomp)
        printlog("매도완료")        
        remain_cash = self.get_balance()
        printlog("잔고 : ", remain_cash)
        self.hold_flag = False
        self.wait_flag = True
    # 매도 주문 확인
    
    def take_order_ask(self): 
        orders = self.get_order(self.ticker)
        ask_count = 0
        for order in orders:    
            # printlog('주문확인', order['created_at'][11:-6],order['market'],order['side'], order['state'],order['price'], order['remaining_volume'])                            
            if order['side'] == 'ask':
                self.remain_price = order['price']
                self.remain_volume = order['remaining_volume']
                ask_count += 1

#        printlog("미채결 매도",ask_count)    
        if ask_count == 0:
            self.hold_flag = False
            self.wait_flag = True
            self.remain_flag = False            
            self.remain_price = 0
            self.remain_volume = 0
            printlog("매도완료")                    
            remain_cash = self.get_balance()
            printlog("잔고 : ", remain_cash)        
        else:
            self.hold_flag = True
            self.wait_flag = True
            self.remain_flag = True
        return ask_count == 0       

if __name__ == "__main__":
    with open("upbit.txt", "r") as f:
        key0 = f.readline().strip()
        key1 = f.readline().strip()

    # upbit =  Realcoin(key0, key1)
    # price = upbit.get_current_price("KRW-BTC")
    # order = upbit.get_order_detail("34cabb23-8171-4fd1-8f05-f25e312461c7")
    #order = upbit.get_outstanding_order("KRW-BTC")
    #printlog(order)
    coin = Real1Percent(key0, key1, "KRW-ADA", 100000)      
    #coin.make_sell_market_order()  # 시장가 판매 
    
    if coin.take_order_ask():
        printlog("매도 성공")
    else:
        printlog("매도 실패, 주문 취소진행")
        coin.make_sell_cancel_order()    
        coin.make_sell_market_order()      
        printlog("#33")
        coin.take_order_ask() 

