import pyupbit
import time
from collections import deque

class Realcoin(pyupbit.Upbit):
    def __init__(self, key0, key1):
        super().__init__(key0, key1)

    def get_current_price(self, ticker):
        while True:
            price = pyupbit.get_current_price(ticker)
            if price != None:
                return price
            else:
                print("get_current_price wait")
                time.sleep(0.3)

    def buy_market_order(self, ticker, cash):
        while True:
            order = super().buy_market_order(ticker, cash)
            if order == None or 'error' in order:
                print("buy_market_order wait", ticker, cash, order)
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
                print("get_order_detail wait", uuid)
                time.sleep(0.3)

    def get_outstanding_order(self, ticker):
        while True:
            order = super().get_order(ticker)
            if order != None and len(order) == 0:
                return order
            else:
                print("get_outstanding_order wait", ticker)
                time.sleep(0.3)

    def get_balance(self, ticker="KRW"):
        while True:
            volume = super().get_balance(ticker)
            if volume != None:
                return volume
            else:
                print("get_balance wait", ticker)
                time.sleep(0.3)

    def sell_limit_order(self, ticker, price, volume):
        price = pyupbit.get_tick_size(price)
        while True:
            order = super().sell_limit_order(ticker, price, volume)
            if order != None and "uuid" in order:
                return order
            else:
                print(price, volume, order)
                print("sell_limit_order wait", ticker, price, volume, order)
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
            self.price_buy  = price_open * 1.01
            self.price_sell = price_open * 1.02
            # self.price_buy  = price_open
            # self.price_sell = price_open
        self.wait_flag  = False

    def can_i_buy(self, price):
        # return self.wait_flag == False
        return self.hold_flag == False and self.wait_flag == False and \
            price >= self.price_buy and self.curr_ma15 >= self.curr_ma50 and \
            self.curr_ma15 <= self.curr_ma50 * 1.03 and self.curr_ma120 <= self.curr_ma50

    def can_i_sell(self):
        return self.hold_flag == True

    def can_i_sell_by_market(self, price):
        return price <= (self.price_sell *0.98)


    def make_order(self):
        ret = self.buy_market_order(self.ticker, self.cash * 0.9995)
        print("매수 주문", ret)

        order = self.get_order(ret['uuid'])
        print(order)
        volume = self.get_balance(self.ticker)

        ret = self.sell_limit_order(self.ticker, self.price_sell, volume)
        print("매도 주문", ret)
        self.uuid = ret['uuid']
        self.hold_flag = True

    def make_sell_market_order(self):
        while True:
            # volume = upbit.get_balance(self.ticker)
            # if volume != None:
            #     break
            ret = upbit.cancel_order(self.uuid)                            
            if ret == None or 'error' in ret:
                print("매도 취소 에러")
                time.sleep(0.5)
            else:
                print("매도 취소", ret)
                break

        volume = upbit.get_balance(self.ticker)
        while True:        
            ret = upbit.sell_market_order(volume)
            time.sleep(0.5)                        
            if ret == None or 'error' in ret:
                print("시장가 매도 주문 에러")
                time.sleep(0.5)
            else:
                print("시장가 매도주문", ret)
                break

    def take_order(self):
        uncomp = self.get_order(self.ticker)
        print(uncomp)
        print("매도완료")        
        remain_cash = self.get_balance()
        print("잔고 : ", remain_cash)
        self.hold_flag = False
        self.wait_flag = True


if __name__ == "__main__":
    with open("upbit.txt", "r") as f:
        key0 = f.readline().strip()
        key1 = f.readline().strip()

    upbit =  Realcoin(key0, key1)
    # price = upbit.get_current_price("KRW-BTC")
    # order = upbit.get_order_detail("34cabb23-8171-4fd1-8f05-f25e312461c7")

    order = upbit.get_outstanding_order("KRW-BTC")
    print(order)