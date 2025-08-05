#!/usr/bin/env node
/**
 * Firebase Firestore 查詢範例 (JavaScript 版本)
 * 
 * 這個腳本示範如何使用 JavaScript 查詢 Firebase Firestore 中的 Shadowverse 卡片資料
 */

import admin from 'firebase-admin';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 載入配置檔案
 */
function loadConfig() {
    const configPath = path.join(__dirname, 'config.json');
    
    if (fs.existsSync(configPath)) {
        const configData = fs.readFileSync(configPath, 'utf8');
        return JSON.parse(configData);
    } else {
        console.log('找不到配置檔案: config.json');
        console.log('請複製 config.example.json 為 config.json 並填入正確的配置');
        return null;
    }
}

/**
 * 初始化 Firebase
 */
function initializeFirebase() {
    const config = loadConfig();
    if (!config) {
        return null;
    }

    try {
        // 檢查是否已經初始化
        if (admin.apps.length === 0) {
            const serviceAccountPath = path.resolve(__dirname, config.service_account_key_path);
            const serviceAccount = JSON.parse(fs.readFileSync(serviceAccountPath, 'utf8'));

            admin.initializeApp({
                credential: admin.credential.cert(serviceAccount),
                projectId: config.project_id
            });
        }

        return admin.firestore();
    } catch (error) {
        console.error('Firebase 初始化失敗:', error.message);
        return null;
    }
}

/**
 * 從卡片資料中獲取指定語言的名稱
 */
function getCardName(cardData, language = 'cht') {
    const nameField = `names.${language}`;
    if (cardData[nameField] && typeof cardData[nameField] === 'object') {
        const name = cardData[nameField].name;
        if (name && name.trim()) {
            return name.trim();
        }
    }
    return '未知';
}

/**
 * 從卡片資料中獲取名稱，如果首選語言不存在則嘗試其他語言
 */
function getCardNameFallback(cardData, preferredLang = 'cht') {
    // 嘗試首選語言
    let name = getCardName(cardData, preferredLang);
    if (name !== '未知') {
        return name;
    }

    // 嘗試其他語言，按優先順序
    const fallbackLangs = ['cht', 'chs', 'en', 'ja', 'ko'];
    for (const lang of fallbackLangs) {
        if (lang !== preferredLang) {
            name = getCardName(cardData, lang);
            if (name !== '未知') {
                return `${name} (${lang})`;
            }
        }
    }

    return '未知';
}

/**
 * 基本查詢範例
 */
async function exampleBasicQueries(db) {
    console.log('=== 基本查詢範例 ===');
    
    try {
        const cardsRef = db.collection('cards');
        
        // 1. 統計總卡片數量
        const totalCards = await cardsRef.count().get();
        console.log(`資料庫中總共有 ${totalCards.data().count} 張卡片`);

        // 2. 各職業卡片數量 (取樣)
        console.log('\n各職業卡片數量 (前10張):');
        const classNames = ['中立', '精靈', '皇家護衛', '巫師', '龍族', '死靈法師', '主教', '復仇者'];
        
        for (let i = 0; i < classNames.length; i++) {
            const classCards = await cardsRef.where('class', '==', i).limit(10).get();
            console.log(`  ${classNames[i]}: ${classCards.size} 張 (樣本)`);
        }

        // 3. 各稀有度卡片數量 (取樣)
        console.log('\n各稀有度卡片數量 (前10張):');
        const rarityNames = ['銅', '銀', '金', '虹'];
        
        for (let i = 1; i <= rarityNames.length; i++) {
            const rarityCards = await cardsRef.where('rarity', '==', i).limit(10).get();
            console.log(`  ${rarityNames[i-1]}: ${rarityCards.size} 張 (樣本)`);
        }

    } catch (error) {
        console.error('基本查詢時發生錯誤:', error.message);
    }
}

/**
 * 卡片搜尋範例
 */
async function exampleCardSearch(db) {
    console.log('\n=== 卡片搜尋範例 ===');
    
    try {
        const cardsRef = db.collection('cards');

        // 1. 按費用搜尋
        console.log('\n費用為 5 的卡片:');
        const cost5Cards = await cardsRef.where('cost', '==', 5).limit(5).get();
        
        cost5Cards.forEach(doc => {
            const cardData = doc.data();
            const cardName = getCardName(cardData);
            console.log(`  ${cardName} - 費用:${cardData.cost} 攻擊:${cardData.atk} 生命:${cardData.life}`);
        });

        // 2. 按攻擊力搜尋
        console.log('\n高攻擊力卡片 (攻擊 >= 8):');
        const highAtkCards = await cardsRef.where('atk', '>=', 8).limit(5).get();
        
        highAtkCards.forEach(doc => {
            const cardData = doc.data();
            const cardName = getCardName(cardData);
            console.log(`  ${cardName} - 攻擊:${cardData.atk} 生命:${cardData.life} 費用:${cardData.cost}`);
        });

    } catch (error) {
        console.error('卡片搜尋時發生錯誤:', error.message);
    }
}

