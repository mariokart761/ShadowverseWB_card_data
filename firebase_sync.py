#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firebase Firestore 資料同步腳本
將爬取的 JSON 資料同步到 Firebase Firestore 資料庫
"""

import json
import os
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import concurrent.futures
from threading import Lock

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from google.cloud.firestore_v1.batch import WriteBatch
except ImportError:
    print("請先安裝 Firebase Admin SDK: pip install firebase-admin")
    exit(1)

# 設定日誌
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/firebase_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FirebaseConfig:
    """Firebase 配置"""
    project_id: str
    service_account_key_path: str

class ShadowverseFirebaseSync:
    """Shadowverse Firebase 同步器"""
    
    def __init__(self, config: FirebaseConfig):
        self.config = config
        self.app = None
        self.db = None
        self.stats = {
            'total_cards': 0,
            'successful_cards': 0,
            'failed_cards': 0,
            'inserted': 0,
            'updated': 0,
            'errors': []
        }
        self.stats_lock = Lock()
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """初始化 Firebase"""
        try:
            # 檢查是否已經初始化
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.config.service_account_key_path)
                self.app = firebase_admin.initialize_app(cred, {
                    'projectId': self.config.project_id
                })
            else:
                self.app = firebase_admin.get_app()
            
            self.db = firestore.client()
            logger.info("✓ Firebase 初始化成功")
            
        except Exception as e:
            logger.error(f"✗ Firebase 初始化失敗: {e}")
            raise
    
    def sync_language_data(self, language: str, json_file_path: str) -> bool:
        """同步單一語言的資料"""
        logger.info(f"開始同步 {language} 語言資料...")
        
        # 記錄同步開始
        sync_log_ref = self._create_sync_log(language)
        
        try:
            # 讀取 JSON 資料
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            card_data = data.get('data', {})
            
            # 同步基礎資料 (卡包、種族、技能)
            self._sync_reference_data(card_data, language)
            
            # 同步卡片資料
            self._sync_cards_data(card_data, language)
            
            # 更新同步記錄
            self._update_sync_log(sync_log_ref, 'success')
            
            logger.info(f"{language} 語言資料同步完成")
            return True
            
        except Exception as e:
            logger.error(f"同步 {language} 語言資料時發生錯誤: {e}")
            self._update_sync_log(sync_log_ref, 'failed', str(e))
            return False
    
    def _create_sync_log(self, language: str) -> firestore.DocumentReference:
        """建立同步記錄"""
        try:
            sync_log_ref = self.db.collection('syncLogs').document()
            sync_log_ref.set({
                'language': language,
                'syncStatus': 'running',
                'startedAt': firestore.SERVER_TIMESTAMP,
                'createdAt': firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"建立同步記錄: {sync_log_ref.id}")
            return sync_log_ref
            
        except Exception as e:
            logger.error(f"建立同步記錄失敗: {e}")
            return None
    
    def _update_sync_log(self, sync_log_ref: firestore.DocumentReference, 
                        status: str, error_message: str = None):
        """更新同步記錄"""
        if not sync_log_ref:
            return
        
        try:
            update_data = {
                'syncStatus': status,
                'totalCards': self.stats['total_cards'],
                'successfulCards': self.stats['successful_cards'],
                'failedCards': self.stats['failed_cards'],
                'completedAt': firestore.SERVER_TIMESTAMP
            }
            
            if error_message:
                update_data['errorMessage'] = error_message
            
            sync_log_ref.update(update_data)
            
        except Exception as e:
            logger.error(f"更新同步記錄失敗: {e}")
    
    def _sync_reference_data(self, card_data: Dict, language: str):
        """同步參考資料 (卡包、種族、技能)"""
        logger.info(f"同步 {language} 參考資料...")
        
        # 同步卡包資料
        if 'card_set_names' in card_data:
            self._sync_card_sets(card_data['card_set_names'], language)
        
        # 同步種族資料
        if 'tribe_names' in card_data:
            self._sync_tribes(card_data['tribe_names'], language)
        
        # 同步技能資料
        if 'skill_names' in card_data:
            self._sync_skills(card_data['skill_names'], language)
    
    def _sync_card_sets(self, card_sets: Dict[str, str], language: str):
        """同步卡包資料"""
        batch = self.db.batch()
        batch_count = 0
        
        for set_id, set_name in card_sets.items():
            try:
                set_ref = self.db.collection('cardSets').document(str(set_id))
                
                # 使用 merge=True 來更新或建立文件
                batch.set(set_ref, {
                    'id': int(set_id),
                    f'names.{language}': set_name,
                    'updatedAt': firestore.SERVER_TIMESTAMP
                }, merge=True)
                
                batch_count += 1
                
                # 每 500 個操作提交一次批次
                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0
                    
            except Exception as e:
                logger.error(f"同步卡包 {set_id} 失敗: {e}")
        
        # 提交剩餘的批次操作
        if batch_count > 0:
            batch.commit()
        
        logger.info(f"同步了 {len(card_sets)} 個卡包")
    
    def _sync_tribes(self, tribes: Dict[str, str], language: str):
        """同步種族資料"""
        batch = self.db.batch()
        batch_count = 0
        
        for tribe_id, tribe_name in tribes.items():
            try:
                tribe_ref = self.db.collection('tribes').document(str(tribe_id))
                
                batch.set(tribe_ref, {
                    'id': int(tribe_id),
                    f'names.{language}': tribe_name,
                    'updatedAt': firestore.SERVER_TIMESTAMP
                }, merge=True)
                
                batch_count += 1
                
                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0
                    
            except Exception as e:
                logger.error(f"同步種族 {tribe_id} 失敗: {e}")
        
        if batch_count > 0:
            batch.commit()
        
        logger.info(f"同步了 {len(tribes)} 個種族")
    
    def _sync_skills(self, skills: Dict[str, str], language: str):
        """同步技能資料"""
        batch = self.db.batch()
        batch_count = 0
        
        for skill_id, skill_name in skills.items():
            try:
                skill_ref = self.db.collection('skills').document(str(skill_id))
                
                batch.set(skill_ref, {
                    'id': int(skill_id),
                    f'names.{language}': skill_name,
                    'updatedAt': firestore.SERVER_TIMESTAMP
                }, merge=True)
                
                batch_count += 1
                
                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0
                    
            except Exception as e:
                logger.error(f"同步技能 {skill_id} 失敗: {e}")
        
        if batch_count > 0:
            batch.commit()
        
        logger.info(f"同步了 {len(skills)} 個技能")

    def _generate_tip_doc_id(self, title: str, language: str, index: int) -> str:
        """生成改進的 tip 文檔ID"""
        import re
        
        # 1. 清理標題，只保留字母、數字、中文字符和基本標點
        cleaned_title = re.sub(r'[^\w\u4e00-\u9fff\s\-_]', '', title)
        
        # 2. 將多個空格替換為單個下劃線
        cleaned_title = re.sub(r'\s+', '_', cleaned_title.strip())
        
        # 3. 移除連續的下劃線
        cleaned_title = re.sub(r'_+', '_', cleaned_title)
        
        # 4. 限制長度，避免過長的文檔ID
        max_title_length = 30
        if len(cleaned_title) > max_title_length:
            # 保持中文字符的完整性
            truncated = cleaned_title[:max_title_length]
            # 如果截斷位置是中文字符的中間，向前調整
            while len(truncated) > 0 and ord(truncated[-1]) > 127:
                if len(truncated) < max_title_length:
                    break
                truncated = truncated[:-1]
            cleaned_title = truncated
        
        # 5. 生成最終的文檔ID: 序號_標題_語言
        # 使用3位數字前綴確保排序
        doc_id = f"{index:03d}_{cleaned_title}_{language}"
        
        # 6. 最終清理，確保沒有以下劃線開始或結束
        doc_id = doc_id.strip('_')
        
        return doc_id

    def _generate_base_tip_doc_id(self, title: str, index: int) -> str:
        """生成基礎 tip 文檔ID（不包含語言後綴，用於多語言合併）"""
        import re
        
        # 1. 清理標題，只保留字母、數字、中文字符和基本標點
        cleaned_title = re.sub(r'[^\w\u4e00-\u9fff\s\-_]', '', title)
        
        # 2. 將多個空格替換為單個下劃線
        cleaned_title = re.sub(r'\s+', '_', cleaned_title.strip())
        
        # 3. 移除連續的下劃線
        cleaned_title = re.sub(r'_+', '_', cleaned_title)
        
        # 4. 限制長度
        max_title_length = 30
        if len(cleaned_title) > max_title_length:
            truncated = cleaned_title[:max_title_length]
            while len(truncated) > 0 and ord(truncated[-1]) > 127:
                if len(truncated) < max_title_length:
                    break
                truncated = truncated[:-1]
            cleaned_title = truncated
        
        # 5. 生成基礎文檔ID: 序號_標題（不包含語言）
        doc_id = f"{index:03d}_{cleaned_title}"
        
        # 6. 最終清理
        doc_id = doc_id.strip('_')
        
        return doc_id

    def _sync_tips_data(self, tips_data: List[Dict], language: str):
        """同步Tips資料到Firebase"""
        logger.info(f"開始同步 {language} Tips資料...")
        
        try:
            tips_ref = self.db.collection('tips')
            batch = self.db.batch()
            batch_count = 0
            
            for index, tip in enumerate(tips_data, 1):
                title = tip.get('title', '').strip()
                desc = tip.get('desc', '').strip()
                
                if not title or not desc:
                    continue
                
                # 改進的文檔ID命名方法
                doc_id = self._generate_tip_doc_id(title, language, index)
                
                # 檢查是否已存在相同標題的文檔（不同語言版本）
                base_doc_id = self._generate_base_tip_doc_id(title, index)
                existing_doc = None
                
                # 先嘗試找到基礎文檔ID
                try:
                    existing_doc = tips_ref.document(base_doc_id).get()
                except:
                    # 如果基礎文檔不存在，嘗試當前語言的文檔ID
                    try:
                        existing_doc = tips_ref.document(doc_id).get()
                    except:
                        pass
                
                # 使用基礎文檔ID（不包含語言後綴）來合併多語言
                final_doc_id = base_doc_id
                
                tip_data = {
                    f'title.{language}': title,
                    f'desc.{language}': desc,
                    'updatedAt': firestore.SERVER_TIMESTAMP,
                    'index': index  # 添加索引用於排序
                }
                
                if existing_doc and existing_doc.exists:
                    # 更新現有文檔
                    batch.update(tips_ref.document(final_doc_id), tip_data)
                    self.stats['updated'] += 1
                else:
                    # 建立新文檔
                    tip_data['createdAt'] = firestore.SERVER_TIMESTAMP
                    batch.set(tips_ref.document(final_doc_id), tip_data)
                    self.stats['inserted'] += 1
                
                batch_count += 1
                
                # 每500個操作提交一次批次
                if batch_count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0
            
            # 提交剩餘的批次
            if batch_count > 0:
                batch.commit()
            
            logger.info(f"同步了 {len(tips_data)} 個Tips")
            
        except Exception as e:
            logger.error(f"同步Tips資料失敗: {e}")
            self.stats['errors'].append(f"同步Tips失敗: {str(e)}")
    
    def _sync_cards_data(self, card_data: Dict, language: str):
        """同步卡片資料"""
        if 'card_details' not in card_data:
            logger.warning(f"{language} 資料中沒有 card_details")
            return
        
        card_details = card_data['card_details']
        self.stats['total_cards'] = len(card_details)
        
        logger.info(f"開始同步 {self.stats['total_cards']} 張卡片...")
        
        # 使用多執行緒同步卡片
        card_ids = list(card_details.keys())
        batch_size = 20  # 每批處理的卡片數量
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for i in range(0, len(card_ids), batch_size):
                batch_ids = card_ids[i:i + batch_size]
                future = executor.submit(
                    self._sync_card_batch, 
                    batch_ids, 
                    card_details, 
                    language
                )
                futures.append(future)
            
            # 等待所有批次完成
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                try:
                    future.result()
                    progress = min((i + 1) * batch_size, len(card_ids))
                    logger.info(f"已處理 {progress}/{len(card_ids)} 張卡片")
                except Exception as e:
                    logger.error(f"批次處理失敗: {e}")
    
    def _sync_card_batch(self, card_ids: List[str], card_details: Dict, language: str):
        """同步一批卡片"""
        batch = self.db.batch()
        
        for card_id in card_ids:
            try:
                card_info = card_details[card_id]
                card_data = self._prepare_card_data(card_id, card_info, language)
                
                card_ref = self.db.collection('cards').document(str(card_id))
                
                # 檢查卡片是否已存在來決定是插入還是更新
                try:
                    existing_doc = card_ref.get()
                    if existing_doc.exists:
                        # 更新現有卡片
                        batch.set(card_ref, card_data, merge=True)
                        with self.stats_lock:
                            self.stats['updated'] += 1
                    else:
                        # 插入新卡片
                        batch.set(card_ref, card_data)
                        with self.stats_lock:
                            self.stats['inserted'] += 1
                except Exception as doc_check_error:
                    # 如果無法檢查文檔存在性，默認使用merge模式
                    logger.warning(f"無法檢查卡片 {card_id} 是否存在，使用merge模式: {doc_check_error}")
                    batch.set(card_ref, card_data, merge=True)
                
                with self.stats_lock:
                    self.stats['successful_cards'] += 1
                    
            except Exception as e:
                logger.error(f"準備卡片 {card_id} 資料失敗: {e}")
                with self.stats_lock:
                    self.stats['failed_cards'] += 1
                    self.stats['errors'].append(f"Card {card_id}: {str(e)}")
        
        # 提交批次
        try:
            batch.commit()
        except Exception as e:
            logger.error(f"提交批次失敗: {e}")
            with self.stats_lock:
                self.stats['failed_cards'] += len(card_ids)
    
    def _prepare_card_data(self, card_id: str, card_info: Dict, language: str) -> Dict:
        """準備卡片資料"""
        common = card_info.get('common', {})
        evo = card_info.get('evo', {})
        
        # 基本卡片資料
        card_data = {
            'id': int(card_id),
            'baseCardId': common.get('base_card_id'),
            'cardResourceId': common.get('card_resource_id'),
            'cardSetId': common.get('card_set_id'),
            'type': common.get('type'),
            'class': common.get('class'),
            'cost': common.get('cost'),
            'atk': common.get('atk'),
            'life': common.get('life'),
            'rarity': common.get('rarity'),
            'isToken': common.get('is_token', False),
            'isIncludeRotation': common.get('is_include_rotation', False),
            'cardImageHash': common.get('card_image_hash'),
            'cardBannerImageHash': common.get('card_banner_image_hash'),
            'updatedAt': firestore.SERVER_TIMESTAMP
        }
        
        # 移除 None 值
        card_data = {k: v for k, v in card_data.items() if v is not None}
        
        # 多語言名稱
        if common.get('name'):
            card_data[f'names.{language}'] = {
                'name': common.get('name', ''),
                'nameRuby': common.get('name_ruby', '')
            }
        
        # 多語言描述 (普通形態)
        if any([common.get('flavour_text'), common.get('skill_text'), 
                common.get('cv'), common.get('illustrator')]):
            card_data[f'descriptions.{language}.common'] = {
                'flavourText': common.get('flavour_text', ''),
                'skillText': common.get('skill_text', ''),
                'cv': common.get('cv', ''),
                'illustrator': common.get('illustrator', '')
            }
        
        # 多語言描述 (進化形態)
        if evo and any([evo.get('flavour_text'), evo.get('skill_text'), 
                       evo.get('cv'), evo.get('illustrator')]):
            card_data[f'descriptions.{language}.evo'] = {
                'flavourText': evo.get('flavour_text', ''),
                'skillText': evo.get('skill_text', ''),
                'cv': evo.get('cv', ''),
                'illustrator': evo.get('illustrator', '')
            }
        
        # 進化資訊
        if evo:
            evolution_data = {}
            if evo.get('card_resource_id'):
                evolution_data['cardResourceId'] = evo.get('card_resource_id')
            if evo.get('card_image_hash'):
                evolution_data['cardImageHash'] = evo.get('card_image_hash')
            if evo.get('card_banner_image_hash'):
                evolution_data['cardBannerImageHash'] = evo.get('card_banner_image_hash')
            
            if evolution_data:
                card_data['evolution'] = evolution_data
        
        # 種族資訊
        if 'tribes' in common and common['tribes']:
            # 過濾掉 0 (無種族)
            tribes = [t for t in common['tribes'] if t != 0]
            if tribes:
                card_data['tribes'] = tribes
        
        # 相關卡片
        if 'related_cards' in card_info and card_info['related_cards']:
            card_data['relatedCards'] = card_info['related_cards']
        
        # 特效相關卡片
        if 'specific_effect_cards' in card_info and card_info['specific_effect_cards']:
            card_data['specificEffectCards'] = card_info['specific_effect_cards']
        
        return card_data
    
    def _sync_card_subcollections(self, card_id: str, card_info: Dict, language: str):
        """同步卡片子集合 (問答和風格變體)"""
        # 同步問答
        if 'questions' in card_info.get('common', {}):
            self._sync_card_questions(card_id, card_info['common']['questions'], language)
        
        # 同步風格變體
        if 'style_card_list' in card_info:
            self._sync_card_styles(card_id, card_info['style_card_list'])
    
    def _sync_card_questions(self, card_id: str, questions: List[Dict], language: str):
        """同步卡片問答"""
        try:
            questions_ref = self.db.collection('cards').document(str(card_id)).collection('questions')
            
            # 先刪除該語言的現有問答
            existing_questions = questions_ref.where('language', '==', language).get()
            batch = self.db.batch()
            
            for doc in existing_questions:
                batch.delete(doc.reference)
            
            # 新增問答
            for q in questions:
                question_ref = questions_ref.document()
                batch.set(question_ref, {
                    'language': language,
                    'question': q.get('question', ''),
                    'answer': q.get('answer', ''),
                    'createdAt': firestore.SERVER_TIMESTAMP
                })
            
            batch.commit()
            
        except Exception as e:
            logger.error(f"同步卡片 {card_id} 問答失敗: {e}")
    
    def _sync_card_styles(self, card_id: str, styles: List[Dict]):
        """同步卡片風格變體"""
        try:
            styles_ref = self.db.collection('cards').document(str(card_id)).collection('styles')
            
            # 先刪除現有風格
            existing_styles = styles_ref.get()
            batch = self.db.batch()
            
            for doc in existing_styles:
                batch.delete(doc.reference)
            
            # 新增風格變體
            for style in styles:
                style_ref = styles_ref.document()
                batch.set(style_ref, {
                    'hash': style.get('hash', ''),
                    'evoHash': style.get('evo_hash', ''),
                    'name': style.get('name', ''),
                    'nameRuby': style.get('name_ruby', ''),
                    'cv': style.get('cv', ''),
                    'illustrator': style.get('illustrator', ''),
                    'skillText': style.get('skill_text', ''),
                    'flavourText': style.get('flavour_text', ''),
                    'evoFlavourText': style.get('evo_flavour_text', ''),
                    'createdAt': firestore.SERVER_TIMESTAMP
                })
            
            batch.commit()
            
        except Exception as e:
            logger.error(f"同步卡片 {card_id} 風格變體失敗: {e}")
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """獲取同步統計資訊"""
        return {
            'total_cards': self.stats['total_cards'],
            'successful_cards': self.stats['successful_cards'],
            'failed_cards': self.stats['failed_cards'],
            'success_rate': (self.stats['successful_cards'] / max(self.stats['total_cards'], 1)) * 100,
            'inserted': self.stats['inserted'],
            'updated': self.stats['updated'],
            'errors': self.stats['errors'][:10]  # 只顯示前 10 個錯誤
        }

def sync_tips_data(config: FirebaseConfig, data_directory: str = 'output/tips_data') -> Dict[str, Any]:
    """同步所有語言的Tips資料"""
    languages = ['cht', 'chs', 'en', 'ja', 'ko']
    sync_results = {}
    
    logger.info("開始同步所有語言的Tips資料到 Firebase...")
    
    # 創建單一的同步實例，用於所有語言
    sync = ShadowverseFirebaseSync(config)
    
    for language in languages:
        tips_file = os.path.join(data_directory, f'tips_data_{language}.json')
        
        if not os.path.exists(tips_file):
            logger.warning(f"找不到 {language} 語言的Tips檔案: {tips_file}")
            sync_results[language] = {'success': False, 'error': 'File not found'}
            continue
        
        try:
            with open(tips_file, 'r', encoding='utf-8') as f:
                tips_data = json.load(f)
            
            # 記錄同步前的統計數據
            before_inserted = sync.stats['inserted']
            before_updated = sync.stats['updated']
            
            # 同步Tips資料
            sync._sync_tips_data(tips_data.get('tips', []), language)
            
            # 計算此語言的統計數據
            language_inserted = sync.stats['inserted'] - before_inserted
            language_updated = sync.stats['updated'] - before_updated
            
            sync_results[language] = {
                'success': True,
                'statistics': {
                    'inserted': language_inserted,
                    'updated': language_updated,
                    'total_tips': len(tips_data.get('tips', []))
                }
            }
            
            logger.info(f"{language} Tips同步結果: 成功 (插入: {language_inserted}, 更新: {language_updated})")
            
        except Exception as e:
            logger.error(f"{language} Tips同步失敗: {e}")
            sync_results[language] = {'success': False, 'error': str(e)}
        
        # 語言間稍作休息
        time.sleep(1)
    
    return sync_results

def sync_all_languages(config: FirebaseConfig, data_directory: str = 'output') -> Dict[str, Any]:
    """同步所有語言的資料"""
    languages = ['cht', 'chs', 'en', 'ja', 'ko']
    sync_results = {}
    
    logger.info("開始同步所有語言的卡牌資料到 Firebase...")
    
    for language in languages:
        json_file = os.path.join(data_directory, f'shadowverse_cards_{language}.json')
        
        if not os.path.exists(json_file):
            logger.warning(f"找不到 {language} 語言的資料檔案: {json_file}")
            sync_results[language] = {'success': False, 'error': 'File not found'}
            continue
        
        sync = ShadowverseFirebaseSync(config)
        success = sync.sync_language_data(language, json_file)
        
        sync_results[language] = {
            'success': success,
            'statistics': sync.get_sync_statistics()
        }
        
        logger.info(f"{language} 同步結果: {'成功' if success else '失敗'}")
        
        # 語言間稍作休息
        time.sleep(2)
    
    return sync_results

def load_config() -> FirebaseConfig:
    """載入 Firebase 配置"""
    config_file = 'firebase/config.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return FirebaseConfig(
            project_id=config_data['project_id'],
            service_account_key_path=config_data['service_account_key_path']
        )
    else:
        # 從環境變數載入
        return FirebaseConfig(
            project_id=os.getenv('FIREBASE_PROJECT_ID', ''),
            service_account_key_path=os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY', '')
        )

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Shadowverse Firebase 同步工具')
    parser.add_argument('--type', choices=['cards', 'tips', 'all'], default='all', 
                       help='同步類型: cards=卡牌資料, tips=Tips資料, all=全部')
    args = parser.parse_args()
    
    try:
        # 載入配置
        config = load_config()
        
        if not config.project_id or not config.service_account_key_path:
            logger.error("請設定 Firebase 連線資訊")
            logger.info("可以建立 firebase/config.json 檔案或設定環境變數")
            return
        
        if not os.path.exists(config.service_account_key_path):
            logger.error(f"找不到服務帳戶金鑰檔案: {config.service_account_key_path}")
            return
        
        # 初始化結果變數
        results = {}
        tips_results = {}
        
        # 根據參數決定同步類型
        if args.type in ['cards', 'all']:
            # 同步卡牌資料
            logger.info("開始同步卡牌資料...")
            results = sync_all_languages(config)
            
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
            tips_results = sync_tips_data(config)
            
            # 顯示Tips同步結果摘要
            print("\n" + "="*60)
            print("Tips資料同步結果摘要")
            print("="*60)
            
            for language, result in tips_results.items():
                status = "✅ 成功" if result['success'] else "❌ 失敗"
                print(f"{language}: {status}")
                
                if result['success'] and 'statistics' in result:
                    stats = result['statistics']
                    print(f"  - 總Tips數: {stats.get('total_tips', 0)}")
                    print(f"  - 插入: {stats.get('inserted', 0)}")
                    print(f"  - 更新: {stats.get('updated', 0)}")
                elif not result['success']:
                    print(f"  - 錯誤: {result.get('error', '未知錯誤')}")
        
        # 顯示結果摘要
        print("\n" + "="*60)
        print("Firebase 資料同步完成摘要")
        print("="*60)
        
        # 合併所有結果
        all_results = {}
        if results:
            all_results.update(results)
        if tips_results:
            # 為 tips 結果添加標識
            for lang, result in tips_results.items():
                key = f"{lang}_tips"
                all_results[key] = result
        
        if all_results:
            for key, result in all_results.items():
                display_name = key.replace('_tips', ' (Tips)').upper()
                status = "✓ 成功" if result['success'] else "✗ 失敗"
                print(f"{display_name}: {status}")
                
                if result['success'] and 'statistics' in result:
                    stats = result['statistics']
                    if '_tips' in key:
                        # Tips 同步統計
                        print(f"  插入: {stats.get('inserted', 0)}")
                        print(f"  更新: {stats.get('updated', 0)}")
                    else:
                        # 卡牌同步統計
                        print(f"  總卡片數: {stats.get('total_cards', 0)}")
                        print(f"  成功: {stats.get('successful_cards', 0)}")
                        print(f"  失敗: {stats.get('failed_cards', 0)}")
                        print(f"  成功率: {stats.get('success_rate', 0):.1f}%")
                elif not result['success']:
                    print(f"  錯誤: {result.get('error', '未知錯誤')}")
                
                print()
        else:
            print("沒有執行任何同步操作")
        
        logger.info("所有語言資料同步完成")
        
    except KeyboardInterrupt:
        logger.info("使用者中斷同步程序")
    except Exception as e:
        logger.error(f"同步過程中發生錯誤: {e}")
        raise

if __name__ == "__main__":
    main()