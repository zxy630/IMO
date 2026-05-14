# 图片账单智能解析API文档

## 功能概述

本API支持用户上传支付宝花呗、微信支付/零钱等支付凭证截图，系统会自动识别并提取关键信息，生成结构化账单，并自动更新用户钱包余额。

### 支持的账单类型
- ✅ 支付宝花呗付款截图
- ✅ 微信支付账单截图  
- ✅ 微信零钱交易截图
- ✅ 其他支付宝/微信支付凭证
- ✅ 银行转账截图（如识别到金额信息）

---

## API 接口清单

| 接口 | 方法 | 说明 |
|------|------|------|
| `/user/bills/parse-image` | POST | 上传并解析账单截图 |
| `/user/bills/list` | GET | 获取账单列表 |
| `/user/bills/report` | GET | 获取账单统计报告 |

---

## 1. 上传并解析账单截图

### 接口地址
```
POST http://localhost:8000/user/bills/parse-image
```

### 请求方式
- **Content-Type**: `multipart/form-data`
- **认证**: 在请求头中添加 `X-Username` 头

### 请求头
```
X-Username: testuser
```

### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | ✓ | 账单截图文件，支持 jpg/jpeg/png/gif/bmp/webp，最大10MB |

### 返回格式
```json
{
  "success": true,
  "message": "账单解析并创建成功",
  "bill_id": "550e8400-e29b-41d4-a716-446655440000",
  "parsed_data": {
    "transaction_time": "2024-04-29T15:30:00+08:00",
    "merchant_name": "星巴克(中关村店)",
    "amount": 28.50,
    "transaction_type": "expense",
    "payment_method": "支付宝",
    "account_type": "花呗",
    "counterparty": "星巴克",
    "actual_amount": 28.50,
    "status": "completed"
  },
  "wallet_balance": 9971.50
}
```

### 返回字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否处理成功 |
| message | string | 处理信息或错误提示 |
| bill_id | string | 账单ID（成功时返回） |
| parsed_data | object | 解析后的账单数据 |
| wallet_balance | number | 更新后的钱包余额 |

### 解析数据字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| transaction_time | string | 交易时间（ISO 8601格式） |
| merchant_name | string | 商户名称 |
| amount | number | 交易金额 |
| transaction_type | string | 交易类型：`income`(收入) 或 `expense`(支出) |
| payment_method | string | 支付方式：支付宝/微信/其他 |
| account_type | string | 账户类型：余额宝/花呗/零钱/储蓄卡等 |
| counterparty | string | 交易对象/收款人 |
| actual_amount | number | 实际交易金额 |
| status | string | 交易状态：completed/pending/cancelled |

### JavaScript/TypeScript 调用示例

#### 方案1：使用 Fetch API
```javascript
async function uploadBillImage(file) {
  const username = 'testuser';
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch('http://localhost:8000/user/bills/parse-image', {
      method: 'POST',
      headers: {
        'X-Username': username
      },
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('✅ 账单解析成功');
      console.log('账单ID:', result.bill_id);
      console.log('钱包余额:', result.wallet_balance);
      console.log('解析数据:', result.parsed_data);
    } else {
      console.error('❌ 解析失败:', result.message);
    }
    
    return result;
  } catch (error) {
    console.error('网络请求失败:', error);
  }
}

// 使用示例
const fileInput = document.getElementById('bill-image');
fileInput.addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (file) {
    uploadBillImage(file);
  }
});
```

#### 方案2：使用 Axios
```javascript
import axios from 'axios';

async function uploadBillImageWithAxios(file) {
  const username = 'testuser';
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await axios.post(
      'http://localhost:8000/user/bills/parse-image',
      formData,
      {
        headers: {
          'X-Username': username,
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    
    const result = response.data;
    
    if (result.success) {
      console.log('✅ 账单解析成功');
      return result;
    } else {
      console.error('❌ 解析失败:', result.message);
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('请求失败:', error.response?.data || error.message);
  }
}
```

