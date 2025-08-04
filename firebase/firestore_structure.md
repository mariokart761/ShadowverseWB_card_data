# Firebase Firestore 資料結構設計

## 概述

Firebase Firestore 是 NoSQL 文件資料庫，採用集合(Collection)和文件(Document)的結構。
以下是 Shadowverse 卡牌資料的 Firestore 設計方案。

## 主要集合結構

### 1. cards (卡片主集合)
```
cards/
├── {cardId}/
│   ├── id: number
│   ├── baseCardId: number
│   ├── cardResourceId: number
│   ├── cardSetId: number
│   ├── type: number (1:從者, 2:護符, 3:建築物, 4:法術)
│   ├── class: number (0:中立, 1:精靈, ...)
│   ├── cost: number
│   ├── atk: number
│   ├── life: number
│   ├── rarity: number (1:銅, 2:銀, 3:金, 4:虹)
│   ├── isToken: boolean
│   ├── isIncludeRotation: boolean
│   ├── cardImageHash: string
│   ├── cardBannerImageHash: string
│   ├── createdAt: timestamp
│   ├── updatedAt: timestamp
│   ├── names: {
│   │   ├── cht: { name: string, nameRuby: string }
│   │   ├── chs: { name: string, nameRuby: string }
│   │   ├── en: { name: string, nameRuby: string }
│   │   ├── ja: { name: string, nameRuby: string }
│   │   └── ko: { name: string, nameRuby: string }
│   │   }
│   ├── descriptions: {
│   │   ├── cht: {
│   │   │   ├── common: { flavourText, skillText, cv, illustrator }
│   │   │   └── evo: { flavourText, skillText, cv, illustrator }
│   │   │   }
│   │   ├── chs: { ... }
│   │   ├── en: { ... }
│   │   ├── ja: { ... }
│   │   └── ko: { ... }
│   │   }
│   ├── evolution: {
│   │   ├── cardResourceId: number
│   │   ├── cardImageHash: string
│   │   └── cardBannerImageHash: string
│   │   }
│   ├── tribes: [number] (種族ID陣列)
│   ├── relatedCards: [number] (相關卡片ID陣列)
│   ├── specificEffectCards: [number] (特效相關卡片ID陣列)
│   └── subcollections/
│       ├── questions/ (問答子集合)
│       └── styles/ (風格變體子集合)
```

### 2. cardSets (卡包集合)
```
cardSets/
├── {setId}/
│   ├── id: number
│   ├── names: {
│   │   ├── cht: string
│   │   ├── chs: string
│   │   ├── en: string
│   │   ├── ja: string
│   │   └── ko: string
│   │   }
│   ├── createdAt: timestamp
│   └── updatedAt: timestamp
```

### 3. tribes (種族集合)
```
tribes/
├── {tribeId}/
│   ├── id: number
│   ├── names: {
│   │   ├── cht: string
│   │   ├── chs: string
│   │   ├── en: string
│   │   ├── ja: string
│   │   └── ko: string
│   │   }
│   ├── createdAt: timestamp
│   └── updatedAt: timestamp
```

### 4. skills (技能集合)
```
skills/
├── {skillId}/
│   ├── id: number
│   ├── names: {
│   │   ├── cht: string
│   │   ├── chs: string
│   │   ├── en: string
│   │   ├── ja: string
│   │   └── ko: string
│   │   }
│   ├── createdAt: timestamp
│   └── updatedAt: timestamp
```

### 5. syncLogs (同步記錄集合)
```
syncLogs/
├── {logId}/
│   ├── language: string
│   ├── totalCards: number
│   ├── successfulCards: number
│   ├── failedCards: number
│   ├── syncStatus: string (success, partial, failed, running)
│   ├── errorMessage: string
│   ├── startedAt: timestamp
│   ├── completedAt: timestamp
│   └── createdAt: timestamp
```

## 子集合結構

### cards/{cardId}/questions (卡片問答子集合)
```
questions/
├── {questionId}/
│   ├── language: string
│   ├── question: string
│   ├── answer: string
│   └── createdAt: timestamp
```

### cards/{cardId}/styles (卡片風格變體子集合)
```
styles/
├── {styleId}/
│   ├── hash: string
│   ├── evoHash: string
│   ├── name: string
│   ├── nameRuby: string
│   ├── cv: string
│   ├── illustrator: string
│   ├── skillText: string
│   ├── flavourText: string
│   ├── evoFlavourText: string
│   └── createdAt: timestamp
```

## 索引設計

### 複合索引 (Composite Indexes)
1. `cards` 集合:
   - `class` (升序) + `cost` (升序)
   - `rarity` (升序) + `class` (升序)
   - `cardSetId` (升序) + `class` (升序)
   - `isToken` (升序) + `isIncludeRotation` (升序)
   - `names.cht.name` (升序) - 用於名稱搜尋

2. `syncLogs` 集合:
   - `language` (升序) + `createdAt` (降序)
   - `syncStatus` (升序) + `createdAt` (降序)

### 陣列包含索引 (Array Contains)
- `cards.tribes` - 用於種族查詢
- `cards.relatedCards` - 用於相關卡片查詢

## 安全規則範例

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 卡片資料 - 讀取公開，寫入需要認證
    match /cards/{cardId} {
      allow read: if true;
      allow write: if request.auth != null;
      
      // 子集合規則
      match /questions/{questionId} {
        allow read: if true;
        allow write: if request.auth != null;
      }
      
      match /styles/{styleId} {
        allow read: if true;
        allow write: if request.auth != null;
      }
    }
    
    // 參考資料 - 讀取公開，寫入需要認證
    match /cardSets/{setId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    
    match /tribes/{tribeId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    
    match /skills/{skillId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    
    // 同步記錄 - 需要認證
    match /syncLogs/{logId} {
      allow read, write: if request.auth != null;
    }
  }
}
```

## 查詢範例

### 基本查詢
```python
# 查詢特定職業的卡片
cards_ref.where('class', '==', 1).limit(10).get()

# 查詢特定費用範圍的卡片
cards_ref.where('cost', '>=', 5).where('cost', '<=', 7).get()

# 查詢包含特定種族的卡片
cards_ref.where('tribes', 'array_contains', 1).get()
```

### 複合查詢
```python
# 查詢特定職業和稀有度的卡片
cards_ref.where('class', '==', 1).where('rarity', '==', 4).get()

# 查詢非代幣且在輪替制的卡片
cards_ref.where('isToken', '==', False).where('isIncludeRotation', '==', True).get()
```

### 文字搜尋 (需要額外處理)
由於 Firestore 不支援全文搜尋，需要使用以下方法之一：
1. 使用 Firebase Extensions 的 Algolia 搜尋
2. 建立搜尋索引欄位
3. 使用客戶端過濾

## 優勢
1. **彈性結構**: NoSQL 設計，易於擴展
2. **即時同步**: 支援即時資料更新
3. **自動擴展**: 無需管理伺服器
4. **安全規則**: 細緻的存取控制
5. **離線支援**: 客戶端快取和離線功能

## 注意事項
1. **查詢限制**: 複合查詢需要建立索引
2. **成本考量**: 讀寫操作和儲存成本
3. **文件大小**: 單一文件最大 1MB
4. **陣列查詢**: array-contains 查詢的限制
5. **交易限制**: 批次寫入最多 500 個操作