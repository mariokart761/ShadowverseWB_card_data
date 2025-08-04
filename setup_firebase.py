#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firebase 設定輔助腳本
自動安裝套件並設定 Firebase
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def install_requirements():
    """安裝必要套件"""
    print("正在安裝 Firebase 相關套件...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'firebase-admin>=6.4.0'])
        print("✓ Firebase Admin SDK 安裝完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 套件安裝失敗: {e}")
        return False

def create_config_file():
    """建立配置檔案"""
    config_path = Path('firebase/config.json')
    example_path = Path('firebase/config.example.json')
    
    if config_path.exists():
        print("✓ Firebase 配置檔案已存在")
        return True
    
    print("建立 Firebase 配置檔案...")
    print("\n請先完成以下步驟:")
    print("1. 前往 Firebase Console (https://console.firebase.google.com)")
    print("2. 建立新專案或選擇現有專案")
    print("3. 啟用 Firestore 資料庫")
    print("4. 前往「專案設定」>「服務帳戶」")
    print("5. 點擊「產生新的私密金鑰」下載 JSON 檔案")
    print("6. 將下載的 JSON 檔案放到專案目錄中")
    print()
    
    project_id = input("請輸入 Firebase Project ID: ").strip()
    service_account_path = input("請輸入服務帳戶金鑰檔案路徑: ").strip()
    
    if not all([project_id, service_account_path]):
        print("✗ 配置資訊不完整")
        return False
    
    # 檢查服務帳戶金鑰檔案是否存在
    if not os.path.exists(service_account_path):
        print(f"✗ 找不到服務帳戶金鑰檔案: {service_account_path}")
        return False
    
    config = {
        "project_id": project_id,
        "service_account_key_path": service_account_path
    }
    
    try:
        os.makedirs('firebase', exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✓ Firebase 配置檔案建立完成")
        return True
    except Exception as e:
        print(f"✗ 建立配置檔案失敗: {e}")
        return False

def test_firebase_connection():
    """測試 Firebase 連線"""
    print("測試 Firebase 連線...")
    
    try:
        from firebase.init_firebase import FirebaseInitializer
        
        initializer = FirebaseInitializer()
        if initializer.initialize_app():
            success = initializer.test_connection()
            return success
        else:
            return False
    except Exception as e:
        print(f"✗ 測試連線時發生錯誤: {e}")
        return False

def initialize_firebase():
    """初始化 Firebase"""
    print("初始化 Firebase 資料庫...")
    
    try:
        from firebase.init_firebase import FirebaseInitializer
        
        initializer = FirebaseInitializer()
        
        # 初始化應用程式
        if not initializer.initialize_app():
            return False
        
        # 測試連線
        if not initializer.test_connection():
            return False
        
        # 建立索引配置
        initializer.create_indexes()
        
        # 建立安全規則
        initializer.create_security_rules()
        
        # 詢問是否建立範例資料
        create_sample = input("\n是否建立範例資料? (y/N): ").lower() == 'y'
        if create_sample:
            initializer.create_sample_data()
        
        return True
    except Exception as e:
        print(f"✗ 初始化 Firebase 時發生錯誤: {e}")
        return False

def show_next_steps():
    """顯示後續步驟"""
    print("\n🎉 Firebase 設定完成！")
    print("\n後續步驟:")
    print("1. 安裝 Firebase CLI (如果尚未安裝):")
    print("   npm install -g firebase-tools")
    print()
    print("2. 登入 Firebase:")
    print("   firebase login")
    print()
    print("3. 初始化 Firebase 專案 (在專案根目錄執行):")
    print("   firebase init firestore")
    print()
    print("4. 部署 Firestore 規則和索引:")
    print("   firebase deploy --only firestore:rules,firestore:indexes")
    print()
    print("5. 開始同步卡牌資料:")
    print("   python firebase_sync.py")
    print()
    print("6. 查看查詢範例:")
    print("   python examples/firebase_queries.py")

def main():
    """主函數"""
    print("=== Firebase 設定輔助程式 ===")
    print()
    
    # 1. 安裝套件
    if not install_requirements():
        print("請手動安裝套件: pip install firebase-admin")
        return
    
    print()
    
    # 2. 建立配置檔案
    if not create_config_file():
        print("請手動建立配置檔案 firebase/config.json")
        return
    
    print()
    
    # 3. 測試連線
    if not test_firebase_connection():
        print("請檢查配置檔案中的連線資訊")
        return
    
    print()
    
    # 4. 初始化 Firebase
    if not initialize_firebase():
        print("Firebase 初始化失敗")
        return
    
    # 5. 顯示後續步驟
    show_next_steps()

if __name__ == "__main__":
    main()