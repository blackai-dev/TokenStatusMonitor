import time

class OpenInterestMonitor:
    def __init__(self, symbol="MYXUSDT"):
        self.symbol = symbol
        self.oi_history = []
        
    def check_oi_drop(self, current_oi):
        """檢測持倉量急速下降"""
        now = time.time()
        self.oi_history.append({'oi': current_oi, 'timestamp': now})
        
        # 保留 2小時歷史
        self.oi_history = [x for x in self.oi_history if now - x['timestamp'] < 7200]
        
        if len(self.oi_history) < 2:
            return None
            
        # 5分鐘降幅檢測
        five_min_ago = [x for x in self.oi_history if now - x['timestamp'] >= 300]
        if five_min_ago:
            old_oi = five_min_ago[-1]['oi']
            drop_5min = (old_oi - current_oi) / old_oi * 100
            if drop_5min > 15:
                return {'type': 'oi_drop_5min', 'drop_pct': drop_5min, 'old_oi': old_oi, 'new_oi': current_oi}
        
        # 1小時降幅檢測
        one_hour_ago = [x for x in self.oi_history if now - x['timestamp'] >= 3600]
        if one_hour_ago:
            old_oi = one_hour_ago[-1]['oi']
            drop_1hour = (old_oi - current_oi) / old_oi * 100
            if drop_1hour > 30:
                return {'type': 'oi_drop_1hour', 'drop_pct': drop_1hour, 'old_oi': old_oi, 'new_oi': current_oi}
        
        return None
    
    def fetch_binance_oi(self):
        """從 Binance API 獲取持倉量"""
        import requests
        url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={self.symbol}"
        response = requests.get(url)
        data = response.json()
        return float(data['openInterest'])
