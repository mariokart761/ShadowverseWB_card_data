#!/usr/bin/env node
/**
 * Firebase Firestore 查詢測試腳本 (JavaScript 版本)
 * 
 * 這個腳本用於測試各種查詢功能
 */

import {
    initializeFirebase,
    getCardName,
    getCardNameFallback,
    exampleBasicQueries
} from './firebase_queries.js';

/**
 * 測試連接
 */
async function testConnection() {
    console.log('=== 測試 Firebase 連接 ===');
    
    const db = initializeFirebase();
    if (!db) {
        console.error('❌ Firebase 初始化失敗');
        return false;
    }

    try {
        // 測試基本查詢
        const cardsRef = db.collection('cards');
        const testQuery = await cardsRef.limit(1).get();
        
        if (testQuery.empty) {
            console.log('⚠️  資料庫中沒有卡片資料');
            return false;
        }

        console.log('✅ Firebase 連接成功');
        console.log(`✅ 找到卡片資料，測試卡片 ID: ${testQuery.docs[0].id}`);
        
        return true;
    } catch (error) {
        console.error('❌ 連接測試失敗:', error.message);
        return false;
    }
}

/**
 * 測試名稱提取功能
 */
async function testNameExtraction() {
    console.log('\n=== 測試名稱提取功能 ===');
    
    const db = initializeFirebase();
    if (!db) {
        return false;
    }

    try {
        const cardsRef = db.collection('cards');
        const testCards = await cardsRef.limit(3).get();
        
        console.log('測試名稱提取:');
        testCards.forEach((doc, index) => {
            const cardData = doc.data();
            
            console.log(`\n卡片 ${index + 1} (ID: ${doc.id}):`);
            
            // 測試各語言名稱提取
            const languages = ['cht', 'chs', 'en', 'ja', 'ko'];
            languages.forEach(lang => {
                const name = getCardName(cardData, lang);
                console.log(`  ${lang}: ${name}`);
            });
            
            // 測試 fallback 功能
            const fallbackName = getCardNameFallback(cardData);
            console.log(`  fallback: ${fallbackName}`);
        });

        console.log('✅ 名稱提取測試完成');
        return true;
    } catch (error) {
        console.error('❌ 名稱提取測試失敗:', error.message);
        return false;
    }
}

/**
 * 測試基本查詢
 */
async function testBasicQueries() {
    console.log('\n=== 測試基本查詢 ===');
    
    const db = initializeFirebase();
    if (!db) {
        return false;
    }

    try {
        await exampleBasicQueries(db);
        console.log('✅ 基本查詢測試完成');
        return true;
    } catch (error) {
        console.error('❌ 基本查詢測試失敗:', error.message);
        return false;
    }
}

/**
 * 測試特定查詢
 */
async function testSpecificQueries() {
    console.log('\n=== 測試特定查詢 ===');
    
    const db = initializeFirebase();
    if (!db) {
        return false;
    }

    try {
        const cardsRef = db.collection('cards');
        
        // 測試費用查詢
        console.log('測試費用查詢...');
        const costQuery = await cardsRef.where('cost', '==', 2).limit(3).get();
        console.log(`✅ 找到 ${costQuery.size} 張費用為 2 的卡片`);
        
        // 測試職業查詢
        console.log('測試職業查詢...');
        const classQuery = await cardsRef.where('class', '==', 0).limit(3).get();
        console.log(`✅ 找到 ${classQuery.size} 張中立卡片`);
        
        // 測試複合查詢
        console.log('測試複合查詢...');
        const complexQuery = await cardsRef
            .where('cost', '>=', 3)
            .where('cost', '<=', 5)
            .limit(3)
            .get();
        console.log(`✅ 找到 ${complexQuery.size} 張 3-5 費的卡片`);

        console.log('✅ 特定查詢測試完成');
        return true;
    } catch (error) {
        console.error('❌ 特定查詢測試失敗:', error.message);
        return false;
    }
}

/**
 * 主測試函數
 */
async function runTests() {
    console.log('Firebase Firestore 查詢測試 (JavaScript 版本)');
    console.log('='.repeat(50));
    
    const tests = [
        { name: '連接測試', func: testConnection },
        { name: '名稱提取測試', func: testNameExtraction },
        { name: '基本查詢測試', func: testBasicQueries },
        { name: '特定查詢測試', func: testSpecificQueries }
    ];

    let passedTests = 0;
    const totalTests = tests.length;

    for (const test of tests) {
        try {
            const result = await test.func();
            if (result) {
                passedTests++;
            }
        } catch (error) {
            console.error(`❌ ${test.name} 發生未預期錯誤:`, error.message);
        }
        
        console.log('-'.repeat(30));
    }

    console.log('\n=== 測試結果摘要 ===');
    console.log(`總測試數: ${totalTests}`);
    console.log(`通過測試: ${passedTests}`);
    console.log(`失敗測試: ${totalTests - passedTests}`);
    console.log(`成功率: ${((passedTests / totalTests) * 100).toFixed(1)}%`);

    if (passedTests === totalTests) {
        console.log('🎉 所有測試通過！');
    } else {
        console.log('⚠️  部分測試失敗，請檢查配置和網路連接');
    }

    process.exit(passedTests === totalTests ? 0 : 1);
}

// 如果直接執行此腳本，則運行測試
if (import.meta.url === `file://${process.argv[1]}`) {
    runTests().catch(console.error);
}