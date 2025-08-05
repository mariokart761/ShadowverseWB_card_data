#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowverse 卡牌資料庫同步腳本
將爬取的 JSON 資料同步到 Supabase 資料庫
"""

import json
import os
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio

try:
    from supabase import create_client, Client
    import asyncpg
except ImportError:
    print("請先安裝必要套件: pip install supabase asyncpg")
    exit(1)

# 設定日誌
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/supabase_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """資料庫配置"""
    supabase_url: str
    supabase_key: str
    database_url: str  # PostgreSQL 連線字串 (用於直接 SQL 操作)

class ShadowverseDatabaseSync:
    """Shadowverse 資料庫同步器"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.supabase: Client = create_client(config.supabase_url, config.supabase_key)
        self.stats = {
            'total_cards': 0,
            'successful_cards': 0,
            'failed_cards': 0,
            'errors': []
        }
    
    async def sync_language_data(self, language: str, json_file_path: str) -> bool:
        """同步單一語言的資料"""
        logger.info(f"開始同步 {language} 語言資料...")
        
        # 記錄同步開始
        sync_log_id = await self._create_sync_log(language)
        
        try:
            # 讀取 JSON 資料
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            card_data = data.get('data', {})
            
            # 同步基礎資料 (卡包、種族、技能)
            await self._sync_reference_data(card_data, language)
            
            # 同步卡片資料
            await self._sync_cards_data(card_data, language)
            
            # 更新同步記錄
            await self._update_sync_log(sync_log_id, 'success')
            
            logger.info(f"{language} 語言資料同步完成")
            return True
            
        except Exception as e:
            logger.error(f"同步 {language} 語言資料時發生錯誤: {e}")
            await self._update_sync_log(sync_log_id, 'failed', str(e))
            return False
    
    async def _create_sync_log(self, language: str) -> int:
        """建立同步記錄"""
        try:
            result = self.supabase.table('data_sync_logs').insert({
                'language': language,
                'sync_status': 'running',
                'started_at': datetime.now().isoformat()
            }).execute()
            
            return result.data[0]['id']
        except Exception as e:
            logger.error(f"建立同步記錄失敗: {e}")
            return 0
    
    async def _update_sync_log(self, log_id: int, status: str, error_message: str = None):
        """更新同步記錄"""
        try:
            update_data = {
                'sync_status': status,
                'total_cards': self.stats['total_cards'],
                'successful_cards': self.stats['successful_cards'],
                'failed_cards': self.stats['failed_cards'],
                'completed_at': datetime.now().isoformat()
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            self.supabase.table('data_sync_logs').update(update_data).eq('id', log_id).execute()
            
        except Exception as e:
            logger.error(f"更新同步記錄失敗: {e}")
    
    async def _sync_reference_data(self, card_data: Dict, language: str):
        """同步參考資料 (卡包、種族、技能)"""
        logger.info(f"同步 {language} 參考資料...")
        
        # 同步卡包資料
        if 'card_set_names' in card_data:
            await self._sync_card_sets(card_data['card_set_names'], language)
        
        # 同步種族資料
        if 'tribe_names' in card_data:
            await self._sync_tribes(card_data['tribe_names'], language)
        
        # 同步技能資料
        if 'skill_names' in card_data:
            await self._sync_skills(card_data['skill_names'], language)

    async def _sync_tips_data(self, tips_data: List[Dict], language: str):
        """同步Tips資料"""
        logger.info(f"同步 {language} Tips資料...")
        
        try:
            for tip in tips_data:
                title = tip.get('title', '').strip()
                desc = tip.get('desc', '').strip()
                
                if not title or not desc:
                    continue
                
                # 檢查是否已存在相同標題的tip
                existing_tip = await self.conn.fetchrow(
                    f"SELECT id FROM tips WHERE title_{language} = $1",
                    title
                )
                
                if existing_tip:
                    # 更新現有tip
                    await self.conn.execute(f"""
                        UPDATE tips 
                        SET title_{language} = $1, desc_{language} = $2, updated_at = NOW()
                        WHERE id = $3
                    """, title, desc, existing_tip['id'])
                    self.stats['updated'] += 1
                else:
                    # 檢查是否有其他語言的相同標題（用於合併多語言）
                    similar_tip = await self.conn.fetchrow("""
                        SELECT id FROM tips 
                        WHERE title_cht = $1 OR title_chs = $1 OR title_en = $1 OR title_ja = $1 OR title_ko = $1
                    """, title)
                    
                    if similar_tip:
                        # 更新現有記錄的該語言欄位
                        await self.conn.execute(f"""
                            UPDATE tips 
                            SET title_{language} = $1, desc_{language} = $2, updated_at = NOW()
                            WHERE id = $3
                        """, title, desc, similar_tip['id'])
                        self.stats['updated'] += 1
                    else:
                        # 建立新tip記錄
                        await self.conn.execute(f"""
                            INSERT INTO tips (title_{language}, desc_{language})
                            VALUES ($1, $2)
                        """, title, desc)
                        self.stats['inserted'] += 1
                        
        except Exception as e:
            self.stats['errors'].append(f"同步Tips資料失敗: {str(e)}")
            logger.error(f"同步Tips資料失敗: {e}")
    
    async def _sync_card_sets(self, card_sets: Dict[str, str], language: str):
        """同步卡包資料"""
        for set_id, set_name in card_sets.items():
            try:
                # 檢查是否已存在
                existing = self.supabase.table('card_sets').select('id').eq('id', int(set_id)).execute()
                
                if existing.data:
                    # 更新現有記錄
                    self.supabase.table('card_sets').update({
                        f'name_{language}': set_name
                    }).eq('id', int(set_id)).execute()
                else:
                    # 建立新記錄
                    self.supabase.table('card_sets').insert({
                        'id': int(set_id),
                        f'name_{language}': set_name
                    }).execute()
                    
            except Exception as e:
                logger.error(f"同步卡包 {set_id} 失敗: {e}")
    
    async def _sync_tribes(self, tribes: Dict[str, str], language: str):
        """同步種族資料"""
        for tribe_id, tribe_name in tribes.items():
            try:
                existing = self.supabase.table('tribes').select('id').eq('id', int(tribe_id)).execute()
                
                if existing.data:
                    self.supabase.table('tribes').update({
                        f'name_{language}': tribe_name
                    }).eq('id', int(tribe_id)).execute()
                else:
                    self.supabase.table('tribes').insert({
                        'id': int(tribe_id),
                        f'name_{language}': tribe_name
                    }).execute()
                    
            except Exception as e:
                logger.error(f"同步種族 {tribe_id} 失敗: {e}")
    
    async def _sync_skills(self, skills: Dict[str, str], language: str):
        """同步技能資料"""
        for skill_id, skill_name in skills.items():
            try:
                existing = self.supabase.table('skills').select('id').eq('id', int(skill_id)).execute()
                
                if existing.data:
                    self.supabase.table('skills').update({
                        f'name_{language}': skill_name
                    }).eq('id', int(skill_id)).execute()
                else:
                    self.supabase.table('skills').insert({
                        'id': int(skill_id),
                        f'name_{language}': skill_name
                    }).execute()
                    
            except Exception as e:
                logger.error(f"同步技能 {skill_id} 失敗: {e}")
    
    async def _sync_cards_data(self, card_data: Dict, language: str):
        """同步卡片資料"""
        if 'card_details' not in card_data:
            logger.warning(f"{language} 資料中沒有 card_details")
            return
        
        card_details = card_data['card_details']
        self.stats['total_cards'] = len(card_details)
        
        logger.info(f"開始同步 {self.stats['total_cards']} 張卡片...")
        
        # 批次處理卡片
        batch_size = 50
        card_ids = list(card_details.keys())
        
        for i in range(0, len(card_ids), batch_size):
            batch_ids = card_ids[i:i + batch_size]
            await self._sync_card_batch(batch_ids, card_details, language)
            
            # 顯示進度
            progress = min(i + batch_size, len(card_ids))
            logger.info(f"已處理 {progress}/{len(card_ids)} 張卡片")
            
            # 稍作休息避免過度請求
            await asyncio.sleep(0.1)
    
    async def _sync_card_batch(self, card_ids: List[str], card_details: Dict, language: str):
        """同步一批卡片"""
        for card_id in card_ids:
            try:
                await self._sync_single_card(card_id, card_details[card_id], language)
                self.stats['successful_cards'] += 1
            except Exception as e:
                logger.error(f"同步卡片 {card_id} 失敗: {e}")
                self.stats['failed_cards'] += 1
                self.stats['errors'].append(f"Card {card_id}: {str(e)}")
    
    async def _sync_single_card(self, card_id: str, card_info: Dict, language: str):
        """同步單張卡片"""
        common = card_info.get('common', {})
        evo = card_info.get('evo', {})
        
        # 1. 同步卡片主要資訊
        await self._upsert_card_main_info(card_id, common)
        
        # 2. 同步卡片名稱
        await self._upsert_card_name(card_id, common, language)
        
        # 3. 同步卡片描述 (普通形態)
        await self._upsert_card_description(card_id, common, language, 'common')
        
        # 4. 同步卡片描述 (進化形態)
        if evo:
            await self._upsert_card_evolution(card_id, evo)
            await self._upsert_card_description(card_id, evo, language, 'evo')
        
        # 5. 同步種族關聯
        if 'tribes' in common:
            await self._sync_card_tribes(card_id, common['tribes'])
        
        # 6. 同步問答
        if 'questions' in common:
            await self._sync_card_questions(card_id, common['questions'], language)
        
        # 7. 同步風格變體
        if 'style_card_list' in card_info:
            await self._sync_card_styles(card_id, card_info['style_card_list'])
    
    async def _upsert_card_main_info(self, card_id: str, common: Dict):
        """更新或插入卡片主要資訊"""
        card_data = {
            'id': int(card_id),
            'base_card_id': common.get('base_card_id'),
            'card_resource_id': common.get('card_resource_id'),
            'card_set_id': common.get('card_set_id'),
            'type': common.get('type'),
            'class': common.get('class'),
            'cost': common.get('cost'),
            'atk': common.get('atk'),
            'life': common.get('life'),
            'rarity': common.get('rarity'),
            'is_token': common.get('is_token', False),
            'is_include_rotation': common.get('is_include_rotation', False),
            'card_image_hash': common.get('card_image_hash'),
            'card_banner_image_hash': common.get('card_banner_image_hash')
        }
        
        # 移除 None 值
        card_data = {k: v for k, v in card_data.items() if v is not None}
        
        try:
            # 檢查是否已存在
            existing = self.supabase.table('cards').select('id').eq('id', int(card_id)).execute()
            
            if existing.data:
                # 更新現有記錄
                self.supabase.table('cards').update(card_data).eq('id', int(card_id)).execute()
            else:
                # 建立新記錄
                self.supabase.table('cards').insert(card_data).execute()
                
        except Exception as e:
            raise Exception(f"同步卡片主要資訊失敗: {e}")
    
    async def _upsert_card_name(self, card_id: str, common: Dict, language: str):
        """更新或插入卡片名稱"""
        name_data = {
            'card_id': int(card_id),
            'language': language,
            'name': common.get('name', ''),
            'name_ruby': common.get('name_ruby', '')
        }
        
        try:
            # 使用 upsert (PostgreSQL 的 ON CONFLICT)
            self.supabase.table('card_names').upsert(name_data).execute()
        except Exception as e:
            raise Exception(f"同步卡片名稱失敗: {e}")
    
    async def _upsert_card_description(self, card_id: str, card_info: Dict, language: str, form: str):
        """更新或插入卡片描述"""
        desc_data = {
            'card_id': int(card_id),
            'language': language,
            'form': form,
            'flavour_text': card_info.get('flavour_text', ''),
            'skill_text': card_info.get('skill_text', ''),
            'cv': card_info.get('cv', ''),
            'illustrator': card_info.get('illustrator', '')
        }
        
        try:
            self.supabase.table('card_descriptions').upsert(desc_data).execute()
        except Exception as e:
            raise Exception(f"同步卡片描述失敗: {e}")
    
    async def _upsert_card_evolution(self, card_id: str, evo: Dict):
        """更新或插入卡片進化資訊"""
        evo_data = {
            'card_id': int(card_id),
            'card_resource_id': evo.get('card_resource_id'),
            'card_image_hash': evo.get('card_image_hash'),
            'card_banner_image_hash': evo.get('card_banner_image_hash')
        }
        
        # 移除 None 值
        evo_data = {k: v for k, v in evo_data.items() if v is not None}
        
        try:
            self.supabase.table('card_evolutions').upsert(evo_data).execute()
        except Exception as e:
            raise Exception(f"同步卡片進化資訊失敗: {e}")
    
    async def _sync_card_tribes(self, card_id: str, tribes: List[int]):
        """同步卡片種族關聯"""
        try:
            # 先刪除現有關聯
            self.supabase.table('card_tribes').delete().eq('card_id', int(card_id)).execute()
            
            # 插入新關聯
            for tribe_id in tribes:
                if tribe_id != 0:  # 0 通常表示無種族
                    self.supabase.table('card_tribes').insert({
                        'card_id': int(card_id),
                        'tribe_id': tribe_id
                    }).execute()
                    
        except Exception as e:
            raise Exception(f"同步卡片種族關聯失敗: {e}")
    
    async def _sync_card_questions(self, card_id: str, questions: List[Dict], language: str):
        """同步卡片問答"""
        try:
            # 先刪除該語言的現有問答
            self.supabase.table('card_questions').delete().eq('card_id', int(card_id)).eq('language', language).execute()
            
            # 插入新問答
            for q in questions:
                self.supabase.table('card_questions').insert({
                    'card_id': int(card_id),
                    'language': language,
                    'question': q.get('question', ''),
                    'answer': q.get('answer', '')
                }).execute()
                
        except Exception as e:
            raise Exception(f"同步卡片問答失敗: {e}")
    
    async def _sync_card_styles(self, card_id: str, styles: List[Dict]):
        """同步卡片風格變體"""
        try:
            # 先刪除現有風格
            self.supabase.table('card_styles').delete().eq('card_id', int(card_id)).execute()
            
            # 插入新風格
            for style in styles:
                self.supabase.table('card_styles').insert({
                    'card_id': int(card_id),
                    'hash': style.get('hash', ''),
                    'evo_hash': style.get('evo_hash', ''),
                    'name': style.get('name', ''),
                    'name_ruby': style.get('name_ruby', ''),
                    'cv': style.get('cv', ''),
                    'illustrator': style.get('illustrator', ''),
                    'skill_text': style.get('skill_text', ''),
                    'flavour_text': style.get('flavour_text', ''),
                    'evo_flavour_text': style.get('evo_flavour_text', '')
                }).execute()
                
        except Exception as e:
            raise Exception(f"同步卡片風格變體失敗: {e}")
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """獲取同步統計資訊"""
        return {
            'total_cards': self.stats['total_cards'],
            'successful_cards': self.stats['successful_cards'],
            'failed_cards': self.stats['failed_cards'],
            'success_rate': (self.stats['successful_cards'] / max(self.stats['total_cards'], 1)) * 100,
            'errors': self.stats['errors'][:10]  # 只顯示前 10 個錯誤
        }

async def sync_tips_data(config: DatabaseConfig, data_directory: str = 'output/tips_data'):
    """同步所有語言的Tips資料"""
    languages = ['cht', 'chs', 'en', 'ja', 'ko']
    sync_results = {}
    
    logger.info("開始同步所有語言的Tips資料到資料庫...")
    
    for language in languages:
        tips_file = os.path.join(data_directory, f'tips_data_{language}.json')
        
        if not os.path.exists(tips_file):
            logger.warning(f"找不到 {language} 語言的Tips檔案: {tips_file}")
            sync_results[language] = {'success': False, 'error': 'File not found'}
            continue
        
        try:
            with open(tips_file, 'r', encoding='utf-8') as f:
                tips_data = json.load(f)
            
            sync = ShadowverseDatabaseSync(config)
            await sync._connect_database()
            
            # 同步Tips資料
            await sync._sync_tips_data(tips_data.get('tips', []), language)
            
            await sync._disconnect_database()
            
            sync_results[language] = {
                'success': True,
                'statistics': sync.get_sync_statistics()
            }
            
            logger.info(f"{language} Tips同步結果: 成功")
            
        except Exception as e:
            logger.error(f"{language} Tips同步失敗: {e}")
            sync_results[language] = {'success': False, 'error': str(e)}
        
        # 語言間稍作休息
        await asyncio.sleep(1)
    
    return sync_results

async def sync_all_languages(config: DatabaseConfig, data_directory: str = 'output'):
    """同步所有語言的資料"""
    languages = ['cht', 'chs', 'en', 'ja', 'ko']
    sync_results = {}
    
    logger.info("開始同步所有語言的卡牌資料到資料庫...")
    
    for language in languages:
        json_file = os.path.join(data_directory, f'shadowverse_cards_{language}.json')
        
        if not os.path.exists(json_file):
            logger.warning(f"找不到 {language} 語言的資料檔案: {json_file}")
            sync_results[language] = {'success': False, 'error': 'File not found'}
            continue
        
        sync = ShadowverseDatabaseSync(config)
        success = await sync.sync_language_data(language, json_file)
        
        sync_results[language] = {
            'success': success,
            'statistics': sync.get_sync_statistics()
        }
        
        logger.info(f"{language} 同步結果: {'成功' if success else '失敗'}")
        
        # 語言間稍作休息
        await asyncio.sleep(1)
    
    return sync_results

def load_config() -> DatabaseConfig:
    """載入資料庫配置"""
    config_file = 'supabase/config.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return DatabaseConfig(
            supabase_url=config_data['supabase_url'],
            supabase_key=config_data['supabase_key'],
            database_url=config_data['database_url']
        )
    else:
        # 從環境變數載入
        return DatabaseConfig(
            supabase_url=os.getenv('SUPABASE_URL', ''),
            supabase_key=os.getenv('SUPABASE_KEY', ''),
            database_url=os.getenv('DATABASE_URL', '')
        )

