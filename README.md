# Shadowverse 多語言卡牌資料爬蟲

這個專案包含用於爬取 Shadowverse 卡牌遊戲資料的 Python 腳本，支援多語言爬取。

## 專案結構

```
SVWB_crawler/
├── shadowverse_simple_crawler.py  # 主要爬蟲腳本
├── tips_data_crawler.py           # 系統Tips爬蟲腳本
├── supabase_sync.py               # Supabase 資料同步腳本
├── firebase_sync.py               # Firebase 資料同步腳本
├── setup_firebase.py              # Firebase 設定輔助程式
├── test_crawler.py                # 測試腳本
├── run.py                         # 互動式啟動腳本
├── run.bat                        # Windows 批次檔
├── run.sh                         # Linux/Mac 執行腳本
├── requirements.txt               # Python 套件相依性
├── README.md                      # 說明文件
├── .gitignore                     # Git 忽略檔案
├── supabase/                      # Supabase 相關檔案
│   ├── schema.sql                 # 資料庫結構定義
│   └── config.example.json        # 配置檔案範例
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

- 請參考`docs/Supabase操作指南.md`

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

### 查詢範例

```bash
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
    "csrf_token": "ce8626e7-7878-46c8-b2a4-393ee4c3e9bf"
  },
  "data": {
    "cards": {
      "10112120": {
        "related_card_ids": [
          90011110
        ],
        "specific_effect_card_ids": []
      },
      "10111310": {
        "related_card_ids": [
          90011110
        ],
        "specific_effect_card_ids": []
      }
    },
    "card_details": {
      "10201110": {
        "common": {
          "card_id": 10201110,
          "name": "雙刃哥布林",
          "name_ruby": "雙刃哥布林",
          "base_card_id": 10201110,
          "card_resource_id": 102011100,
          "atk": 1,
          "life": 1,
          "flavour_text": "人們首次發現到拿著兩把相同武器的哥布林。\n由於在魔物中有許多會隨著環境而進化的物種，\n因此研究者們開始議論紛紛，這是否也是進化徵兆。",
          "skill_text": "【<color=Keyword>入場曲</color>】如果自己戰場上有已超進化的從者卡，則會指定1張敵方戰場上的從者卡。給予其4點傷害。",
          "card_set_id": 10002,
          "type": 1,
          "class": 0,
          "tribes": [
            0
          ],
          "cost": 1,
          "rarity": 1,
          "cv": "江口拓也",
          "illustrator": "tricky胡坐",
          "questions": [],
          "is_token": false,
          "is_include_rotation": false,
          "card_image_hash": "0a8181b6031d489c9b3d1d14466bef44",
          "card_banner_image_hash": "aca2639fc5674ba097d94dda4c321979"
        },
        "evo": {
          "card_resource_id": 102011101,
          "flavour_text": "比起只有一把武器，拿兩把會更厲害喔！\n這樣就能一次切兩個水果了！\n方便又好吃喔──！",
          "skill_text": "【<color=Keyword>入場曲</color>】如果自己戰場上有已超進化的從者卡，則會指定1張敵方戰場上的從者卡。給予其4點傷害。",
          "card_image_hash": "1b254af517af482f9e43424dfd0c5879",
          "card_banner_image_hash": "20caecab73814e389845426df4f1ed6f"
        },
        "style_card_list": []
      }
    },
    "specific_effect_card_info": [
      "10233312",
      "10263312",
      "10204122",
      "10124132"
    ],
    "tribe_names": {
      "0": "-",
      "2": "士兵",
      "3": "魯米那斯",
      "4": "雷維翁",
      "5": "妖精"
    },
    "card_set_names": {
      "10000": "基本卡",
      "10001": "傳說揭幕",
      "10002": "無限進化"
    },
    "skill_names": {
      "0": "",
      "1": "入場曲",
      "2": "謝幕曲",
      "3": "進化時",
      "4": "攻擊時",
      "5": "守護"
    },
    "skill_replace_text_names": {
      "12": "魔力增幅"
    },
    "count": 327,
    "sort_card_id_list": [
      10201110,
      10012110,
      10112120
    ],
    "stats_list": {
      "atk": {
        "min": 0,
        "max": 13
      },
      "life": {
        "min": 0,
        "max": 13
      },
      "cost": {
        "min": 0,
        "max": 18
      }
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
1. **Supabase 支援**: PostgreSQL 關聯式資料庫
2. **Firebase 支援**: Firestore NoSQL 文件資料庫，反正規化設計
3. **多語言資料同步**: 支援將爬取的多語言資料同步到資料庫
4. **異步處理**: 使用異步操作提升資料庫同步效能

### 查詢範例
1. **Python 查詢範例**: 完整的 Python 資料庫查詢範例
2. **JavaScript 查詢範例**: Node.js Firebase 查詢範例
3. **多語言名稱支援**: 自動 fallback 到其他語言
4. **複合查詢**: 支援複雜的條件組合查詢

## 資料內容概述

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

## 注意事項

1. 請適當控制爬取頻率，避免對伺服器造成過大負擔
2. 腳本會自動處理請求失敗和重試

## 故障排除

如果遇到問題，請檢查：

1. 網路連線是否正常
2. 目標網站是否可以正常存取
3. 是否有防火牆或代理設定阻擋請求
4. Python 套件是否正確安裝
