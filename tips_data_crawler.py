#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowverse WB 系統Tips資料爬蟲
專門爬取系統通用的tips資訊，支援多語言，結果存至`./output/tips_data/tips_data_<lang>.json`。
"""

import os
import json
import time
import re
import glob
from pathlib import Path
from bs4 import BeautifulSoup
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def parse_tips_data(html):
    """解析系統通用的tips資訊"""
    soup = BeautifulSoup(html, 'html.parser')
    tips_list = []
    
    # 嘗試多個可能的選擇器
    tips_area = soup.select_one('#tips-list, .keyword-list, .tips-list')
    if tips_area:
        for li in tips_area.select('li, .keyword-line'):
            title = li.select_one('.title, .keyword')
            desc = li.select_one('.desc, .description')
            if title and desc:
                tips_list.append({
                    'title': title.text.strip(),
                    'desc': desc.text.strip()
                })
    return tips_list

def save_tips_data(tips_data, output_dir, lang_code):
    """儲存系統tips資料"""
    tips_file = output_dir / f'tips_data_{lang_code}.json'
    with open(tips_file, 'w', encoding='utf-8') as f:
        json.dump({
            'language': lang_code,
            'total': len(tips_data),
            'tips': tips_data
        }, f, ensure_ascii=False, indent=2)
    print(f"💡 系統Tips已儲存: {tips_file}")

def setup_selenium(headless=True):
    """設定Selenium WebDriver"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')  # 使用新版無頭模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--lang=zh-TW')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # 禁用圖片載入以加速
    chrome_options.add_argument('--disable-images')
    # 禁用擴充功能
    chrome_options.add_argument('--disable-extensions')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def crawl_tips_data(lang_code, sample_url, output_dir, headless=True):
    """爬取指定語言的系統tips資料"""
    print(f"\n==== {lang_code} 系統Tips爬取開始 ====")
    
    driver = setup_selenium(headless=headless)
    
    try:
        print(f"[{lang_code}] 正在訪問: {sample_url}")
        driver.get(sample_url)
        
        # 等待主要內容載入 - 嘗試多個可能的元素
        wait = WebDriverWait(driver, 15)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.sts-info')))
        except:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.card-details')))
            except:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#card-detail')))
        
        # 額外等待JavaScript渲染
        time.sleep(2)
        
        html = driver.page_source
        tips_data = parse_tips_data(html)
        
        if tips_data:
            save_tips_data(tips_data, output_dir, lang_code)
            print(f"[{lang_code}] 成功爬取 {len(tips_data)} 條Tips資料")
        else:
            print(f"[{lang_code}] 未找到Tips資料")
            
    except Exception as e:
        print(f"[{lang_code}] 爬取失敗: {e}")
    finally:
        driver.quit()
    
    print(f"==== {lang_code} 系統Tips爬取完成 ====")

def main():
    parser = argparse.ArgumentParser(description='Shadowverse WB 系統Tips爬蟲')
    parser.add_argument('--langs', nargs='+', help='指定語言代碼 (如 cht ja en chs ko)，預設全部')
    parser.add_argument('--output-dir', type=str, default='./output/tips_data', help='輸出資料夾')
    parser.add_argument('--no-headless', action='store_true', help='顯示瀏覽器視窗（預設為無頭模式）')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 如果直接指定URL，則爬取所有語言
    if args.langs:
        target_langs = args.langs
    else:
        target_langs = ['cht', 'ja', 'en', 'chs', 'ko']
    
    for lang_code in target_langs:
        sample_url = f"https://shadowverse-wb.com/{lang_code}/deck/cardslist/card/?card_id=10201110"
        
        if sample_url:
            crawl_tips_data(lang_code, sample_url, output_dir, headless=not args.no_headless)
        else:
            print(f"[Error] sample_url:{sample_url} 設定錯誤")

if __name__ == '__main__':
    main()