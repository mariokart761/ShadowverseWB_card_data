# Shadowverse WB 牌組資訊爬蟲

這是一個用於爬取 Shadowverse: Worlds Beyond 牌組資訊的 Python 腳本。

## 功能特色

- 支援從 shadowverse-wb.com 爬取牌組詳細資訊
- 優先使用 API 方式獲取資料，失敗時自動降級到 Selenium 爬取
- 回傳 JSON 格式的結構化資料
- 只提取必要的牌組資訊欄位
- 支援無頭模式運行

## 安裝需求

### 1. 安裝 Python 依賴

```bash
pip install -r requirements_shadowverse_scraper.txt
```

### 2. 安裝 Chrome 瀏覽器

確保系統已安裝 Google Chrome 瀏覽器。

### 3. ChromeDriver

腳本會自動處理 ChromeDriver，但如果遇到問題，可以手動安裝：

```bash
pip install webdriver-manager
```

## 使用方法

### 基本使用

```python
from shadowverse_deck_scraper import scrape_shadowverse_deck

# 牌組 URL
url = "https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=2.5.cYLU.cYLU.cYb6.cYb6.cYb6.cYqk.cYqk.ckYk.ckYk.ckaI.ckaI.ckoW.ckoW.ckoW.ckog.ckog.ckrU.ckrU.ckrU.cl1-.cl1-.cl1-.cl28.cl28.cl28.cl2I.cl2I.cl2I.cxFE.cxFE.d6mk.d6mk.d6mk.d6zE.d6zE.d6zE.d7SU.d7SU.d7Se.d7Se&lang=cht"

# 爬取資料
deck_info = scrape_shadowverse_deck(url)
print(deck_info)
```

### 直接運行主腳本

```bash
python shadowverse_deck_scraper.py
```

## 回傳資料格式

腳本會回傳包含以下欄位的 JSON 物件：

```json
{
  "total_red_ether": 68710,
  "num_follower": 32,
  "num_spell": 6,
  "num_amulet": 2,
  "mana_curve": { "2": 14, "3": 7, "4": 2, "5": 5, "7": 7, "8": 5 },
  "battle_format": 2,
  "class_id": 5,
  "sub_class_id": null,
  "sort_card_id_list": [
    10103110, 10152110, 10153120, 10153310, 10251310, 10102110, 10252110,
    10152210, 10153130, 10154130, 10254120, 10104110, 10204110, 10154120,
    10154110, 10254110
  ],
  "deck_card_num": {
    "10103110": 3,
    "10152110": 2,
    "10153120": 3,
    "10153310": 3,
    "10251310": 3,
    "10102110": 2,
    "10252110": 3,
    "10152210": 2,
    "10153130": 2,
    "10154130": 3,
    "10254120": 2,
    "10104110": 2,
    "10204110": 2,
    "10154120": 3,
    "10154110": 3,
    "10254110": 2
  }
}
```

## 欄位說明

- `total_red_ether`: 總紅以太消耗
- `num_follower`: 隨從卡數量
- `num_spell`: 法術卡數量
- `num_amulet`: 護符卡數量
- `mana_curve`: 法力曲線（費用 -> 卡牌數量）
- `battle_format`: 對戰格式 ID
- `class_id`: 主職業 ID
- `sub_class_id`: 副職業 ID（如果有）
- `sort_card_id_list`: 排序後的卡牌 ID 列表
- `deck_card_num`: 每張卡的數量（卡牌 ID -> 數量）

## 進階用法

### 自訂參數

```python
from shadowverse_deck_scraper import ShadowverseDeckScraper

# 使用自訂參數
with ShadowverseDeckScraper(headless=False, timeout=60) as scraper:
    deck_info = scraper.scrape_deck_info(url)
```

### 批次處理

```python
urls = [
    "url1",
    "url2",
    "url3"
]

results = []
for url in urls:
    try:
        deck_info = scrape_shadowverse_deck(url)
        results.append({"url": url, "data": deck_info, "success": True})
    except Exception as e:
        results.append({"url": url, "error": str(e), "success": False})
```

## 故障排除

### 常見問題

1. **ChromeDriver 錯誤**
   - 確保已安裝 Google Chrome
   - 嘗試更新 Chrome 到最新版本
   - 手動安裝 webdriver-manager

2. **網路超時**
   - 增加 timeout 參數值
   - 檢查網路連線

3. **爬取失敗**
   - 檢查 URL 是否正確
   - 確認網站是否可正常訪問
   - 嘗試關閉無頭模式查看瀏覽器行為

### 調試模式

設定 `headless=False` 可以看到瀏覽器的實際操作過程：

```python
deck_info = scrape_shadowverse_deck(url, headless=False)
```

## 注意事項

1. 請遵守網站的使用條款和 robots.txt
2. 建議在請求之間加入適當的延遲
3. 大量爬取時請考慮對伺服器的影響
4. 網站結構可能會變更，屆時需要更新腳本

## 授權

此腳本僅供學習和研究用途。使用時請遵守相關法律法規和網站條款。 