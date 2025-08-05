# Shadowverse 多語言卡牌資料爬蟲

這個專案包含用於爬取 Shadowverse 卡牌遊戲資料的 Python 腳本，支援多語言爬取。

## 專案結構

```
SVWB_crawler/
├── shadowverse_simple_crawler.py  # 主要爬蟲腳本
├── tips_data_crawler.py           # 系統Tips爬蟲腳本
├── supabase_sync.py               # Supabase 資料同步腳本
├── firebase_sync.py               # Firebase 資料同步腳本
├── setup_supabase.py              # Supabase 設定輔助程式
├── setup_firebase.py              # Firebase 設定輔助程式
├── test_crawler.py                # 測試腳本
├── run.py                         # 互動式啟動腳本
├── run.bat                        # Windows 批次檔
├── run.sh                         # Linux/Mac 執行腳本
├── requirements.txt               # Python 套件相依性
├── README.md                      # 說明文件
├── .gitignore                     # Git 忽略檔案
├── CHANGELOG.md                   # 更新日誌
├── supabase/                      # Supabase 相關檔案
│   ├── schema.sql                 # 資料庫結構定義
│   ├── init_supabase.py           # 資料庫初始化腳本
│   ├── config.example.json        # 配置檔案範例
│   └── env.example                # 環境變數範例
├── firebase/                      # Firebase 相關檔案
│   ├── firestore_structure.md     # Firestore 資料結構說明
│   ├── init_firebase.py           # Firebase 初始化腳本
│   ├── config.example.json        # 配置檔案範例
│   ├── firestore.rules            # Firestore 安全規則
│   └── firestore.indexes.json     # Firestore 索引配置
├── docs/                          # 文件目錄
│   └── response.example.json      # API 回應格式範例
├── examples/                      # 範例程式
│   ├── example_usage.py           # 爬蟲使用範例
│   ├── supabase_queries.py        # Supabase 查詢範例
│   └── firebase_queries.py        # Firebase 查詢範例
├── output/                        # 輸出檔案目錄
│   ├── shadowverse_cards_cht.json # 繁體中文卡牌資料
│   ├── shadowverse_cards_chs.json # 簡體中文卡牌資料
│   ├── shadowverse_cards_en.json  # 英文卡牌資料
│   ├── shadowverse_cards_ja.json  # 日文卡牌資料
│   ├── shadowverse_cards_ko.json  # 韓文卡牌資料
│   └── tips_data/                 # Tips資料目錄
│       ├── tips_data_cht.json     # 繁體中文Tips資料
│       ├── tips_data_chs.json     # 簡體中文Tips資料
│       ├── tips_data_en.json      # 英文Tips資料
│       ├── tips_data_ja.json      # 日文Tips資料
│       └── tips_data_ko.json      # 韓文Tips資料
└── logs/                          # 日誌檔案目錄
    ├── shadowverse_crawler.log    # 爬蟲執行日誌
    ├── supabase_sync.log          # Supabase 同步日誌
    └── firebase_sync.log          # Firebase 同步日誌
```

## 安裝相依套件

```bash
pip install -r requirements.txt
```

## 資料庫整合

本專案支援兩種資料庫方案，您可以根據需求選擇：

### 🗄️ Supabase (PostgreSQL) 整合

適合需要關聯式資料庫和複雜查詢的場景。

#### 設定 Supabase

