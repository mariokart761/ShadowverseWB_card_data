-- 創建 schema
CREATE SCHEMA IF NOT EXISTS svwb_data;

-- 設置語言枚舉類型
CREATE TYPE svwb_data.language_code AS ENUM ('cht', 'chs', 'en', 'ja', 'ko');

-- 卡片類型枚舉
CREATE TYPE svwb_data.card_type AS ENUM ('follower', 'spell', 'amulet');

-- 卡片職業枚舉
CREATE TYPE svwb_data.card_class AS ENUM ('neutral', 'forestcraft', 'swordcraft', 'runecraft', 'dragoncraft', 'shadowcraft', 'bloodcraft', 'havencraft', 'portalcraft');

-- 卡片稀有度枚舉
CREATE TYPE svwb_data.card_rarity AS ENUM ('bronze', 'silver', 'gold', 'legendary');

-- 卡組系列表
CREATE TABLE svwb_data.card_sets (
    id INTEGER PRIMARY KEY,
    name JSONB NOT NULL DEFAULT '{}', -- 多語言名稱 {"cht": "基本卡", "en": "Basic", ...}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 部族表
CREATE TABLE svwb_data.tribes (
    id INTEGER PRIMARY KEY,
    name JSONB NOT NULL DEFAULT '{}', -- 多語言名稱
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 技能表
CREATE TABLE svwb_data.skills (
    id INTEGER PRIMARY KEY,
    name JSONB NOT NULL DEFAULT '{}', -- 多語言名稱
    replace_text JSONB DEFAULT '{}', -- 替換文字
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 卡片主表
CREATE TABLE svwb_data.cards (
    card_id BIGINT PRIMARY KEY,
    base_card_id BIGINT NOT NULL,
    card_resource_id BIGINT NOT NULL,
    name JSONB NOT NULL DEFAULT '{}', -- 多語言名稱
    name_ruby JSONB DEFAULT '{}', -- 多語言振假名
    atk INTEGER,
    life INTEGER,
    cost INTEGER NOT NULL,
    type INTEGER NOT NULL, -- 1=從者, 2=護符(無倒數), 3=護符(有倒數), 4=法術
    class INTEGER NOT NULL, -- 職業
    rarity INTEGER NOT NULL, -- 1=青銅, 2=白銀, 3=黃金, 4=虹彩
    card_set_id INTEGER NOT NULL REFERENCES svwb_data.card_sets(id),
    cv JSONB DEFAULT '{}', -- 多語言聲優
    illustrator TEXT,
    is_token BOOLEAN DEFAULT FALSE,
    is_include_rotation BOOLEAN DEFAULT TRUE,
    card_image_hash TEXT,
    card_banner_image_hash TEXT,
    evo_card_resource_id BIGINT,
    evo_card_image_hash TEXT,
    evo_card_banner_image_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT fk_card_set FOREIGN KEY (card_set_id) REFERENCES svwb_data.card_sets(id)
);

-- 卡片文字內容表（分語言存儲）
CREATE TABLE svwb_data.card_texts (
    id BIGSERIAL PRIMARY KEY,
    card_id BIGINT NOT NULL REFERENCES svwb_data.cards(card_id) ON DELETE CASCADE,
    language svwb_data.language_code NOT NULL,
    skill_text TEXT DEFAULT '',
    flavour_text TEXT DEFAULT '',
    evo_skill_text TEXT DEFAULT '',
    evo_flavour_text TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(card_id, language)
);

-- 卡片部族關聯表
CREATE TABLE svwb_data.card_tribes (
    id BIGSERIAL PRIMARY KEY,
    card_id BIGINT NOT NULL REFERENCES svwb_data.cards(card_id) ON DELETE CASCADE,
    tribe_id INTEGER NOT NULL REFERENCES svwb_data.tribes(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(card_id, tribe_id)
);

-- 卡片關聯表（相關卡片）
CREATE TABLE svwb_data.card_relations (
    id BIGSERIAL PRIMARY KEY,
    card_id BIGINT NOT NULL REFERENCES svwb_data.cards(card_id) ON DELETE CASCADE,
    related_card_id BIGINT NOT NULL,
    relation_type TEXT DEFAULT 'related', -- 'related', 'specific_effect'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(card_id, related_card_id, relation_type)
);

-- 卡片問答表
CREATE TABLE svwb_data.card_questions (
    id BIGSERIAL PRIMARY KEY,
    card_id BIGINT NOT NULL REFERENCES svwb_data.cards(card_id) ON DELETE CASCADE,
    language svwb_data.language_code NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 提示表
CREATE TABLE svwb_data.tips (
    id BIGSERIAL PRIMARY KEY,
    language svwb_data.language_code NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(language, title)
);

-- 創建索引
CREATE INDEX idx_cards_base_card_id ON svwb_data.cards(base_card_id);
CREATE INDEX idx_cards_card_set_id ON svwb_data.cards(card_set_id);
CREATE INDEX idx_cards_type ON svwb_data.cards(type);
CREATE INDEX idx_cards_class ON svwb_data.cards(class);
CREATE INDEX idx_cards_rarity ON svwb_data.cards(rarity);
CREATE INDEX idx_cards_cost ON svwb_data.cards(cost);
CREATE INDEX idx_card_texts_card_id_language ON svwb_data.card_texts(card_id, language);
CREATE INDEX idx_card_tribes_card_id ON svwb_data.card_tribes(card_id);
CREATE INDEX idx_card_relations_card_id ON svwb_data.card_relations(card_id);
CREATE INDEX idx_card_questions_card_id_language ON svwb_data.card_questions(card_id, language);
CREATE INDEX idx_tips_language ON svwb_data.tips(language);

-- 更新時間觸發器函數
CREATE OR REPLACE FUNCTION svwb_data.update_modified_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 創建觸發器
CREATE TRIGGER update_card_sets_modified_time
    BEFORE UPDATE ON svwb_data.card_sets
    FOR EACH ROW
    EXECUTE FUNCTION svwb_data.update_modified_time();

CREATE TRIGGER update_tribes_modified_time
    BEFORE UPDATE ON svwb_data.tribes
    FOR EACH ROW
    EXECUTE FUNCTION svwb_data.update_modified_time();

CREATE TRIGGER update_skills_modified_time
    BEFORE UPDATE ON svwb_data.skills
    FOR EACH ROW
    EXECUTE FUNCTION svwb_data.update_modified_time();

CREATE TRIGGER update_cards_modified_time
    BEFORE UPDATE ON svwb_data.cards
    FOR EACH ROW
    EXECUTE FUNCTION svwb_data.update_modified_time();

CREATE TRIGGER update_card_texts_modified_time
    BEFORE UPDATE ON svwb_data.card_texts
    FOR EACH ROW
    EXECUTE FUNCTION svwb_data.update_modified_time();

CREATE TRIGGER update_card_questions_modified_time
    BEFORE UPDATE ON svwb_data.card_questions
    FOR EACH ROW
    EXECUTE FUNCTION svwb_data.update_modified_time();

CREATE TRIGGER update_tips_modified_time
    BEFORE UPDATE ON svwb_data.tips
    FOR EACH ROW
    EXECUTE FUNCTION svwb_data.update_modified_time();

-- RLS 啟用
ALTER TABLE svwb_data.card_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE svwb_data.tribes ENABLE ROW LEVEL SECURITY;
ALTER TABLE svwb_data.skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE svwb_data.cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE svwb_data.card_texts ENABLE ROW LEVEL SECURITY;
ALTER TABLE svwb_data.card_tribes ENABLE ROW LEVEL SECURITY;
ALTER TABLE svwb_data.card_relations ENABLE ROW LEVEL SECURITY;
ALTER TABLE svwb_data.card_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE svwb_data.tips ENABLE ROW LEVEL SECURITY;

-- 創建 RLS 政策（允許所有操作給認證用戶，如果需要更細緻的權限控制可以修改）
-- 讀取政策（所有人可讀）
CREATE POLICY "Enable read access for all users" ON svwb_data.card_sets FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON svwb_data.tribes FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON svwb_data.skills FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON svwb_data.cards FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON svwb_data.card_texts FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON svwb_data.card_tribes FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON svwb_data.card_relations FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON svwb_data.card_questions FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON svwb_data.tips FOR SELECT USING (true);

-- 寫入政策（認證用戶可寫）
CREATE POLICY "Enable write access for authenticated users" ON svwb_data.card_sets FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON svwb_data.tribes FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON svwb_data.skills FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON svwb_data.cards FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON svwb_data.card_texts FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON svwb_data.card_tribes FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON svwb_data.card_relations FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON svwb_data.card_questions FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Enable write access for authenticated users" ON svwb_data.tips FOR ALL USING (auth.role() = 'authenticated');

-- 服務角色政策（用於腳本同步）
CREATE POLICY "Enable all access for service role" ON svwb_data.card_sets FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Enable all access for service role" ON svwb_data.tribes FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Enable all access for service role" ON svwb_data.skills FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Enable all access for service role" ON svwb_data.cards FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Enable all access for service role" ON svwb_data.card_texts FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Enable all access for service role" ON svwb_data.card_tribes FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Enable all access for service role" ON svwb_data.card_relations FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Enable all access for service role" ON svwb_data.card_questions FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Enable all access for service role" ON svwb_data.tips FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- 初始化一些基本數據
INSERT INTO svwb_data.card_sets (id, name) VALUES 
(10000, '{"cht": "基本卡", "chs": "基本卡", "en": "Basic", "ja": "ベーシック", "ko": "베이직"}'),
(10001, '{"cht": "傳說揭幕", "chs": "传说揭幕", "en": "Rise of Legends", "ja": "レジェンドライズ", "ko": "레전드 라이즈"}'),
(10002, '{"cht": "無限進化", "chs": "无限进化", "en": "Infinite Evolution", "ja": "インフィニット・エヴォリューション", "ko": "무한 진화"}');

INSERT INTO svwb_data.tribes (id, name) VALUES 
(0, '{"cht": "-", "chs": "-", "en": "-", "ja": "-", "ko": "-"}'),
(2, '{"cht": "士兵", "chs": "士兵", "en": "Officer", "ja": "兵士", "ko": "병사"}'),
(3, '{"cht": "魯米那斯", "chs": "鲁米那斯", "en": "Luminas", "ja": "ルミナス", "ko": "루미나스"}'),
(4, '{"cht": "雷維翁", "chs": "雷维翁", "en": "Levin", "ja": "雷維翁", "ko": "레비온"}'),
(5, '{"cht": "妖精", "chs": "妖精", "en": "Fairy", "ja": "フェアリー", "ko": "페어리"}'),
(6, '{"cht": "死者", "chs": "死者", "en": "Undead", "ja": "死者", "ko": "언데드"}'),
(8, '{"cht": "土之印", "chs": "土之印", "en": "Earth Sigil", "ja": "土の印", "ko": "대지의 인장"}'),
(11, '{"cht": "馬納歷亞", "chs": "马纳历亚", "en": "Manaria", "ja": "マナリア", "ko": "마나리아"}'),
(12, '{"cht": "巨像", "chs": "巨像", "en": "Golem", "ja": "ゴーレム", "ko": "골렘"}'),
(13, '{"cht": "式神", "chs": "式神", "en": "Shikigami", "ja": "式神", "ko": "시키가미"}'),
(14, '{"cht": "創造物", "chs": "创造物", "en": "Artifact", "ja": "アーティファクト", "ko": "아티팩트"}'),
(15, '{"cht": "人偶", "chs": "人偶", "en": "Puppet", "ja": "操り人形", "ko": "인형"}'),
(17, '{"cht": "海洋", "chs": "海洋", "en": "Oceanic", "ja": "海洋", "ko": "해양"}'),
(20, '{"cht": "弒滅者", "chs": "弑灭者", "en": "Destroyer", "ja": "デストロイヤー", "ko": "파괴자"}');

INSERT INTO svwb_data.skills (id, name, replace_text) VALUES 
(0, '{"cht": "", "chs": "", "en": "", "ja": "", "ko": ""}', '{}'),
(1, '{"cht": "入場曲", "chs": "入场曲", "en": "Fanfare", "ja": "ファンファーレ", "ko": "팡파르"}', '{}'),
(2, '{"cht": "謝幕曲", "chs": "谢幕曲", "en": "Last Words", "ja": "ラストワード", "ko": "라스트 워드"}', '{}'),
(3, '{"cht": "進化時", "chs": "进化时", "en": "Evolve", "ja": "進化時", "ko": "진화시"}', '{}'),
(4, '{"cht": "攻擊時", "chs": "攻击时", "en": "Strike", "ja": "攻撃時", "ko": "공격시"}', '{}'),
(5, '{"cht": "守護", "chs": "守护", "en": "Ward", "ja": "守護", "ko": "수호"}', '{}'),
(6, '{"cht": "疾馳", "chs": "疾驰", "en": "Storm", "ja": "疾走", "ko": "질주"}', '{}'),
(7, '{"cht": "潛行", "chs": "潜行", "en": "Stealth", "ja": "潜伏", "ko": "잠복"}', '{}'),
(8, '{"cht": "必殺", "chs": "必杀", "en": "Bane", "ja": "必殺", "ko": "필살"}', '{}'),
(9, '{"cht": "吸血", "chs": "吸血", "en": "Drain", "ja": "ドレイン", "ko": "드레인"}', '{}'),
(10, '{"cht": "覺醒", "chs": "觉醒", "en": "Overflow", "ja": "覚醒", "ko": "각성"}', '{}'),
(12, '{"cht": "魔力增幅時", "chs": "魔力增幅时", "en": "Spellboost", "ja": "スペルブースト", "ko": "스펠부스트"}', '{"cht": "魔力增幅", "chs": "魔力增幅", "en": "Spellboost", "ja": "スペルブースト", "ko": "스펠부스트"}'),
(13, '{"cht": "倒數", "chs": "倒数", "en": "Countdown", "ja": "カウントダウン", "ko": "카운트다운"}', '{}'),
(14, '{"cht": "死靈術", "chs": "死灵术", "en": "Necromancy", "ja": "ネクロマンス", "ko": "네크로맨스"}', '{}'),
(15, '{"cht": "土之秘術", "chs": "土之秘术", "en": "Earth Rite", "ja": "土の秘術", "ko": "대지의 비술"}', '{}'),
(16, '{"cht": "突進", "chs": "突进", "en": "Rush", "ja": "突進", "ko": "돌진"}', '{}'),
(17, '{"cht": "交戰時", "chs": "交战时", "en": "Clash", "ja": "交戦時", "ko": "교전시"}', '{}'),
(18, '{"cht": "爆能強化", "chs": "爆能强化", "en": "Accelerate", "ja": "アクセラレート", "ko": "액셀러레이트"}', '{}'),
(19, '{"cht": "亡者召還", "chs": "亡者召唤", "en": "Reanimate", "ja": "リアニメイト", "ko": "리애니메이트"}', '{}'),
(25, '{"cht": "融合", "chs": "融合", "en": "Fusion", "ja": "フュージョン", "ko": "퓨전"}', '{}'),
(26, '{"cht": "協作", "chs": "协作", "en": "Union Burst", "ja": "ユニオンバースト", "ko": "유니온 버스트"}', '{}'),
(27, '{"cht": "土之印", "chs": "土之印", "en": "Earth Sigil", "ja": "土の印", "ko": "대지의 인장"}', '{}'),
(29, '{"cht": "連擊", "chs": "连击", "en": "Combo", "ja": "コンボ", "ko": "콤보"}', '{}'),
(30, '{"cht": "威懾", "chs": "威慑", "en": "Intimidate", "ja": "威圧", "ko": "위압"}', '{}'),
(31, '{"cht": "光紋", "chs": "光纹", "en": "Crystallize", "ja": "結晶", "ko": "결정"}', '{}'),
(32, '{"cht": "障壁", "chs": "障壁", "en": "Barrier", "ja": "バリア", "ko": "배리어"}', '{}'),
(33, '{"cht": "超進化時", "chs": "超进化时", "en": "Evo", "ja": "エボ", "ko": "에보"}', '{}'),
(34, '{"cht": "模式", "chs": "模式", "en": "Choose", "ja": "チョイス", "ko": "초이스"}', '{}'),
(35, '{"cht": "策動", "chs": "策动", "en": "Invocation", "ja": "起動", "ko": "기동"}', '{}'),
(36, '{"cht": "紋章", "chs": "纹章", "en": "Crest", "ja": "クレスト", "ko": "크레스트"}', '{}'),
(38, '{"cht": "啟示錄牌組", "chs": "启示录牌组", "en": "Apocalypse Deck", "ja": "アポカリプスデッキ", "ko": "아포칼립스 덱"}', '{}');

-- 視圖：卡片完整信息（便於查詢）
CREATE VIEW svwb_data.cards_full_info AS
SELECT 
    c.*,
    cs.name as card_set_name,
    ct.language,
    ct.skill_text,
    ct.flavour_text,
    ct.evo_skill_text,
    ct.evo_flavour_text
FROM svwb_data.cards c
LEFT JOIN svwb_data.card_sets cs ON c.card_set_id = cs.id
LEFT JOIN svwb_data.card_texts ct ON c.card_id = ct.card_id;