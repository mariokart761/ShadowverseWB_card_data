#!/usr/bin/env python3
"""
Shadowverse 卡片資料同步至 Supabase 腳本
支援多語言卡片資料和提示資料同步
修正版本：正確指定 schema 以避免 42P01 錯誤
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    print("請先安裝 supabase-py: pip install supabase")
    sys.exit(1)

class ShadowverseDataSync:
    def __init__(self):
        """初始化同步器"""
        self.supabase: Optional[Client] = None
        self.schema_name = 'svwb_data'  # 指定 schema 名稱
        self.load_config()
        
    def load_config(self):
        """從配置文件載入 Supabase 連線資訊"""
        config_path = Path("supabase/config.json")
        
        if not config_path.exists():
            print(f"配置文件不存在: {config_path}")
            print("請創建配置文件，格式如下:")
            print("""
{
    "supabase_url": "https://your-project.supabase.co",
    "supabase_key": "your-service-role-key"
}
            """)
            sys.exit(1)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            required_keys = ['supabase_url', 'supabase_key']
            for key in required_keys:
                if key not in config:
                    print(f"配置文件缺少必要參數: {key}")
                    sys.exit(1)
            
            # 創建 Supabase 客戶端
            self.supabase = create_client(config['supabase_url'], config['supabase_key'])
            print(f"✓ 成功連接到 Supabase: {config['supabase_url']}")
            
        except json.JSONDecodeError as e:
            print(f"配置文件格式錯誤: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"載入配置失敗: {e}")
            sys.exit(1)
    
    def _get_table(self, table_name: str):
        """獲取指定 schema 的表引用"""
        return self.supabase.schema(self.schema_name).table(table_name)
    
    def sync_card_data(self, language_code: str):
        """同步卡片資料"""
        card_file_path = Path(f"output/shadowverse_cards_{language_code}.json")
        
        if not card_file_path.exists():
            print(f"卡片資料文件不存在: {card_file_path}")
            return False
        
        try:
            with open(card_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n開始同步 {language_code} 語言卡片資料...")
            
            # 同步基礎數據
            self._sync_card_sets(data.get('data', {}).get('card_set_names', {}), language_code)
            self._sync_tribes(data.get('data', {}).get('tribe_names', {}), language_code)
            self._sync_skills(data.get('data', {}).get('skill_names', {}), 
                            data.get('data', {}).get('skill_replace_text_names', {}), language_code)
            
            # 同步卡片詳細資料
            card_details = data.get('data', {}).get('card_details', {})
            cards_data = data.get('data', {}).get('cards', {})
            
            self._sync_cards(card_details, cards_data, language_code)
            
            print(f"✓ {language_code} 語言卡片資料同步完成")
            return True
            
        except Exception as e:
            print(f"✗ 同步 {language_code} 語言卡片資料失敗: {e}")
            return False
    
    def _sync_card_sets(self, card_sets: Dict[str, str], language_code: str):
        """同步卡組系列資料"""
        if not card_sets:
            return
        
        print(f"  同步卡組系列資料...")
        
        for set_id, set_name in card_sets.items():
            try:
                set_id_int = int(set_id)
                
                # 檢查是否已存在
                existing = self._get_table('card_sets').select('*').eq('id', set_id_int).execute()
                
                if existing.data:
                    # 更新多語言名稱
                    current_name = existing.data[0].get('name', {})
                    current_name[language_code] = set_name
                    
                    self._get_table('card_sets').update({
                        'name': current_name
                    }).eq('id', set_id_int).execute()
                else:
                    # 新增
                    self._get_table('card_sets').insert({
                        'id': set_id_int,
                        'name': {language_code: set_name}
                    }).execute()
                    
            except Exception as e:
                print(f"    ✗ 同步卡組系列 {set_id} 失敗: {e}")
    
    def _sync_tribes(self, tribes: Dict[str, str], language_code: str):
        """同步部族資料"""
        if not tribes:
            return
        
        print(f"  同步部族資料...")
        
        for tribe_id, tribe_name in tribes.items():
            try:
                tribe_id_int = int(tribe_id)
                
                # 檢查是否已存在
                existing = self._get_table('tribes').select('*').eq('id', tribe_id_int).execute()
                
                if existing.data:
                    # 更新多語言名稱
                    current_name = existing.data[0].get('name', {})
                    current_name[language_code] = tribe_name
                    
                    self._get_table('tribes').update({
                        'name': current_name
                    }).eq('id', tribe_id_int).execute()
                else:
                    # 新增
                    self._get_table('tribes').insert({
                        'id': tribe_id_int,
                        'name': {language_code: tribe_name}
                    }).execute()
                    
            except Exception as e:
                print(f"    ✗ 同步部族 {tribe_id} 失敗: {e}")
    
    def _sync_skills(self, skills: Dict[str, str], skill_replace_texts: Dict[str, str], language_code: str):
        """同步技能資料"""
        if not skills:
            return
        
        print(f"  同步技能資料...")
        
        for skill_id, skill_name in skills.items():
            try:
                skill_id_int = int(skill_id)
                
                # 檢查是否已存在
                existing = self._get_table('skills').select('*').eq('id', skill_id_int).execute()
                
                replace_text = skill_replace_texts.get(skill_id, "")
                
                if existing.data:
                    # 更新多語言名稱
                    current_name = existing.data[0].get('name', {})
                    current_name[language_code] = skill_name
                    
                    current_replace = existing.data[0].get('replace_text', {})
                    if replace_text:
                        current_replace[language_code] = replace_text
                    
                    self._get_table('skills').update({
                        'name': current_name,
                        'replace_text': current_replace
                    }).eq('id', skill_id_int).execute()
                else:
                    # 新增
                    replace_data = {language_code: replace_text} if replace_text else {}
                    self._get_table('skills').insert({
                        'id': skill_id_int,
                        'name': {language_code: skill_name},
                        'replace_text': replace_data
                    }).execute()
                    
            except Exception as e:
                print(f"    ✗ 同步技能 {skill_id} 失敗: {e}")
    
    def _sync_cards(self, card_details: Dict[str, Any], cards_data: Dict[str, Any], language_code: str):
        """同步卡片資料"""
        if not card_details:
            return
        
        print(f"  同步卡片資料... (共 {len(card_details)} 張)")
        
        processed = 0
        for card_id, card_info in card_details.items():
            try:
                card_id_int = int(card_id)
                common = card_info.get('common', {})
                evo = card_info.get('evo', {})
                
                if not common:
                    continue
                
                # 判斷是否為關聯卡牌
                card_set_id = common.get('card_set_id')
                is_related_only = card_set_id == 90000
                
                # 準備卡片基本資料
                card_data = {
                    'card_id': card_id_int,
                    'base_card_id': common.get('base_card_id', card_id_int),
                    'card_resource_id': common.get('card_resource_id'),
                    'name': {language_code: common.get('name', '')},
                    'name_ruby': {language_code: common.get('name_ruby', '')},
                    'atk': common.get('atk'),
                    'life': common.get('life'),
                    'cost': common.get('cost', 0),
                    'type': common.get('type', 1),
                    'class': common.get('class', 0),
                    'rarity': common.get('rarity', 1),
                    'card_set_id': card_set_id if not is_related_only else None,  # 關聯卡牌設為 NULL
                    'cv': {language_code: common.get('cv', '')},
                    'illustrator': common.get('illustrator', ''),
                    'is_token': common.get('is_token', False),
                    'is_include_rotation': common.get('is_include_rotation', True),
                    'related_only': is_related_only,  # 新增：標記是否僅作為關聯卡牌
                    'card_image_hash': common.get('card_image_hash', ''),
                    'card_banner_image_hash': common.get('card_banner_image_hash', ''),
                    'evo_card_resource_id': evo.get('card_resource_id') if evo else None,
                    'evo_card_image_hash': evo.get('card_image_hash', '') if evo else '',
                    'evo_card_banner_image_hash': evo.get('card_banner_image_hash', '') if evo else ''
                }
                
                # 檢查是否已存在
                existing = self._get_table('cards').select('*').eq('card_id', card_id_int).execute()
                
                if existing.data:
                    # 更新多語言字段
                    current_card = existing.data[0]
                    current_name = current_card.get('name', {})
                    current_name[language_code] = common.get('name', '')
                    
                    current_ruby = current_card.get('name_ruby', {})
                    current_ruby[language_code] = common.get('name_ruby', '')
                    
                    current_cv = current_card.get('cv', {})
                    current_cv[language_code] = common.get('cv', '')
                    
                    update_data = {
                        'name': current_name,
                        'name_ruby': current_ruby,
                        'cv': current_cv
                    }
                    
                    # 更新其他非語言相關字段（如果需要）
                    for field in ['atk', 'life', 'cost', 'type', 'class', 'rarity', 'card_set_id', 
                                'illustrator', 'is_token', 'is_include_rotation', 'card_image_hash',
                                'card_banner_image_hash', 'evo_card_resource_id', 'evo_card_image_hash', 
                                'evo_card_banner_image_hash']:
                        if card_data[field] is not None:
                            update_data[field] = card_data[field]
                    
                    self._get_table('cards').update(update_data).eq('card_id', card_id_int).execute()
                else:
                    # 新增
                    self._get_table('cards').insert(card_data).execute()
                
                # 同步卡片文字內容
                self._sync_card_texts(card_id_int, common, evo, language_code)
                
                # 同步部族關係
                if language_code == 'cht':  # 只在中文繁體時同步部族關係（避免重複）
                    self._sync_card_tribes(card_id_int, common.get('tribes', []))
                
                # 同步相關卡片
                if language_code == 'cht':  # 只在中文繁體時同步相關卡片
                    card_relations = cards_data.get(card_id, {})
                    self._sync_card_relations(card_id_int, card_relations)
                
                # 同步問答
                questions = common.get('questions', [])
                if questions:
                    self._sync_card_questions(card_id_int, questions, language_code)
                
                processed += 1
                if processed % 50 == 0:
                    print(f"    已處理 {processed}/{len(card_details)} 張卡片")
                    
            except Exception as e:
                print(f"    ✗ 同步卡片 {card_id} 失敗: {e}")
        
        print(f"    ✓ 完成處理 {processed} 張卡片")
    
    def _sync_card_texts(self, card_id: int, common: Dict, evo: Dict, language_code: str):
        """同步卡片文字內容"""
        text_data = {
            'card_id': card_id,
            'language': language_code,
            'skill_text': common.get('skill_text', ''),
            'flavour_text': common.get('flavour_text', ''),
            'evo_skill_text': evo.get('skill_text', '') if evo else '',
            'evo_flavour_text': evo.get('flavour_text', '') if evo else ''
        }
        
        # 檢查是否已存在
        existing = self._get_table('card_texts').select('*').eq('card_id', card_id).eq('language', language_code).execute()
        
        if existing.data:
            # 更新
            self._get_table('card_texts').update(text_data).eq('card_id', card_id).eq('language', language_code).execute()
        else:
            # 新增
            self._get_table('card_texts').insert(text_data).execute()
    
    def _sync_card_tribes(self, card_id: int, tribes: List[int]):
        """同步卡片部族關係"""
        if not tribes:
            return
        
        # 刪除舊的關係
        self._get_table('card_tribes').delete().eq('card_id', card_id).execute()
        
        # 新增關係
        for tribe_id in tribes:
            if tribe_id > 0:  # 跳過 0 (無部族)
                try:
                    self._get_table('card_tribes').insert({
                        'card_id': card_id,
                        'tribe_id': tribe_id
                    }).execute()
                except Exception as e:
                    # 可能是外鍵約束錯誤，忽略不存在的部族 ID
                    print(f"    警告: 部族 ID {tribe_id} 不存在，跳過")
    
    def _sync_card_relations(self, card_id: int, relations: Dict):
        """同步卡片關係"""
        # 刪除舊的關係
        self._get_table('card_relations').delete().eq('card_id', card_id).execute()
        
        # 新增相關卡片
        related_cards = relations.get('related_card_ids', [])
        for related_id in related_cards:
            try:
                self._get_table('card_relations').insert({
                    'card_id': card_id,
                    'related_card_id': related_id,
                    'relation_type': 'related'
                }).execute()
            except Exception as e:
                # 忽略關係錯誤
                pass
        
        # 新增特效卡片
        specific_effect_cards = relations.get('specific_effect_card_ids', [])
        for effect_id in specific_effect_cards:
            try:
                self._get_table('card_relations').insert({
                    'card_id': card_id,
                    'related_card_id': effect_id,
                    'relation_type': 'specific_effect'
                }).execute()
            except Exception as e:
                # 忽略關係錯誤
                pass
    
    def _sync_card_questions(self, card_id: int, questions: List[Dict], language_code: str):
        """同步卡片問答"""
        # 刪除舊的問答（該語言）
        self._get_table('card_questions').delete().eq('card_id', card_id).eq('language', language_code).execute()
        
        # 新增問答
        for qa in questions:
            self._get_table('card_questions').insert({
                'card_id': card_id,
                'language': language_code,
                'question': qa.get('question', ''),
                'answer': qa.get('answer', '')
            }).execute()
    
    def sync_tips_data(self, language_code: str):
        """同步提示資料"""
        tips_file_path = Path(f"output/tips_data/tips_data_{language_code}.json")
        
        if not tips_file_path.exists():
            print(f"提示資料文件不存在: {tips_file_path}")
            return False
        
        try:
            with open(tips_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n開始同步 {language_code} 語言提示資料...")
            
            tips = data.get('tips', [])
            if not tips:
                print(f"  無提示資料")
                return True
            
            # 刪除舊的提示資料（該語言）
            self._get_table('tips').delete().eq('language', language_code).execute()
            
            # 新增提示資料
            for i, tip in enumerate(tips):
                self._get_table('tips').insert({
                    'language': language_code,
                    'title': tip.get('title', ''),
                    'description': tip.get('desc', ''),
                    'sort_order': i + 1
                }).execute()
            
            print(f"✓ {language_code} 語言提示資料同步完成 (共 {len(tips)} 條)")
            return True
            
        except Exception as e:
            print(f"✗ 同步 {language_code} 語言提示資料失敗: {e}")
            return False
    
    def sync_all_languages(self, languages: List[str] = None):
        """同步所有語言的資料"""
        if languages is None:
            languages = ['cht', 'chs', 'en', 'ja', 'ko']
        
        print("=== 開始同步 Shadowverse 資料到 Supabase ===")
        
        success_count = 0
        total_count = len(languages) * 2  # 卡片 + 提示
        
        for lang in languages:
            print(f"\n--- 處理 {lang.upper()} 語言 ---")
            
            # 同步卡片資料
            if self.sync_card_data(lang):
                success_count += 1
            
            # 同步提示資料
            if self.sync_tips_data(lang):
                success_count += 1
        
        print(f"\n=== 同步完成 ===")
        print(f"成功: {success_count}/{total_count}")
        
        if success_count == total_count:
            print("✓ 所有資料同步成功")
            return True
        else:
            print(f"✗ {total_count - success_count} 項同步失敗")
            return False
    
    def validate_data_integrity(self):
        """驗證資料完整性"""
        print("\n=== 驗證資料完整性 ===")
        
        try:
            # 檢查卡片數量
            cards_result = self._get_table('cards').select('card_id').execute()
            cards_count = len(cards_result.data) if cards_result.data else 0
            print(f"卡片總數: {cards_count}")
            
            # 檢查各語言的文字內容
            languages = ['cht', 'chs', 'en', 'ja', 'ko']
            for lang in languages:
                texts_result = self._get_table('card_texts').select('id').eq('language', lang).execute()
                tips_result = self._get_table('tips').select('id').eq('language', lang).execute()
                
                texts_count = len(texts_result.data) if texts_result.data else 0
                tips_count = len(tips_result.data) if tips_result.data else 0
                
                print(f"{lang.upper()} - 卡片文字: {texts_count}, 提示: {tips_count}")
            
            # 檢查關係資料
            tribes_result = self._get_table('card_tribes').select('id').execute()
            relations_result = self._get_table('card_relations').select('id').execute()
            questions_result = self._get_table('card_questions').select('id').execute()
            
            tribes_count = len(tribes_result.data) if tribes_result.data else 0
            relations_count = len(relations_result.data) if relations_result.data else 0
            questions_count = len(questions_result.data) if questions_result.data else 0
            
            print(f"部族關係: {tribes_count}")
            print(f"卡片關係: {relations_count}")
            print(f"問答: {questions_count}")
            
            print("✓ 資料完整性檢查完成")
            return True
            
        except Exception as e:
            print(f"✗ 資料完整性檢查失敗: {e}")
            return False
    
    def clean_database(self):
        """清理資料庫（警告：會刪除所有資料）"""
        print("\n=== 清理資料庫 ===")
        
        confirm = input("⚠️  這將刪除所有同步的資料，確定要繼續嗎？(yes/no): ")
        if confirm.lower() != 'yes':
            print("操作已取消")
            return False
        
        try:
            # 刪除順序很重要，先刪除有外鍵約束的表
            tables_to_clean = [
                'card_questions',
                'card_relations', 
                'card_tribes',
                'card_texts',
                'cards',
                'tips'
            ]
            
            for table in tables_to_clean:
                # 使用 neq 來刪除所有記錄，因為 id 欄位可能不存在於所有表中
                try:
                    result = self._get_table(table).delete().gte('created_at', '1970-01-01').execute()
                    print(f"✓ 已清理 {table}")
                except Exception as e:
                    print(f"✗ 清理 {table} 失敗: {e}")
            
            print("✓ 資料庫清理完成")
            return True
            
        except Exception as e:
            print(f"✗ 資料庫清理失敗: {e}")
            return False
    
    def test_connection(self):
        """測試 Supabase 連線和 schema 存取"""
        print("\n=== 測試連線和 schema 存取 ===")
        
        try:
            # 測試 schema 存取
            result = self._get_table('card_sets').select('id').limit(1).execute()
            print(f"✓ 成功存取 {self.schema_name}.card_sets")
            
            # 測試其他主要表
            test_tables = ['tribes', 'skills', 'cards', 'card_texts', 'tips']
            for table in test_tables:
                try:
                    result = self._get_table(table).select('*').limit(1).execute()
                    print(f"✓ 成功存取 {self.schema_name}.{table}")
                except Exception as e:
                    print(f"✗ 無法存取 {self.schema_name}.{table}: {e}")
            
            return True
            
        except Exception as e:
            print(f"✗ 連線測試失敗: {e}")
            print("\n可能的解決方案:")
            print("1. 確認 schema 'svwb_data' 已正確創建")
            print("2. 確認使用的是 service_role key 而非 anon key")
            print("3. 確認 RLS 政策已正確設置")
            return False


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='同步 Shadowverse 資料到 Supabase')
    parser.add_argument('--languages', '-l', nargs='+', default=['cht', 'chs', 'en', 'ja', 'ko'],
                       help='要同步的語言代碼 (預設: cht chs en ja ko)')
    parser.add_argument('--cards-only', action='store_true', help='只同步卡片資料')
    parser.add_argument('--tips-only', action='store_true', help='只同步提示資料')
    parser.add_argument('--validate', action='store_true', help='驗證資料完整性')
    parser.add_argument('--clean', action='store_true', help='清理資料庫（危險操作）')
    parser.add_argument('--test', action='store_true', help='測試連線和 schema 存取')
    
    args = parser.parse_args()
    
    # 創建同步器實例
    sync = ShadowverseDataSync()
    
    try:
        if args.test:
            # 測試連線
            sync.test_connection()
        elif args.clean:
            # 清理資料庫
            sync.clean_database()
        elif args.validate:
            # 驗證資料完整性
            sync.validate_data_integrity()
        elif args.cards_only:
            # 只同步卡片資料
            success_count = 0
            for lang in args.languages:
                if sync.sync_card_data(lang):
                    success_count += 1
            print(f"\n卡片資料同步完成: {success_count}/{len(args.languages)} 成功")
        elif args.tips_only:
            # 只同步提示資料
            success_count = 0
            for lang in args.languages:
                if sync.sync_tips_data(lang):
                    success_count += 1
            print(f"\n提示資料同步完成: {success_count}/{len(args.languages)} 成功")
        else:
            # 同步所有資料
            success = sync.sync_all_languages(args.languages)
            
            # 可選：同步完成後驗證資料
            if success:
                print("\n自動驗證資料完整性...")
                sync.validate_data_integrity()
    
    except KeyboardInterrupt:
        print("\n\n操作被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 程式執行失敗: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()