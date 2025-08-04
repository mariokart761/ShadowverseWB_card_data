# Firebase 操作指南

本文檔詳細說明如何設定和使用 Firebase Firestore 來儲存和查詢 Shadowverse 卡牌資料。

## 目錄

1. [前置準備](#前置準備)
2. [Firebase 專案設定](#firebase-專案設定)
3. [本地環境設定](#本地環境設定)
4. [資料同步](#資料同步)
5. [資料查詢](#資料查詢)
6. [常見問題](#常見問題)
7. [最佳實務](#最佳實務)

---

## 前置準備

### 系統需求
- Python 3.7 或更高版本
- 網路連線
- Google 帳戶

### 必要套件
```bash
pip install firebase-admin>=6.4.0
```

---

## Firebase 專案設定

### 步驟 1: 建立 Firebase 專案

1. 前往 [Firebase Console](https://console.firebase.google.com)
2. 點擊「新增專案」
3. 輸入專案名稱（例如：`shadowverse-cards`）
4. 選擇是否啟用 Google Analytics（建議啟用）
5. 完成專案建立

### 步驟 2: 啟用 Firestore 資料庫

1. 在 Firebase Console 中選擇您的專案
2. 點擊左側選單的「Firestore Database」
3. 點擊「建立資料庫」
4. 選擇安全規則模式：
   - **測試模式**：開發階段使用，30天後自動關閉寫入權限
   - **正式版模式**：需要設定安全規則
5. 選擇資料庫位置（建議選擇 `asia-east1` 或 `asia-southeast1`）

### 步驟 3: 建立服務帳戶

1. 前往「專案設定」（齒輪圖示）
2. 選擇「服務帳戶」分頁
3. 點擊「產生新的私密金鑰」
4. 下載 JSON 金鑰檔案
5. **重要**：妥善保管此檔案，不要上傳到版本控制系統

---

## 本地環境設定

### 方法一：自動設定（推薦）

```bash
# 執行自動設定腳本
python setup_firebase.py
```

腳本會引導您完成以下步驟：
1. 安裝必要套件
2. 建立配置檔案
3. 測試連線
4. 初始化資料庫結構

### 方法二：手動設定

#### 1. 建立配置檔案

```bash
# 建立 Firebase 配置
python firebase/init_firebase.py config
```

輸入以下資訊：
- **Firebase Project ID**：在 Firebase Console 專案設定中找到
- **服務帳戶金鑰檔案路徑**：剛才下載的 JSON 檔案路徑

#### 2. 測試連線

```bash
# 測試 Firebase 連線
python firebase/init_firebase.py test
```

#### 3. 初始化資料庫

```bash
# 初始化 Firebase 資料庫結構
python firebase/init_firebase.py init
```

此步驟會：
- 建立索引配置檔案
- 建立安全規則檔案
- 建立範例資料（可選）

#### 4. 部署規則和索引（需要 Firebase CLI）

```bash
# 安裝 Firebase CLI
npm install -g firebase-tools

# 登入 Firebase
firebase login

# 初始化專案
firebase init firestore

# 部署規則和索引
firebase deploy --only firestore:rules,firestore:indexes
```

---

## 資料同步

### 同步所有語言資料

```bash
# 同步所有語言的卡牌資料到 Firebase
python firebase_sync.py
```

### 同步過程說明

1. **讀取 JSON 資料**：從 `output/` 目錄讀取爬取的資料
2. **同步參考資料**：先同步卡包、種族、技能等基礎資料
3. **批次同步卡片**：使用多執行緒批次處理卡片資料
4. **記錄同步狀態**：在 `syncLogs` 集合中記錄同步結果

### 同步統計資訊

同步完成後會顯示：
- 總卡片數量
- 成功同步數量
- 失敗數量
- 成功率
- 錯誤摘要

---

## 資料查詢

### 執行查詢範例

```bash
# 執行 Firebase 查詢範例
python examples/firebase_queries.py
```

### 常用查詢模式

#### 1. 基本查詢

```python
import firebase_admin
from firebase_admin import credentials, firestore

# 初始化 Firebase
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# 查詢所有卡片
cards_ref = db.collection('cards')
cards = cards_ref.limit(10).get()

for card in cards:
    print(f"卡片 ID: {card.id}")
    print(f"資料: {card.to_dict()}")
```

#### 2. 條件查詢

```python
# 查詢特定職業的卡片
elf_cards = cards_ref.where('class', '==', 1).limit(5).get()

# 查詢特定費用範圍
mid_cost_cards = cards_ref.where('cost', '>=', 4).where('cost', '<=', 6).get()

# 查詢包含特定種族的卡片
angel_cards = cards_ref.where('tribes', 'array_contains', 1).get()
```

#### 3. 多語言查詢

```python
# 獲取卡片的繁體中文名稱
card = cards_ref.document('900011010').get()
if card.exists:
    card_data = card.to_dict()
    cht_name = card_data['names']['cht']['name']
    print(f"繁體中文名稱: {cht_name}")
```

#### 4. 子集合查詢

```python
# 查詢卡片的問答資料
card_ref = cards_ref.document('900011010')
questions_ref = card_ref.collection('questions')
questions = questions_ref.where('language', '==', 'cht').get()

for q in questions:
    q_data = q.to_dict()
    print(f"問題: {q_data['question']}")
    print(f"答案: {q_data['answer']}")
```

#### 5. 排序和分頁

```python
# 按費用排序
sorted_cards = cards_ref.order_by('cost').limit(10).get()

# 分頁查詢
first_page = cards_ref.order_by('cost').limit(5).get()
if first_page:
    last_doc = first_page[-1]
    next_page = cards_ref.order_by('cost').start_after(last_doc).limit(5).get()
```

---

## 常見問題

### Q1: 同步時出現權限錯誤
**A**: 檢查以下項目：
- 服務帳戶金鑰檔案路徑是否正確
- 金鑰檔案是否有效
- Firebase 專案 ID 是否正確
- Firestore 資料庫是否已啟用

### Q2: 查詢速度很慢
**A**: 優化建議：
- 建立適當的複合索引
- 使用 `limit()` 限制查詢結果數量
- 避免使用 `!=` 和 `not-in` 查詢
- 考慮資料反正規化

### Q3: 超過 Firestore 配額限制
**A**: 解決方案：
- 檢查 Firebase Console 中的使用量
- 考慮升級到付費方案
- 優化查詢以減少讀取次數
- 使用本地快取

### Q4: 無法建立複合索引
**A**: 處理步驟：
1. 檢查 Firebase Console 中的錯誤訊息
2. 手動在 Console 中建立索引
3. 或使用 Firebase CLI 部署索引配置

### Q5: 資料結構需要修改
**A**: 注意事項：
- Firestore 不支援結構變更
- 需要寫入遷移腳本
- 考慮使用新的集合名稱
- 保持向後相容性

---

## 最佳實務

### 1. 資料結構設計

```javascript
// 好的設計：嵌套相關資料
{
  "id": 900011010,
  "cost": 2,
  "names": {
    "cht": {"name": "雙刃哥布林", "nameRuby": ""},
    "en": {"name": "Goblin", "nameRuby": ""}
  },
  "descriptions": {
    "cht": {
      "common": {"skillText": "...", "flavourText": "..."}
    }
  }
}
```

### 2. 查詢優化

```python
# 好的做法：使用索引欄位查詢
cards_ref.where('class', '==', 1).where('cost', '==', 3)

# 避免：全集合掃描
cards_ref.where('names.cht.name', '==', '特定名稱')  # 需要建立索引
```

### 3. 批次操作

```python
# 批次寫入（最多 500 個操作）
batch = db.batch()
for i in range(100):
    doc_ref = db.collection('cards').document()
    batch.set(doc_ref, card_data)
batch.commit()
```

### 4. 錯誤處理

```python
try:
    doc_ref = db.collection('cards').document('card_id')
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        print("文件不存在")
except Exception as e:
    print(f"查詢錯誤: {e}")
```

### 5. 安全性

```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 讀取公開，寫入需要認證
    match /cards/{cardId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

### 6. 成本控制

- 使用 `limit()` 限制查詢結果
- 避免不必要的即時監聽
- 合理設計資料結構以減少讀取次數
- 定期監控 Firebase Console 中的使用量

### 7. 監控與維護

```python
# 監控同步狀態
sync_logs = db.collection('syncLogs').order_by('createdAt', direction=firestore.Query.DESCENDING).limit(10).get()

for log in sync_logs:
    log_data = log.to_dict()
    print(f"語言: {log_data['language']}, 狀態: {log_data['syncStatus']}")
```

---

## 進階功能

### 1. 即時監聽

```python
def on_snapshot(col_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == 'ADDED':
            print(f'新增卡片: {change.document.id}')
        elif change.type.name == 'MODIFIED':
            print(f'修改卡片: {change.document.id}')
        elif change.type.name == 'REMOVED':
            print(f'刪除卡片: {change.document.id}')

# 監聽卡片集合變化
cards_ref.on_snapshot(on_snapshot)
```

### 2. 交易操作

```python
@firestore.transactional
def update_card_stats(transaction, card_ref):
    snapshot = card_ref.get(transaction=transaction)
    if snapshot.exists:
        current_data = snapshot.to_dict()
        # 更新統計資料
        transaction.update(card_ref, {'updatedAt': firestore.SERVER_TIMESTAMP})

# 執行交易
transaction = db.transaction()
update_card_stats(transaction, card_ref)
```

### 3. 聚合查詢

```python
# 計算卡片總數（需要 Firebase Admin SDK v6.0+）
from google.cloud.firestore_v1.aggregation import AggregationQuery

total_count = cards_ref.count().get()
print(f"總卡片數: {total_count[0][0].value}")
```

---

## 總結

Firebase Firestore 為 Shadowverse 卡牌資料提供了彈性且強大的 NoSQL 儲存解決方案。通過本指南，您可以：

1. ✅ 完成 Firebase 專案設定和本地環境配置
2. ✅ 成功同步卡牌資料到 Firestore
3. ✅ 執行各種複雜的資料查詢
4. ✅ 遵循最佳實務確保效能和安全性
5. ✅ 處理常見問題和進階功能

如需更多協助，請參考：
- [Firebase 官方文檔](https://firebase.google.com/docs/firestore)
- [Python Admin SDK 參考](https://firebase.google.com/docs/reference/admin/python)
- 專案中的 `examples/firebase_queries.py` 範例檔案