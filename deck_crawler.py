#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowverse WB 牌組資訊爬蟲腳本 (簡化版本)
直接從 JSON API 獲取牌組資訊，移除 Selenium 依賴
"""

import json
import requests
import re
from urllib.parse import urlparse, parse_qs
import time


class ShadowverseDeckScraperSimple:
    def __init__(self, timeout=30):
        """
        初始化簡化爬蟲

        Args:
            timeout (int): 請求超時時間（秒）
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def scrape_deck_info(self, url):
        """
        從 JSON API 或 HTML 頁面獲取牌組資訊

        Args:
            url (str): 牌組詳細頁面 URL

        Returns:
            dict: 包含所需牌組資訊的字典
        """
        try:
            print(f"正在請求 API: {url}")

            # 發送請求獲取數據
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # 首先嘗試直接解析為 JSON（如果響應是純 JSON）
            try:
                deck_data = response.json()
                print("成功獲取純 JSON 數據")
                print(f"JSON 數據內容: {deck_data}")
                return self.format_deck_data(deck_data)
            except json.JSONDecodeError:
                print("響應不是純 JSON，嘗試從 HTML 中提取 JSON 數據")
                print(f"響應內容前 200 字符: {response.text[:200]}")
                # 如果不是純 JSON，嘗試從 HTML 中提取
                return self.extract_json_from_html(response.text)

        except requests.exceptions.RequestException as e:
            print(f"請求失敗: {e}")
            raise
        except Exception as e:
            print(f"處理過程中發生錯誤: {e}")
            raise

    def extract_json_from_html(self, html_content):
        """
        從 HTML 內容中提取 JSON 數據

        Args:
            html_content (str): HTML 頁面內容

        Returns:
            dict: 提取並格式化後的牌組資料
        """
        try:
            # 尋找可能包含牌組資料的 JSON 模式
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
                match = re.search(pattern, html_content)
                if match:
                    field_name = pattern.split('"')[1]
                    extracted_data[field_name] = int(match.group(1))

            if extracted_data:
                print("從 HTML 中提取到基本資料")

                # 嘗試提取更多複雜數據
                self.extract_complex_data(html_content, extracted_data)

                return self.format_deck_data(extracted_data)
            else:
                print("無法從 HTML 中提取資料")
                raise Exception("無法從 HTML 內容中提取牌組資料")

        except Exception as e:
            print(f"HTML 解析失敗: {e}")
            raise

    def extract_complex_data(self, html_content, extracted_data):
        """
        提取複雜的數據結構

        Args:
            html_content (str): HTML 內容
            extracted_data (dict): 已提取的基本數據
        """
        # 提取 mana_curve
        mana_curve_match = re.search(r'"mana_curve":\s*({[^}]+})', html_content)
        if mana_curve_match:
            try:
                extracted_data['mana_curve'] = json.loads(mana_curve_match.group(1))
            except:
                extracted_data['mana_curve'] = {}

        # 提取 sort_card_id_list
        card_list_match = re.search(r'"sort_card_id_list":\s*(\[[^\]]+\])', html_content)
        if card_list_match:
            try:
                extracted_data['sort_card_id_list'] = json.loads(card_list_match.group(1))
            except:
                extracted_data['sort_card_id_list'] = []

        # 提取 deck_card_num
        deck_card_match = re.search(r'"deck_card_num":\s*({[^}]+})', html_content)
        if deck_card_match:
            try:
                extracted_data['deck_card_num'] = json.loads(deck_card_match.group(1))
            except:
                extracted_data['deck_card_num'] = {}

    def format_deck_data(self, raw_data):
        """
        格式化牌組資料，只保留需要的欄位

        Args:
            raw_data (dict): 原始 JSON 數據

        Returns:
            dict: 格式化後的牌組資料
        """
        try:
            # 檢查數據結構類型
            if 'data' in raw_data and isinstance(raw_data['data'], dict):
                # 新版 API 結構
                data = raw_data['data']
                print("檢測到新版 API 數據結構")

                # 從 deck_card_num 計算卡牌統計
                deck_card_num = data.get('deck_card_num', {})
                sort_card_id_list = data.get('sort_card_id_list', [])

                # 計算各類型卡牌數量
                num_follower = 0
                num_spell = 0
                num_amulet = 0
                mana_curve = {}

                for card_id in sort_card_id_list:
                    if str(card_id) in deck_card_num:
                        count = deck_card_num[str(card_id)]
                        # 從 card_details 中獲取卡牌信息
                        card_details = data.get('card_details', {}).get(str(card_id), {})
                        card_common = card_details.get('common', {})

                        # 判斷卡牌類型
                        card_type = card_common.get('type', 0)
                        if card_type == 1:  # 從者
                            num_follower += count
                        elif card_type == 4:  # 法術
                            num_spell += count
                        elif card_type == 2 or card_type == 3:  # 護符
                            num_amulet += count

                        # 計算法力曲線
                        cost = card_common.get('cost', 0)
                        if cost in mana_curve:
                            mana_curve[cost] += count
                        else:
                            mana_curve[cost] = count

                formatted_data = {
                    "total_red_ether": 0,  # API 沒有提供這個數據
                    "num_follower": num_follower,
                    "num_spell": num_spell,
                    "num_amulet": num_amulet,
                    "mana_curve": mana_curve,
                    "battle_format": 2,  # 默認值
                    "class_id": -1,  # 默認值
                    "sub_class_id": None,
                    "sort_card_id_list": sort_card_id_list,
                    "deck_card_num": deck_card_num
                }

            else:
                # 舊版或兼容結構
                print("使用兼容模式處理數據")
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
        """關閉會話"""
        if self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def scrape_shadowverse_deck_simple(url, timeout=30):
    """
    爬取 Shadowverse WB 牌組資訊的簡化便利函數

    Args:
        url (str): 牌組詳細頁面 URL
        timeout (int): 超時時間（秒）

    Returns:
        dict: 牌組資訊
    """
    with ShadowverseDeckScraperSimple(timeout=timeout) as scraper:
        return scraper.scrape_deck_info(url)


