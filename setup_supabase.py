#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫設定輔助腳本
自動安裝套件並設定資料庫
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def install_requirements():
    """安裝必要套件"""
    print("正在安裝資料庫相關套件...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'supabase>=2.3.0', 'asyncpg>=0.29.0'])
        print("✓ 套件安裝完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 套件安裝失敗: {e}")
        return False

def create_config_file():
    """建立配置檔案"""
    config_path = Path('supabase/config.json')
    example_path = Path('supabase/config.example.json')
    
    if config_path.exists():
        print("✓ 配置檔案已存在")
        return True
    
    if not example_path.exists():
        print("✗ 找不到配置範例檔案")
        return False
    
    print("建立配置檔案...")
    print("請輸入您的 Supabase 資訊:")
    
    supabase_url = input("Supabase URL: ").strip()
    supabase_key = input("Supabase Key: ").strip()
    database_url = input("Database URL: ").strip()
    
    if not all([supabase_url, supabase_key, database_url]):
        print("✗ 配置資訊不完整")
        return False
    
    config = {
        "supabase_url": supabase_url,
        "supabase_key": supabase_key,
        "database_url": database_url
    }
    
    try:
        os.makedirs('supabase', exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✓ 配置檔案建立完成")
        return True
    except Exception as e:
        print(f"✗ 建立配置檔案失敗: {e}")
        return False

def check_database_connection():
    """檢查資料庫連線"""
    print("檢查資料庫連線...")
    
    try:
        import asyncio
        from supabase.init_supabase import check_database_connection
        
        result = asyncio.run(check_database_connection())
        return result
    except Exception as e:
        print(f"✗ 檢查連線時發生錯誤: {e}")
        return False

def initialize_database():
    """初始化資料庫"""
    print("初始化資料庫結構...")
    
    try:
        import asyncio
        from supabase.init_supabase import init_database
        
        result = asyncio.run(init_database())
        return result
    except Exception as e:
        print(f"✗ 初始化資料庫時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("=== Shadowverse 資料庫設定輔助程式 ===")
    print()
    
    # 1. 安裝套件
    if not install_requirements():
        print("請手動安裝套件: pip install supabase asyncpg")
        return
    
    print()
    
    # 2. 建立配置檔案
    if not create_config_file():
        print("請手動建立配置檔案 supabase/config.json")
        return
    
    print()
    
    # 3. 檢查連線
    if not check_database_connection():
        print("請檢查配置檔案中的連線資訊")
        return
    
    print()
    
    # 4. 初始化資料庫
    if not initialize_database():
        print("資料庫初始化失敗")
        return
    
    print()
    print("🎉 資料庫設定完成！")
    print("現在可以執行以下命令:")
    print("  python supabase_sync.py          # 同步卡牌資料")
    print("  python examples/supabase_queries.py  # 查詢範例")

if __name__ == "__main__":
    main()