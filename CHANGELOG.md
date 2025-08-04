# 更新日誌

## v2.2.0 - 2024-12-19

### 新功能 🎉
- 🔥 **Firebase Firestore 整合** - 新增 NoSQL 資料庫支援
- 🗄️ **雙資料庫支援** - 同時支援 Supabase (PostgreSQL) 和 Firebase (Firestore)
- 📱 即時資料同步和離線支援 (Firebase)
- 🚀 自動擴展的雲端資料庫 (Firebase)
- 🔧 完整的設定輔助工具

### Firebase 功能
- 📋 NoSQL 文件資料庫設計，支援彈性資料結構
- 🌐 多語言資料嵌套儲存，減少查詢次數
- 🔄 多執行緒批次同步，提升效能
- 🛡️ Firestore 安全規則和索引配置
- 📊 子集合支援 (問答、風格變體)

### 新增檔案
- `firebase_sync.py` - Firebase 資料同步腳本
- `setup_firebase.py` - Firebase 設定輔助程式
- `firebase/init_firebase.py` - Firebase 初始化工具
- `firebase/firestore_structure.md` - Firestore 資料結構說明
- `examples/firebase_queries.py` - Firebase 查詢範例

### 檔案重新組織
- `database_sync.py` → `supabase_sync.py` - 重新命名以明確區分
- `setup_database.py` → `setup_supabase.py` - 統一命名規範
- `database/` → `supabase/` - 資料夾重新組織
- `examples/database_queries.py` → `examples/supabase_queries.py` - 查詢範例重新命名

### 技術改進
- 🔧 新增 firebase-admin 套件依賴
- 📁 完善的 Firebase 配置檔案管理
- 🛠️ 自動化設定和初始化流程
- 📖 詳細的雙資料庫比較和使用指南

## v2.1.0 - 2024-12-19

### 新功能 🎉
- 🗄️ **Supabase 資料庫整合** - 支援將卡牌資料同步到 PostgreSQL 資料庫
- 📊 設計完整的正規化資料庫結構，支援多語言資料
- 🔄 非同步資料同步，支援批次處理和錯誤恢復
- 📈 資料同步記錄和統計功能
- 🔍 豐富的資料庫查詢範例

### 資料庫功能
- 📋 12 個主要資料表，完整支援卡牌資料結構
- 🌐 多語言支援（卡片名稱、描述分語言儲存）
- 🔗 完整的關聯資料（種族、技能、卡片關聯等）
- 📝 卡片問答和風格變體支援
- 🚀 效能優化的索引設計

### 新增檔案
- `supabase_sync.py` - 主要資料庫同步腳本
- `supabase/schema.sql` - 完整資料庫結構定義
- `supabase/init_supabase.py` - 資料庫初始化工具
- `examples/supabase_queries.py` - 資料庫查詢範例
- `setup_supabase.py` - 資料庫設定輔助程式

### 技術改進
- 🔧 新增 Supabase 和 asyncpg 套件依賴
- 📁 完善的配置檔案管理
- 🛡️ 完整的錯誤處理和日誌記錄
- 📖 詳細的使用文件和範例

### 新功能
- ✨ 添加多語言支援（cht, chs, en, ja, ko）
- 📁 重新整理專案結構，分類檔案到不同目錄
- 🔧 簡化安裝和使用流程

### 改進
- 🚀 移除 Selenium 依賴，使用純 requests 實現
- 📊 改進日誌記錄和進度追蹤
- 🎯 優化錯誤處理和恢復機制
- 📝 更新文件和使用範例

### 專案結構
- 📂 `output/` - 爬取的 JSON 資料檔案
- 📂 `docs/` - 文件和 API 範例
- 📂 `examples/` - 使用範例程式
- 📂 `logs/` - 執行日誌檔案

### 刪除的檔案
- ❌ `shadowverse_crawler.py` - Selenium 版本爬蟲
- ❌ 各種臨時和測試檔案
- ❌ 重複的範例檔案

## v1.0.0 - 初始版本
- 基本的卡牌資料爬取功能
- Selenium WebDriver 實現