# Shadowverse 卡片資料同步至 Supabase

這個專案提供了將 Shadowverse 卡片資料和提示資料同步到 Supabase 資料庫的完整解決方案。

## 專案結構

```
project/
├── supabase/
│   ├── config.json          # Supabase 連線配置
│   └── schema.sql           # 資料庫結構定義
├── output/
│   ├── shadowverse_cards_cht.json
│   ├── shadowverse_cards_chs.json
│   ├── shadowverse_cards_en.json
│   ├── shadowverse_cards_ja.json
│   ├── shadowverse_cards_ko.json
│   └── tips_data/
│       ├── tips_data_cht.json
│       ├── tips_data_chs.json
│       ├── tips_data_en.json
│       ├── tips_data_ja.json
│       └── tips_data_ko.json
└── supabase_sync.py # 同步腳本
```

## 安裝依賴

```bash
pip install supabase
```

## 設置步驟

### 1. 創建 Supabase 專案

1. 前往 [Supabase](https://supabase.com/) 創建新專案
2. 記下專案的 URL 和 service_role key

### 2. 執行資料庫結構

在 Supabase Dashboard 的 SQL Editor 中執行 `schema.sql` 中的所有 SQL 指令，這會創建：

- `svwb_data` schema
- 所有必要的資料表
- RLS 政策
- 觸發器
- 初始化資料（卡組系列、部族、技能）

### 3. 配置連線資訊

創建 `supabase/config.json` 文件：

```json
{
  "supabase_url": "https://your-project-id.supabase.co",
  "supabase_key": "your-service-role-key-here"
}
```

**注意：** 使用 service_role key（不是 anon key）以便有完整的讀寫權限。

## 使用方法

### 基本同步操作

#### 同步所有語言的所有資料
```bash
python supabase_sync.py
```

#### 同步特定語言
```bash
python supabase_sync.py -l cht en ja
```

#### 只同步卡片資料
```bash
python supabase_sync.py --cards-only
```

#### 只同步提示資料
```bash
python supabase_sync.py --tips-only
```

#### 只同步特定語言的卡片資料
```bash
python supabase_sync.py -l cht --cards-only
```

### 資料管理操作

#### 驗證資料完整性
```bash
python supabase_sync.py --validate
```

#### 清理資料庫（危險操作）
```bash
python supabase_sync.py --clean
```

### 查看幫助
```bash
python supabase_sync.py --help
```

### 常用組合命令

#### 清理並重新同步所有資料
```bash
python supabase_sync.py --clean
python supabase_sync.py
```

#### 同步後驗證資料
```bash
python supabase_sync.py
python supabase_sync.py --validate
```

## 資料庫結構說明

### 主要資料表

| 資料表 | 說明 |
|--------|------|
| `card_sets` | 卡組系列 |
| `tribes` | 部族 |
| `skills` | 技能 |
| `cards` | 卡片主資料 |
| `card_texts` | 卡片文字內容（多語言） |
| `card_tribes` | 卡片-部族關聯 |
| `card_relations` | 卡片相關關係 |
| `card_questions` | 卡片問答 |
| `tips` | 遊戲提示 |

### 多語言支援

- 支援語言：`cht`, `chs`, `en`, `ja`, `ko`
- 名稱類字段使用 JSONB 格式儲存多語言內容
- 文字內容分語言存儲在獨立記錄中

### 查詢範例

```sql
-- 查詢特定語言的所有卡片
SELECT c.*, ct.skill_text, ct.flavour_text 
FROM svwb_data.cards c
LEFT JOIN svwb_data.card_texts ct ON c.card_id = ct.card_id 
WHERE ct.language = 'cht';

-- 查詢特定卡片的所有語言版本
SELECT c.name, ct.language, ct.skill_text 
FROM svwb_data.cards c
JOIN svwb_data.card_texts ct ON c.card_id = ct.card_id 
WHERE c.card_id = 10201110;

-- 查詢特定語言的提示
SELECT * FROM svwb_data.tips 
WHERE language = 'cht' 
ORDER BY sort_order;
```

## 權限設定

### RLS 政策

- **讀取權限：** 所有用戶可讀取
- **寫入權限：** 認證用戶可寫入
- **服務權限：** service_role 有完整權限（用於腳本同步）

### 安全建議

1. 不要在客戶端使用 service_role key
2. 生產環境建議設置更細緻的 RLS 政策
3. 定期輪換 API key

## 故障排除

## 故障排除

### 常見錯誤

#### 1. 連線失敗
```
✗ 載入配置失敗: Invalid API key
```
**解決方法：**
- 檢查 `supabase/config.json` 配置是否正確
- 確認 URL 格式：`https://your-project-id.supabase.co`
- 確認使用 service_role key（不是 anon key）
- 檢查 key 是否已過期或被禁用

#### 2. 權限錯誤
```
✗ 同步卡片資料失敗: Insufficient privileges
```
**解決方法：**
- 確保使用 service_role key（有完整讀寫權限）
- 檢查 RLS 政策是否正確設定
- 確認資料庫 schema 已正確創建

#### 3. 資料格式錯誤
```
✗ 同步卡片 10201110 失敗: Invalid input syntax for type integer
```
**解決方法：**
- 確認 JSON 文件格式正確，沒有損壞
- 檢查必要字段是否存在且格式正確
- 驗證卡片 ID 是否為有效的整數

#### 4. 文件不存在
```
卡片資料文件不存在: output/shadowverse_cards_cht.json
```
**解決方法：**
- 確認文件路徑正確
- 檢查文件名稱格式：`shadowverse_cards_{language_code}.json`
- 確保 `output/` 和 `output/tips_data/` 目錄存在

#### 5. 外鍵約束錯誤
```
警告: 部族 ID 999 不存在，跳過
```
**說明：**
- 這是正常的警告訊息，不會影響同步
- 腳本會自動跳過不存在的外鍵關聯
- 如需要，可在基礎資料中新增對應的部族/技能資料

### 日誌輸出說明

腳本會輸出詳細的同步進度和狀態：

```bash
=== 開始同步 Shadowverse 資料到 Supabase ===
✓ 成功連接到 Supabase: https://xxx.supabase.co

--- 處理 CHT 語言 ---

開始同步 cht 語言卡片資料...
  同步卡組系列資料...
  同步部族資料...
  同步技能資料...
  同步卡片資料... (共 327 張)
    已處理 50/327 張卡片
    已處理 100/327 張卡片
    ✓ 完成處理 327 張卡片
✓ cht 語言卡片資料同步完成

開始同步 cht 語言提示資料...
✓ cht 語言提示資料同步完成 (共 71 條)

=== 同步完成 ===
成功: 10/10
✓ 所有資料同步成功

自動驗證資料完整性...
=== 驗證資料完整性 ===
卡片總數: 327
CHT - 卡片文字: 327, 提示: 71
CHS - 卡片文字: 327, 提示: 71
EN - 卡片文字: 327, 提示: 71
JA - 卡片文字: 327, 提示: 71
KO - 卡片文字: 327, 提示: 71
部族關聯: 156
卡片關聯: 89
問答: 45
✓ 資料完整性檢查完成
```

## 補充
若遇到權限錯誤（schema未公開，無法同步），可以在 SQL Editor 運行以下命令：
```
alter database postgres
set
  search_path = svwb_data,
  public;

GRANT USAGE ON SCHEMA svwb_data TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA svwb_data TO anon, authenticated, service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA svwb_data TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA svwb_data TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA svwb_data GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA svwb_data GRANT ALL ON ROUTINES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA svwb_data GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
```

### 狀態圖示說明
- ✓ 成功操作
- ✗ 失敗操作  
- ⚠️ 警告訊息（不影響同步）

## 性能優化

### 批次處理

腳本每處理 50 張卡片會顯示進度，對於大量資料同步很有效。

### 索引優化

資料庫已創建必要的索引來優化查詢性能：
- 卡片 ID 索引
- 語言索引
- 複合索引

## 擴展性

### 新增語言

1. 在 `language_code` 枚舉中新增語言代碼
2. 更新同步腳本的語言列表
3. 準備對應語言的資料文件

### 新增字段

1. 修改資料表結構
2. 更新同步腳本邏輯
3. 重新同步資料

## 版本兼容性

- Python 3.7+
- supabase-py 最新版本
- PostgreSQL 14+（Supabase 預設）