async def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Shadowverse 資料庫同步工具')
    parser.add_argument('--type', choices=['cards', 'tips', 'all'], default='all', 
                       help='同步類型: cards=卡牌資料, tips=Tips資料, all=全部')
    args = parser.parse_args()
    
    try:
        # 載入配置
        config = load_config()
        
        if not config.supabase_url or not config.supabase_key:
            logger.error("請設定 Supabase 連線資訊")
            logger.info("可以建立 supabase/config.json 檔案或設定環境變數")
            return
        
        # 根據參數決定同步類型
        if args.type in ['cards', 'all']:
            # 同步卡牌資料
            logger.info("開始同步卡牌資料...")
            results = await sync_all_languages(config)
            
            # 顯示卡牌同步結果摘要
            print("\n" + "="*60)
            print("卡牌資料同步結果摘要")
            print("="*60)
            
            for language, result in results.items():
                status = "✅ 成功" if result['success'] else "❌ 失敗"
                print(f"{language}: {status}")
                
                if result['success'] and 'statistics' in result:
                    stats = result['statistics']
                    print(f"  - 插入: {stats.get('inserted', 0)}")
                    print(f"  - 更新: {stats.get('updated', 0)}")
                    print(f"  - 成功率: {stats.get('success_rate', 0):.1f}%")
                elif not result['success']:
                    print(f"  - 錯誤: {result.get('error', '未知錯誤')}")
        
        if args.type in ['tips', 'all']:
            # 同步Tips資料
            logger.info("開始同步Tips資料...")
            tips_results = await sync_tips_data(config)
            
            # 顯示Tips同步結果摘要
            print("\n" + "="*60)
            print("Tips資料同步結果摘要")
            print("="*60)
            
            for language, result in tips_results.items():
                status = "✅ 成功" if result['success'] else "❌ 失敗"
                print(f"{language}: {status}")
                
                if result['success'] and 'statistics' in result:
                    stats = result['statistics']
                    print(f"  - 插入: {stats.get('inserted', 0)}")
                    print(f"  - 更新: {stats.get('updated', 0)}")
                elif not result['success']:
                    print(f"  - 錯誤: {result.get('error', '未知錯誤')}")
        
        # 顯示結果摘要
        print("\n" + "="*60)
        print("資料庫同步完成摘要")
        print("="*60)
        
        for language, result in results.items():
            status = "✓ 成功" if result['success'] else "✗ 失敗"
            print(f"{language.upper()}: {status}")
            
            if result['success'] and 'statistics' in result:
                stats = result['statistics']
                print(f"  總卡片數: {stats['total_cards']}")
                print(f"  成功: {stats['successful_cards']}")
                print(f"  失敗: {stats['failed_cards']}")
                print(f"  成功率: {stats['success_rate']:.1f}%")
            
            print()
        
        logger.info("所有語言資料同步完成")
        
    except KeyboardInterrupt:
        logger.info("使用者中斷同步程序")
    except Exception as e:
        logger.error(f"同步過程中發生錯誤: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())