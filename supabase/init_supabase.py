#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 資料庫初始化腳本
執行 SQL 腳本來建立資料庫結構
"""

import os
import sys
import json
import asyncio
import asyncpg
from pathlib import Path

async def execute_sql_file(database_url: str, sql_file: str):
    """執行 SQL 檔案"""
    print(f"正在執行 {sql_file}...")
    
    try:
        # 讀取 SQL 檔案
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 連接資料庫
        conn = await asyncpg.connect(database_url)
        
        try:
            # 執行 SQL
            await conn.execute(sql_content)
            print(f"✓ {sql_file} 執行成功")
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"✗ 執行 {sql_file} 時發生錯誤: {e}")
        raise

async def init_database():
    """初始化資料庫"""
    print("=== Supabase 資料庫初始化 ===")
    
    # 載入配置
    config_file = 'supabase/config.json'
    
    if not os.path.exists(config_file):
        print(f"找不到配置檔案: {config_file}")
        print("請複製 supabase/config.example.json 為 supabase/config.json 並填入正確的配置")
        return False
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    database_url = config.get('database_url')
    if not database_url:
        print("配置檔案中缺少 database_url")
        return False
    
    # 執行 schema.sql
    schema_file = 'supabase/schema.sql'
    if not os.path.exists(schema_file):
        print(f"找不到 SQL 檔案: {schema_file}")
        return False
    
    try:
        await execute_sql_file(database_url, schema_file)
        print("\n✓ 資料庫初始化完成！")
        print("現在可以執行 database_sync.py 來同步卡牌資料")
        return True
        
    except Exception as e:
        print(f"\n✗ 資料庫初始化失敗: {e}")
        return False

async def check_database_connection():
    """檢查資料庫連線"""
    print("檢查資料庫連線...")
    
    config_file = 'supabase/config.json'
    if not os.path.exists(config_file):
        print("找不到配置檔案")
        return False
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    database_url = config.get('database_url')
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # 執行簡單查詢
        result = await conn.fetchval('SELECT version()')
        print(f"✓ 資料庫連線成功")
        print(f"PostgreSQL 版本: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 資料庫連線失敗: {e}")
        return False

async def main():
    """主函數"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'check':
            await check_database_connection()
        elif command == 'init':
            await init_database()
        else:
            print("使用方法:")
            print("  python supabase/init_supabase.py check  # 檢查資料庫連線")
            print("  python supabase/init_supabase.py init   # 初始化資料庫結構")
    else:
        print("使用方法:")
        print("  python supabase/init_supabase.py check  # 檢查資料庫連線")
        print("  python supabase/init_supabase.py init   # 初始化資料庫結構")

if __name__ == "__main__":
    asyncio.run(main())