#### 方案3：使用 Vue 3 + Composition API
```vue
<template>
  <div class="bill-upload">
    <div v-if="loading" class="loading">处理中...</div>
    
    <div v-else>
      <input 
        type="file" 
        accept="image/*"
        @change="handleFileSelect"
        ref="fileInput"
      />
      
      <div v-if="result" class="result">
        <div v-if="result.success" class="success">
          <p>✅ {{ result.message }}</p>
          <p>账单ID: {{ result.bill_id }}</p>
          <p>新余额: ¥{{ result.wallet_balance }}</p>
          <div class="bill-info">
            <p>商户: {{ result.parsed_data.merchant_name }}</p>
            <p>金额: ¥{{ result.parsed_data.amount }}</p>
            <p>支付方式: {{ result.parsed_data.payment_method }}</p>
            <p>交易时间: {{ result.parsed_data.transaction_time }}</p>
          </div>
        </div>
        
        <div v-else class="error">
          <p>❌ {{ result.message }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const fileInput = ref(null);
const loading = ref(false);
const result = ref(null);
const username = 'testuser'; // 实际应该从用户认证获取

async function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件');
    return;
  }
  
  // 验证文件大小
  if (file.size > 10 * 1024 * 1024) {
    alert('文件大小不能超过10MB');
    return;
  }
  
  loading.value = true;
  
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(
      'http://localhost:8000/user/bills/parse-image',
      formData,
      {
        headers: {
          'X-Username': username
        }
      }
    );
    
    result.value = response.data;
  } catch (error) {
    result.value = {
      success: false,
      message: error.response?.data?.message || '请求失败，请重试'
    };
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.bill-upload {
  padding: 20px;
}

.loading {
  text-align: center;
  font-size: 18px;
  color: #666;
}

.result {
  margin-top: 20px;
  padding: 15px;
  border-radius: 8px;
}

.success {
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  color: #0050b3;
}

.error {
  background: #fef2f0;
  border: 1px solid #ffccc7;
  color: #d4380d;
}

.bill-info {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid currentColor;
}

.bill-info p {
  margin: 5px 0;
}
</style>
```

#### 方案4：使用 React + TypeScript
```typescript
import React, { useState } from 'react';
import axios from 'axios';

interface ParsedData {
  transaction_time: string;
  merchant_name: string;
  amount: number;
  transaction_type: 'income' | 'expense';
  payment_method: string;
  account_type: string;
  counterparty: string;
  actual_amount: number;
  status: string;
}

interface UploadResult {
  success: boolean;
  message: string;
  bill_id?: string;
  parsed_data?: ParsedData;
  wallet_balance?: number;
}

export const BillUpload: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const username = 'testuser';

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 验证文件
    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert('文件大小不能超过10MB');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post<UploadResult>(
        'http://localhost:8000/user/bills/parse-image',
        formData,
        {
          headers: {
            'X-Username': username
          }
        }
      );

      setResult(response.data);
    } catch (error: any) {
      setResult({
        success: false,
        message: error.response?.data?.message || '请求失败，请重试'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bill-upload">
      {loading && <p>处理中...</p>}

      {!loading && (
        <>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            disabled={loading}
          />

          {result && (
            <div className={`result ${result.success ? 'success' : 'error'}`}>
              <p>{result.message}</p>
              {result.success && (
                <>
                  <p>账单ID: {result.bill_id}</p>
                  <p>新余额: ¥{result.wallet_balance}</p>
                  {result.parsed_data && (
                    <div>
                      <p>商户: {result.parsed_data.merchant_name}</p>
                      <p>金额: ¥{result.parsed_data.amount}</p>
                      <p>支付方式: {result.parsed_data.payment_method}</p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};
```

---

## 2. 获取账单列表

### 接口地址
```
GET http://localhost:8000/user/bills/list?limit=50
```

### 请求头
```
X-Username: testuser
```

### 请求参数
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | integer | ✗ | 100 | 返回的最大账单数（1-1000） |

