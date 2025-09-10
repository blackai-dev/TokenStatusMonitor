# TokenStatusMonitor
監控三大失效信號：15分鐘 RSI 背離、持倉量急降、資金費率轉正

Exchange APIs → WebSocket Stream → Signal Detection → Alert System
     ↓              ↓                    ↓              ↓
  價格/OI/FR → 即時數據處理 → 失效信號檢測 → Telegram推播

目前先將 TG 通知移除，只留單機測試，可自行開發增加

https://asksurf.ai/share/9edb175b-1f78-4c84-9784-0aa7ee87562b
