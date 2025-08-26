# Shadowverse 資料庫說明文檔（Supabase）

> 本文件說明 `schema.sql` 的資料模型、權限、索引與維運作業；並補充 `supabase_sync.py` 同步腳本的使用重點與最佳實務。

---

## 1. 目標與範圍

* 以 **base + i18n** 正規化模型管理多語系卡片資料（卡組、部族、技能、卡片本體與文字、問答、提示等）。
* 以 **RLS（Row Level Security）** 與策略區分匿名/已登入/Service Role 權限。
* 以觸發器自動維護 `updated_at`，並提供一個查詢友善的匯總視圖 `cards_full_info`。

---

## 2. 名詞與命名約定

* **Base**：語言獨立屬性（例如 ID、數值屬性、所屬卡包）。
* **i18n**：語言相關屬性（例如名稱、圖片雜湊、文案）。
* **語言代碼**：`cht`、`chs`、`en`、`ja`、`ko`。

> 註：DDL 中亦定義 `card_type`、`card_class`、`card_rarity` 枚舉，但目前欄位仍以整數存放（保留向枚舉遷移的可能）。

---

## 3. 資料模型總覽（ER 重點）

```
card_set_bases (1) ─┐
                    ├─< card_set_i18n (多語)
tribe_bases (1) ────┤
                    └─< tribe_i18n   (多語)
skill_bases (1) ────┐
                    └─< skill_i18n   (多語)

card_bases (1) ──< card_i18n (多語)
   │               │
   │               ├─< card_texts (每語言 1 筆)
   │
   ├─< card_tribes (多對多至 tribe_bases)
   ├─< card_relations (自關聯: related / specific_effect)
   └─< card_questions (多語)
```

---

## 4. 枚舉型別（Enums）

* `language_code`: `cht | chs | en | ja | ko`
* `card_type`: `follower | spell | amulet`
* `card_class`: `neutral | forestcraft | swordcraft | runecraft | dragoncraft | shadowcraft | bloodcraft | havencraft | portalcraft`
* `card_rarity`: `bronze | silver | gold | legendary`

> 目前 `card_bases.type/class/rarity` 為整數欄位，對應關係建議於應用層或參照表維護；未來可視需要遷移為上述枚舉。

---

## 5. 資料表一覽與欄位說明

### 5.1 卡組系列（Set）

**card\_set\_bases**

* `id` (PK)
* `created_at`, `updated_at`

**card\_set\_i18n**（PK: `card_set_id + language`）

* `card_set_id` → `card_set_bases.id`
* `language` (language\_code)
* `name`
* 時戳欄位同上

### 5.2 部族（Tribe）

**tribe\_bases** / **tribe\_i18n**：結構與卡組系列相同（`name` 為部族名稱）。

### 5.3 技能（Skill）

**skill\_bases** / **skill\_i18n**：

* `skill_i18n.name` 技能名
* `skill_i18n.replace_text` 技能取代文字（模板/渲染用）

### 5.4 卡片（Card）

**card\_bases**（語言獨立屬性）

* `card_id` (PK)
* `base_card_id`：同卡多版本聚合鍵（同屬一張卡不同語言/進化圖等）
* 數值屬性：`atk`, `life`, `cost`
* 類別屬性：`type`（1=從者, 2=護符(無倒數), 3=護符(有倒數), 4=法術）、`class`（職業）、`rarity`（1\~4）
* 其他：`card_set_id`, `is_token`（是否衍生物）、`is_include_rotation`（是否輪替可用）
* 時戳：`created_at`, `updated_at`

**card\_i18n**（語言相關屬性，PK: `card_id + language`）

* 基本：`name`, `name_ruby`, `cv`, `illustrator`
* 靜態資源：`card_resource_id` / `card_image_hash` / `card_banner_image_hash`
* 進化圖資源：`evo_card_resource_id` / `evo_card_image_hash` / `evo_card_banner_image_hash`

**card\_texts**（每語言一筆，Unique: `card_id + language`）

* `skill_text`, `flavour_text`
* 進化後：`evo_skill_text`, `evo_flavour_text`
* FK：(`card_id`, `language`) → `card_i18n(card_id, language)`（ON DELETE CASCADE）

**card\_tribes**（卡片與部族多對多）

* `card_id` → `card_bases.card_id`
* `tribe_id` → `tribe_bases.id`
* `UNIQUE(card_id, tribe_id)`

**card\_relations**（卡片之間的引用關係）

* `card_id`, `related_card_id`
* `relation_type`：`related` / `specific_effect`
* `UNIQUE(card_id, related_card_id, relation_type)`

**card\_questions**（Q\&A，依語言分筆）

* `card_id`, `language`, `question`, `answer`
* FK：(`card_id`, `language`) → `card_i18n(card_id, language)`（ON DELETE CASCADE）

### 5.5 提示（Tips）

**tips**

* `language`, `title`, `description`, `sort_order`
* `UNIQUE(language, title)`

---

## 6. 視圖（View）

**cards\_full\_info**：便於單表查詢卡片完整資訊的匯總視圖。

* 來源：`card_bases` 內聯 `card_i18n`；左外聯 `card_set_i18n`（同語言）與 `card_texts`（同語言）。
* 欄位：

  * 來自 `card_bases` 的所有欄位
  * 語言欄位與 `card_i18n` 文案/資源欄位
  * `card_set_name`（由 `card_set_i18n.name` 投影）
  * `skill_text`, `flavour_text`, `evo_skill_text`, `evo_flavour_text`

> 建議用於 API 讀取與後台檢索；進階篩選（部族、關聯）可額外 JOIN 對應表。

---

## 7. 索引與效能

已建立針對常用篩選欄位的索引：

