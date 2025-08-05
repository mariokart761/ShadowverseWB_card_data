#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 資料庫查詢範例
展示如何查詢已同步的卡牌資料
"""

import json
import os
import sys
import asyncio
from supabase import create_client, Client

def load_config():
    """載入資料庫配置"""
    config_file = 'supabase/config.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return config_data
    else:
        print("找不到配置檔案: supabase/config.json")
        print("請先設定 Supabase 連線資訊")
        return None

def create_supabase_client():
    """建立 Supabase 客戶端"""
    config = load_config()
    if not config:
        return None
    
    return create_client(config['supabase_url'], config['supabase_key'])

def example_basic_queries():
    """基本查詢範例"""
    print("=== 基本查詢範例 ===")
    
    supabase = create_supabase_client()
    if not supabase:
        return
    
    try:
        # 1. 查詢卡片總數
        result = supabase.table('cards').select('id', count='exact').execute()
        print(f"資料庫中總共有 {len(result.data)} 張卡片")
        
        # 2. 查詢各職業卡片數量
        print("\n各職業卡片數量:")
        classes = {
            0: '中立', 1: '精靈', 2: '皇家護衛', 3: '巫師', 
            4: '龍族', 5: '死靈法師', 6: '主教', 7: '復仇者'
        }
        
        for class_id, class_name in classes.items():
            result = supabase.table('cards').select('id', count='exact').eq('class', class_id).execute()
            print(f"  {class_name}: {len(result.data)} 張")
        
        # 3. 查詢各稀有度卡片數量
        print("\n各稀有度卡片數量:")
        rarities = {1: '銅', 2: '銀', 3: '金', 4: '虹'}
        
        for rarity_id, rarity_name in rarities.items():
            result = supabase.table('cards').select('id', count='exact').eq('rarity', rarity_id).execute()
            print(f"  {rarity_name}: {len(result.data)} 張")
        
    except Exception as e:
        print(f"查詢時發生錯誤: {e}")

def example_card_search():
    """卡片搜尋範例"""
    print("\n=== 卡片搜尋範例 ===")
    
    supabase = create_supabase_client()
    if not supabase:
        return
    
    try:
        # 搜尋包含特定關鍵字的卡片 (繁體中文)
        keyword = "天使"
        result = supabase.table('card_names').select(
            'card_id, name, cards(cost, atk, life, rarity)'
        ).eq('language', 'cht').ilike('name', f'%{keyword}%').execute()
        
        print(f"包含 '{keyword}' 的卡片:")
        for card in result.data[:5]:  # 只顯示前5張
            card_info = card['cards']
            print(f"  {card['name']} - 費用:{card_info['cost']} 攻擊:{card_info['atk']} 生命:{card_info['life']} 稀有度:{card_info['rarity']}")
        
    except Exception as e:
        print(f"搜尋時發生錯誤: {e}")

def example_multilingual_comparison():
    """多語言比較範例"""
    print("\n=== 多語言比較範例 ===")
    
    supabase = create_supabase_client()
    if not supabase:
        return
    
    try:
        # 獲取第一張非isToken卡片的多語言名稱
        card_result = supabase.table('cards').select('id').eq('is_token', False).limit(1).execute()
        
        if card_result.data:
            card_id = card_result.data[0]['id']
            
            # 獲取該卡片的所有語言名稱
            names_result = supabase.table('card_names').select('language, name').eq('card_id', card_id).execute()
            
            print(f"卡片 ID {card_id} 的多語言名稱:")
            lang_names = {'cht': '繁體中文', 'chs': '簡體中文', 'en': '英文', 'ja': '日文', 'ko': '韓文'}
            
            for name_info in names_result.data:
                lang = name_info['language']
                lang_display = lang_names.get(lang, lang)
                print(f"  {lang_display}: {name_info['name']}")
        
    except Exception as e:
        print(f"多語言比較時發生錯誤: {e}")

def example_advanced_queries():
    """進階查詢範例"""
    print("\n=== 進階查詢範例 ===")
    
    supabase = create_supabase_client()
    if not supabase:
        return
    
    try:
        # 1. 查詢高費用高攻擊力的卡片
        result = supabase.table('cards').select(
            'id, cost, atk, life, card_names!inner(name)'
        ).gte('cost', 7).gte('atk', 7).eq('card_names.language', 'cht').limit(5).execute()
        
        print("高費用高攻擊力卡片 (費用≥7, 攻擊≥7):")
        for card in result.data:
            name = card['card_names'][0]['name'] if card['card_names'] else '未知'
            print(f"  {name} - 費用:{card['cost']} 攻擊:{card['atk']} 生命:{card['life']}")
        
        # 2. 查詢有問答的卡片數量
        qa_result = supabase.table('card_questions').select('card_id', count='exact').execute()
        unique_cards = len(set(item['card_id'] for item in qa_result.data))
        print(f"\n有問答說明的卡片數量: {unique_cards} 張")
        
        # 3. 查詢最近的同步記錄
        sync_result = supabase.table('data_sync_logs').select(
            'language, sync_status, total_cards, successful_cards, created_at'
        ).order('created_at', desc=True).limit(5).execute()
        
        print("\n最近的同步記錄:")
        for log in sync_result.data:
            print(f"  {log['language']} - {log['sync_status']} - {log['successful_cards']}/{log['total_cards']} 張成功")
        
    except Exception as e:
        print(f"進階查詢時發生錯誤: {e}")

def example_card_details():
    """卡片詳細資訊範例"""
    print("\n=== 卡片詳細資訊範例 ===")
    
    supabase = create_supabase_client()
    if not supabase:
        return
    
    try:
        # 搜尋一張特定卡片的完整資訊
        card_name = "雙刃哥布林"
        
        # 先找到卡片ID
        name_result = supabase.table('card_names').select('card_id').eq('language', 'cht').eq('name', card_name).execute()
        
        if name_result.data:
            card_id = name_result.data[0]['card_id']
            
            # 獲取卡片基本資訊
            card_result = supabase.table('cards').select('*').eq('id', card_id).execute()
            
            # 獲取卡片描述
            desc_result = supabase.table('card_descriptions').select('*').eq('card_id', card_id).eq('language', 'cht').execute()
            
            # 獲取種族資訊
            tribe_result = supabase.table('card_tribes').select(
                'tribes(name_cht)'
            ).eq('card_id', card_id).execute()
            
            if card_result.data:
                card = card_result.data[0]
                print(f"卡片名稱: {card_name}")
                print(f"費用: {card['cost']}, 攻擊: {card['atk']}, 生命: {card['life']}")
                print(f"稀有度: {card['rarity']}, 職業: {card['class']}")
                
                if desc_result.data:
                    for desc in desc_result.data:
                        print(f"\n{desc['form']} 形態:")
                        if desc['skill_text']:
                            print(f"  技能: {desc['skill_text']}")
                        if desc['flavour_text']:
                            print(f"  風味文字: {desc['flavour_text']}")
                        if desc['cv']:
                            print(f"  CV: {desc['cv']}")
                        if desc['illustrator']:
                            print(f"  繪師: {desc['illustrator']}")
                
                if tribe_result.data:
                    tribes = [t['tribes']['name_cht'] for t in tribe_result.data if t['tribes']]
                    if tribes:
                        print(f"種族: {', '.join(tribes)}")
        else:
            print(f"找不到卡片: {card_name}")
        
    except Exception as e:
        print(f"查詢卡片詳細資訊時發生錯誤: {e}")

def main():
    """主函數"""
    print("Supabase 資料庫查詢範例")
    print("=" * 50)
    
    # 檢查配置
    if not load_config():
        return
    
    # 執行各種查詢範例
    example_basic_queries()
    example_card_search()
    example_multilingual_comparison()
    example_advanced_queries()
    example_card_details()
    
    print("\n查詢範例執行完成！")

if __name__ == "__main__":
    main()