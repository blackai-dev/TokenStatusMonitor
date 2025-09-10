import pandas as pd
import numpy as np
import websocket
import json
from scipy.signal import argrelextrema
import talib

class RSIDivergenceDetector:
    def __init__(self, symbol="MYXUSDT", timeframe="15m"):
        self.symbol = symbol
        self.timeframe = timeframe
        # Initialize empty DataFrame with columns
        self.df = pd.DataFrame(columns=['timestamp', 'close', 'rsi'])
        # Set explicit dtypes
        self.df = self.df.astype({'timestamp': 'datetime64[ns]', 'close': 'float64', 'rsi': 'float64'})
        self.ws_url = f"wss://fstream.binance.com/ws/{symbol.lower()}@kline_{timeframe}"
        
    def detect_divergence(self, lookback=20, order=5):
        """檢測 RSI 背離"""
        if len(self.df) < 50:
            return None
            
        # 計算 RSI 使用 talib
        rsi_values = talib.RSI(self.df['close'].values, timeperiod=14)
        self.df['rsi'] = pd.Series(rsi_values, index=self.df.index)
        
        # 找價格和 RSI 的局部極值
        price_highs = argrelextrema(self.df['close'].values, np.greater_equal, order=order)[0]
        price_lows = argrelextrema(self.df['close'].values, np.less_equal, order=order)[0]
        rsi_highs = argrelextrema(self.df['rsi'].values, np.greater_equal, order=order)[0]
        rsi_lows = argrelextrema(self.df['rsi'].values, np.less_equal, order=order)[0]
        
        signal = None
        
        # 檢測 Bearish 背離 (失效信號)
        if len(price_highs) >= 2 and len(rsi_highs) >= 2:
            p1, p2 = price_highs[-2], price_highs[-1]
            r1, r2 = rsi_highs[-2], rsi_highs[-1]
            
            if (p2 - p1 <= lookback and 
                self.df['close'].iloc[p2] > self.df['close'].iloc[p1] and  # 價格更高
                self.df['rsi'].iloc[r2] < self.df['rsi'].iloc[r1]):        # RSI 更低
                signal = {
                    'type': 'bearish_divergence',
                    'price_1': self.df['close'].iloc[p1],
                    'price_2': self.df['close'].iloc[p2],
                    'rsi_1': self.df['rsi'].iloc[r1],
                    'rsi_2': self.df['rsi'].iloc[r2],
                    'timestamp': self.df['timestamp'].iloc[-1]
                }
        
        return signal
    
    def on_message(self, ws, message):
        """WebSocket 訊息處理"""
        data = json.loads(message)
        kline = data['k']
        
        if kline['x']:  # K線收盤
            new_row = {
                'timestamp': pd.to_datetime(kline['T'], unit='ms'),
                'close': float(kline['c']),
                'rsi': np.nan  # Explicitly set rsi to NaN
            }
            new_df = pd.DataFrame([new_row], columns=['timestamp', 'close', 'rsi'])
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            
            # 保持最近 200 根 K線
            if len(self.df) > 200:
                self.df = self.df.tail(200).reset_index(drop=True)
            
            # 檢測背離
            divergence = self.detect_divergence()
            if divergence:
                self.send_alert(divergence)
    
    def send_alert(self, signal):
        """發送告警"""
        message = f"🔴 {self.symbol} RSI背離失效信號！\n"
        message += f"類型: {signal['type']}\n"
        message += f"價格: {signal['price_1']:.4f} → {signal['price_2']:.4f}\n"
        message += f"RSI: {signal['rsi_1']:.2f} → {signal['rsi_2']:.2f}\n"
        message += f"時間: {signal['timestamp']}"
        print(message)