def extract_deck_hash_from_url(url):
    """
    從 URL 中提取牌組 hash

    Args:
        url (str): 牌組 URL

    Returns:
        str: 牌組 hash，如果無法提取則返回 None
    """
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return query_params.get('hash', [None])[0]
    except Exception as e:
        print(f"提取 hash 失敗: {e}")
        return None


def main():
    """主函數 - 示例用法"""
    # 示例 URL
    example_url = "https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=2.5.cYLU.cYLU.cYb6.cYb6.cYb6.cYqk.cYqk.ckYk.ckYk.ckaI.ckaI.ckoW.ckoW.ckoW.ckog.ckog.ckrU.ckrU.ckrU.cl1-.cl1-.cl1-.cl28.cl28.cl28.cl2I.cl2I.cl2I.cxFE.cxFE.d6mk.d6mk.d6mk.d6zE.d6zE.d6zE.d7SU.d7SU.d7Se.d7Se&lang=cht"

    try:
        print("開始爬取牌組資訊...")
        print(f"目標 URL: {example_url}")

        # 提取並顯示牌組 hash
        deck_hash = extract_deck_hash_from_url(example_url)
        if deck_hash:
            print(f"牌組 Hash: {deck_hash}")

        # 爬取資料
        deck_info = scrape_shadowverse_deck_simple(example_url)

        # 輸出結果
        print("\n爬取結果:")
        print(json.dumps(deck_info, indent=2, ensure_ascii=False))

        # 儲存到檔案
        with open('scraped_deck_info_simple.json', 'w', encoding='utf-8') as f:
            json.dump(deck_info, f, indent=2, ensure_ascii=False)

        print("\n結果已儲存到 scraped_deck_info_simple.json")

    except Exception as e:
        print(f"爬取失敗: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
