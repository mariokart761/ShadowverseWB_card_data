#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firebase 初始化腳本
設定 Firestore 資料庫和安全規則
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("請先安裝 Firebase Admin SDK: pip install firebase-admin")
    sys.exit(1)

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FirebaseInitializer:
    """Firebase 初始化器"""
    
    def __init__(self, config_path: str = 'firebase/config.json'):
        self.config_path = config_path
        self.app = None
        self.db = None
        
    def load_config(self) -> Dict[str, Any]:
        """載入 Firebase 配置"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"找不到配置檔案: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def initialize_app(self) -> bool:
        """初始化 Firebase 應用程式"""
        try:
            config = self.load_config()
            
            # 檢查服務帳戶金鑰檔案
            service_account_path = config.get('service_account_key_path')
            if not service_account_path or not os.path.exists(service_account_path):
                raise FileNotFoundError(f"找不到服務帳戶金鑰檔案: {service_account_path}")
            
            # 初始化 Firebase Admin SDK
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_path)
                self.app = firebase_admin.initialize_app(cred, {
                    'projectId': config.get('project_id')
                })
            
            # 獲取 Firestore 客戶端
            self.db = firestore.client()
            
            logger.info("✓ Firebase 初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"✗ Firebase 初始化失敗: {e}")
            return False
    
    def create_indexes(self) -> bool:
        """建立 Firestore 索引 (需要手動在 Firebase Console 建立)"""
        logger.info("建立 Firestore 索引...")
        
        # Firestore 索引需要在 Firebase Console 手動建立，或使用 Firebase CLI
        # 這裡提供索引配置資訊
        indexes_config = {
            "indexes": [
                {
                    "collectionGroup": "cards",
                    "queryScope": "COLLECTION",
                    "fields": [
                        {"fieldPath": "class", "order": "ASCENDING"},
                        {"fieldPath": "cost", "order": "ASCENDING"}
                    ]
                },
                {
                    "collectionGroup": "cards",
                    "queryScope": "COLLECTION",
                    "fields": [
                        {"fieldPath": "rarity", "order": "ASCENDING"},
                        {"fieldPath": "class", "order": "ASCENDING"}
                    ]
                },
                {
                    "collectionGroup": "cards",
                    "queryScope": "COLLECTION",
                    "fields": [
                        {"fieldPath": "cardSetId", "order": "ASCENDING"},
                        {"fieldPath": "class", "order": "ASCENDING"}
                    ]
                },
                {
                    "collectionGroup": "cards",
                    "queryScope": "COLLECTION",
                    "fields": [
                        {"fieldPath": "isToken", "order": "ASCENDING"},
                        {"fieldPath": "isIncludeRotation", "order": "ASCENDING"}
                    ]
                },
                {
                    "collectionGroup": "syncLogs",
                    "queryScope": "COLLECTION",
                    "fields": [
                        {"fieldPath": "language", "order": "ASCENDING"},
                        {"fieldPath": "createdAt", "order": "DESCENDING"}
                    ]
                },
                {
                    "collectionGroup": "syncLogs",
                    "queryScope": "COLLECTION",
                    "fields": [
                        {"fieldPath": "syncStatus", "order": "ASCENDING"},
                        {"fieldPath": "createdAt", "order": "DESCENDING"}
                    ]
                }
            ],
            "fieldOverrides": [
                {
                    "collectionGroup": "cards",
                    "fieldPath": "tribes",
                    "indexes": [
                        {"arrayConfig": "CONTAINS", "queryScope": "COLLECTION"}
                    ]
                },
                {
                    "collectionGroup": "cards",
                    "fieldPath": "relatedCards",
                    "indexes": [
                        {"arrayConfig": "CONTAINS", "queryScope": "COLLECTION"}
                    ]
                }
            ]
        }
        
        # 儲存索引配置到檔案
        indexes_file = 'firebase/firestore.indexes.json'
        os.makedirs('firebase', exist_ok=True)
        
        with open(indexes_file, 'w', encoding='utf-8') as f:
            json.dump(indexes_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ 索引配置已儲存到 {indexes_file}")
        logger.info("請使用 Firebase CLI 部署索引:")
        logger.info("  firebase deploy --only firestore:indexes")
        
        return True
    
    def create_security_rules(self) -> bool:
        """建立 Firestore 安全規則檔案"""
        logger.info("建立 Firestore 安全規則...")
        
        rules_content = '''rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 卡片資料 - 讀取公開，寫入需要認證
    match /cards/{cardId} {
      allow read: if true;
      allow write: if request.auth != null;
      
      // 卡片問答子集合
      match /questions/{questionId} {
        allow read: if true;
        allow write: if request.auth != null;
      }
      
      // 卡片風格變體子集合
      match /styles/{styleId} {
        allow read: if true;
        allow write: if request.auth != null;
      }
    }
    
    // 卡包資料 - 讀取公開，寫入需要認證
    match /cardSets/{setId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    
    // 種族資料 - 讀取公開，寫入需要認證
    match /tribes/{tribeId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    
    // 技能資料 - 讀取公開，寫入需要認證
    match /skills/{skillId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    
    // 同步記錄 - 需要認證
    match /syncLogs/{logId} {
      allow read, write: if request.auth != null;
    }
  }
}'''
        
        rules_file = 'firebase/firestore.rules'
        with open(rules_file, 'w', encoding='utf-8') as f:
            f.write(rules_content)
        
        logger.info(f"✓ 安全規則已儲存到 {rules_file}")
        logger.info("請使用 Firebase CLI 部署安全規則:")
        logger.info("  firebase deploy --only firestore:rules")
        
        return True
    
    def test_connection(self) -> bool:
        """測試 Firestore 連線"""
        logger.info("測試 Firestore 連線...")
        
        try:
            # 嘗試讀取一個不存在的文件來測試連線
            test_ref = self.db.collection('test').document('connection_test')
            test_ref.get()
            
            logger.info("✓ Firestore 連線測試成功")
            return True
            
        except Exception as e:
            logger.error(f"✗ Firestore 連線測試失敗: {e}")
            return False
    
    def create_sample_data(self) -> bool:
        """建立範例資料"""
        logger.info("建立範例資料...")
        
        try:
            # 建立範例卡包
            card_set_ref = self.db.collection('cardSets').document('1')
            card_set_ref.set({
                'id': 1,
                'names': {
                    'cht': '基本卡包',
                    'chs': '基本卡包',
                    'en': 'Basic Set',
                    'ja': 'ベーシックセット',
                    'ko': '기본 세트'
                },
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            })
            
            # 建立範例種族
            tribe_ref = self.db.collection('tribes').document('1')
            tribe_ref.set({
                'id': 1,
                'names': {
                    'cht': '天使',
                    'chs': '天使',
                    'en': 'Angel',
                    'ja': '天使',
                    'ko': '천사'
                },
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            })
            
            # 建立範例技能
            skill_ref = self.db.collection('skills').document('1')
            skill_ref.set({
                'id': 1,
                'names': {
                    'cht': '守護',
                    'chs': '守护',
                    'en': 'Ward',
                    'ja': '守護',
                    'ko': '수호'
                },
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            })
            
            # 建立範例卡片
            card_ref = self.db.collection('cards').document('900011010')
            card_ref.set({
                'id': 900011010,
                'baseCardId': 900011010,
                'cardResourceId': 900011010,
                'cardSetId': 1,
                'type': 1,  # 從者
                'class': 0,  # 中立
                'cost': 2,
                'atk': 2,
                'life': 1,
                'rarity': 1,  # 銅
                'isToken': False,
                'isIncludeRotation': True,
                'cardImageHash': 'sample_hash',
                'cardBannerImageHash': 'sample_banner_hash',
                'names': {
                    'cht': {'name': '雙刃哥布林', 'nameRuby': ''},
                    'chs': {'name': '双刃哥布林', 'nameRuby': ''},
                    'en': {'name': 'Goblin', 'nameRuby': ''},
                    'ja': {'name': 'ゴブリン', 'nameRuby': ''},
                    'ko': {'name': '고블린', 'nameRuby': ''}
                },
                'descriptions': {
                    'cht': {
                        'common': {
                            'flavourText': '最普通的哥布林。',
                            'skillText': '',
                            'cv': '',
                            'illustrator': '範例繪師'
                        }
                    }
                },
                'tribes': [1],
                'relatedCards': [],
                'specificEffectCards': [],
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            })
            
            logger.info("✓ 範例資料建立成功")
            return True
            
        except Exception as e:
            logger.error(f"✗ 建立範例資料失敗: {e}")
            return False

def create_config_file():
    """建立配置檔案"""
    config_path = 'firebase/config.json'
    example_path = 'firebase/config.example.json'
    
    if os.path.exists(config_path):
        print("✓ Firebase 配置檔案已存在")
        return True
    
    print("建立 Firebase 配置檔案...")
    print("請輸入您的 Firebase 專案資訊:")
    
    project_id = input("Firebase Project ID: ").strip()
    service_account_path = input("服務帳戶金鑰檔案路徑: ").strip()
    
    if not all([project_id, service_account_path]):
        print("✗ 配置資訊不完整")
        return False
    
    config = {
        "project_id": project_id,
        "service_account_key_path": service_account_path
    }
    
    try:
        os.makedirs('firebase', exist_ok=True)
        
        # 建立配置檔案
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 建立範例配置檔案
        example_config = {
            "project_id": "your-firebase-project-id",
            "service_account_key_path": "path/to/your/service-account-key.json"
        }
        
        with open(example_path, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=2, ensure_ascii=False)
        
        print("✓ Firebase 配置檔案建立完成")
        return True
        
    except Exception as e:
        print(f"✗ 建立配置檔案失敗: {e}")
        return False

def main():
    """主函數"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'config':
            create_config_file()
            return
        
        elif command == 'init':
            initializer = FirebaseInitializer()
            
            print("=== Firebase 初始化 ===")
            
            # 初始化應用程式
            if not initializer.initialize_app():
                return
            
            # 測試連線
            if not initializer.test_connection():
                return
            
            # 建立索引配置
            initializer.create_indexes()
            
            # 建立安全規則
            initializer.create_security_rules()
            
            # 建立範例資料
            if input("\n是否建立範例資料? (y/N): ").lower() == 'y':
                initializer.create_sample_data()
            
            print("\n🎉 Firebase 初始化完成！")
            print("接下來請執行:")
            print("  firebase deploy --only firestore:indexes,firestore:rules")
            print("  python firebase_sync.py")
            
        elif command == 'test':
            initializer = FirebaseInitializer()
            if initializer.initialize_app():
                initializer.test_connection()
        
        else:
            print_usage()
    else:
        print_usage()

def print_usage():
    """顯示使用說明"""
    print("Firebase 初始化工具")
    print("使用方法:")
    print("  python firebase/init_firebase.py config  # 建立配置檔案")
    print("  python firebase/init_firebase.py init    # 初始化 Firebase")
    print("  python firebase/init_firebase.py test    # 測試連線")

if __name__ == "__main__":
    main()