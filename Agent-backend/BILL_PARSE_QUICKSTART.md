# 图片账单解析功能 - 快速开始指南

## 📚 文件清单

实现的功能相关文件：

| 文件 | 类型 | 说明 |
|------|------|------|
| `app/services/bill_parser_service.py` | 新增 | 核心图片解析服务，包含AI识别和数据处理逻辑 |
| `app/routers/user_features.py` | 已更新 | 添加3个新API接口 |
| `app/schemas/billing.py` | 已更新 | 添加账单解析相关数据模型 |
| `app/config.py` | 已更新 | 添加账单上传目录配置 |
| `BILL_PARSE_API.md` | 新增 | 完整的API文档和前端调用示例 |
| `BILL_PARSE_QUICKSTART.md` | 新增 | 本文件 |

---

## 🚀 快速部署

### 1. 前置条件检查

```bash
# 确保虚拟环境已激活
cd f:\Project\RagAgent\Agent-backend

# 检查依赖是否完整
f:\Project\RagAgent\.venv\Scripts\python.exe -c "import requests; print('✅ requests 模块已安装')"
```

### 2. 环境配置

编辑 `.env` 文件，添加 DashScope API Key：

```env
DASHSCOPE_API_KEY=your_api_key_here
```

获取方式：
1. 访问 https://dashscope.aliyuncs.com
2. 创建新的API密钥
3. 粘贴到上面的配置中

### 3. 创建上传目录

```bash
# 创建账单图片上传目录（自动创建）
# 系统会在首次上传时自动创建
# 也可手动创建：
mkdir -p f:\Project\RagAgent\Agent-backend\uploads\bills
```

### 4. 启动服务

```bash
cd f:\Project\RagAgent\Agent-backend

# 使用已有的启动脚本
run_server.bat

# 或使用命令行
set PYTHONPATH=%CD%
f:\Project\RagAgent\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🎯 功能使用

### 场景1：上传支付宝花呗账单

```javascript
// 1. 准备图片文件
const file = document.getElementById('file-input').files[0];

// 2. 创建表单数据
const formData = new FormData();
formData.append('file', file);

// 3. 上传并解析
const response = await fetch(
  'http://localhost:8000/user/bills/parse-image',
  {
    method: 'POST',
    headers: {
      'X-Username': 'testuser'
    },
    body: formData
  }
);

const result = await response.json();

// 4. 处理结果
if (result.success) {
  console.log('✅ 账单已创建');
  console.log('账单ID:', result.bill_id);
  console.log('新余额:', result.wallet_balance);
  console.log('解析信息:', {
    商户: result.parsed_data.merchant_name,
    金额: result.parsed_data.amount,
    时间: result.parsed_data.transaction_time,
    类型: result.parsed_data.payment_method
  });
}
```

### 场景2：查看最近的账单

```javascript
const response = await fetch(
  'http://localhost:8000/user/bills/list?limit=20',
  {
    headers: { 'X-Username': 'testuser' }
  }
);

const { bills, total_count } = await response.json();

console.log(`共 ${total_count} 条账单：`);
bills.forEach(bill => {
  const type = bill.transaction_type === 'income' ? '收入' : '支出';
  const sign = bill.amount >= 0 ? '+' : '';
  console.log(`${bill.transaction_time} | ${bill.merchant_name} | ${sign}¥${bill.amount} | ${type}`);
});
```

### 场景3：生成账单报告

```javascript
// 获取最近30天的账单统计
const response = await fetch(
  'http://localhost:8000/user/bills/report?days=30',
  {
    headers: { 'X-Username': 'testuser' }
  }
);

const { summary, wallet_balance, advice } = await response.json();

console.log('📊 账单统计：');
console.log(`总收入: ¥${summary.total_income}`);
console.log(`总支出: ¥${summary.total_expense}`);
console.log(`净结余: ¥${summary.net_change}`);
console.log(`日均: ¥${summary.daily_avg}`);
console.log(`当前余额: ¥${wallet_balance}`);
console.log('\n💡 AI建议:\n' + advice);
```

---

## 📋 API 速查表

### 上传账单
```
POST /user/bills/parse-image
Header: X-Username: testuser
Body: multipart/form-data (file)

Response:
{
  "success": true,
  "message": "账单解析并创建成功",
  "bill_id": "...",
  "parsed_data": { ... },
  "wallet_balance": 9971.50
}
```

### 获取账单列表
```
GET /user/bills/list?limit=50
Header: X-Username: testuser

Response:
{
  "success": true,
  "bills": [ ... ],
  "total_count": 10
}
```

### 获取统计报告
```
GET /user/bills/report?days=30
Header: X-Username: testuser

