-- 設置語言枚舉類型
DO $$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'language_code') THEN
      CREATE TYPE language_code AS ENUM ('cht', 'chs', 'en', 'ja', 'ko');
   END IF;
END
$$;

-- 卡片類型枚舉
DO $$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'card_type') THEN
      CREATE TYPE card_type AS ENUM ('follower', 'spell', 'amulet');
   END IF;
END
$$;

-- 卡片職業枚舉
DO $$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'card_class') THEN
      CREATE TYPE card_class AS ENUM ('neutral', 'forestcraft', 'swordcraft', 'runecraft', 'dragoncraft', 'shadowcraft', 'bloodcraft', 'havencraft', 'portalcraft');
   END IF;
END
$$;

-- 卡片稀有度枚舉
DO $$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'card_rarity') THEN
      CREATE TYPE card_rarity AS ENUM ('bronze', 'silver', 'gold', 'legendary');
   END IF;
END
$$;

-- === 卡組系列表 (正規化: base + i18n) ===
-- 卡組系列基礎表 (語言獨立)
CREATE TABLE card_set_bases (
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 卡組系列多語系表
CREATE TABLE card_set_i18n (
    card_set_id INTEGER NOT NULL REFERENCES card_set_bases(id) ON DELETE CASCADE,
    language language_code NOT NULL,
    name TEXT NOT NULL DEFAULT '', -- 卡組名稱
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (card_set_id, language)
);

-- === 部族表 (正規化: base + i18n) ===
-- 部族基礎表 (語言獨立)
CREATE TABLE tribe_bases (
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 部族多語系表
CREATE TABLE tribe_i18n (
    tribe_id INTEGER NOT NULL REFERENCES tribe_bases(id) ON DELETE CASCADE,
    language language_code NOT NULL,
    name TEXT NOT NULL DEFAULT '', -- 部族名稱
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tribe_id, language)
);

-- === 技能表 (正規化: base + i18n) ===
-- 技能基礎表 (語言獨立)
CREATE TABLE skill_bases (
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 技能多語系表
CREATE TABLE skill_i18n (
    skill_id INTEGER NOT NULL REFERENCES skill_bases(id) ON DELETE CASCADE,
    language language_code NOT NULL,
    name TEXT NOT NULL DEFAULT '', -- 技能名稱
    replace_text TEXT DEFAULT '', -- 替換文字
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (skill_id, language)
);

-- === 卡片主表 (正規化: base + i18n) ===
-- 卡片基礎表 (語言獨立屬性)
CREATE TABLE card_bases (
    card_id BIGINT PRIMARY KEY,
    base_card_id BIGINT NOT NULL,
    -- 語言不變屬性
    atk INTEGER,
    life INTEGER,
    cost INTEGER NOT NULL,
    type INTEGER NOT NULL, -- 1=從者, 2=護符(無倒數), 3=護符(有倒數), 4=法術
    class INTEGER NOT NULL, -- 職業
    rarity INTEGER NOT NULL, -- 1=青銅, 2=白銀, 3=黃金, 4=虹彩
    card_set_id INTEGER NOT NULL,
    is_token BOOLEAN DEFAULT FALSE,
    is_include_rotation BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 卡片多語系表
CREATE TABLE card_i18n (
    card_id BIGINT NOT NULL REFERENCES card_bases(card_id) ON DELETE CASCADE,
    language language_code NOT NULL,
    -- 語言相關屬性
    name TEXT NOT NULL DEFAULT '', -- 卡片名稱
    name_ruby TEXT DEFAULT '', -- 振假名
    cv TEXT DEFAULT '', -- 聲優
    illustrator TEXT,
    card_resource_id BIGINT NOT NULL,
    card_image_hash TEXT,
    card_banner_image_hash TEXT,
    evo_card_resource_id BIGINT,
    evo_card_image_hash TEXT,
    evo_card_banner_image_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (card_id, language)
);

-- 卡片文字內容表（分語言存儲）
CREATE TABLE card_texts (
    id BIGSERIAL PRIMARY KEY,
    card_id BIGINT NOT NULL,
    language language_code NOT NULL,
    skill_text TEXT DEFAULT '',
    flavour_text TEXT DEFAULT '',
    evo_skill_text TEXT DEFAULT '',
    evo_flavour_text TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(card_id, language),
    FOREIGN KEY (card_id, language) REFERENCES card_i18n(card_id, language) ON DELETE CASCADE
);

-- 卡片部族關聯表
CREATE TABLE card_tribes (
    id BIGSERIAL PRIMARY KEY,
    card_id BIGINT NOT NULL REFERENCES card_bases(card_id) ON DELETE CASCADE,
    tribe_id INTEGER NOT NULL REFERENCES tribe_bases(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(card_id, tribe_id)
);

-- 卡片關聯表（相關卡片）
CREATE TABLE card_relations (
    id BIGSERIAL PRIMARY KEY,
    card_id BIGINT NOT NULL,
    related_card_id BIGINT NOT NULL,
    relation_type TEXT DEFAULT 'related', -- 'related', 'specific_effect'
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(card_id, related_card_id, relation_type)
);

-- 卡片問答表
CREATE TABLE card_questions (
    id BIGSERIAL PRIMARY KEY,
    card_id BIGINT NOT NULL,
    language language_code NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (card_id, language) REFERENCES card_i18n(card_id, language) ON DELETE CASCADE
);

-- 提示表
CREATE TABLE tips (
    id BIGSERIAL PRIMARY KEY,
    language language_code NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(language, title)
);

-- 創建索引
-- 卡片相關索引
CREATE INDEX idx_card_bases_base_card_id ON card_bases(base_card_id);
CREATE INDEX idx_card_bases_card_set_id ON card_bases(card_set_id);
CREATE INDEX idx_card_bases_type ON card_bases(type);
CREATE INDEX idx_card_bases_class ON card_bases(class);
CREATE INDEX idx_card_bases_rarity ON card_bases(rarity);
CREATE INDEX idx_card_bases_cost ON card_bases(cost);
CREATE INDEX idx_card_i18n_language ON card_i18n(language);
CREATE INDEX idx_card_i18n_lang_card ON card_i18n(language, card_id);

-- 卡組系列相關索引
CREATE INDEX idx_card_set_i18n_language ON card_set_i18n(language);
CREATE INDEX idx_card_set_i18n_lang_id ON card_set_i18n(language, card_set_id);

-- 部族相關索引
CREATE INDEX idx_tribe_i18n_language ON tribe_i18n(language);
CREATE INDEX idx_tribe_i18n_lang_id ON tribe_i18n(language, tribe_id);

-- 技能相關索引
CREATE INDEX idx_skill_i18n_language ON skill_i18n(language);
CREATE INDEX idx_skill_i18n_lang_id ON skill_i18n(language, skill_id);

-- 其他索引
CREATE INDEX idx_card_texts_card_id_language ON card_texts(card_id, language);
CREATE INDEX idx_card_tribes_card_id ON card_tribes(card_id);
CREATE INDEX idx_card_relations_card_id ON card_relations(card_id);
CREATE INDEX idx_card_questions_card_id_language ON card_questions(card_id, language);
CREATE INDEX idx_tips_language ON tips(language);

-- 更新時間觸發器函數
CREATE OR REPLACE FUNCTION update_modified_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 創建觸發器
-- 基礎表觸發器
CREATE TRIGGER update_card_set_bases_modified_time
    BEFORE UPDATE ON card_set_bases
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER update_tribe_bases_modified_time
    BEFORE UPDATE ON tribe_bases
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER update_skill_bases_modified_time
    BEFORE UPDATE ON skill_bases
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER update_card_bases_modified_time
    BEFORE UPDATE ON card_bases
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

-- i18n表觸發器
CREATE TRIGGER update_card_set_i18n_modified_time
    BEFORE UPDATE ON card_set_i18n
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER update_tribe_i18n_modified_time
    BEFORE UPDATE ON tribe_i18n
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER update_skill_i18n_modified_time
    BEFORE UPDATE ON skill_i18n
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER update_card_i18n_modified_time
    BEFORE UPDATE ON card_i18n
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

-- 其他表觸發器
CREATE TRIGGER update_card_texts_modified_time
    BEFORE UPDATE ON card_texts
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER update_card_questions_modified_time
    BEFORE UPDATE ON card_questions
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

CREATE TRIGGER update_tips_modified_time
    BEFORE UPDATE ON tips
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_time();

-- 啟用 RLS
-- 基礎表
ALTER TABLE card_set_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE tribe_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_bases ENABLE ROW LEVEL SECURITY;

-- i18n表
ALTER TABLE card_set_i18n ENABLE ROW LEVEL SECURITY;
ALTER TABLE tribe_i18n ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_i18n ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_i18n ENABLE ROW LEVEL SECURITY;

-- 其他表
ALTER TABLE card_texts ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_tribes ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_relations ENABLE ROW LEVEL SECURITY;
ALTER TABLE card_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tips ENABLE ROW LEVEL SECURITY;

-- === RLS Policies ===

-- 讀取政策（所有人可讀）
-- 基礎表
CREATE POLICY "Enable read access for all users" ON card_set_bases FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON tribe_bases FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON skill_bases FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON card_bases FOR SELECT USING (true);

-- i18n表
CREATE POLICY "Enable read access for all users" ON card_set_i18n FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON tribe_i18n FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON skill_i18n FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON card_i18n FOR SELECT USING (true);

-- 其他表
CREATE POLICY "Enable read access for all users" ON card_texts FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON card_tribes FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON card_relations FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON card_questions FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON tips FOR SELECT USING (true);

-- 服務角色政策（用於腳本同步，允許所有操作）
-- 基礎表
CREATE POLICY "Enable all access for service role" ON card_set_bases FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Enable all access for service role" ON tribe_bases FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Enable all access for service role" ON skill_bases FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Enable all access for service role" ON card_bases FOR ALL USING (auth.role() = 'service_role');

-- i18n表
CREATE POLICY "Enable all access for service role" ON card_set_i18n FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Enable all access for service role" ON tribe_i18n FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Enable all access for service role" ON skill_i18n FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Enable all access for service role" ON card_i18n FOR ALL USING (auth.role() = 'service_role');

-- 其他表
CREATE POLICY "Enable all access for service role" ON card_texts FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Enable all access for service role" ON card_tribes FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Enable all access for service role" ON card_relations FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Enable all access for service role" ON card_questions FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Enable all access for service role" ON tips FOR ALL USING (auth.role() = 'service_role');

-- 寫入政策（只有 authenticated 用戶可寫，如果前端完全不需要寫，可以移掉這段）
-- 基礎表
CREATE POLICY "Enable write access for authenticated users" ON card_set_bases FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON tribe_bases FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON skill_bases FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON card_bases FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

-- i18n表
CREATE POLICY "Enable write access for authenticated users" ON card_set_i18n FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON tribe_i18n FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON skill_i18n FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON card_i18n FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

-- 其他表
CREATE POLICY "Enable write access for authenticated users" ON card_texts FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON card_tribes FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON card_relations FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON card_questions FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON tips FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

-- 初始化數據將在同步腳本中處理

-- 視圖：卡片完整信息（便於查詢）
CREATE VIEW cards_full_info AS
SELECT
    b.*,
    i.language,
    i.name,
    i.name_ruby,
    i.cv,
    i.illustrator,
    i.card_resource_id,
    i.card_image_hash,
    i.card_banner_image_hash,
    i.evo_card_resource_id,
    i.evo_card_image_hash,
    i.evo_card_banner_image_hash,
    csi.name AS card_set_name,
    ct.skill_text,
    ct.flavour_text,
    ct.evo_skill_text,
    ct.evo_flavour_text
FROM card_bases b
JOIN card_i18n i ON b.card_id = i.card_id
LEFT JOIN card_set_i18n csi ON b.card_set_id = csi.card_set_id AND i.language = csi.language
LEFT JOIN card_texts ct ON b.card_id = ct.card_id AND i.language = ct.language;

-- === 遷移腳本：從舊表結構遷移到新結構 ===
-- 注意：請在確認新表結構正確且無資料後執行此腳本
-- 執行順序：1. 建立新表 2. 執行遷移 3. 驗證資料 4. 刪除舊表

-- 步驟1: 回填基礎表資料
-- INSERT INTO card_set_bases(id, created_at, updated_at)
-- SELECT id, MIN(created_at), MAX(updated_at) FROM card_sets GROUP BY id;

-- INSERT INTO tribe_bases(id, created_at, updated_at)
-- SELECT id, MIN(created_at), MAX(updated_at) FROM tribes GROUP BY id;

-- INSERT INTO skill_bases(id, created_at, updated_at)
-- SELECT id, MIN(created_at), MAX(updated_at) FROM skills GROUP BY id;

-- INSERT INTO card_bases (card_id, base_card_id, atk, life, cost, type, class, rarity, card_set_id, is_token, is_include_rotation, created_at, updated_at)
-- SELECT card_id, base_card_id, atk, life, cost, type, class, rarity, card_set_id, is_token, is_include_rotation,
--        MIN(created_at), MAX(updated_at)
-- FROM cards
-- GROUP BY card_id, base_card_id, atk, life, cost, type, class, rarity, card_set_id, is_token, is_include_rotation;

-- 步驟2: 回填i18n表資料
-- INSERT INTO card_set_i18n(card_set_id, language, name, created_at, updated_at)
-- SELECT id, language, name, created_at, updated_at FROM card_sets;

-- INSERT INTO tribe_i18n(tribe_id, language, name, created_at, updated_at)
-- SELECT id, language, name, created_at, updated_at FROM tribes;

-- INSERT INTO skill_i18n(skill_id, language, name, replace_text, created_at, updated_at)
-- SELECT id, language, name, replace_text, created_at, updated_at FROM skills;

-- INSERT INTO card_i18n (card_id, language, name, name_ruby, cv, illustrator,
--                        card_resource_id, card_image_hash, card_banner_image_hash,
--                        evo_card_resource_id, evo_card_image_hash, evo_card_banner_image_hash,
--                        created_at, updated_at)
-- SELECT card_id, language, name, name_ruby, cv, illustrator,
--        card_resource_id, card_image_hash, card_banner_image_hash,
--        evo_card_resource_id, evo_card_image_hash, evo_card_banner_image_hash,
--        created_at, updated_at
-- FROM cards;

-- 步驟3: 更新外鍵（如果尚未執行 ALTER TABLE 語句）
-- ALTER TABLE card_tribes DROP CONSTRAINT IF EXISTS card_tribes_tribe_id_fkey;
-- ALTER TABLE card_tribes ADD CONSTRAINT card_tribes_tribe_id_fkey FOREIGN KEY (tribe_id) REFERENCES tribe_bases(id);

-- ALTER TABLE card_texts DROP CONSTRAINT IF EXISTS card_texts_card_id_language_fkey;
-- ALTER TABLE card_texts ADD CONSTRAINT card_texts_card_lang_fkey FOREIGN KEY (card_id, language) REFERENCES card_i18n(card_id, language) ON DELETE CASCADE;

-- ALTER TABLE card_questions DROP CONSTRAINT IF EXISTS card_questions_card_id_language_fkey;
-- ALTER TABLE card_questions ADD CONSTRAINT card_questions_card_lang_fkey FOREIGN KEY (card_id, language) REFERENCES card_i18n(card_id, language) ON DELETE CASCADE;

-- 步驟4: 驗證遷移
-- SELECT 'card_sets' as table_name, COUNT(*) as old_count FROM card_sets
-- UNION ALL
-- SELECT 'card_set_bases', COUNT(*) FROM card_set_bases
-- UNION ALL
-- SELECT 'card_set_i18n', COUNT(*) FROM card_set_i18n;

-- 步驟5: 刪除舊表（在確認遷移成功後）
-- DROP TABLE IF EXISTS card_sets CASCADE;
-- DROP TABLE IF EXISTS tribes CASCADE;
-- DROP TABLE IF EXISTS skills CASCADE;
-- DROP TABLE IF EXISTS cards CASCADE;