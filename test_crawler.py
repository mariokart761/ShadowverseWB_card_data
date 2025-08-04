#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Shadowverse 爬蟲功能
"""

import json
from shadowverse_simple_crawler import ShadowverseSimpleCrawler

def test_single_request():
    """測試單一請求"""
    print("=== 測試單一請求 ===")
    
    # 測試繁體中文
    crawler = ShadowverseSimpleCrawler('cht')
    
    # 測試獲取第一批資料
    data = crawler.fetch_card_data(0)
    
    if data:
        print(f"✓ 成功獲取資料")
        print(f"  卡片數量: {len(data.get('data', {}).get('card_details', {}))}")
        print(f"  資料結構完整: {'data' in data and 'card_details' in data['data']}")
        
        # 顯示第一張卡片的資訊
        card_details = data.get('data', {}).get('card_details', {})
        if card_details:
            first_card_id = list(card_details.keys())[0]
            first_card = card_details[first_card_id]
            common = first_card.get('common', {})
            
            print(f"  第一張卡片:")
            print(f"    ID: {first_card_id}")
            print(f"    名稱: {common.get('name', 'N/A')}")
            print(f"    費用: {common.get('cost', 'N/A')}")
            print(f"    攻擊力: {common.get('atk', 'N/A')}")
            print(f"    生命值: {common.get('life', 'N/A')}")
        
        return True
    else:
        print("✗ 無法獲取資料")
        return False

def test_data_merge():
    """測試資料合併功能"""
    print("\n=== 測試資料合併功能 ===")
    
    crawler = ShadowverseSimpleCrawler('cht')
    
    # 獲取前兩批資料並合併
    data1 = crawler.fetch_card_data(0)
    data2 = crawler.fetch_card_data(30)
    
    if data1 and data2:
        initial_count = len(crawler.complete_data['data']['card_details'])
        print(f"初始卡片數量: {initial_count}")
        
        crawler.merge_data(data1)
        after_first = len(crawler.complete_data['data']['card_details'])
        print(f"合併第一批後: {after_first}")
        
        crawler.merge_data(data2)
        after_second = len(crawler.complete_data['data']['card_details'])
        print(f"合併第二批後: {after_second}")
        
        if after_second > after_first:
            print("✓ 資料合併功能正常")
            return True
        else:
            print("✗ 資料合併可能有問題")
            return False
    else:
        print("✗ 無法獲取測試資料")
        return False

def test_save_functionality():
    """測試儲存功能"""
    print("\n=== 測試儲存功能 ===")
    
    crawler = ShadowverseSimpleCrawler('cht')
    
    # 獲取一些資料
    data = crawler.fetch_card_data(0)
    if data:
        crawler.merge_data(data)
        
        # 測試儲存
        try:
            crawler.save_to_file("output/test_output.json")
            
            # 驗證檔案內容
            with open("output/test_output.json", 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            if 'data' in saved_data and 'card_details' in saved_data['data']:
                card_count = len(saved_data['data']['card_details'])
                print(f"✓ 成功儲存 {card_count} 張卡片到檔案")
                
                # 清理測試檔案
                import os
                os.remove("output/test_output.json")
                return True
            else:
                print("✗ 儲存的檔案格式不正確")
                return False
                
        except Exception as e:
            print(f"✗ 儲存失敗: {e}")
            return False
    else:
        print("✗ 無法獲取測試資料")
        return False

def test_multi_language():
    """測試多語言支援"""
    print("\n=== 測試多語言支援 ===")
    
    languages = ['cht', 'en']  # 只測試兩種語言以節省時間
    lang_names = {'cht': '繁體中文', 'en': '英文'}
    
    success_count = 0
    
    for lang in languages:
        try:
            print(f"測試 {lang} ({lang_names[lang]})...")
            crawler = ShadowverseSimpleCrawler(lang)
            data = crawler.fetch_card_data(0)
            
            if data and 'data' in data and data['data'].get('card_details'):
                card_details = data['data']['card_details']
                if card_details:
                    # 檢查第一張卡片的名稱
                    first_card = list(card_details.values())[0]
                    card_name = first_card.get('common', {}).get('name', '')
                    print(f"  ✓ 成功獲取 {lang} 資料，第一張卡片名稱: {card_name}")
                    success_count += 1
                else:
                    print(f"  ✗ {lang} 資料為空")
            else:
                print(f"  ✗ {lang} 無法獲取有效資料")
                
        except Exception as e:
            print(f"  ✗ {lang} 測試失敗: {e}")
    
    if success_count == len(languages):
        print("✓ 多語言支援測試通過")
        return True
    else:
        print(f"✗ 多語言測試部分失敗 ({success_count}/{len(languages)})")
        return False

def main():
    """執行所有測試"""
    print("開始測試 Shadowverse 爬蟲...")
    
    tests = [
        test_single_request,
        test_data_merge,
        test_save_functionality,
        test_multi_language
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ 測試執行時發生錯誤: {e}")
    
    print(f"\n=== 測試結果 ===")
    print(f"通過: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有測試通過！爬蟲應該可以正常運作。")
    else:
        print("✗ 部分測試失敗，請檢查網路連線或網站狀態。")

if __name__ == "__main__":
    main()