### 返回格式
```json
{
  "success": true,
  "message": "获取成功",
  "bills": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "transaction_time": "2024-04-29T15:30:00+08:00",
      "merchant_name": "星巴克(中关村店)",
      "amount": -28.50,
      "transaction_type": "expense",
      "payment_method": "支付宝",
      "account_type": "花呗",
      "counterparty": "星巴克",
      "actual_amount": 28.50,
      "status": "completed"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "transaction_time": "2024-04-28T10:15:00+08:00",
      "merchant_name": "工资转账",
      "amount": 5000.00,
      "transaction_type": "income",
      "payment_method": "微信",
      "account_type": "零钱",
      "counterparty": "公司人事",
      "actual_amount": 5000.00,
      "status": "completed"
    }
  ],
  "total_count": 2
}
```

### JavaScript 调用示例
```javascript
async function fetchBillsList(limit = 50) {
  const username = 'testuser';
  
  try {
    const response = await fetch(
      `http://localhost:8000/user/bills/list?limit=${limit}`,
      {
        method: 'GET',
        headers: {
          'X-Username': username
        }
      }
    );
    
    const result = await response.json();
    
    if (result.success) {
      console.log('✅ 获取账单列表成功');
      console.log(`总共 ${result.total_count} 条账单`);
      
      result.bills.forEach(bill => {
        console.log(`
          时间: ${bill.transaction_time}
          商户: ${bill.merchant_name}
          金额: ¥${bill.amount}
          类型: ${bill.transaction_type === 'income' ? '收入' : '支出'}
        `);
      });
    }
    
    return result;
  } catch (error) {
    console.error('获取失败:', error);
  }
}

// 使用示例
fetchBillsList(50);
```

---

## 3. 获取账单统计报告

### 接口地址
```
GET http://localhost:8000/user/bills/report?days=30
```

### 请求头
```
X-Username: testuser
```

### 请求参数
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| days | integer | ✗ | 30 | 统计天数（1-365） |

### 返回格式
```json
{
  "success": true,
  "message": "报告生成成功",
  "summary": {
    "total_income": 5000.00,
    "total_expense": 1250.50,
    "net_change": 3749.50,
    "bill_count": 15,
    "payment_methods": {
      "支付宝": -850.00,
      "微信": 5000.00,
      "银行卡": -400.50
    },
    "top_merchants": [
      {
        "merchant": "工资转账",
        "amount": 5000.00
      },
      {
        "merchant": "日常消费",
        "amount": -500.00
      },
      {
        "merchant": "电商购物",
        "amount": -350.50
      }
    ],
    "daily_avg": 124.98,
    "period_days": 30
  },
  "wallet_balance": 10000.00,
  "advice": "✅ 收支情况良好，本期结余 ¥3749.50。\n📊 主要消费来源：工资转账，金额 ¥5000.00。\n💡 建议：定期检查账单，监控消费趋势。"
}
```

### 返回字段说明

#### summary 对象
| 字段 | 类型 | 说明 |
|------|------|------|
| total_income | number | 总收入 |
| total_expense | number | 总支出 |
| net_change | number | 净变化（收入-支出） |
| bill_count | integer | 账单总数 |
| payment_methods | object | 按支付方式分类统计 |
| top_merchants | array | 排名前5的商户 |
| daily_avg | number | 日均收支 |
| period_days | integer | 统计天数 |

### JavaScript 调用示例
```javascript
async function fetchBillsReport(days = 30) {
  const username = 'testuser';
  
  try {
    const response = await fetch(
      `http://localhost:8000/user/bills/report?days=${days}`,
      {
        method: 'GET',
        headers: {
          'X-Username': username
        }
      }
    );
    
    const result = await response.json();
    
    if (result.success) {
      console.log('✅ 报告生成成功\n');
      
      const { summary, wallet_balance, advice } = result;
      
      console.log('📊 账单汇总:');
      console.log(`  总收入: ¥${summary.total_income.toFixed(2)}`);
      console.log(`  总支出: ¥${summary.total_expense.toFixed(2)}`);
      console.log(`  净结余: ¥${summary.net_change.toFixed(2)}`);
      console.log(`  日均: ¥${summary.daily_avg.toFixed(2)}`);
      console.log(`  账单数: ${summary.bill_count}\n`);
      
      console.log('💳 支付方式分析:');
      Object.entries(summary.payment_methods).forEach(([method, amount]) => {
        console.log(`  ${method}: ¥${amount.toFixed(2)}`);
      });
      
      console.log('\n🏪 消费排名:');
      summary.top_merchants.forEach((merchant, index) => {
        console.log(`  ${index + 1}. ${merchant.merchant}: ¥${Math.abs(merchant.amount).toFixed(2)}`);
      });
      
      console.log(`\n💰 当前余额: ¥${wallet_balance.toFixed(2)}\n`);
      console.log('💡 AI建议:\n' + advice);
    }
    
    return result;
  } catch (error) {
    console.error('获取报告失败:', error);
  }
}

