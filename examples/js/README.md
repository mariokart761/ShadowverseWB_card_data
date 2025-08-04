# Shadowverse Firebase JavaScript 範例

這個目錄包含使用 JavaScript (Node.js) 查詢 Firebase Firestore 中 Shadowverse 卡片資料的範例。

## 📁 檔案結構

```
examples/js/
├── package.json              # Node.js 專案配置和依賴
├── config.example.json       # Firebase 配置範例
├── env.example              # 環境變數範例
├── firebase_queries.js      # 主要查詢範例腳本
├── test_queries.js          # 測試腳本
├── setup.js                 # 自動設置腳本
└── README.md               # 說明文件 (本檔案)
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
# 進入 JavaScript 範例目錄
cd examples/js

# 安裝 Node.js 依賴
npm install
```

### 2. 配置 Firebase

```bash
# 複製配置範例檔案
cp config.example.json config.json

# 編輯配置檔案，填入您的 Firebase 專案資訊
# {
#   "project_id": "your-firebase-project-id",
#   "service_account_key_path": "../../firebase/your-service-account-key.json",
#   "database_url": "https://your-project-id-default-rtdb.firebaseio.com/"
# }
```

### 3. 執行範例

```bash
# 執行查詢範例
node firebase_queries.js

# 或使用 npm 腳本
npm start
```

### 4. 執行測試

```bash
# 執行測試腳本
node test_queries.js

# 或使用 npm 腳本
npm test
```

## 🛠️ 自動設置

使用自動設置腳本快速配置環境：

```bash
node setup.js
```

設置腳本會：
- 安裝必要的依賴套件
- 建立配置檔案
- 檢查服務帳戶金鑰
- 提供使用說明

## 📚 功能範例

### 基本查詢
- 統計卡片總數
- 按職業統計卡片數量
- 按稀有度統計卡片數量

### 卡片搜尋
- 按費用搜尋卡片
- 按攻擊力搜尋卡片
- 按生命值搜尋卡片

### 複合查詢
- 多條件組合查詢
- 範圍查詢
- 陣列查詢

### 多語言支援
- 提取不同語言的卡片名稱
- 自動 fallback 到其他語言
- 多語言資料展示

### 參考資料查詢
- 卡包資料查詢
- 種族資料查詢
- 技能資料查詢

### 同步記錄查詢
- 查看資料同步狀態
- 檢查同步成功率
- 按語言查詢同步記錄

## 🔧 主要函數

### 初始化函數
```javascript
import { initializeFirebase } from './firebase_queries.js';

const db = initializeFirebase();
```

### 名稱提取函數
```javascript
import { getCardName, getCardNameFallback } from './firebase_queries.js';

// 獲取指定語言的名稱
const name = getCardName(cardData, 'cht');

// 自動 fallback 到其他語言
const nameWithFallback = getCardNameFallback(cardData, 'cht');
```

### 查詢範例函數
```javascript
import { 
    exampleBasicQueries,
    exampleCardSearch,
    exampleComplexQueries,
    exampleMultilingualData
} from './firebase_queries.js';

// 執行各種查詢範例
await exampleBasicQueries(db);
await exampleCardSearch(db);
await exampleComplexQueries(db);
await exampleMultilingualData(db);
```

## 📊 資料結構

### 卡片文件 (cards 集合)
```javascript
{
  id: 10001110,
  cost: 2,
  atk: 2,
  life: 2,
  class: 0,
  rarity: 1,
  isToken: false,
  isIncludeRotation: true,
  tribes: [1, 2],
  "names.cht": {
    name: "不屈的劍鬥士",
    nameRuby: "不屈的劍鬥士"
  },
  "names.en": {
    name: "Indomitable Fighter",
    nameRuby: "Indomitable Fighter"
  }
  // ... 其他語言名稱
}
```

### 參考資料集合
- `cardSets`: 卡包資料
- `tribes`: 種族資料  
- `skills`: 技能資料
- `syncLogs`: 同步記錄

## ⚠️ 注意事項

### Firestore 查詢限制
- 不支援全文搜尋
- 複合查詢可能需要建立索引
- 範圍查詢和排序有特定規則
- 陣列查詢有特殊語法

### 效能考量
- 大量資料查詢時注意成本
- 使用 `limit()` 限制結果數量
- 考慮使用分頁查詢
- 避免掃描整個集合

### 錯誤處理
- 檢查 Firebase 初始化狀態
- 處理網路連接錯誤
- 驗證查詢結果
- 記錄錯誤資訊

## 🔍 疑難排解

### 常見問題

**Q: 執行時出現 "Firebase 初始化失敗"**
A: 檢查 `config.json` 配置是否正確，服務帳戶金鑰檔案是否存在

**Q: 查詢結果為空**
A: 確認資料庫中有資料，檢查查詢條件是否正確

**Q: 卡片名稱顯示為 "未知"**
A: 檢查卡片資料是否包含對應語言的名稱欄位

**Q: 複合查詢失敗**
A: 可能需要在 Firebase Console 中建立複合索引

### 除錯技巧

1. **啟用詳細日誌**
   ```javascript
   console.log('查詢條件:', queryConditions);
   console.log('查詢結果:', queryResults.size);
   ```

2. **檢查資料結構**
   ```javascript
   const doc = await cardsRef.doc('cardId').get();
   console.log('卡片資料:', doc.data());
   ```

3. **測試連接**
   ```bash
   node test_queries.js
   ```

## 📈 進階用法

### 批次查詢
```javascript
const batch = db.batch();
// 批次操作...
await batch.commit();
```

### 即時監聽
```javascript
const unsubscribe = cardsRef.onSnapshot(snapshot => {
    snapshot.docChanges().forEach(change => {
        // 處理資料變更
    });
});
```

### 分頁查詢
```javascript
let lastDoc = null;
const pageSize = 10;

const query = cardsRef.limit(pageSize);
if (lastDoc) {
    query = query.startAfter(lastDoc);
}

const snapshot = await query.get();
lastDoc = snapshot.docs[snapshot.docs.length - 1];
```

## 🤝 貢獻

如果您發現問題或有改進建議，歡迎：
1. 提交 Issue
2. 建立 Pull Request
3. 改進文檔

## 📄 授權

本專案採用 MIT 授權條款。