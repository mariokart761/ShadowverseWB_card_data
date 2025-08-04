-- Shadowverse 卡牌資料庫結構

-- 1. 卡包資訊表
CREATE TABLE card_sets (
    id INTEGER PRIMARY KEY,
    name_cht TEXT,
    name_chs TEXT,
    name_en TEXT,
    name_ja TEXT,
    name_ko TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 種族資訊表
CREATE TABLE tribes (
    id INTEGER PRIMARY KEY,
    name_cht TEXT,
    name_chs TEXT,
    name_en TEXT,
    name_ja TEXT,
    name_ko TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 技能資訊表
CREATE TABLE skills (
    id INTEGER PRIMARY KEY,
    name_cht TEXT,
    name_chs TEXT,
    name_en TEXT,
    name_ja TEXT,
    name_ko TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 卡片主表
CREATE TABLE cards (
    id BIGINT PRIMARY KEY,
    base_card_id BIGINT,
    card_resource_id BIGINT,
    card_set_id INTEGER REFERENCES card_sets(id),
    type INTEGER, -- 1:從者, 2:護符, 3:建築物, 4:法術
    class INTEGER, -- 0:中立, 1:精靈, 2:皇家護衛, 3:巫師, 4:龍族, 5:死靈法師, 6:主教, 7:復仇者
    cost INTEGER,
    atk INTEGER,
    life INTEGER,
    rarity INTEGER, -- 1:銅, 2:銀, 3:金, 4:虹
    is_token BOOLEAN DEFAULT FALSE,
    is_include_rotation BOOLEAN DEFAULT FALSE,
    card_image_hash TEXT,
    card_banner_image_hash TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 卡片多語言名稱表
CREATE TABLE card_names (
    card_id BIGINT REFERENCES cards(id) ON DELETE CASCADE,
    language VARCHAR(3), -- cht, chs, en, ja, ko
    name TEXT NOT NULL,
    name_ruby TEXT,
    PRIMARY KEY (card_id, language)
);

-- 6. 卡片多語言描述表
CREATE TABLE card_descriptions (
    card_id BIGINT REFERENCES cards(id) ON DELETE CASCADE,
    language VARCHAR(3),
    form VARCHAR(10), -- common, evo
    flavour_text TEXT,
    skill_text TEXT,
    cv TEXT,
    illustrator TEXT,
    PRIMARY KEY (card_id, language, form)
);

-- 7. 卡片進化資訊表
CREATE TABLE card_evolutions (
    card_id BIGINT REFERENCES cards(id) ON DELETE CASCADE,
    card_resource_id BIGINT,
    card_image_hash TEXT,
    card_banner_image_hash TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (card_id)
);

-- 8. 卡片種族關聯表
CREATE TABLE card_tribes (
    card_id BIGINT REFERENCES cards(id) ON DELETE CASCADE,
    tribe_id INTEGER REFERENCES tribes(id),
    PRIMARY KEY (card_id, tribe_id)
);

-- 9. 卡片關聯表 (相關卡片)
CREATE TABLE card_relations (
    card_id BIGINT REFERENCES cards(id) ON DELETE CASCADE,
    related_card_id BIGINT,
    relation_type VARCHAR(20) DEFAULT 'related', -- related, specific_effect
    PRIMARY KEY (card_id, related_card_id, relation_type)
);

-- 10. 卡片問答表
CREATE TABLE card_questions (
    id SERIAL PRIMARY KEY,
    card_id BIGINT REFERENCES cards(id) ON DELETE CASCADE,
    language VARCHAR(3),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. 卡片風格變體表
CREATE TABLE card_styles (
    id SERIAL PRIMARY KEY,
    card_id BIGINT REFERENCES cards(id) ON DELETE CASCADE,
    hash TEXT,
    evo_hash TEXT,
    name TEXT,
    name_ruby TEXT,
    cv TEXT,
    illustrator TEXT,
    skill_text TEXT,
    flavour_text TEXT,
    evo_flavour_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 12. 資料更新記錄表
CREATE TABLE data_sync_logs (
    id SERIAL PRIMARY KEY,
    language VARCHAR(3),
    total_cards INTEGER,
    successful_cards INTEGER,
    failed_cards INTEGER,
    sync_status VARCHAR(20), -- success, partial, failed
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 建立索引以提升查詢效能
CREATE INDEX idx_cards_class ON cards(class);
CREATE INDEX idx_cards_cost ON cards(cost);
CREATE INDEX idx_cards_rarity ON cards(rarity);
CREATE INDEX idx_cards_card_set_id ON cards(card_set_id);
CREATE INDEX idx_cards_is_token ON cards(is_token);
CREATE INDEX idx_cards_is_include_rotation ON cards(is_include_rotation);
CREATE INDEX idx_card_names_language ON card_names(language);
CREATE INDEX idx_card_names_name ON card_names(name);
CREATE INDEX idx_card_descriptions_language ON card_descriptions(language);
CREATE INDEX idx_data_sync_logs_language ON data_sync_logs(language);
CREATE INDEX idx_data_sync_logs_created_at ON data_sync_logs(created_at);

-- 建立更新時間的觸發器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_card_sets_updated_at BEFORE UPDATE ON card_sets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tribes_updated_at BEFORE UPDATE ON tribes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_skills_updated_at BEFORE UPDATE ON skills FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cards_updated_at BEFORE UPDATE ON cards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 建立 RLS (Row Level Security) 策略 (可選)
-- ALTER TABLE cards ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE card_names ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE card_descriptions ENABLE ROW LEVEL SECURITY;

-- 註解說明
COMMENT ON TABLE cards IS '卡片主要資訊表';
COMMENT ON TABLE card_names IS '卡片多語言名稱表';
COMMENT ON TABLE card_descriptions IS '卡片多語言描述表';
COMMENT ON TABLE card_evolutions IS '卡片進化資訊表';
COMMENT ON TABLE card_tribes IS '卡片種族關聯表';
COMMENT ON TABLE card_relations IS '卡片關聯表';
COMMENT ON TABLE card_questions IS '卡片問答表';
COMMENT ON TABLE card_styles IS '卡片風格變體表';
COMMENT ON TABLE data_sync_logs IS '資料同步記錄表';

COMMENT ON COLUMN cards.type IS '卡片類型: 1=從者, 2=護符, 3=建築物, 4=法術';
COMMENT ON COLUMN cards.class IS '職業: 0=中立, 1=精靈, 2=皇家護衛, 3=巫師, 4=龍族, 5=死靈法師, 6=主教, 7=復仇者';
COMMENT ON COLUMN cards.rarity IS '稀有度: 1=銅, 2=銀, 3=金, 4=虹';