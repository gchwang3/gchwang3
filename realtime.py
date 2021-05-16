import threading
import queue
import time
import pyupbit
import datetime
from collections import deque
import realcoin

import logging

printlog_filename = 'real_'+datetime.datetime.now().strftime('%Y_%m%d_%H_%M_%S')+'.log'

def printlog(message, *args):
    """인자로 받은 문자열을 파이썬 셸에 출력한다."""
    print(datetime.datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args)
    with open(printlog_filename, 'a') as out:
        out.flush()                 
        # print( message, *args, file=out)
        print(datetime.datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args, file=out)                
        out.flush()         

tickers = ["KRW-ADA", "KRW-LTC", "KRW-DOGE", "KRW-ETH", "KRW-DOT", "KRW-HUNT",\
            "KRW-CHZ", "KRW-SAND", "KRW-ATOM", "KRW-PLA", "KRW-XLM", "KRW-HBAR"]
# tickers = ["KRW-DOGE"]


class Consumer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q
        
        with open("upbit.txt", "r") as f:
            key0 = f.readline().strip()
            key1 = f.readline().strip()


        upbit = pyupbit.Upbit(key0, key1)
        self.ubit = upbit   
        self.pyupbit = pyupbit
        totalcash  = upbit.get_balance()
        printlog("보유현금", totalcash)
        cash = (totalcash * 0.95) / len(tickers)
        # cash = 5500

        price_curr = pyupbit.get_current_price(tickers)        
        printlog(price_curr)
        printlog('tickers len:', len(tickers))
        for ticker in tickers:
            printlog("ticker", ticker, cash )


        self.u = { }
        for ticker in tickers:
            self.u[ticker] = realcoin.Real1Percent(key0, key1, ticker, cash)
        printlog("init end")
    def run(self):
        price_curr = { }
        for ticker in tickers:
            price_curr[ticker] = None
        i = 0
        # check_buy = False        
        while True:

            try:
                if not self.q.empty():
                    price_open = self.q.get()
                    for ticker in price_open:
                        self.u[ticker].update(price_open[ticker], price_curr[ticker])

                price_curr = pyupbit.get_current_price(tickers)
                # time.sleep(0.03)                
                #time.sleep(1)                                
                time.sleep(0.5)                                                
                # printlog(price_curr)

                # printlog("##2")                
                for ticker in tickers:
                    # if self.u[ticker].can_i_buy(price_curr[ticker]) and check_buy == False:
                    if self.u[ticker].can_i_buy(price_curr[ticker]):                        
                        # check_buy = True                        
                        self.u[ticker].make_order()


                    if self.u[ticker].can_i_sell():
                        self.u[ticker].take_order_ask()                        
                    
                    if self.u[ticker].can_i_sell():                    
                        if self.u[ticker].can_i_sell_by_market(price_curr[ticker]):                        
                            printlog("ticker", ticker, "손절")
                            self.u[ticker].make_sell_cancel_order()    
                            self.u[ticker].make_sell_market_order()                               

                # 1 minutes
                if i == (5 * 60 * 1):
                # if i == (1):                
                # if True :                    
                    now = datetime.datetime.now()
                    for ticker in tickers:
                        printlog(f"{ticker} : 현재가 {price_curr[ticker]}, 목표가 {self.u[ticker].price_buy}, 매도가 {self.u[ticker].remain_price}, 매도잔량 {self.u[ticker].remain_volume}, ma {self.u[ticker].curr_ma15:.2f}/{self.u[ticker].curr_ma50:.2f}/{self.u[ticker].curr_ma120:.2f}, h {self.u[ticker].hold_flag}, w {self.u[ticker].wait_flag}")

                        
                    i = 0
                i += 1
            except Exception as x:
                # printlog(x.__class__.__name__)
                printlog("error")
                time.sleep(0.2)
                # break

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