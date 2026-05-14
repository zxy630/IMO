# 钱包系统后端接口文档

## 接口概览

钱包系统需要以下两个核心接口：

1. **获取钱包余额信息** - 获取三项余额
2. **获取账单列表** - 获取历史收支记录

---

## 1. 获取钱包余额信息

### 接口路径
```
GET /api/wallet/balance
```

### 请求头
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 请求参数
无

### 响应格式

**成功响应 (200):**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "cash_balance": 1234.56,      // 零钱余额 (单位: 元)
    "bank_balance": 9876.54,       // 银行卡余额 (单位: 元)
    "debt_amount": 100.00          // 欠贷金额 (单位: 元)
  }
}
```

**字段说明:**
| 字段 | 类型 | 说明 |
|-----|-----|------|
| cash_balance | decimal | 零钱余额，可直接使用 |
| bank_balance | decimal | 银行卡余额，预留资金 |
| debt_amount | decimal | 欠贷金额，待偿还 |

**错误响应 (4xx/5xx):**
```json
{
  "code": -1,
  "msg": "failed to fetch wallet info",
  "data": null
}
```

---

## 2. 获取账单列表

### 接口路径
```
GET /api/wallet/bills
```

### 请求头
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|-----|-----|-----|------|
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页条数，默认 20 |
| type | string | 否 | 账单类型筛选: all(全部) / income(收入) / expense(支出)，默认 all |

### 请求示例
```
GET /api/wallet/bills?page=1&page_size=20&type=all
```

### 响应格式

**成功响应 (200):**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "bills": [
      {
        "id": "bill_123456",
        "type": "income",                    // income(收入) 或 expense(支出)
        "amount": 100.50,                    // 金额 (单位: 元)
        "description": "签到奖励",           // 账单描述
        "created_at": "2024-04-20 14:30:00", // 创建时间 (格式: YYYY-MM-DD HH:mm:ss)
        "remark": "每日签到获得"             // 备注 (可选)
      },
      {
        "id": "bill_123457",
        "type": "expense",
        "amount": 50.00,
        "description": "充值云服务",
        "created_at": "2024-04-19 10:15:00",
        "remark": "充值订单号: ORDER123"
      }
    ],
    "total": 150,           // 总数 (可选)
    "page": 1,              // 当前页码
    "page_size": 20,        // 每页条数
    "has_more": true        // 是否有更多数据 (可选)
  }
}
```

**字段说明:**
| 字段 | 类型 | 说明 |
|-----|-----|------|
| id | string | 账单ID，唯一标识 |
| type | string | 账单类型: income(收入) 或 expense(支出) |
| amount | decimal | 交易金额，单位元 |
| description | string | 账单描述/标题 |
| created_at | string | 创建时间戳，格式: YYYY-MM-DD HH:mm:ss |
| remark | string | 备注说明 (可选) |

**错误响应 (4xx/5xx):**
```json
{
  "code": -1,
  "msg": "failed to fetch bills",
  "data": null
}
```

---

## 3. 账单类型说明

### 常见收入类型 (income)
- 签到奖励
- 推荐奖励
- 充值发放
- 返现
- 其他收入

### 常见支出类型 (expense)
- 充值消费
- 提现
- 转账
- 购买服务
- 其他支出

---

## 4. 错误码定义

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| -1 | 通用业务错误 |
| 400 | 请求参数错误 |
| 401 | 未授权/token过期 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

---

## 5. 集成说明

### 认证方式
所有接口都需要在请求头中携带有效的 `Bearer Token`：
```
Authorization: Bearer {jwt_token}
```

### 数据格式
- 所有金额字段使用 decimal/float 类型，精确到分（2位小数）
- 所有时间戳采用 ISO 8601 格式或 "YYYY-MM-DD HH:mm:ss" 格式
- 所有响应遵循统一的 JSON 格式

### 分页说明
- 默认每页 20 条记录
- 最大可请求 100 条/页
- 页码从 1 开始

### 超时配置
- 建议单次请求超时时间为 10 秒
- 建议下拉加载更多时的超时为 15 秒

---

## 6. 测试接口示例

**获取钱包余额：**
```curl
curl -X GET \
  http://127.0.0.1:8000/api/wallet/balance \
  -H 'Authorization: Bearer your_token_here' \
  -H 'Content-Type: application/json'
```

**获取账单列表（第1页，每页20条，全部类型）：**
```curl
curl -X GET \
  'http://127.0.0.1:8000/api/wallet/bills?page=1&page_size=20&type=all' \
  -H 'Authorization: Bearer your_token_here' \
  -H 'Content-Type: application/json'
```

**获取收入账单：**
```curl
curl -X GET \
  'http://127.0.0.1:8000/api/wallet/bills?page=1&page_size=20&type=income' \
  -H 'Authorization: Bearer your_token_here' \
  -H 'Content-Type: application/json'
```

---

## 7. 前端实现笔记

所有接口已在 `pages/wallet/wallet.vue` 中集成：

- **fetchWalletInfo()** - 调用余额接口获取余额信息
- **fetchBills()** - 调用账单接口获取历史记录
- 支持分页加载和类型筛选
- 自动处理错误提示和加载状态