1. 在 [Supabase](https://supabase.com) 建立新專案
2. 複製 `supabase/config.example.json` 為 `supabase/config.json`
3. 填入您的 Supabase 連線資訊：
   ```json
   {
     "supabase_url": "https://your-project.supabase.co",
     "supabase_key": "your-supabase-anon-key",
     "database_url": "postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres"
   }
   ```

#### 快速設定
```bash
# 自動設定 Supabase
python setup_supabase.py
```

#### 手動設定
```bash
# 檢查資料庫連線
python supabase/init_supabase.py check

# 建立資料庫結構
python supabase/init_supabase.py init

# 同步卡牌資料
python supabase_sync.py --type cards

# 同步Tips資料
python supabase_sync.py --type tips

# 同步所有資料
python supabase_sync.py --type all
```

### 🔥 Firebase (Firestore) 整合

適合需要即時同步和彈性 NoSQL 結構的場景。

#### 設定 Firebase

1. 在 [Firebase Console](https://console.firebase.google.com) 建立新專案
2. 啟用 Firestore 資料庫
3. 下載服務帳戶金鑰檔案
4. 複製 `firebase/config.example.json` 為 `firebase/config.json`
5. 填入您的 Firebase 連線資訊：
   ```json
   {
     "project_id": "your-firebase-project-id",
     "service_account_key_path": "path/to/your/service-account-key.json"
   }
   ```

#### 快速設定
```bash
# 自動設定 Firebase
python setup_firebase.py
```

#### 手動設定
```bash
# 建立配置檔案
python firebase/init_firebase.py config

# 初始化 Firebase
python firebase/init_firebase.py init

# 部署規則和索引 (需要 Firebase CLI)
firebase deploy --only firestore:rules,firestore:indexes

# 同步卡牌資料
python firebase_sync.py --type cards

# 同步Tips資料
python firebase_sync.py --type tips

# 同步所有資料
python firebase_sync.py --type all
```

### 資料庫結構比較

| 特性 | Supabase (PostgreSQL) | Firebase (Firestore) |
|------|----------------------|----------------------|
| 資料庫類型 | 關聯式 (SQL) | NoSQL 文件資料庫 |
| 查詢能力 | 強大的 SQL 查詢 | 有限的查詢功能 |
| 即時同步 | 支援 | 原生支援 |
| 擴展性 | 垂直擴展 | 自動水平擴展 |
| 成本 | 按使用量計費 | 按讀寫操作計費 |
| 離線支援 | 無 | 原生支援 |

### 查詢範例

```bash
# Supabase 查詢範例
python examples/supabase_queries.py

# Firebase 查詢範例 (Python)
python examples/firebase_queries.py

# Firebase 查詢範例 (JavaScript)
cd examples/js && node firebase_queries.js
```

## 使用方法

### 快速開始（推薦）

```bash
python run.py
```

這會啟動互動式選單，讓您選擇要執行的功能。

### 直接爬取所有語言

```bash
python shadowverse_simple_crawler.py
```

這會自動爬取所有支援的語言（cht, chs, en, ja, ko）並分別儲存。

### 爬取特定語言

```python
from shadowverse_simple_crawler import crawl_single_language

# 爬取繁體中文
crawl_single_language('cht')

# 爬取英文
crawl_single_language('en')
```

### 爬取系統Tips資料

```bash
# 爬取所有語言的Tips資料
python tips_data_crawler.py

# 爬取特定語言的Tips資料
python tips_data_crawler.py --langs cht en

# 顯示瀏覽器視窗（除錯用）
python tips_data_crawler.py --no-headless
```

系統Tips資料會儲存在 `output/tips_data/` 目錄下，每種語言一個JSON檔案。

### 完整版爬蟲（進階）

```bash
python shadowverse_crawler.py
```

這個版本使用 Selenium，需要安裝 Chrome 瀏覽器和 ChromeDriver。

## 支援語言

- `cht` - 繁體中文
- `chs` - 簡體中文  
- `en` - 英文
- `ja` - 日文
- `ko` - 韓文

## 輸出格式

腳本會根據語言產生對應的 JSON 檔案：
- `shadowverse_cards_cht.json` - 繁體中文版本
- `shadowverse_cards_chs.json` - 簡體中文版本
- `shadowverse_cards_en.json` - 英文版本
- `shadowverse_cards_ja.json` - 日文版本
- `shadowverse_cards_ko.json` - 韓文版本

每個檔案都包含以下結構：

```json
{
  "data_headers": {
    "result_code": 1,
    "user_id": 0,
    "user_name": "",
    "is_login": false,
    "csrf_token": "..."
  },
  "data": {
    "cards": { ... },
    "card_details": { ... },
    "specific_effect_card_info": [ ... ],
    "tribe_names": { ... },
    "card_set_names": { ... },
    "skill_names": { ... },
    "skill_replace_text_names": { ... },
    "count": 275,
    "sort_card_id_list": [ ... ],
    "stats_list": {
      "atk": {"min": 0, "max": 13},
      "life": {"min": 0, "max": 13},
      "cost": {"min": 0, "max": 18}
    },
    "result_error_code": null
  }
}
```

## 功能特色

### 爬蟲功能
1. **多語言支援**: 支援 5 種語言（cht, chs, en, ja, ko）
2. **完整資料收集**: 迭代所有 offset（每次間隔 30）直到沒有更多資料
3. **資料合併**: 將所有批次的資料合併成完整的資料集
4. **去重處理**: 避免重複的卡片和資訊
5. **統計資訊**: 保留卡片的統計數據（攻擊力、生命值、費用範圍）
6. **錯誤處理**: 包含完整的錯誤處理和日誌記錄
7. **進度追蹤**: 即時顯示爬取進度
8. **分語言儲存**: 每種語言的資料分別儲存為獨立檔案

### 資料庫整合
1. **Supabase 支援**: PostgreSQL 關聯式資料庫，正規化設計
2. **Firebase 支援**: Firestore NoSQL 文件資料庫，反正規化設計
3. **多語言資料同步**: 支援將爬取的多語言資料同步到資料庫
4. **異步處理**: 使用異步操作提升資料庫同步效能

### 查詢範例
1. **Python 查詢範例**: 完整的 Python 資料庫查詢範例
2. **JavaScript 查詢範例**: Node.js Firebase 查詢範例
3. **多語言名稱支援**: 自動 fallback 到其他語言
4. **複合查詢**: 支援複雜的條件組合查詢

## 資料內容

### 卡牌資料 (`shadowverse_cards_*.json`)
- **cards**: 卡片關聯資訊
- **card_details**: 詳細卡片資訊（包含普通和進化形態）
- **specific_effect_card_info**: 特殊效果卡片資訊
- **tribe_names**: 種族名稱對照表
- **card_set_names**: 卡包名稱對照表
- **skill_names**: 技能名稱對照表
- **sort_card_id_list**: 完整的卡片 ID 排序列表
- **stats_list**: 卡片數值統計

### Tips資料 (`tips_data_*.json`)
- **tips**: 遊戲系統Tips和說明
  - **title**: Tips標題
  - **desc**: Tips詳細說明
- **language**: 語言代碼
- **total**: Tips總數

### 資料庫結構
- **Supabase**: 正規化的關聯式資料庫結構，支援複雜查詢
- **Firebase**: 反正規化的文件資料庫結構，支援即時同步

## 注意事項

1. 請適當控制爬取頻率，避免對伺服器造成過大負擔
2. 腳本會自動處理請求失敗和重試
3. 建議使用簡化版爬蟲，除非需要處理 JavaScript 渲染的內容
4. 輸出的 JSON 檔案可能會很大（數 MB），請確保有足夠的磁碟空間

## 故障排除

如果遇到問題，請檢查：

1. 網路連線是否正常
2. 目標網站是否可以正常存取
3. 是否有防火牆或代理設定阻擋請求
4. Python 套件是否正確安裝

日誌檔案 `shadowverse_crawler.log` 會記錄詳細的執行資訊，可用於故障排除。