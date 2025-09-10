import time

class FundingRateMonitor:
    def __init__(self, symbol="MYXUSDT"):
        self.symbol = symbol
        self.rate_history = []
        
    def check_funding_flip(self, current_rate):
        """檢測資金費率轉正"""
        now = time.time()
        self.rate_history.append({'rate': current_rate, 'timestamp': now})
        
        # 保留 24小時歷史
        self.rate_history = [x for x in self.rate_history if now - x['timestamp'] < 86400]
        
        if len(self.rate_history) < 3:
            return None
            
        # 檢查是否從深度負值轉正
        recent_rates = [x['rate'] for x in self.rate_history[-10:]]  # 最近10次
        
        # 條件1：曾經深度負值
        had_deep_negative = any(rate < -0.02 for rate in recent_rates[:-1])  # 除了最新的
        
        # 條件2：現在轉正
        is_now_positive = current_rate > 0.001  # 0.1%
        
        if had_deep_negative and is_now_positive:
            min_rate = min(recent_rates[:-1])
            return {
                'type': 'funding_flip_positive',
                'min_rate': min_rate * 100,  # 轉為百分比
                'current_rate': current_rate * 100,
                'change': (current_rate - min_rate) * 100
            }
        
        return None
    
    def fetch_binance_funding_rate(self):
        """從 Binance API 獲取資金費率"""
        import requests
        url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={self.symbol}"
        response = requests.get(url)
        data = response.json()
        return float(data['lastFundingRate'])