// 使用示例
fetchBillsReport(30);
```

---

## 错误处理

### 常见错误响应

#### 1. 用户不存在
```json
{
  "success": false,
  "message": "用户不存在",
  "bill_id": null,
  "parsed_data": null,
  "wallet_balance": null
}
```

#### 2. 不支持的文件格式
```json
{
  "success": false,
  "message": "不支持的文件格式，请上传图片文件",
  "bill_id": null,
  "parsed_data": null,
  "wallet_balance": null
}
```

#### 3. 文件过大
```json
{
  "success": false,
  "message": "文件大小不能超过10MB",
  "bill_id": null,
  "parsed_data": null,
  "wallet_balance": null
}
```

#### 4. 图片解析失败
```json
{
  "success": false,
  "message": "图片解析失败: 无法识别账单信息",
  "bill_id": null,
  "parsed_data": null,
  "wallet_balance": null
}
```

### 错误代码及处理建议

| 错误信息 | 状态码 | 处理建议 |
|---------|--------|---------|
| 用户不存在 | 200 | 检查用户是否已登录，X-Username是否正确 |
| 不支持的文件格式 | 200 | 请选择 jpg/jpeg/png/gif/bmp/webp 格式的图片 |
| 文件大小不能超过10MB | 200 | 压缩图片后重试 |
| 图片解析失败 | 200 | 确保图片清晰，包含完整的账单信息 |
| 未配置 DASHSCOPE_API_KEY | 200 | 联系系统管理员配置API密钥 |

---

## 注意事项

### 1. 认证要求
- ⚠️ **必须** 在请求头中包含 `X-Username` 头
- X-Username 必须对应已注册的有效用户

### 2. 文件限制
- ✅ 支持格式：jpg、jpeg、png、gif、bmp、webp
- ✅ 最大大小：10MB
- ⚠️ 建议图片大小：1-5MB（识别效果更好）

### 3. 图片质量要求
- 📷 **清晰度**：账单信息必须清晰可见
- 📷 **完整性**：需要包含金额、商户、交易时间等关键信息
- 📷 **角度**：建议正面拍摄，避免过度倾斜或拍照角度不佳

### 4. 钱包更新
- 💰 成功解析后，**系统自动更新用户钱包余额**
- 💰 支出类交易会减少余额，收入类交易会增加余额
- 💰 余额更新实时生效，无需二次操作

### 5. 速率限制
- ⏱️ 建议相邻两次请求间隔不少于1秒
- ⏱️ 单个用户每分钟最多60次请求（可按需调整）

### 6. 隐私保护
- 🔒 上传的图片会保存在本地服务器
- 🔒 建议定期清理过期账单数据
- 🔒 不建议在公共网络环境上传敏感账单

### 7. API超时
- ⏱️ 建议设置请求超时时间：30秒
- ⏱️ 网络条件差时可能需要更长时间

---

## 完整调用示例：从上传到显示报告

### HTML 页面示例
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>账单智能解析系统</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 20px;
    }

    .container {
      background: white;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      max-width: 600px;
      width: 100%;
      padding: 40px;
    }

    h1 {
      color: #333;
      margin-bottom: 30px;
      font-size: 28px;
      text-align: center;
    }

    .upload-area {
      border: 2px dashed #667eea;
      border-radius: 8px;
      padding: 40px;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s;
      background: #f8f9ff;
      margin-bottom: 20px;
    }

    .upload-area:hover {
      border-color: #764ba2;
      background: #f0f2ff;
    }

    .upload-area.dragover {
      border-color: #764ba2;
      background: #e8ebff;
    }

    .upload-icon {
      font-size: 48px;
      margin-bottom: 10px;
    }

    .upload-text {
      color: #666;
      margin-bottom: 5px;
    }

    .upload-hint {
      color: #999;
      font-size: 12px;
    }

    input[type="file"] {
      display: none;
    }

    .loading {
      text-align: center;
      padding: 20px;
      color: #667eea;
      font-size: 16px;
    }

    .spinner {
      display: inline-block;
      width: 20px;
      height: 20px;
      border: 3px solid #f3f3f3;
      border-top: 3px solid #667eea;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-right: 10px;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    .result {
      padding: 20px;
      border-radius: 8px;
      margin-top: 20px;
    }

    .result.success {
      background: #f0fdf4;
      border: 1px solid #86efac;
    }

    .result.error {
      background: #fef2f2;
      border: 1px solid #fca5a5;
    }

    .result-header {
      display: flex;
      align-items: center;
      margin-bottom: 15px;
    }

    .result-icon {
      font-size: 24px;
      margin-right: 10px;
    }

    .result-title {
      font-size: 16px;
      font-weight: bold;
    }

    .result.success .result-title {
      color: #16a34a;
    }

    .result.error .result-title {
      color: #dc2626;
    }

    .bill-details {
      background: white;
      padding: 15px;
      border-radius: 6px;
      margin-top: 15px;
    }

    .bill-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #eee;
    }

    .bill-row:last-child {
      border-bottom: none;
    }

    .bill-label {
      color: #666;
      font-size: 14px;
    }

    .bill-value {
      color: #333;
      font-weight: 500;
    }

    .wallet-balance {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px;
      border-radius: 6px;
      margin-top: 15px;
      text-align: center;
    }

    .balance-label {
      font-size: 12px;
      opacity: 0.9;
      margin-bottom: 5px;
    }

    .balance-amount {
      font-size: 28px;
      font-weight: bold;
    }

    .tabs {
      display: flex;
      gap: 10px;
      margin-top: 20px;
      border-bottom: 2px solid #eee;
    }

    .tab-button {
      padding: 10px 15px;
      background: none;
      border: none;
      cursor: pointer;
      color: #666;
      font-size: 14px;
      border-bottom: 3px solid transparent;
      transition: all 0.3s;
    }

    .tab-button.active {
      color: #667eea;
      border-bottom-color: #667eea;
    }

    .tab-content {
      display: none;
      margin-top: 15px;
    }

    .tab-content.active {
      display: block;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 10px;
    }

    .stat-card {
      background: #f8f9fa;
      padding: 15px;
      border-radius: 6px;
      text-align: center;
    }

    .stat-label {
      color: #666;
      font-size: 12px;
      margin-bottom: 5px;
    }

    .stat-value {
      color: #333;
      font-size: 18px;
      font-weight: bold;
    }

    .stat-value.positive {
      color: #16a34a;
    }

    .stat-value.negative {
      color: #dc2626;
    }

    .advice-box {
      background: #fffacd;
      border: 1px solid #ffd700;
      padding: 15px;
      border-radius: 6px;
      margin-top: 10px;
      color: #333;
      font-size: 14px;
      line-height: 1.6;
    }

    button {
      background: #667eea;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.3s;
      margin-top: 10px;
    }

    button:hover {
      background: #764ba2;
      transform: translateY(-2px);
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>📱 账单智能解析</h1>

    <div id="uploadSection">
      <div class="upload-area" id="uploadArea">
        <div class="upload-icon">📸</div>
        <div class="upload-text">点击或拖拽上传账单截图</div>
        <div class="upload-hint">支持 JPG/PNG/GIF，最大 10MB</div>
        <input type="file" id="fileInput" accept="image/*" />
      </div>
    </div>

    <div id="loadingSection" class="loading" style="display: none;">
      <div class="spinner"></div>
      正在处理图片...
    </div>

    <div id="resultSection"></div>

    <div id="billsSection" style="display: none;">
      <div class="tabs">
        <button class="tab-button active" data-tab="bills">最近账单</button>
        <button class="tab-button" data-tab="report">统计报告</button>
      </div>

      <div id="bills" class="tab-content active"></div>
      <div id="report" class="tab-content"></div>
    </div>
  </div>

  <script>
    const username = 'testuser';
    const API_BASE = 'http://localhost:8000';

    // 上传区域事件
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
      uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');
      handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', (e) => {
      handleFiles(e.target.files);
    });

    async function handleFiles(files) {
      const file = files[0];
      if (!file) return;

      if (!file.type.startsWith('image/')) {
        showResult(false, '请选择图片文件');
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        showResult(false, '文件大小不能超过10MB');
        return;
      }

      showLoading(true);

      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/user/bills/parse-image`, {
          method: 'POST',
          headers: {
            'X-Username': username
          },
          body: formData
        });

        const result = await response.json();

        if (result.success) {
          showResult(true, result.message, result);
          await loadBillsList();
          await loadBillsReport();
        } else {
          showResult(false, result.message);
        }
      } catch (error) {
        showResult(false, `请求失败: ${error.message}`);
      } finally {
        showLoading(false);
      }
    }

    function showLoading(show) {
      document.getElementById('loadingSection').style.display = show ? 'block' : 'none';
      document.getElementById('uploadSection').style.display = show ? 'none' : 'block';
    }

    function showResult(success, message, data = null) {
      const resultSection = document.getElementById('resultSection');

      let html = `
        <div class="result ${success ? 'success' : 'error'}">
          <div class="result-header">
            <div class="result-icon">${success ? '✅' : '❌'}</div>
            <div class="result-title">${message}</div>
          </div>
      `;

      if (success && data && data.parsed_data) {
        html += `
          <div class="bill-details">
            <div class="bill-row">
              <span class="bill-label">交易时间</span>
              <span class="bill-value">${data.parsed_data.transaction_time}</span>
            </div>
            <div class="bill-row">
              <span class="bill-label">商户名称</span>
              <span class="bill-value">${data.parsed_data.merchant_name}</span>
            </div>
            <div class="bill-row">
              <span class="bill-label">交易金额</span>
              <span class="bill-value">¥${data.parsed_data.amount}</span>
            </div>
            <div class="bill-row">
              <span class="bill-label">交易类型</span>
              <span class="bill-value">${data.parsed_data.transaction_type === 'income' ? '收入' : '支出'}</span>
            </div>
            <div class="bill-row">
              <span class="bill-label">支付方式</span>
              <span class="bill-value">${data.parsed_data.payment_method}</span>
            </div>
            <div class="bill-row">
              <span class="bill-label">账户类型</span>
              <span class="bill-value">${data.parsed_data.account_type}</span>
            </div>
          </div>
          <div class="wallet-balance">
            <div class="balance-label">当前钱包余额</div>
            <div class="balance-amount">¥${data.wallet_balance.toFixed(2)}</div>
          </div>
        `;
      }

      html += '</div>';
      resultSection.innerHTML = html;
    }

    async function loadBillsList() {
      try {
        const response = await fetch(`${API_BASE}/user/bills/list?limit=10`, {
          headers: { 'X-Username': username }
        });
        const result = await response.json();

        if (result.success) {
          let html = '<h3 style="margin-bottom: 15px;">最近 10 条账单</h3>';
          if (result.bills.length === 0) {
            html += '<p style="color: #999;">暂无账单记录</p>';
          } else {
            html += '<div style="max-height: 300px; overflow-y: auto;">';
            result.bills.forEach(bill => {
              const amountClass = bill.amount >= 0 ? 'positive' : 'negative';
              html += `
                <div class="bill-row" style="border-bottom: 1px solid #eee; padding: 10px 0;">
                  <div>
                    <div style="color: #333; font-weight: 500;">${bill.merchant_name}</div>
                    <div style="color: #999; font-size: 12px;">${bill.transaction_time.split('T')[0]}</div>
                  </div>
                  <div class="stat-value ${amountClass}">
                    ${bill.amount >= 0 ? '+' : ''}¥${Math.abs(bill.amount).toFixed(2)}
                  </div>
                </div>
              `;
            });
            html += '</div>';
          }
          document.getElementById('bills').innerHTML = html;
          document.getElementById('billsSection').style.display = 'block';
        }
      } catch (error) {
        console.error('加载账单列表失败:', error);
      }
    }

    async function loadBillsReport() {
      try {
        const response = await fetch(`${API_BASE}/user/bills/report?days=30`, {
          headers: { 'X-Username': username }
        });
        const result = await response.json();

        if (result.success) {
          const { summary, advice } = result;
          let html = '<h3 style="margin-bottom: 15px;">30 天统计报告</h3>';
          
          html += `
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-label">总收入</div>
                <div class="stat-value positive">+¥${summary.total_income.toFixed(2)}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">总支出</div>
                <div class="stat-value negative">-¥${summary.total_expense.toFixed(2)}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">净结余</div>
                <div class="stat-value ${summary.net_change >= 0 ? 'positive' : 'negative'}">
                  ${summary.net_change >= 0 ? '+' : ''}¥${summary.net_change.toFixed(2)}
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-label">日均</div>
                <div class="stat-value">¥${summary.daily_avg.toFixed(2)}</div>
              </div>
            </div>
          `;

          if (summary.top_merchants.length > 0) {
            html += '<h4 style="margin-top: 15px; margin-bottom: 10px;">消费排名</h4>';
            html += '<div>';
            summary.top_merchants.slice(0, 5).forEach((merchant, index) => {
              html += `
                <div class="bill-row">
                  <span>${index + 1}. ${merchant.merchant}</span>
                  <span style="color: #666;">¥${Math.abs(merchant.amount).toFixed(2)}</span>
                </div>
              `;
            });
            html += '</div>';
          }

          if (advice) {
            html += `<div class="advice-box">${advice.replace(/\n/g, '<br>')}</div>`;
          }

          document.getElementById('report').innerHTML = html;
        }
      } catch (error) {
        console.error('加载报告失败:', error);
      }
    }

    // 标签页切换
    document.querySelectorAll('.tab-button').forEach(button => {
      button.addEventListener('click', () => {
        const tab = button.dataset.tab;
        document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        button.classList.add('active');
        document.getElementById(tab).classList.add('active');
      });
    });
  </script>