* `card_bases`: `base_card_id`, `card_set_id`, `type`, `class`, `rarity`, `cost`
* `card_i18n`: `language`, `(language, card_id)`
* `card_set_i18n/tribe_i18n/skill_i18n`: `language`, `(language, *_id)`
* 其他：`card_texts(card_id, language)`, `card_tribes(card_id)`, `card_relations(card_id)`, `card_questions(card_id, language)`, `tips(language)`

**查詢建議**

* 以語言為先：多語內容檢索時先以 `language = :lang` 篩選，再以其他條件縮小結果。
* 依卡包/職業/費用做複合條件，讓單欄索引仍能快速篩選。

---

## 8. RLS（列級安全）與政策

**RLS 啟用於所有表**，並配置三類政策：

1. **Read for all users**：任何角色可 `SELECT`（公開讀）
2. **All access for service\_role**：Service Role 可 `ALL`（供離線同步腳本使用）
3. **Write for authenticated**：登入用戶可 `ALL`（如前端需要寫入；若前端純讀可移除此組）

> 若僅允許後端/腳本寫入，建議移除「authenticated 寫入」政策，或改為更細粒度（逐表/逐動作）。

---

## 9. 觸發器與時間戳

* 通用觸發器函數 `update_modified_time()`：於 **UPDATE** 時回填 `updated_at = now()`。
* 已套用於 base、i18n 與其他主要表。
* 注意：**INSERT** 不會觸發更新 `updated_at`，其值維持預設 `now()`。

---

## 10. 資料遷移（舊→新 base+i18n）操作指南

> DDL 內已備妥步驟註解與範例 SQL，建議流程：

1. **建立新表**（本 schema 已完成）
2. **回填 base 與 i18n**（依舊表 `card_sets/tribes/skills/cards` 匯入）
3. **調整外鍵**：讓 `card_tribes`、`card_texts`、`card_questions` 指向新結構
4. **驗證數量**：以 UNION 檢視舊/新筆數是否一致
5. **刪除舊表**：確認成功後再清理

---

## 11. 同步腳本使用（`supabase_sync.py`）

### 11.1 作用

* 從 `output/` 內各語言 JSON 匯入：卡組名稱、部族、技能（含 `replace_text`）、卡片（含進化/圖片哈希/文字）、部族關聯、卡片關聯、Q\&A、提示（tips）。
* 預設語言集：`cht chs en ja ko`；可選 `--cards-only` / `--tips-only`。
* 提供 `--test`（表可存取性）、`--validate`（統計數量）、`--clean`（危險：清空資料）。

### 11.2 權限與 Schema

* 以 **Service Role key** 連線（需具 `service_role` 政策與 `public` schema）。
* 以 `schema('public').table(name)` 方式操作各表。

### 11.3 匯入邏輯摘要

* **idempotent**：先查有無，再決定 `insert/update`；關聯表如 `card_tribes`/`card_relations` 先全刪後重建，確保與來源一致。
* **語言依賴**：部族/關聯只在 `cht` 語言回寫一次，避免重複。
* **一致性**：`card_texts`、`card_questions` 依語言唯一；`tips` 依語言全量覆蓋（先刪舊再插入）。

### 11.4 常見問題

* `permission denied`：多半為 RLS/金鑰錯誤，請確認 `schema.sql` 已套用、使用 service\_role key、並重新建立連線。
* `42P01`（關聯不存在）：請確認已於正確 schema 建表且客戶端指定 `public`。

---

## 12. 常見查詢範例（SQL）

**A. 以視圖查卡片（含卡包名與文案）**

```sql
SELECT card_id, language, name, card_set_name, cost, type, class, rarity,
       skill_text, evo_skill_text
FROM cards_full_info
WHERE language = 'cht' AND card_set_id = 900 AND class = 2
ORDER BY cost, rarity DESC;
```

**B. 查指定卡片的部族**

```sql
SELECT t.*
FROM card_tribes ct
JOIN tribe_i18n t ON t.tribe_id = ct.tribe_id AND t.language = 'cht'
WHERE ct.card_id = 123456;
```

**C. 查與某卡相關的卡（含特效關係）**

```sql
SELECT cr.related_card_id, cr.relation_type
FROM card_relations cr
WHERE cr.card_id = 123456;
```

**D. 查某語言的 Tips（依排序）**

```sql
SELECT title, description
FROM tips
WHERE language = 'ja'
ORDER BY sort_order;
```

---

## 13. 維運建議與最佳實務

* **唯讀應用**：若前台不需寫入，建議移除或收斂「authenticated 全寫入」政策，避免誤用。
* **枚舉一致性**：若切換至枚舉型別，需規劃好舊整數值→枚舉值的遷移與檢核。
* **批次匯入**：大量更新建議以語言/卡包分批執行，觀察寫入量與延遲。
* **索引維護**：觀測慢查詢（特別是多條件檢索），必要時新增複合索引。
* **備援/回滾**：在 `--clean` 或大量刪改前先備份（或在非正式環境驗證）。

---

## 14. 版本控管與變更紀錄（建議）

* 將 `schema.sql` 納入版本控管，以 migration 檔標記版本/日期。
* 對 `supabase_sync.py` 的語言集/匯入策略/刪除策略變更應記錄在 CHANGELOG。

---

### 附錄：欄位對照（速查）

* **語言欄位**：所有 i18n 表與 `card_texts`、`card_questions`、`tips` 皆有 `language`（enum）。
* **主鍵/唯一**：

  * `*_bases`: `id` 或 `card_id`
  * `*_i18n`: `(*_id, language)`
  * `card_texts`: `UNIQUE(card_id, language)`
  * `card_tribes`: `UNIQUE(card_id, tribe_id)`
  * `card_relations`: `UNIQUE(card_id, related_card_id, relation_type)`
  * `tips`: `UNIQUE(language, title)`
