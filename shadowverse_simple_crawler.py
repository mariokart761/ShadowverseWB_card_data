#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowverse 卡牌資料爬蟲腳本（簡化版）
使用 requests 爬取 shadowverse-wb.com 的卡牌資料並整理成 JSON 格式
"""

import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional

# 設定日誌和目錄
import os
os.makedirs('logs', exist_ok=True)
os.makedirs('output', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/shadowverse_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ShadowverseSimpleCrawler:
    def __init__(self, lang: str = 'cht'):
        self.base_url = "https://shadowverse-wb.com/web/CardList/cardList"
        self.lang = lang
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://shadowverse-wb.com/web/cardList',
            'Connection': 'keep-alive',
            'lang': lang
        })
        
        # 初始化完整資料結構
        self.complete_data = {
            "data_headers": {
                "result_code": 1,
                "user_id": 0,
                "user_name": "",
                "is_login": False,
                "csrf_token": "crawler-generated"
            },
            "data": {
                "cards": {},
                "card_details": {},
                "specific_effect_card_info": [],
                "tribe_names": {},
                "card_set_names": {},
                "skill_names": {},
                "skill_replace_text_names": {},
                "count": 0,
                "sort_card_id_list": [],
                "stats_list": {
                    "atk": {"min": 0, "max": 0},
                    "life": {"min": 0, "max": 0},
                    "cost": {"min": 0, "max": 0}
                },
                "result_error_code": None
            }
        }
    
    def fetch_card_data(self, offset: int = 0) -> Optional[Dict[str, Any]]:
        """獲取指定 offset 的卡牌資料"""
        try:
            logger.info(f"正在獲取 {self.lang} 語言 offset={offset} 的資料...")
            
            # 構建參數
            params = {
                'offset': offset,
                'class': '0,1,2,3,4,5,6,7',
                'cost': '0,1,2,3,4,5,6,7,8,9,10',
                'lang': self.lang
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            
            # 檢查狀態碼
            if response.status_code == 200:
                try:
                    data = response.json()
                    card_count = len(data.get('data', {}).get('card_details', {}))
                    logger.info(f"成功獲取 {self.lang} 語言 offset={offset} 的資料，包含 {card_count} 張卡片")
                    return data
                except json.JSONDecodeError:
                    logger.warning(f"offset={offset} 回應不是有效的 JSON")
                    return None
            else:
                logger.warning(f"offset={offset} HTTP 狀態碼: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"請求 offset={offset} 超時")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"請求 offset={offset} 時發生錯誤: {e}")
            return None
    
    def merge_data(self, new_data: Dict[str, Any]) -> None:
        """合併新資料到完整資料集中"""
        if not new_data or 'data' not in new_data:
            return
        
        data = new_data['data']
        
        # 更新 data_headers（使用最新的）
        if 'data_headers' in new_data:
            self.complete_data['data_headers'].update(new_data['data_headers'])
        
        # 合併 cards
        if 'cards' in data:
            self.complete_data['data']['cards'].update(data['cards'])
        
        # 合併 card_details
        if 'card_details' in data:
            self.complete_data['data']['card_details'].update(data['card_details'])
        
        # 合併 specific_effect_card_info（去重）
        if 'specific_effect_card_info' in data:
            existing_info = {str(item) for item in self.complete_data['data']['specific_effect_card_info']}
            for item in data['specific_effect_card_info']:
                if str(item) not in existing_info:
                    self.complete_data['data']['specific_effect_card_info'].append(item)
        
        # 更新名稱對應表
        name_fields = ['tribe_names', 'card_set_names', 'skill_names', 'skill_replace_text_names']
        for field in name_fields:
            if field in data:
                self.complete_data['data'][field].update(data[field])
        
        # 擴展 sort_card_id_list（去重並保持順序）
        if 'sort_card_id_list' in data:
            existing_ids = set(self.complete_data['data']['sort_card_id_list'])
            for card_id in data['sort_card_id_list']:
                if card_id not in existing_ids:
                    self.complete_data['data']['sort_card_id_list'].append(card_id)
                    existing_ids.add(card_id)
        
        # 更新統計資料
        if 'stats_list' in data:
            stats = self.complete_data['data']['stats_list']
            new_stats = data['stats_list']
            
            for stat_type in ['atk', 'life', 'cost']:
                if stat_type in new_stats:
                    if stats[stat_type]['min'] == 0 and stats[stat_type]['max'] == 0:
                        # 首次設定
                        stats[stat_type] = new_stats[stat_type].copy()
                    else:
                        # 更新最小最大值
                        stats[stat_type]['min'] = min(stats[stat_type]['min'], new_stats[stat_type]['min'])
                        stats[stat_type]['max'] = max(stats[stat_type]['max'], new_stats[stat_type]['max'])
        
        # 更新總數
        self.complete_data['data']['count'] = len(self.complete_data['data']['card_details'])
        
        logger.info(f"目前總共有 {self.complete_data['data']['count']} 張卡片")
    
    def crawl_all_cards(self) -> Dict[str, Any]:
        """爬取所有卡牌資料"""
        logger.info(f"開始爬取 Shadowverse {self.lang} 語言卡牌資料...")
        
        offset = 0
        consecutive_empty = 0
        max_consecutive_empty = 3  # 連續 3 次空回應就停止
        
        while consecutive_empty < max_consecutive_empty:
            data = self.fetch_card_data(offset)
            
            if data and 'data' in data and data['data'].get('card_details'):
                self.merge_data(data)
                consecutive_empty = 0  # 重置計數器
                
                # 檢查是否還有更多資料
                card_count = len(data['data'].get('card_details', {}))
                if card_count < 30:  # 如果回傳的卡片數量少於 30，可能已經到底了
                    logger.info(f"{self.lang} 語言 offset={offset} 只回傳了 {card_count} 張卡片，可能已接近結尾")
                    if card_count == 0:
                        consecutive_empty += 1
            else:
                consecutive_empty += 1
                logger.warning(f"{self.lang} 語言 offset={offset} 沒有獲取到有效資料 (連續第 {consecutive_empty} 次)")
            
            offset += 30  # 每次增加 30
            time.sleep(3)  # 避免請求過於頻繁
            
            # 安全機制：避免無限迴圈
            if offset > 10000:  # 假設不會超過 10000 個 offset
                logger.warning(f"{self.lang} 語言已達到最大 offset 限制，停止爬取")
                break
        
        logger.info(f"{self.lang} 語言爬取完成！總共獲取了 {self.complete_data['data']['count']} 張卡片")
        return self.complete_data
    
    def save_to_file(self, filename: str = "shadowverse_cards.json") -> None:
        """將資料儲存到檔案"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.complete_data, f, ensure_ascii=False, indent=2)
            logger.info(f"資料已儲存到 {filename}")
            
            # 顯示檔案大小
            import os
            file_size = os.path.getsize(filename)
            logger.info(f"檔案大小: {file_size / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            logger.error(f"儲存檔案時發生錯誤: {e}")
            raise

def crawl_single_language(lang: str) -> Dict[str, Any]:
    """爬取單一語言的卡牌資料"""
    try:
        crawler = ShadowverseSimpleCrawler(lang)
        
        # 爬取所有卡牌資料
        complete_data = crawler.crawl_all_cards()
        
        # 儲存到檔案
        filename = f"output/shadowverse_cards_{lang}.json"
        crawler.save_to_file(filename)
        
        # 顯示統計資訊
        card_count = complete_data['data']['count']
        sort_count = len(complete_data['data']['sort_card_id_list'])
        
        print(f"\n=== {lang.upper()} 語言爬取完成統計 ===")
        print(f"總卡片數量: {card_count}")
        print(f"排序列表長度: {sort_count}")
        print(f"種族數量: {len(complete_data['data']['tribe_names'])}")
        print(f"卡包數量: {len(complete_data['data']['card_set_names'])}")
        print(f"技能數量: {len(complete_data['data']['skill_names'])}")
        
        if complete_data['data']['stats_list']['atk']['max'] > 0:
            stats = complete_data['data']['stats_list']
            print(f"攻擊力範圍: {stats['atk']['min']} - {stats['atk']['max']}")
            print(f"生命值範圍: {stats['life']['min']} - {stats['life']['max']}")
            print(f"費用範圍: {stats['cost']['min']} - {stats['cost']['max']}")
        
        # 顯示一些範例卡片
        if complete_data['data']['card_details']:
            print(f"\n=== {lang.upper()} 範例卡片 ===")
            sample_cards = list(complete_data['data']['card_details'].items())[:2]
            for card_id, card_info in sample_cards:
                common = card_info.get('common', {})
                print(f"卡片ID: {card_id}")
                print(f"  名稱: {common.get('name', 'N/A')}")
                print(f"  費用: {common.get('cost', 'N/A')}")
                print(f"  攻擊力: {common.get('atk', 'N/A')}")
                print(f"  生命值: {common.get('life', 'N/A')}")
                print()
        
        return complete_data
        
    except Exception as e:
        logger.error(f"爬取 {lang} 語言時發生錯誤: {e}")
        raise

def main():
    """主函數 - 爬取所有語言"""
    # 支援的語言列表
    languages = ['cht', 'chs', 'en', 'ja', 'ko']
    
    # 語言名稱對照
    lang_names = {
        'cht': '繁體中文',
        'chs': '簡體中文', 
        'en': '英文',
        'ja': '日文',
        'ko': '韓文'
    }
    
    print("=== Shadowverse 多語言卡牌資料爬蟲 ===")
    print(f"將爬取以下語言: {', '.join([f'{lang}({lang_names[lang]})' for lang in languages])}")
    print()
    
    all_results = {}
    successful_languages = []
    failed_languages = []
    
    try:
        for i, lang in enumerate(languages, 1):
            print(f"\n{'='*50}")
            print(f"開始爬取第 {i}/{len(languages)} 種語言: {lang.upper()} ({lang_names[lang]})")
            print(f"{'='*50}")
            
            try:
                result = crawl_single_language(lang)
                all_results[lang] = result
                successful_languages.append(lang)
                
                # 在語言之間稍作休息
                if i < len(languages):
                    print(f"\n等待 5 秒後繼續下一種語言...")
                    time.sleep(5)
                    
            except KeyboardInterrupt:
                logger.info("使用者中斷程式執行")
                break
            except Exception as e:
                logger.error(f"爬取 {lang} 語言失敗: {e}")
                failed_languages.append(lang)
                continue
        
        # 顯示最終統計
        print(f"\n{'='*60}")
        print("=== 多語言爬取完成總結 ===")
        print(f"{'='*60}")
        print(f"成功爬取語言數量: {len(successful_languages)}/{len(languages)}")
        
        if successful_languages:
            print(f"成功語言: {', '.join([f'{lang}({lang_names[lang]})' for lang in successful_languages])}")
            
            # 顯示各語言統計
            print(f"\n=== 各語言卡片數量統計 ===")
            for lang in successful_languages:
                count = all_results[lang]['data']['count']
                print(f"{lang.upper()} ({lang_names[lang]}): {count} 張卡片")
                print(f"  檔案: output/shadowverse_cards_{lang}.json")
        
        if failed_languages:
            print(f"\n失敗語言: {', '.join([f'{lang}({lang_names[lang]})' for lang in failed_languages])}")
        
        print(f"\n所有檔案已儲存完成！")
        
    except KeyboardInterrupt:
        logger.info("使用者中斷程式執行")
    except Exception as e:
        logger.error(f"程式執行時發生錯誤: {e}")
        raise

if __name__ == "__main__":
    main()