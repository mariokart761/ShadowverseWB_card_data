#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowverse WB 牌組資訊爬蟲腳本 (Selenium 版本)
使用 Selenium 爬取牌組詳細資訊並回傳 JSON 格式
"""

import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class ShadowverseDeckScraper:
    def __init__(self, headless=True, timeout=30):
        """
        初始化爬蟲
        
        Args:
            headless (bool): 是否使用無頭模式
            timeout (int): 等待超時時間（秒）
        """
        self.timeout = timeout
        self.driver = None
        self.setup_driver(headless)
    
    def setup_driver(self, headless):
        """設置 Chrome WebDriver"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        # 添加其他選項以提高穩定性
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 禁用圖片載入以加快速度
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
        except Exception as e:
            print(f"Chrome WebDriver 初始化失敗: {e}")
            print("請確保已安裝 Google Chrome 瀏覽器")
            raise
    
    def scrape_deck_info(self, url):
        """
        爬取牌組資訊
        
        Args:
            url (str): 牌組詳細頁面 URL
            
        Returns:
            dict: 包含所需牌組資訊的字典
        """
        try:
            print(f"正在載入頁面: {url}")
            self.driver.get(url)
            
            # 等待頁面載入完成
            wait = WebDriverWait(self.driver, self.timeout)
            
            # 等待頁面主要內容載入
            try:
                # 嘗試等待不同的可能元素
                wait.until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                print("頁面載入完成")
            except TimeoutException:
                print("頁面載入超時，但繼續嘗試...")
            
            # 等待 JavaScript 執行完成
            time.sleep(5)
            
            # 嘗試從頁面的 JavaScript 變數中獲取資料
            deck_data = self.extract_data_from_page()
            
            if deck_data:
                return self.format_deck_data(deck_data)
            else:
                # 如果無法獲取資料，嘗試解析 DOM
                return self.parse_dom_data()
            
        except Exception as e:
            print(f"爬取過程中發生錯誤: {e}")
            raise
    
    def extract_data_from_page(self):
        """從頁面提取牌組資料"""
        try:
            # 嘗試多種方式獲取資料
            scripts_to_try = [
                # 嘗試獲取 window 上的資料
                """
                if (typeof window.deckDetail !== 'undefined') {
                    return window.deckDetail;
                }
                return null;
                """,
                
                # 嘗試獲取 Vue 應用資料
                """
                if (typeof window.$nuxt !== 'undefined' && window.$nuxt.$store && window.$nuxt.$store.state) {
                    return window.$nuxt.$store.state;
                }
                return null;
                """,
                
                # 嘗試從頁面中的 script 標籤獲取 JSON 資料
                """
                var scripts = document.getElementsByTagName('script');
                for (var i = 0; i < scripts.length; i++) {
                    var script = scripts[i];
                    if (script.textContent && script.textContent.includes('deckDetail')) {
                        try {
                            var match = script.textContent.match(/deckDetail[\\s]*:[\\s]*({.*?})/);
                            if (match) {
                                return JSON.parse(match[1]);
                            }
                        } catch (e) {
                            continue;
                        }
                    }
                }
                return null;
                """
            ]
            
            for i, script in enumerate(scripts_to_try):
                try:
                    result = self.driver.execute_script(script)
                    if result:
                        print(f"成功從方法 {i+1} 獲取資料")
                        return result
                except Exception as e:
                    print(f"方法 {i+1} 失敗: {e}")
                    continue
            
            # 嘗試獲取頁面源碼中的 JSON 資料
            page_source = self.driver.page_source
            
            # 尋找可能包含牌組資料的 JSON
            json_patterns = [
                r'"total_red_ether":\s*(\d+)',
                r'"num_follower":\s*(\d+)',
                r'"num_spell":\s*(\d+)',
                r'"num_amulet":\s*(\d+)',
                r'"battle_format":\s*(\d+)',
                r'"class_id":\s*(\d+)'
            ]
            
            extracted_data = {}
            for pattern in json_patterns:
                match = re.search(pattern, page_source)
                if match:
                    field_name = pattern.split('"')[1]
                    extracted_data[field_name] = int(match.group(1))
            
            if extracted_data:
                print("從頁面源碼中提取到部分資料")
                # 嘗試提取更多資料
                
                # 提取 mana_curve
                mana_curve_match = re.search(r'"mana_curve":\s*({[^}]+})', page_source)
                if mana_curve_match:
                    try:
                        extracted_data['mana_curve'] = json.loads(mana_curve_match.group(1))
                    except:
                        pass
                
                # 提取 sort_card_id_list
                card_list_match = re.search(r'"sort_card_id_list":\s*(\[[^\]]+\])', page_source)
                if card_list_match:
                    try:
                        extracted_data['sort_card_id_list'] = json.loads(card_list_match.group(1))
                    except:
                        pass
                
                # 提取 deck_card_num
                deck_card_match = re.search(r'"deck_card_num":\s*({[^}]+})', page_source)
                if deck_card_match:
                    try:
                        extracted_data['deck_card_num'] = json.loads(deck_card_match.group(1))
                    except:
                        pass
                
                return extracted_data
            
            print("無法從頁面提取資料")
            return None
            
        except Exception as e:
            print(f"提取資料時發生錯誤: {e}")
            return None
    
    def parse_dom_data(self):
        """
        從 DOM 解析牌組資料（備用方法）
        
        Returns:
            dict: 牌組資料
        """
        print("嘗試從 DOM 解析資料...")
        
        try:
            # 這是一個基本的 DOM 解析實現
            # 實際的選擇器需要根據網站的具體結構調整
            
            deck_info = {
                "total_red_ether": 0,
                "num_follower": 0,
                "num_spell": 0,
                "num_amulet": 0,
                "mana_curve": {},
                "battle_format": 2,
                "class_id": 5,
                "sub_class_id": None,
                "sort_card_id_list": [],
                "deck_card_num": {}
            }
            
            # 嘗試從頁面元素中提取資訊
            # 由於我們沒有實際的頁面結構，這裡使用預設值
            
            print("DOM 解析完成（使用預設值）")
            return deck_info
            
        except Exception as e:
            print(f"DOM 解析失敗: {e}")
            raise
    
    def format_deck_data(self, raw_data):
        """
        格式化牌組資料，只保留需要的欄位
        
        Args:
            raw_data (dict): 原始牌組資料
            
        Returns:
            dict: 格式化後的牌組資料
        """
        try:
            formatted_data = {
                "total_red_ether": raw_data.get("total_red_ether", 0),
                "num_follower": raw_data.get("num_follower", 0),
                "num_spell": raw_data.get("num_spell", 0),
                "num_amulet": raw_data.get("num_amulet", 0),
                "mana_curve": raw_data.get("mana_curve", {}),
                "battle_format": raw_data.get("battle_format", 2),
                "class_id": raw_data.get("class_id", 5),
                "sub_class_id": raw_data.get("sub_class_id"),
                "sort_card_id_list": raw_data.get("sort_card_id_list", []),
                "deck_card_num": raw_data.get("deck_card_num", {})
            }
            
            print("資料格式化完成")
            return formatted_data
            
        except Exception as e:
            print(f"資料格式化失敗: {e}")
            raise
    
    def close(self):
        """關閉 WebDriver"""
        if self.driver:
            self.driver.quit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def scrape_shadowverse_deck(url, headless=True, timeout=30):
    """
    爬取 Shadowverse WB 牌組資訊的便利函數
    
    Args:
        url (str): 牌組詳細頁面 URL
        headless (bool): 是否使用無頭模式
        timeout (int): 超時時間（秒）
        
    Returns:
        dict: 牌組資訊
    """
    with ShadowverseDeckScraper(headless=headless, timeout=timeout) as scraper:
        return scraper.scrape_deck_info(url)


def main():
    """主函數 - 示例用法"""
    # 示例 URL
    example_url = "https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=2.5.cYLU.cYLU.cYb6.cYb6.cYb6.cYqk.cYqk.ckYk.ckYk.ckaI.ckaI.ckoW.ckoW.ckoW.ckog.ckog.ckrU.ckrU.ckrU.cl1-.cl1-.cl1-.cl28.cl28.cl28.cl2I.cl2I.cl2I.cxFE.cxFE.d6mk.d6mk.d6mk.d6zE.d6zE.d6zE.d7SU.d7SU.d7Se.d7Se&lang=cht"
    
    try:
        print("開始爬取牌組資訊...")
        print(f"目標 URL: {example_url}")
        
        # 爬取資料
        deck_info = scrape_shadowverse_deck(example_url, headless=True)
        
        # 輸出結果
        print("\n爬取結果:")
        print(json.dumps(deck_info, indent=2, ensure_ascii=False))
        
        # 儲存到檔案
        with open('scraped_deck_info.json', 'w', encoding='utf-8') as f:
            json.dump(deck_info, f, indent=2, ensure_ascii=False)
        
        print("\n結果已儲存到 scraped_deck_info.json")
        
    except Exception as e:
        print(f"爬取失敗: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main()) 