# Shadowverse 牌組資訊擷取器（Supabase Edge Function）

**功能重點**

* **雙模式**：`url`（抓取會回傳 JSON 的網址） / `deck_code`（POST 到官方 `getDeck` 端點）。
* **舊網址自動轉換**：`https://shadowverse-wb.com/<lang>/deck/detail/?hash=...` → `https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=...&lang=<lang>`。
* **統一回傳結構**：將來源 JSON 轉為標準欄位（`total_red_ether`、`num_follower`…）。
* 內建 **CORS** 與 **OPTIONS** 預檢。

> 本文件針對 **Supabase Dashboard**（雲端）部署及使用；本地開發指令（`supabase functions serve` 等）不在此範圍。

---

## 1. 在 Supabase Dashboard 建立與部署

1. 進入你的 Supabase 專案 → **Edge Functions**。
2. 點 **New Function**，輸入名稱：`deck-crawler`。
3. 開啟新建的函式，於 **index.ts** 貼上我們提供的程式碼（你畫布中的版本）。

   * 本函式無外部 `import`，不需要 `import_map.json`。
4. 點選 **Deploy** 完成部署。

> 重新部署：日後修改 `index.ts` 後，再按 **Deploy** 即可更新。

---

## 2. 認證與端點

* 雲端端點格式：

```
https://<PROJECT-REF>.functions.supabase.co/deck-crawler
```

* 一般情況下，**雲端 Function 需要 JWT**。從前端或工具呼叫時，請於 Header 加上：

  * `Authorization: Bearer <YOUR_ANON_KEY>`
  * `apikey: <YOUR_ANON_KEY>`

> **安全提醒**
>
> * Browser/前端：使用 **Anon Key**（公開可用）。
> * 伺服器端：可用 **Service Role Key**（更高權限，**請勿**在前端公開）。

---

## 3. 請求模式與參數

函式同時支援 **GET Query** 與 **POST JSON Body**。兩種模式擇一提供參數即可。

### 3.1 URL 模式（抓取指定 JSON 網址）

* 參數：`url`（必要，擇一）
* 可選：`lang`（會覆蓋/補上 URL 的 `lang` 參數）、`ua`（自訂 User-Agent）

**支援舊網址**：若 `url` 符合
`https://shadowverse-wb.com/<lang>/deck/detail/?hash=<HASH>`
或
`https://shadowverse-wb.com/deck/detail/?hash=<HASH>`
會自動轉為
`https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=<HASH>&lang=<lang?>`

### 3.2 Deck Code 模式（POST 到官方端點）

* 參數：`deck_code` 或 `deckCode`（必要，擇一）
* 可選：`ua`（自訂 User-Agent）
* 會對 `https://shadowverse-wb.com/web/DeckCode/getDeck` 發送：

  ```json
  { "deck_code": "<四碼代碼>" }
  ```

### 3.3 互斥規則

* `url` 與 `deck_code`（或 `deckCode`）**不可同時提供**；擇一必填。

---

## 4. 範例

> **建議**：含 `&` 的 URL 務必 **URL Encode**（或改用 POST body），避免殼層或工具誤解參數。

### 4.1 使用 Deck Code（POST JSON）

```bash
curl -i \
  -H "Authorization: Bearer <YOUR_ANON_KEY>" \
  -H "apikey: <YOUR_ANON_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"deck_code":"Ab1C"}' \
  "https://<PROJECT-REF>.functions.supabase.co/deck-crawler"
```

### 4.2 URL 模式（新式 URL，GET）

```bash
# 將整段 URL 做 URL encode 後放進 ?url=
curl -i \
  -H "Authorization: Bearer <YOUR_ANON_KEY>" \
  -H "apikey: <YOUR_ANON_KEY>" \
  "https://<PROJECT-REF>.functions.supabase.co/deck-crawler?url=https%3A%2F%2Fshadowverse-wb.com%2Fweb%2FDeckBuilder%2FdeckHashDetail%3Fhash%3Dabc%26lang%3Dcht"
```

### 4.3 URL 模式（舊式 URL → 自動轉換，GET）

