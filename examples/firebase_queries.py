#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firebase Firestore 查詢範例
展示如何查詢已同步的卡牌資料
"""

import json
import os
import sys
from typing import List, Dict, Any

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("請先安裝 Firebase Admin SDK: pip install firebase-admin")
    sys.exit(1)

def load_config():
    """載入 Firebase 配置"""
    config_file = 'firebase/config.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return config_data
    else:
        print("找不到配置檔案: firebase/config.json")
        print("請先執行 python firebase/init_firebase.py config")
        return None

def initialize_firebase():
    """初始化 Firebase"""
    config = load_config()
    if not config:
        return None
    
    try:
        # 檢查是否已經初始化
        if not firebase_admin._apps:
            cred = credentials.Certificate(config['service_account_key_path'])
            firebase_admin.initialize_app(cred, {
                'projectId': config['project_id']
            })
        
        return firestore.client()
    except Exception as e:
        print(f"Firebase 初始化失敗: {e}")
        return None

def get_card_name(card_data: dict, language: str = 'cht') -> str:
    """從卡片資料中獲取指定語言的名稱"""
    name_field = f'names.{language}'
    if name_field in card_data:
        name_info = card_data[name_field]
        if isinstance(name_info, dict):
            name = name_info.get('name', '').strip()
            if name:
                return name
    return '未知'

def get_card_name_fallback(card_data: dict, preferred_lang: str = 'cht') -> str:
    """從卡片資料中獲取名稱，如果首選語言不存在則嘗試其他語言"""
    # 嘗試首選語言
    name = get_card_name(card_data, preferred_lang)
    if name != '未知':
        return name
    
    # 嘗試其他語言，按優先順序
    fallback_langs = ['cht', 'chs', 'en', 'ja', 'ko']
    for lang in fallback_langs:
        if lang != preferred_lang:
            name = get_card_name(card_data, lang)
            if name != '未知':
                return f"{name} ({lang})"
    
    return '未知'

def example_basic_queries():
    """基本查詢範例"""
    print("=== 基本查詢範例 ===")
    
    db = initialize_firebase()
    if not db:
        return
    
    try:
        # 1. 查詢卡片總數
        cards_ref = db.collection('cards')
        cards = cards_ref.limit(1).get()  # 只取一個來檢查是否有資料
        
        if cards:
            # 使用聚合查詢獲取總數 (需要 Firebase Admin SDK v6.0+)
            try:
                from google.cloud.firestore_v1.aggregation import AggregationQuery
                total_count = cards_ref.count().get()
                print(f"資料庫中總共有 {total_count[0][0].value} 張卡片")
            except:
                # 如果不支援聚合查詢，使用估算
                print("資料庫中有卡片資料 (無法精確計算總數)")
        else:
            print("資料庫中沒有卡片資料")
            return
        
        # 2. 查詢各職業卡片數量 (限制每個查詢的結果數量)
        print("\n各職業卡片數量 (前10張):")
        classes = {
            0: '中立', 1: '精靈', 2: '皇家護衛', 3: '巫師', 
            4: '龍族', 5: '死靈法師', 6: '主教', 7: '復仇者'
        }
        
        for class_id, class_name in classes.items():
            class_cards = cards_ref.where('class', '==', class_id).limit(10).get()
            print(f"  {class_name}: {len(class_cards)} 張 (樣本)")
        
        # 3. 查詢各稀有度卡片數量
        print("\n各稀有度卡片數量 (前10張):")
        rarities = {1: '銅', 2: '銀', 3: '金', 4: '虹'}
        
        for rarity_id, rarity_name in rarities.items():
            rarity_cards = cards_ref.where('rarity', '==', rarity_id).limit(10).get()
            print(f"  {rarity_name}: {len(rarity_cards)} 張 (樣本)")
        
    except Exception as e:
        print(f"查詢時發生錯誤: {e}")

def example_card_search():
    """卡片搜尋範例"""
    print("\n=== 卡片搜尋範例 ===")
    
    db = initialize_firebase()
    if not db:
        return
    
    try:
        # 由於 Firestore 不支援全文搜尋，我們展示其他查詢方式
        
        # 1. 查詢特定費用的卡片
        cards_ref = db.collection('cards')
        cost_5_cards = cards_ref.where('cost', '==', 5).limit(5).get()
        
        print("費用為 5 的卡片:")
        for card in cost_5_cards:
            card_data = card.to_dict()
            cht_name = get_card_name(card_data)
            print(f"  {cht_name} - 費用:{card_data.get('cost')} 攻擊:{card_data.get('atk')} 生命:{card_data.get('life')}")
        
        # 2. 查詢高攻擊力卡片
        high_atk_cards = cards_ref.where('atk', '>=', 8).limit(5).get()
        
        print("\n高攻擊力卡片 (攻擊 >= 8):")
        for card in high_atk_cards:
            card_data = card.to_dict()
            cht_name = get_card_name(card_data)
            print(f"  {cht_name} - 攻擊:{card_data.get('atk')} 生命:{card_data.get('life')} 費用:{card_data.get('cost')}")
        
    except Exception as e:
        print(f"搜尋時發生錯誤: {e}")

def example_complex_queries():
    """複合查詢範例"""
    print("\n=== 複合查詢範例 ===")
    
    db = initialize_firebase()
    if not db:
        return
    
    try:
        cards_ref = db.collection('cards')
        
        # 1. 查詢特定職業和費用的卡片
        elf_cost_3 = cards_ref.where('class', '==', 1).where('cost', '==', 3).limit(5).get()
        
        print("精靈職業費用 3 的卡片:")
        for card in elf_cost_3:
            card_data = card.to_dict()
            cht_name = get_card_name(card_data)
            print(f"  {cht_name} - 攻擊:{card_data.get('atk')} 生命:{card_data.get('life')}")
        
        # 2. 查詢非isToken卡片
        non_token_cards = cards_ref.where('isToken', '==', False).limit(5).get()
        
        print("\n非isToken卡片:")
        for card in non_token_cards:
            card_data = card.to_dict()
            cht_name = get_card_name(card_data)
            print(f"  {cht_name} - 職業:{card_data.get('class')} 費用:{card_data.get('cost')}")
        
        # 3. 查詢包含特定種族的卡片
        # 查詢更多卡片來找到有種族的卡片
        all_cards = cards_ref.limit(100).get()
        cards_with_tribes = [card for card in all_cards if card.to_dict().get('tribes', [])]
        
        if cards_with_tribes:
            # 收集所有種族ID並使用第一個進行查詢
            found_tribes = set()
            for card in cards_with_tribes:
                tribes = card.to_dict().get('tribes', [])
                if tribes:
                    found_tribes.update(tribes)
            
            if found_tribes:
                first_tribe = min(found_tribes)
                # 從所有卡片中過濾包含該種族的卡片
                tribe_cards = [card for card in all_cards 
                             if first_tribe in card.to_dict().get('tribes', [])]
                
                print(f"\n包含種族 {first_tribe} 的卡片:")
                for card in tribe_cards[:5]:  # 只顯示前5張
                    card_data = card.to_dict()
                    card_name = get_card_name_fallback(card_data)
                    tribes = card_data.get('tribes', [])
                    print(f"  {card_name} - 種族:{tribes}")
            else:
                print("\n未找到有效的種族資料")
        else:
            print("\n未找到有種族的卡片")
        
    except Exception as e:
        print(f"複合查詢時發生錯誤: {e}")

def example_multilingual_data():
    """多語言資料範例"""
    print("\n=== 多語言資料範例 ===")
    
    db = initialize_firebase()
    if not db:
        return
    
    try:
        # 獲取一張卡片的多語言資料
        cards_ref = db.collection('cards')
        cards = cards_ref.where('isToken', '==', False).limit(1).get()
        
        if cards:
            card = cards[0]
            card_data = card.to_dict()
            card_id = card.id
            
            print(f"卡片 ID {card_id} 的多語言名稱:")
            
            lang_names = {'cht': '繁體中文', 'chs': '簡體中文', 'en': '英文', 'ja': '日文', 'ko': '韓文'}
            
            for lang, lang_display in lang_names.items():
                name = get_card_name(card_data, lang)
                if name != '未知':
                    print(f"  {lang_display}: {name}")
            
            # 顯示卡片基本資訊
            print(f"\n基本資訊:")
            print(f"  費用: {card_data.get('cost')}")
            print(f"  攻擊: {card_data.get('atk')}")
            print(f"  生命: {card_data.get('life')}")
            print(f"  稀有度: {card_data.get('rarity')}")
            print(f"  職業: {card_data.get('class')}")
        
    except Exception as e:
        print(f"多語言資料查詢時發生錯誤: {e}")

def example_subcollection_queries():
    """子集合查詢範例"""
    print("\n=== 子集合查詢範例 ===")
    
    db = initialize_firebase()
    if not db:
        return
    
    try:
        # 查詢有問答的卡片
        cards_ref = db.collection('cards')
        cards = cards_ref.limit(5).get()
        
        cards_with_questions = 0
        
        for card in cards:
            card_id = card.id
            questions_ref = card.reference.collection('questions')
            questions = questions_ref.limit(1).get()
            
            if questions:
                cards_with_questions += 1
                card_data = card.to_dict()
                cht_name = get_card_name(card_data)
                
                print(f"卡片 {cht_name} 有問答資料:")
                
                # 顯示問答內容
                all_questions = questions_ref.limit(3).get()
                for q in all_questions:
                    q_data = q.to_dict()
                    print(f"  Q: {q_data.get('question', '')}")
                    print(f"  A: {q_data.get('answer', '')}")
                    print()
        
        print(f"檢查了 {len(cards)} 張卡片，其中 {cards_with_questions} 張有問答資料")
        
    except Exception as e:
        print(f"子集合查詢時發生錯誤: {e}")

def example_reference_data():
    """參考資料查詢範例"""
    print("\n=== 參考資料查詢範例 ===")
    
    db = initialize_firebase()
    if not db:
        return
    
    try:
        # 查詢卡包資料
        card_sets_ref = db.collection('cardSets')
        card_sets = card_sets_ref.limit(5).get()
        
        print("卡包資料:")
        for card_set in card_sets:
            set_data = card_set.to_dict()
            names = set_data.get('names', {})
            cht_name = names.get('cht', '未知')
            print(f"  ID {card_set.id}: {cht_name}")
        
        # 查詢種族資料
        tribes_ref = db.collection('tribes')
        tribes = tribes_ref.limit(5).get()
        
        print("\n種族資料:")
        for tribe in tribes:
            tribe_data = tribe.to_dict()
            names = tribe_data.get('names', {})
            cht_name = names.get('cht', '未知')
            print(f"  ID {tribe.id}: {cht_name}")
        
        # 查詢技能資料
        skills_ref = db.collection('skills')
        skills = skills_ref.limit(5).get()
        
        print("\n技能資料:")
        for skill in skills:
            skill_data = skill.to_dict()
            names = skill_data.get('names', {})
            cht_name = names.get('cht', '未知')
            print(f"  ID {skill.id}: {cht_name}")
        
    except Exception as e:
        print(f"參考資料查詢時發生錯誤: {e}")

def example_sync_logs():
    """同步記錄查詢範例"""
    print("\n=== 同步記錄查詢範例 ===")
    
    db = initialize_firebase()
    if not db:
        return
    
    try:
        # 查詢最近的同步記錄
        sync_logs_ref = db.collection('syncLogs')
        recent_logs = sync_logs_ref.order_by('createdAt', direction=firestore.Query.DESCENDING).limit(5).get()
        
        print("最近的同步記錄:")
        for log in recent_logs:
            log_data = log.to_dict()
            language = log_data.get('language', '未知')
            status = log_data.get('syncStatus', '未知')
            total_cards = log_data.get('totalCards', 0)
            successful_cards = log_data.get('successfulCards', 0)
            created_at = log_data.get('createdAt')
            
            if created_at:
                # 轉換時間戳
                created_time = created_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                created_time = '未知時間'
            
            print(f"  {language} - {status} - {successful_cards}/{total_cards} 張成功 - {created_time}")
        
        # 查詢特定語言的同步記錄
        cht_logs = sync_logs_ref.where('language', '==', 'cht').limit(3).get()
        
        print(f"\n繁體中文同步記錄:")
        for log in cht_logs:
            log_data = log.to_dict()
            status = log_data.get('syncStatus', '未知')
            total_cards = log_data.get('totalCards', 0)
            successful_cards = log_data.get('successfulCards', 0)
            success_rate = (successful_cards / max(total_cards, 1)) * 100
            
            print(f"  狀態: {status}, 成功率: {success_rate:.1f}%")
        
    except Exception as e:
        print(f"同步記錄查詢時發生錯誤: {e}")

def example_advanced_filtering():
    """進階過濾範例"""
    print("\n=== 進階過濾範例 ===")
    
    db = initialize_firebase()
    if not db:
        return
    
    try:
        cards_ref = db.collection('cards')
        
        # 1. 查詢費用範圍內的卡片
        mid_cost_cards = cards_ref.where('cost', '>=', 4).where('cost', '<=', 6).limit(5).get()
        
        print("中費用卡片 (4-6費):")
        for card in mid_cost_cards:
            card_data = card.to_dict()
            cht_name = get_card_name(card_data)
            print(f"  {cht_name} - 費用:{card_data.get('cost')} 攻擊:{card_data.get('atk')}")
        
        # 2. 查詢輪替制中的高稀有度卡片
        rotation_legendaries = cards_ref.where('isIncludeRotation', '==', True).where('rarity', '==', 4).limit(3).get()
        
        print("\n輪替制中的傳說卡片:")
        for card in rotation_legendaries:
            card_data = card.to_dict()
            cht_name = get_card_name(card_data)
            print(f"  {cht_name} - 職業:{card_data.get('class')} 費用:{card_data.get('cost')}")
        
        # 3. 使用 in 查詢多個值
        neutral_and_elf = cards_ref.where('class', 'in', [0, 1]).limit(5).get()
        
        print("\n中立和精靈卡片:")
        for card in neutral_and_elf:
            card_data = card.to_dict()
            cht_name = get_card_name(card_data)
            class_name = '中立' if card_data.get('class') == 0 else '精靈'
            print(f"  {cht_name} - {class_name}")
        
    except Exception as e:
        print(f"進階過濾時發生錯誤: {e}")

def example_tips_queries():
    """Tips查詢範例"""
    print("\n=== Tips查詢範例 ===")
    
    db = initialize_firebase()
    if not db:
        return
    
    try:
        tips_ref = db.collection('tips')
        
        # 1. 查詢Tips總數
        tips_count = tips_ref.count().get()
        print(f"資料庫中總共有 {tips_count[0][0].value} 條Tips")
        
        # 2. 搜尋包含特定關鍵字的Tips
        keyword = "從者"
        tips_docs = tips_ref.limit(50).get()  # 先獲取一批Tips
        
        matching_tips = []
        for doc in tips_docs:
            tip_data = doc.to_dict()
            # 檢查繁體中文標題是否包含關鍵字
            if 'title.cht' in tip_data and keyword in tip_data['title.cht']:
                matching_tips.append(tip_data)
        
        print(f"\n包含 '{keyword}' 的Tips:")
        for tip in matching_tips[:3]:  # 只顯示前3條
            title = tip.get('title.cht', '未知標題')
            desc = tip.get('desc.cht', '未知說明')
            print(f"  標題: {title}")
            print(f"  說明: {desc[:100]}{'...' if len(desc) > 100 else ''}")
            print()
        
        # 3. 多語言Tips比較
        tips_sample = tips_ref.limit(2).get()
        
        print("多語言Tips比較:")
        for doc in tips_sample:
            tip_data = doc.to_dict()
            cht_title = tip_data.get('title.cht', '未知')
            en_title = tip_data.get('title.en', '未知')
            cht_desc = tip_data.get('desc.cht', '未知')
            en_desc = tip_data.get('desc.en', '未知')
            
            print(f"  繁中標題: {cht_title}")
            print(f"  英文標題: {en_title}")
            print(f"  繁中說明: {cht_desc[:80]}...")
            print(f"  英文說明: {en_desc[:80]}...")
            print()
        
        # 4. 按索引排序的Tips
        ordered_tips = tips_ref.order_by('index').limit(5).get()
        
        print("按索引排序的Tips (前5條):")
        for doc in ordered_tips:
            tip_data = doc.to_dict()
            title = tip_data.get('title.cht', '未知標題')
            desc = tip_data.get('desc.cht', '未知說明')
            index = tip_data.get('index', 0)
            print(f"  [{index:03d}] {title}: {desc[:60]}...")
        
        # 5. 搜尋特定遊戲概念的Tips
        concepts = ["職業", "法術", "護符"]
        all_tips = tips_ref.get()
        
        for concept in concepts:
            found_tip = None
            for doc in all_tips:
                tip_data = doc.to_dict()
                title = tip_data.get('title.cht', '')
                desc = tip_data.get('desc.cht', '')
                
                if concept in title or concept in desc:
                    found_tip = tip_data
                    break
            
            if found_tip:
                title = found_tip.get('title.cht', '未知標題')
                desc = found_tip.get('desc.cht', '未知說明')
                print(f"\n關於 '{concept}' 的Tips:")
                print(f"  {title}: {desc}")
        
        # 6. 統計各語言的Tips數量
        language_stats = {'cht': 0, 'chs': 0, 'en': 0, 'ja': 0, 'ko': 0}
        
        for doc in all_tips:
            tip_data = doc.to_dict()
            for lang in language_stats.keys():
                if f'title.{lang}' in tip_data and tip_data[f'title.{lang}']:
                    language_stats[lang] += 1
        
        print(f"\n各語言Tips統計:")
        lang_names = {'cht': '繁體中文', 'chs': '簡體中文', 'en': '英文', 'ja': '日文', 'ko': '韓文'}
        for lang, count in language_stats.items():
            print(f"  {lang_names[lang]}: {count} 條")
        
    except Exception as e:
        print(f"Tips查詢時發生錯誤: {e}")

def main():
    """主函數"""
    print("Firebase Firestore 查詢範例")
    print("=" * 50)
    
    # 檢查配置
    if not load_config():
        return
    
    # 執行各種查詢範例
    example_basic_queries()
    example_card_search()
    example_complex_queries()
    example_multilingual_data()
    example_subcollection_queries()
    example_reference_data()
    example_sync_logs()
    example_advanced_filtering()
    example_tips_queries()
    
    print("\n查詢範例執行完成！")
    print("\n注意事項:")
    print("- Firestore 查詢有一些限制，例如不支援全文搜尋")
    print("- 複合查詢可能需要建立索引")
    print("- 大量資料查詢時請注意成本和效能")

if __name__ == "__main__":
    main()