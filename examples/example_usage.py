#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowverse 爬蟲使用範例
"""

from shadowverse_simple_crawler import ShadowverseSimpleCrawler, crawl_single_language

def example_single_language():
    """範例：爬取單一語言"""
    print("=== 範例：爬取繁體中文卡牌資料 ===")
    
    # 爬取繁體中文資料
    data = crawl_single_language('cht')
    
    print(f"爬取完成，共 {data['data']['count']} 張卡片")
    print("檔案已儲存為: output/shadowverse_cards_cht.json")

def example_custom_crawler():
    """範例：自訂爬蟲設定"""
    print("\n=== 範例：自訂爬蟲設定 ===")
    
    # 建立英文版爬蟲
    crawler = ShadowverseSimpleCrawler('en')
    
    # 只獲取前 60 張卡片（前兩批）
    print("獲取前兩批資料...")
    
    for offset in [0, 30]:
        data = crawler.fetch_card_data(offset)
        if data:
            crawler.merge_data(data)
    
    print(f"獲取了 {crawler.complete_data['data']['count']} 張卡片")
    
    # 儲存到自訂檔案
    crawler.save_to_file("output/sample_cards_en.json")
    print("檔案已儲存為: output/sample_cards_en.json")

def example_compare_languages():
    """範例：比較不同語言的卡片名稱"""
    print("\n=== 範例：比較不同語言的卡片名稱 ===")
    
    languages = ['cht', 'en']
    card_names = {}
    
    for lang in languages:
        crawler = ShadowverseSimpleCrawler(lang)
        data = crawler.fetch_card_data(0)  # 只獲取第一批
        
        if data and 'data' in data:
            card_details = data['data'].get('card_details', {})
            if card_details:
                # 獲取第一張卡片的名稱
                first_card_id = list(card_details.keys())[0]
                first_card = card_details[first_card_id]
                card_name = first_card.get('common', {}).get('name', 'N/A')
                card_names[lang] = card_name
    
    if card_names:
        print("第一張卡片的不同語言名稱：")
        for lang, name in card_names.items():
            lang_display = {'cht': '繁體中文', 'en': '英文'}
            print(f"  {lang_display[lang]}: {name}")

def main():
    """執行所有範例"""
    print("Shadowverse 爬蟲使用範例")
    print("=" * 40)
    
    # 範例 1：爬取單一語言
    example_single_language()
    
    # 範例 2：自訂爬蟲設定
    example_custom_crawler()
    
    # 範例 3：比較不同語言
    example_compare_languages()
    
    print("\n所有範例執行完成！")

if __name__ == "__main__":
    main()