```bash
curl -i \
  -H "Authorization: Bearer <YOUR_ANON_KEY>" \
  -H "apikey: <YOUR_ANON_KEY>" \
  "https://<PROJECT-REF>.functions.supabase.co/deck-crawler?url=https%3A%2F%2Fshadowverse-wb.com%2Fcht%2Fdeck%2Fdetail%2F%3Fhash%3Dabc"
```

### 4.4 推薦：以 POST 傳 URL（避免編碼麻煩）

```bash
curl -i \
  -H "Authorization: Bearer <YOUR_ANON_KEY>" \
  -H "apikey: <YOUR_ANON_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=abc&lang=cht"}' \
  "https://<PROJECT-REF>.functions.supabase.co/deck-crawler"
```

### 4.5 前端（Browser/JS）

```js
const endpoint = "https://<PROJECT-REF>.functions.supabase.co/deck-crawler";
const ANON_KEY = "<YOUR_ANON_KEY>";

// Deck Code 模式
const res = await fetch(endpoint, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${ANON_KEY}`,
    "apikey": ANON_KEY,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ deck_code: "Ab1C" }),
});
const json = await res.json();
console.log(json);

// URL 模式（舊式 URL 也可，函式會自動轉換）
const res2 = await fetch(`${endpoint}?url=${encodeURIComponent("https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=abc&lang=cht")}`, {
  headers: {
    "Authorization": `Bearer ${ANON_KEY}`,
    "apikey": ANON_KEY,
  },
});
const json2 = await res2.json();
console.log(json2);
```

---

## 5. 回應格式

### 成功

```json
{
  "ok": true,
  "data": {
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
}
```

### 失敗

```json
{ "ok": false, "error": "<錯誤訊息>" }
```

常見錯誤：

* `請提供 url 或 deck_code 其中之一`：未提供必要參數。
* `url 與 deck_code 僅能擇一`：同時提供兩者。
* `HTTP 4xx/5xx ...`：上游端點回應錯誤。
* `內容不是合法 JSON` / `最外層 JSON 不是物件`：來源回應格式不符。

---

## 6. 參數一覽

| 名稱                       | 位置                | 必填        | 說明                                            |
| ------------------------ | ----------------- | --------- | --------------------------------------------- |
| `url`                    | Query 或 JSON Body | 兩者擇一      | 直接取用 JSON 的完整網址（含 query）。支援舊式 URL 自動轉換。       |
| `deck_code` / `deckCode` | Query 或 JSON Body | 兩者擇一      | 牌組代碼（4 碼）。POST 到官方 `getDeck` 端點。              |
| `lang`                   | Query 或 JSON Body | 否（URL 模式） | 覆蓋/補上 URL 的 `lang` 參數。舊式 URL 會先嘗試由 path 偵測語言。 |
| `ua`                     | Query 或 JSON Body | 否         | 自訂 User-Agent。                                |

---

## 7. CORS 與用戶端存取

本函式已設定：

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: authorization, x-client-info, apikey, content-type
Access-Control-Allow-Methods: GET, POST, OPTIONS
```

可直接從瀏覽器前端呼叫（需帶 `Authorization` / `apikey`）。

---

## 8. 監控與除錯

* **Logs**：Dashboard → Edge Functions → `deck-crawler` → **Logs**。
* **重試**：上游偶發性失敗時，建議由客戶端或你的後端實作重試（本函式未內建重試）。
* **診斷**：在請求中可暫時加入自訂 `ua` 以辨識來源；必要時可在程式中加上更多錯誤訊息（不含敏感資訊）。

---

## 9. 最佳實務建議

* **URL 編碼**：GET query 的 `url` 請使用 `encodeURIComponent` / URL Encode；或優先採 **POST JSON**。
* **模式擇一**：避免同時提供 `url` 與 `deck_code`。
* **金鑰管理**：前端僅使用 **Anon Key**；**勿**將 Service Role Key 放在前端。
* **快取**：若要在 CDN/瀏覽器快取，可在函式回應加上 `Cache-Control`（目前範例未設快取）。
* **風險控管**：必要時可在函式側增加對來源網域白名單檢查（目前未限制來源網域）。