Response:
{
  "success": true,
  "summary": { ... },
  "wallet_balance": 10000.00,
  "advice": "..."
}
```

---

## 🧪 测试方法

### 使用 cURL 测试

```bash
# 1. 测试上传（Windows下使用 Invoke-WebRequest）
$file = Get-Item "C:\path\to\bill_image.jpg"
$response = Invoke-WebRequest -Uri "http://localhost:8000/user/bills/parse-image" `
  -Method Post `
  -Headers @{"X-Username" = "testuser"} `
  -Form @{file = $file}
$response.Content | ConvertFrom-Json | ConvertTo-Json

# 2. 获取账单列表
Invoke-WebRequest -Uri "http://localhost:8000/user/bills/list" `
  -Headers @{"X-Username" = "testuser"} | Select-Object -ExpandProperty Content | ConvertFrom-Json

# 3. 获取统计报告
Invoke-WebRequest -Uri "http://localhost:8000/user/bills/report?days=30" `
  -Headers @{"X-Username" = "testuser"} | Select-Object -ExpandProperty Content | ConvertFrom-Json
```

### 使用 Python 测试

```python
import requests
import json

BASE_URL = "http://localhost:8000"
USERNAME = "testuser"
HEADERS = {"X-Username": USERNAME}

# 测试1：上传账单
def test_upload_bill():
    with open("bill_screenshot.jpg", "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{BASE_URL}/user/bills/parse-image",
            headers=HEADERS,
            files=files
        )
    print("上传结果:", response.json())

# 测试2：获取列表
def test_get_bills_list():
    response = requests.get(
        f"{BASE_URL}/user/bills/list?limit=50",
        headers=HEADERS
    )
    data = response.json()
    print(f"账单总数: {data['total_count']}")
    for bill in data['bills'][:5]:
        print(f"  - {bill['transaction_time']}: {bill['merchant_name']} ¥{bill['amount']}")

# 测试3：获取报告
def test_get_report():
    response = requests.get(
        f"{BASE_URL}/user/bills/report?days=30",
        headers=HEADERS
    )
    summary = response.json()['summary']
    print(f"收入: ¥{summary['total_income']}")
    print(f"支出: ¥{summary['total_expense']}")
    print(f"净结余: ¥{summary['net_change']}")

# 运行测试
if __name__ == "__main__":
    test_upload_bill()
    test_get_bills_list()
    test_get_report()
```

---

## ⚠️ 常见问题排查

### 问题1: 上传时返回 "未配置 DASHSCOPE_API_KEY"

**解决方案**：
```bash
# 检查 .env 文件
cat .env | findstr DASHSCOPE

# 确保已添加：
# DASHSCOPE_API_KEY=sk-xxxxxx

# 重启服务使配置生效
```

### 问题2: 文件上传成功但无法识别

**解决方案**：
- ✅ 检查图片是否清晰（建议2-5MB）
- ✅ 确保账单信息完整（包含金额、商户、时间）
- ✅ 避免拍照角度过度倾斜
- ✅ 重新拍摄或使用原始截图

### 问题3: "钱包余额未更新"

**解决方案**：
- ✅ 确认账单解析成功（parsed_data 不为空）
- ✅ 检查用户是否存在
- ✅ 查看返回的 wallet_balance 字段

### 问题4: API 响应超时

**解决方案**：
```javascript
// 增加超时时间
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 60000); // 60秒

try {
  const response = await fetch(url, {
    signal: controller.signal,
    // ... 其他选项
  });
} finally {
  clearTimeout(timeoutId);
}
```

### 问题5: CORS 错误（跨域问题）

**解决方案**：
在 `app/main.py` 添加 CORS 配置：
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 💾 数据存储位置

- **图片文件**: `uploads/bills/` 目录
- **账单记录**: ChromaDB 中的 `bills` 集合
- **用户信息**: ChromaDB 中的 `users` 集合（wallet_balance 更新）

---

## 📊 性能参考

| 操作 | 平均耗时 | 说明 |
|------|--------|------|
| 图片上传解析 | 3-8秒 | 取决于网络和API响应 |
| 获取账单列表 | <100ms | 本地查询 |
| 生成统计报告 | <200ms | 计算10-100条账单 |

---

## 🔐 安全建议

1. **API认证**：生产环境下改进X-Username认证机制
2. **文件验证**：定期清理过期账单图片
3. **访问控制**：限制API调用频率（当前建议1秒/次）
4. **数据加密**：对敏感字段进行加密存储
5. **日志监控**：监控异常上传或频繁调用

---

## 📞 需要帮助？

1. 查看完整API文档：`BILL_PARSE_API.md`
2. 检查服务日志：`app/routers/user_features.py` 中有详细的日志输出
3. 联系系统管理员获取支持

---

**最后更新**: 2024-04-29  
**版本**: 1.0.0  
**支持**: Python 3.7+, FastAPI 0.100+
