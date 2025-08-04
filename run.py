#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowverse 爬蟲快速啟動腳本
"""

import sys
import os

def check_requirements():
    """檢查必要套件是否已安裝"""
    try:
        import requests
        print("✓ requests 套件已安裝")
        return True
    except ImportError:
        print("✗ 缺少 requests 套件")
        print("請執行: pip install requests")
        return False

def main():
    """主函數"""
    print("=== Shadowverse 卡牌資料爬蟲 ===")
    print()
    
    # 檢查套件
    if not check_requirements():
        return
    
    # 詢問使用者要執行哪個功能
    print("請選擇要執行的功能：")
    print("1. 執行測試（推薦新使用者）")
    print("2. 爬取所有語言的卡牌資料（cht, chs, en, ja, ko）")
    print("3. 爬取單一語言的卡牌資料")
    print("4. 退出")
    
    while True:
        choice = input("\n請輸入選項 (1-4): ").strip()
        
        if choice == "1":
            print("\n開始執行測試...")
            try:
                from test_crawler import main as test_main
                test_main()
            except Exception as e:
                print(f"測試執行失敗: {e}")
            break
            
        elif choice == "2":
            print("\n開始爬取所有語言的卡牌資料...")
            print("這將爬取 cht, chs, en, ja, ko 五種語言")
            print("預計需要 15-30 分鐘，請耐心等待...")
            try:
                from shadowverse_simple_crawler import main as crawler_main
                crawler_main()
            except Exception as e:
                print(f"爬蟲執行失敗: {e}")
            break
            
        elif choice == "3":
            print("\n請選擇要爬取的語言：")
            print("1. cht (繁體中文)")
            print("2. chs (簡體中文)")
            print("3. en (英文)")
            print("4. ja (日文)")
            print("5. ko (韓文)")
            
            lang_choice = input("請輸入語言選項 (1-5): ").strip()
            lang_map = {'1': 'cht', '2': 'chs', '3': 'en', '4': 'ja', '5': 'ko'}
            lang_names = {'cht': '繁體中文', 'chs': '簡體中文', 'en': '英文', 'ja': '日文', 'ko': '韓文'}
            
            if lang_choice in lang_map:
                selected_lang = lang_map[lang_choice]
                print(f"\n開始爬取 {selected_lang} ({lang_names[selected_lang]}) 語言的卡牌資料...")
                print("這可能需要 5-10 分鐘時間，請耐心等待...")
                try:
                    from shadowverse_simple_crawler import crawl_single_language
                    crawl_single_language(selected_lang)
                except Exception as e:
                    print(f"爬蟲執行失敗: {e}")
            else:
                print("無效的語言選項")
            break
            
        elif choice == "4":
            print("退出程式")
            break
            
        else:
            print("無效選項，請重新輸入")

if __name__ == "__main__":
    main()