/**
 * 複合查詢範例
 */
async function exampleComplexQueries(db) {
    console.log('\n=== 複合查詢範例 ===');
    
    try {
        const cardsRef = db.collection('cards');

        // 1. 精靈職業且費用為 3 的卡片
        console.log('\n精靈職業費用 3 的卡片:');
        const elfCost3 = await cardsRef
            .where('class', '==', 1)
            .where('cost', '==', 3)
            .limit(5)
            .get();
        
        elfCost3.forEach(doc => {
            const cardData = doc.data();
            const cardName = getCardName(cardData);
            console.log(`  ${cardName} - 攻擊:${cardData.atk} 生命:${cardData.life}`);
        });

        // 2. 非isToken卡片
        console.log('\n非isToken卡片:');
        const nonTokenCards = await cardsRef.where('isToken', '==', false).limit(5).get();
        
        nonTokenCards.forEach(doc => {
            const cardData = doc.data();
            const cardName = getCardName(cardData);
            console.log(`  ${cardName} - 職業:${cardData.class} 費用:${cardData.cost}`);
        });

        // 3. 查詢包含特定種族的卡片
        console.log('\n查詢有種族的卡片...');
        const allCards = await cardsRef.limit(100).get();
        const cardsWithTribes = [];
        
        allCards.forEach(doc => {
            const cardData = doc.data();
            if (cardData.tribes && cardData.tribes.length > 0) {
                cardsWithTribes.push({doc, cardData});
            }
        });

        if (cardsWithTribes.length > 0) {
            // 收集所有種族ID
            const foundTribes = new Set();
            cardsWithTribes.forEach(({cardData}) => {
                if (cardData.tribes) {
                    cardData.tribes.forEach(tribe => foundTribes.add(tribe));
                }
            });

            if (foundTribes.size > 0) {
                const firstTribe = Math.min(...foundTribes);
                const tribeCards = cardsWithTribes.filter(({cardData}) => 
                    cardData.tribes && cardData.tribes.includes(firstTribe)
                );

                console.log(`\n包含種族 ${firstTribe} 的卡片:`);
                tribeCards.slice(0, 5).forEach(({cardData}) => {
                    const cardName = getCardNameFallback(cardData);
                    console.log(`  ${cardName} - 種族:[${cardData.tribes.join(',')}]`);
                });
            } else {
                console.log('\n未找到有效的種族資料');
            }
        } else {
            console.log('\n未找到有種族的卡片');
        }

    } catch (error) {
        console.error('複合查詢時發生錯誤:', error.message);
    }
}

/**
 * 多語言資料範例
 */
async function exampleMultilingualData(db) {
    console.log('\n=== 多語言資料範例 ===');
    
    try {
        const cardsRef = db.collection('cards');
        const firstCard = await cardsRef.limit(1).get();
        
        if (!firstCard.empty) {
            const cardDoc = firstCard.docs[0];
            const cardData = cardDoc.data();
            
            console.log(`\n卡片 ID ${cardDoc.id} 的多語言名稱:`);
            
            const languages = [
                {code: 'cht', name: '繁體中文'},
                {code: 'chs', name: '簡體中文'},
                {code: 'en', name: '英文'},
                {code: 'ja', name: '日文'},
                {code: 'ko', name: '韓文'}
            ];
            
            languages.forEach(({code, name}) => {
                const cardName = getCardName(cardData, code);
                console.log(`  ${name}: ${cardName}`);
            });

            console.log('\n基本資訊:');
            console.log(`  費用: ${cardData.cost}`);
            console.log(`  攻擊: ${cardData.atk}`);
            console.log(`  生命: ${cardData.life}`);
            console.log(`  稀有度: ${cardData.rarity}`);
            console.log(`  職業: ${cardData.class}`);
        }

    } catch (error) {
        console.error('多語言資料查詢時發生錯誤:', error.message);
    }
}

/**
 * 參考資料查詢範例
 */
async function exampleReferenceData(db) {
    console.log('\n=== 參考資料查詢範例 ===');
    
    try {
        // 卡包資料
        console.log('\n卡包資料:');
        const cardSets = await db.collection('cardSets').limit(5).get();
        cardSets.forEach(doc => {
            const data = doc.data();
            const name = getCardName(data) || '未知';
            console.log(`  ID ${doc.id}: ${name}`);
        });

        // 種族資料
        console.log('\n種族資料:');
        const tribes = await db.collection('tribes').limit(5).get();
        tribes.forEach(doc => {
            const data = doc.data();
            const name = getCardName(data) || '未知';
            console.log(`  ID ${doc.id}: ${name}`);
        });

        // 技能資料
        console.log('\n技能資料:');
        const skills = await db.collection('skills').limit(5).get();
        skills.forEach(doc => {
            const data = doc.data();
            const name = getCardName(data) || '未知';
            console.log(`  ID ${doc.id}: ${name}`);
        });

    } catch (error) {
        console.error('參考資料查詢時發生錯誤:', error.message);
    }
}

