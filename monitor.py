import asyncio
import time
from datetime import datetime
import websocket
from rsidector import RSIDivergenceDetector
from oidector import OpenInterestMonitor
from funddector import FundingRateMonitor

class MYXFailureSignalMonitor:
    def __init__(self):
        self.rsi_detector = RSIDivergenceDetector("MYXUSDT")
        self.oi_monitor = OpenInterestMonitor("MYXUSDT")
        self.funding_monitor = FundingRateMonitor("MYXUSDT")
        
    async def send_alert(self, message):
        """輸出告警到控制台"""
        print(f"[ALERT] {datetime.now()}: {message}")
    
    async def monitor_loop(self):
        """主監控循環"""
        while True:
            try:
                # 檢測持倉量
                print("Fetching open interest...")  # Debug
                current_oi = self.oi_monitor.fetch_binance_oi()
                print(f"Open Interest: {current_oi}")  # Debug
                oi_signal = self.oi_monitor.check_oi_drop(current_oi)
                
                if oi_signal:
                    message = f"⚠️ $MYX 持倉量急降失效信號！\n"
                    message += f"類型: {oi_signal['type']}\n"
                    message += f"降幅: {oi_signal['drop_pct']:.2f}%\n"
                    message += f"持倉量: {oi_signal['old_oi']:,.0f} → {oi_signal['new_oi']:,.0f}"
                    await self.send_alert(message)
                
                # 檢測資金費率
                print("Fetching funding rate...")  # Debug
                current_funding = self.funding_monitor.fetch_binance_funding_rate()
                print(f"Funding Rate: {current_funding}")  # Debug
                funding_signal = self.funding_monitor.check_funding_flip(current_funding)
                
                if funding_signal:
                    message = f"🔄 $MYX 資金費率轉正失效信號！\n"
                    message += f"從 {funding_signal['min_rate']:.3f}% 轉為 {funding_signal['current_rate']:.3f}%\n"
                    message += f"變化幅度: +{funding_signal['change']:.3f}%"
                    await self.send_alert(message)
                
                await asyncio.sleep(30)  # 30秒檢查一次
                
            except Exception as e:
                print(f"監控循環錯誤: {e}")
                await asyncio.sleep(60)
    
    def start_monitoring(self):
        """啟動監控"""
        print("啟動 $MYX 失效信號監控系統...")
        
        # 啟動 RSI WebSocket 監控
        def start_rsi_ws():
            ws = websocket.WebSocketApp(
                self.rsi_detector.ws_url,
                on_message=self.rsi_detector.on_message,
                on_error=lambda ws, error: print(f"RSI WebSocket 錯誤: {error}"),
                on_close=lambda ws: print("RSI WebSocket 連線關閉")
            )
            ws.run_forever()
        
        # 在背景執行緒啟動 WebSocket
        import threading
        threading.Thread(target=start_rsi_ws, daemon=True).start()
        
        # 啟動主監控循環
        asyncio.run(self.monitor_loop())

# 使用範例
if __name__ == "__main__":
    monitor = MYXFailureSignalMonitor()
    monitor.start_monitoring()
