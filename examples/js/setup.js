#!/usr/bin/env node
/**
 * JavaScript Firebase 範例設置腳本
 * 
 * 這個腳本幫助快速設置 JavaScript Firebase 範例環境
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 檢查並安裝依賴
 */
function installDependencies() {
    console.log('=== 安裝依賴套件 ===');
    
    try {
        console.log('檢查 package.json...');
        const packagePath = path.join(__dirname, 'package.json');
        
        if (!fs.existsSync(packagePath)) {
            console.error('❌ 找不到 package.json');
            return false;
        }

        console.log('安裝 npm 套件...');
        execSync('npm install', { 
            cwd: __dirname, 
            stdio: 'inherit' 
        });
        
        console.log('✅ 依賴套件安裝完成');
        return true;
    } catch (error) {
        console.error('❌ 安裝依賴套件失敗:', error.message);
        return false;
    }
}

/**
 * 建立配置檔案
 */
function createConfigFile() {
    console.log('\n=== 建立配置檔案 ===');
    
    try {
        const configPath = path.join(__dirname, 'config.json');
        const exampleConfigPath = path.join(__dirname, 'config.example.json');
        
        if (fs.existsSync(configPath)) {
            console.log('⚠️  config.json 已存在，跳過建立');
            return true;
        }

        if (!fs.existsSync(exampleConfigPath)) {
            console.error('❌ 找不到 config.example.json');
            return false;
        }

        // 複製範例配置檔案
        fs.copyFileSync(exampleConfigPath, configPath);
        console.log('✅ 已建立 config.json');
        console.log('📝 請編輯 config.json 填入正確的 Firebase 配置');
        
        return true;
    } catch (error) {
        console.error('❌ 建立配置檔案失敗:', error.message);
        return false;
    }
}

/**
 * 檢查 Firebase 服務帳戶金鑰
 */
function checkServiceAccountKey() {
    console.log('\n=== 檢查服務帳戶金鑰 ===');
    
    try {
        const configPath = path.join(__dirname, 'config.json');
        
        if (!fs.existsSync(configPath)) {
            console.log('⚠️  請先建立 config.json');
            return false;
        }

        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        const keyPath = path.resolve(__dirname, config.service_account_key_path);
        
        if (fs.existsSync(keyPath)) {
            console.log('✅ 找到服務帳戶金鑰檔案');
            return true;
        } else {
            console.log('⚠️  找不到服務帳戶金鑰檔案');
            console.log(`   預期路徑: ${keyPath}`);
            console.log('   請將 Firebase 服務帳戶金鑰檔案放在正確位置');
            return false;
        }
    } catch (error) {
        console.error('❌ 檢查服務帳戶金鑰失敗:', error.message);
        return false;
    }
}

/**
 * 執行測試
 */
function runTest() {
    console.log('\n=== 執行連接測試 ===');
    
    try {
        execSync('node test_queries.js', { 
            cwd: __dirname, 
            stdio: 'inherit' 
        });
        return true;
    } catch (error) {
        console.error('❌ 測試執行失敗');
        return false;
    }
}

/**
 * 顯示使用說明
 */
function showUsage() {
    console.log('\n=== 使用說明 ===');
    console.log('設置完成後，您可以使用以下命令:');
    console.log('');
    console.log('1. 執行查詢範例:');
    console.log('   node firebase_queries.js');
    console.log('');
    console.log('2. 執行測試:');
    console.log('   node test_queries.js');
    console.log('   或');
    console.log('   npm test');
    console.log('');
    console.log('3. 快速執行:');
    console.log('   npm start');
    console.log('');
    console.log('注意事項:');
    console.log('- 確保已正確配置 Firebase 專案');
    console.log('- 確保服務帳戶金鑰檔案路徑正確');
    console.log('- 確保資料庫中有卡片資料');
}

/**
 * 主設置函數
 */
async function main() {
    console.log('JavaScript Firebase 範例設置');
    console.log('='.repeat(40));
    
    const steps = [
        { name: '安裝依賴套件', func: installDependencies },
        { name: '建立配置檔案', func: createConfigFile },
        { name: '檢查服務帳戶金鑰', func: checkServiceAccountKey }
    ];

    let completedSteps = 0;
    const totalSteps = steps.length;

    for (const step of steps) {
        try {
            const result = step.func();
            if (result) {
                completedSteps++;
            }
        } catch (error) {
            console.error(`❌ ${step.name} 發生未預期錯誤:`, error.message);
        }
        
        console.log('-'.repeat(30));
    }

    console.log('\n=== 設置結果摘要 ===');
    console.log(`完成步驟: ${completedSteps}/${totalSteps}`);

    if (completedSteps === totalSteps) {
        console.log('🎉 設置完成！');
        
        // 詢問是否執行測試
        console.log('\n是否要執行連接測試？ (y/N)');
        
        // 在 Node.js 中讀取用戶輸入比較複雜，這裡先跳過互動式測試
        console.log('您可以手動執行: node test_queries.js');
    } else {
        console.log('⚠️  設置未完全完成，請檢查上述錯誤訊息');
    }

    showUsage();
}

// 如果直接執行此腳本，則運行設置
if (process.argv[1] && process.argv[1].endsWith('setup.js')) {
    main().catch(console.error);
}