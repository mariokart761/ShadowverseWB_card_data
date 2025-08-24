# Shadowverse WB 牌組爬蟲腳本 (簡化版本)

## 概述

`deck_crawler_simple.py` 是 `deck_crawler.py` 的簡化版本，專門用於爬取直接返回 JSON 格式的牌組資訊 API。

## 主要差異

### 原始版本 (`deck_crawler.py`)
- 使用 Selenium 進行完整的網頁爬取
- 支持複雜的網頁結構解析
- 包含多種備用數據提取方法
- 需要 Chrome WebDriver
- 適合處理動態生成的內容

### 簡化版本 (`deck_crawler_simple.py`)
- 使用 `requests` 直接請求 JSON API
- 移除複雜的網頁解析邏輯
- 更輕量級，啟動更快
- 僅依賴標準 HTTP 請求
- 適合直接提供 JSON 的 API

## 功能特點

### 核心功能
- ✅ 直接從 JSON API 獲取牌組資訊
- ✅ 自動格式化數據結構
- ✅ 錯誤處理和重試機制
- ✅ 支援超時設置

### 數據處理
- ✅ 提取 `total_red_ether` (紅以太總數)
- ✅ 提取 `num_follower` (從者數量)
- ✅ 提取 `num_spell` (法術數量)
- ✅ 提取 `num_amulet` (護符數量)
- ✅ 提取 `mana_curve` (法力曲線)
- ✅ 提取 `battle_format` (對戰格式)
- ✅ 提取 `class_id` (職業ID)
- ✅ 提取 `sub_class_id` (子職業ID)
- ✅ 提取 `sort_card_id_list` (排序卡牌ID列表)
- ✅ 提取 `deck_card_num` (牌組卡牌數量)

### 工具函數
- ✅ `extract_deck_hash_from_url()` - 從 URL 提取牌組 Hash

## 使用方法

### 基本用法

```python
from deck_crawler_simple import scrape_shadowverse_deck_simple

# 直接爬取牌組資訊
url = "https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=2.5.cYLU.cYLU.cYb6.cYb6.cYb6.cYqk.cYqk.ckYk.ckYk.ckaI.ckaI.ckoW.ckoW.ckoW.ckog.ckog.ckrU.ckrU.ckrU.cl1-.cl1-.cl1-.cl28.cl28.cl28.cl2I.cl2I.cl2I.cxFE.cxFE.d6mk.d6mk.d6mk.d6zE.d6zE.d6zE.d7SU.d7SU.d7Se.d7Se&lang=cht"

deck_info = scrape_shadowverse_deck_simple(url)
print(deck_info)
```

### 進階用法

```python
from deck_crawler_simple import ShadowverseDeckScraperSimple, extract_deck_hash_from_url

# 使用類對象（可重用會話）
with ShadowverseDeckScraperSimple(timeout=60) as scraper:
    deck_info = scraper.scrape_deck_info(url)

# 提取牌組 Hash
deck_hash = extract_deck_hash_from_url(url)
print(f"牌組 Hash: {deck_hash}")
```

### 命令行運行

```bash
python deck_crawler_simple.py
```

## 依賴項目

- ✅ `requests` - HTTP 請求庫 (已包含在 `requirements.txt`)

## 輸出格式

腳本會生成以下格式的 JSON 數據：

```json
{
  "total_red_ether": 0,
  "num_follower": 0,
  "num_spell": 0,
  "num_amulet": 0,
  "mana_curve": {},
  "battle_format": 2,
  "class_id": 5,
  "sub_class_id": null,
  "sort_card_id_list": [],
  "deck_card_num": {}
}
```

## 錯誤處理

腳本包含完善的錯誤處理：

- ✅ 網路請求失敗
- ✅ JSON 解析錯誤
- ✅ 數據格式化錯誤
- ✅ 超時處理

## 適用場景

### 推薦使用簡化版本的情況
- 目標 API 直接返回 JSON 格式
- 不需要處理複雜的網頁結構
- 希望更快的啟動速度
- 資源有限的環境

### 仍需使用原始版本的情況
- 網站使用大量 JavaScript 生成內容
- 需要模擬用戶行為（如點擊、滾動）
- 處理動態載入的內容
- 需要繞過反爬蟲機制

## 性能比較

| 指標 | 原始版本 | 簡化版本 |
|------|----------|----------|
| 啟動時間 | 慢 (需啟動瀏覽器) | 快 (直接請求) |
| 記憶體使用 | 高 | 低 |
| 網路請求 | 複雜 | 簡單 |
| 依賴複雜度 | 高 (Selenium + Chrome) | 低 (僅 requests) |
| 適用場景 | 複雜網頁 | JSON API |

## 擴展建議

如果需要處理其他格式的 API，可以：

1. 修改 `format_deck_data()` 方法適配新的數據結構
2. 添加自定義的請求頭或參數
3. 實現數據驗證邏輯
4. 添加重試機制

## 相關文件

- `deck_crawler.py` - 完整的 Selenium 版本
- `requirements.txt` - 項目依賴
- `scraped_deck_info_simple.json` - 輸出示例