</body>
</html>
```

---

## 常见问题 (FAQ)

### Q1: 如何获取 DashScope API Key？
A: 
1. 访问 https://dashscope.aliyuncs.com
2. 注册或登录阿里云账户
3. 在"API密钥"页面创建新的密钥
4. 将密钥配置到服务器的 `.env` 文件中：`DASHSCOPE_API_KEY=your_key_here`

### Q2: 为什么有些账单无法识别？
A: 
- 确保图片清晰，避免拍照角度不佳或过度倾斜
- 检查图片中是否包含完整的账单信息（金额、商户、时间）
- 建议使用 2-5MB 大小的图片，过小可能影响识别
- 尝试重新拍摄或裁剪图片

### Q3: 如何修改已解析的账单数据？
A: 
当前版本不支持直接修改账单。建议联系系统管理员手动调整，或使用 POST /user/bills/adjust 接口（如已实现）。

### Q4: 能否批量上传多张账单？
A: 
当前API不支持批量上传。建议前端实现循环调用，逐张上传处理。

### Q5: 钱包更新后是否可以回滚？
A: 
当前版本的钱包更新不可回滚。建议谨慎上传，确保账单信息准确。

---

## 技术支持

如有任何问题或建议，请联系系统管理员。

**最后更新**: 2024-04-29  
**版本**: 1.0.0
