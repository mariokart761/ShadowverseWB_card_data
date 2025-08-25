# Shadowverse 牌組資訊擷取器（Python）

**雙模式：URL / Deck Code，含網址前處理**

本腳本用於從 Shadowverse WB 取得牌組資訊。支援兩種資料來源：

1. **URL 模式**：直接對會回傳 JSON 的網址發送請求並解析。
2. **Deck Code 模式**：POST 到官方端點 `https://shadowverse-wb.com/web/DeckCode/getDeck`，payload 為 `{"deck_code": "<4碼>"}`，回應 JSON 與 URL 模式一致。

支援**網址**自動轉換：
`https://shadowverse-wb.com/<lang>/deck/detail/?hash=<...>`
→ 轉為
`https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=<...>&lang=<lang>`

---

## 功能特點

* **雙模式**：`--url` 或 `--deck-code` 取用牌組資訊，輸出欄位一致。
* **網址前處理**：自動將 `/cht/deck/detail/?hash=...` 等格式改為 API。
* **語言代碼**：`--lang` 自動補到 URL query（會覆蓋前處理偵測到的語言）。
* **User-Agent**：可自訂 `--ua`。
* **零相依**：只用 Python 標準函式庫，無需額外套件。
* **標準輸出/檔案輸出**：結果可印出或存檔（`-o`）。

---

## 系統需求

* Python 3.8+
* 可連線網際網路

---

## 安裝

將腳本儲存為 `deck_crawler_dual.py`（檔名自訂皆可）。

---

## 快速開始

> **❗重要：URL 請用引號包起來**（尤其含 `&lang=...` 時，避免殼層把 `&` 當成指令分隔）。

### URL 模式（API URL）

```bash
python3 deck_crawler_dual.py --url "https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=...&lang=cht"
```

### URL 模式（官網URL，自動轉換）

```bash
python3 deck_crawler_dual.py --url "https://shadowverse-wb.com/cht/deck/detail/?hash=..."
```

### Deck Code 模式（四碼代碼）

```bash
python3 deck_crawler_dual.py --deck-code Ab1C
```

### 指定 User-Agent 與輸出檔名

```bash
python3 deck_crawler_dual.py --deck-code Ab1C --ua "Mozilla/5.0" -o deck.json
```

---

## 命令列參數

| 參數                     | 說明                                                     | 範例                                                    |
| ---------------------- | ------------------------------------------------------ | ----------------------------------------------------- |
| `--url`                | 直接取用 JSON 的完整網址（含 query）。與 `--deck-code` 二選一。          | `--url "https://...deckHashDetail?hash=...&lang=cht"` |
| `--deck-code`          | 牌組代碼（4 碼英數）。與 `--url` 二選一。                             | `--deck-code Ab1C`                                    |
| `--lang`               | **URL 模式可選**：語言代碼（如 `cht/jpn`），會加到/覆蓋 URL 的 `lang` 參數。 | `--lang jpn`                                          |
| `--ua`, `--user-agent` | 自訂 User-Agent                                          | `--ua "Mozilla/5.0"`                                  |
| `-o`, `--output`       | 將結果輸出為檔案（預設印到 stdout）                                  | `-o deck.json`                                        |

---

## URL 前處理規則

當 `--url` 指向下列格式時：

```
https://shadowverse-wb.com/<lang>/deck/detail/?hash=<HASH>
https://shadowverse-wb.com/deck/detail/?hash=<HASH>         # 無語言片段
```

會自動轉為：

```
https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=<HASH>&lang=<lang?>
```

* 若路徑含語言（如 `cht`），會補成 `?lang=cht`。
* 若原本 query 已帶 `lang`，沿用原值。
* 若同時指定 `--lang`，**以 `--lang` 為準**。

---

## 欄位輸出（Schema）

兩種模式最終輸出欄位一致（皆為 JSON 物件）：

```json
{
  "total_red_ether": 0,
  "num_follower": 0,
  "num_spell": 0,
  "num_amulet": 0,
  "mana_curve": {},
  "battle_format": 2,
  "class_id": 0,
  "sub_class_id": null,
  "sort_card_id_list": [],
  "deck_card_num": {}
}
```

### 欄位說明

| 欄位                  | 型別             | 說明                       |
| ------------------- | -------------- | ------------------------ |
| `total_red_ether`   | number         | 分解紅乙太總量（或成本）             |
| `num_follower`      | number         | 隨從張數                     |
| `num_spell`         | number         | 法術張數                     |
| `num_amulet`        | number         | 護符張數                     |
| `mana_curve`        | object         | 費曲分佈，key 通常是費用、value 是張數 |
| `battle_format`     | number         | 對戰格式代碼                   |
| `class_id`          | number         | 職業 ID                    |
| `sub_class_id`      | number \| null | 子職業 ID（若有）               |
| `sort_card_id_list` | array          | 依排序的卡片 ID（或字串）清單         |
| `deck_card_num`     | object         | 卡片 ID → 張數對照             |

> 若來源 JSON 缺少對應欄位，腳本會給預設值（如 `0`、`{}`、`[]` 或 `null`）。

---

## 跨殼層使用範例（避免 `&` 問題）

### Windows CMD

```bat
python deck_crawler_dual.py --url "https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=...&lang=cht"
REM 或使用跳脫：
python deck_crawler_dual.py --url https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=...^&lang=cht
```

### PowerShell

```powershell
python .\deck_crawler_dual.py --url 'https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=...&lang=cht'
```

### macOS / Linux（Bash/Zsh）

```bash
python3 deck_crawler_dual.py --url 'https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=...&lang=cht'
```

---

## 錯誤處理與退出碼

* 網路或 HTTP 錯誤（如 4xx/5xx）、回應非 JSON、或最外層不是物件：

  * 會在 **stderr** 印出 `[錯誤] <訊息>`
  * 以 **非 0** 代碼結束（方便 CI 判斷）。
* 成功執行：結束碼 **0**。

---

## 常見問題（FAQ）

**Q1：為什麼看到** `'lang' is not recognized as an internal or external command` ？
A：你在 **Windows CMD**（或 Bash）直接貼了含 `&lang=...` 的 URL 而未加引號，殼層把 `&` 當成指令分隔。請用引號或跳脫 `^&`，或改用 `--lang` 參數。

**Q2：我只知道 Deck Code，沒有 URL 可以用？**
A：使用 Deck Code 模式：
`python deck_crawler_dual.py --deck-code Ab1C`

**Q3：來源回應 JSON 外面還包了一層 `data` / `result` / `deckDetail`？**
A：腳本會嘗試在常見 root key（`data/result/deckDetail/deck/payload`）下挖取欄位，通常不需更改。

**Q4：需要代理或額外 headers 嗎？**
A：預設帶簡單 `User-Agent`。若環境需要，可用 `--ua` 指定自訂 UA；如需代理，請用系統層代理或自行擴充程式碼。