/**
 * 同步記錄查詢範例
 */
async function exampleSyncLogs(db) {
    console.log('\n=== 同步記錄查詢範例 ===');
    
    try {
        // 最近的同步記錄
        console.log('\n最近的同步記錄:');
        const recentLogs = await db.collection('syncLogs')
            .orderBy('timestamp', 'desc')
            .limit(5)
            .get();
        
        recentLogs.forEach(doc => {
            const data = doc.data();
            const timestamp = data.timestamp.toDate().toLocaleString('zh-TW');
            console.log(`  ${data.language} - ${data.status} - ${data.successful_count}/${data.total_count} 張成功 - ${timestamp}`);
        });

        // 特定語言的同步記錄
        const chtLogs = await db.collection('syncLogs')
            .where('language', '==', 'cht')
            .orderBy('timestamp', 'desc')
            .limit(1)
            .get();
        
        if (!chtLogs.empty) {
            const logData = chtLogs.docs[0].data();
            const successRate = ((logData.successful_count / logData.total_count) * 100).toFixed(1);
            console.log(`\n繁體中文同步記錄:`);
            console.log(`  狀態: ${logData.status}, 成功率: ${successRate}%`);
        }

    } catch (error) {
        console.error('同步記錄查詢時發生錯誤:', error.message);
    }
}

/**
 * 進階過濾範例
 */
async function exampleAdvancedFilters(db) {
    console.log('\n=== 進階過濾範例 ===');
    
    try {
        const cardsRef = db.collection('cards');

        // 1. 範圍查詢 (中費用卡片)
        console.log('\n中費用卡片 (4-6費):');
        const midCostCards = await cardsRef
            .where('cost', '>=', 4)
            .where('cost', '<=', 6)
            .limit(5)
            .get();
        
        midCostCards.forEach(doc => {
            const cardData = doc.data();
            const cardName = getCardName(cardData);
            console.log(`  ${cardName} - 費用:${cardData.cost} 攻擊:${cardData.atk}`);
        });

        // 2. 多條件查詢 (輪替制中的傳說卡片)
        console.log('\n輪替制中的傳說卡片:');
        const rotationLegendaries = await cardsRef
            .where('isIncludeRotation', '==', true)
            .where('rarity', '==', 4)
            .limit(3)
            .get();
        
        rotationLegendaries.forEach(doc => {
            const cardData = doc.data();
            const cardName = getCardName(cardData);
            console.log(`  ${cardName} - 職業:${cardData.class} 費用:${cardData.cost}`);
        });

        // 3. 陣列查詢 (中立和精靈卡片)
        console.log('\n中立和精靈卡片:');
        const neutralElfCards = await cardsRef
            .where('class', 'in', [0, 1])
            .limit(5)
            .get();
        
        neutralElfCards.forEach(doc => {
            const cardData = doc.data();
            const cardName = getCardName(cardData);
            const className = cardData.class === 0 ? '中立' : '精靈';
            console.log(`  ${cardName} - ${className}`);
        });

    } catch (error) {
        console.error('進階過濾時發生錯誤:', error.message);
    }
}

/**
 * 主函數
 */
async function main() {
    console.log('Firebase Firestore 查詢範例 (JavaScript 版本)');
    
    const db = initializeFirebase();
    if (!db) {
        console.error('無法初始化 Firebase，請檢查配置');
        process.exit(1);
    }

    try {
        await exampleBasicQueries(db);
        await exampleCardSearch(db);
        await exampleComplexQueries(db);
        await exampleMultilingualData(db);
        await exampleReferenceData(db);
        await exampleSyncLogs(db);
        await exampleAdvancedFilters(db);

        console.log('\n查詢範例執行完成！');
        console.log('\n注意事項:');
        console.log('- Firestore 查詢有一些限制，例如不支援全文搜尋');
        console.log('- 複合查詢可能需要建立索引');
        console.log('- 大量資料查詢時請注意成本和效能');

    } catch (error) {
        console.error('執行查詢範例時發生錯誤:', error.message);
    } finally {
        // 關閉 Firebase 連接
        process.exit(0);
    }
}

// 如果直接執行此腳本，則運行主函數
// 檢查是否為直接執行（不是被 import）
if (process.argv[1] && process.argv[1].endsWith('firebase_queries.js')) {
    main().catch(console.error);
}

export {
    initializeFirebase,
    getCardName,
    getCardNameFallback,
    exampleBasicQueries,
    exampleCardSearch,
    exampleComplexQueries,
    exampleMultilingualData,
    exampleReferenceData,
    exampleSyncLogs,
    exampleAdvancedFilters
};