import threading
import queue
import time
import pyupbit
import datetime
from collections import deque
import realcoin

tickers = ["KRW-ADA", "KRW-LTC", "KRW-DOGE", "KRW-ETH", "KRW-DOT", "KRW-HUNT"]

class Consumer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q

        with open("upbit.txt", "r") as f:
            key0 = f.readline().strip()
            key1 = f.readline().strip()

        upbit = pyupbit.Upbit(key0, key1)
        totalcash  = upbit.get_balance()
        print("보유현금", totalcash)
        cash = (totalcash * 0.8) / len(tickers)
        print("보유현금", totalcash)
        for ticker in tickers:
            print("ticker", ticker, cash )

        self.u = { }
        for ticker in tickers:
            self.u[ticker] = realcoin.Real1Percent(key0, key1, ticker, cash)

    def run(self):
        price_curr = { }
        for ticker in tickers:
            price_curr[ticker] = None

        i = 0
        while True:
            try:
                if not self.q.empty():
                    price_open = self.q.get()
                    for ticker in price_open:
                        self.u[ticker].update(price_open[ticker], price_curr[ticker])

                price_curr = pyupbit.get_current_price(tickers)

                for ticker in tickers:
                    if self.u[ticker].can_i_buy(price_curr[ticker]) :
                        self.u[ticker].make_order()

                    if self.u[ticker].can_i_sell():
                        self.u[ticker].take_order()
                        if self.u[ticker].can_i_sell_by_market(price_curr[ticker]):                        
                            print("ticker", ticker, "손절")
                            self.u[ticker].make_sell_market_order

                # 1 minutes
                if i == (5 * 60 * 1):
                    now = datetime.datetime.now()
                    for ticker in tickers:
                        print(f"[{now}] {ticker} : 현재가 {price_curr[ticker]}, 목표가 {self.u[ticker].price_buy}, ma {self.u[ticker].curr_ma15:.2f}/{self.u[ticker].curr_ma50:.2f}/{self.u[ticker].curr_ma120:.2f}, hold_flag {self.u[ticker].hold_flag}, wait_flag {self.u[ticker].wait_flag}")
                    i = 0
                i += 1
            except:
                print("error")

            time.sleep(0.2)

class Producer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q

    def run(self):
        while True:
            prices = pyupbit.get_current_price(tickers)
            self.q.put(prices)
            time.sleep(60)

q = queue.Queue()
Producer(q).start()
Consumer(q).start()