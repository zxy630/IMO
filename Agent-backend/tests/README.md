# 单元测试说明

## 账单解析服务单元测试

### 测试覆盖的功能
- `parse_bill_image_with_dashscope()` 函数的完整测试覆盖

### 测试场景
1. **API 密钥未配置** - 验证错误处理
2. **成功解析** - 完整的账单数据解析
3. **API 调用失败** - 网络异常处理
4. **API 错误响应** - DashScope API 错误码处理
5. **JSON 解析** - 从 markdown 代码块和纯文本中提取 JSON
6. **无效响应** - 无法解析的返回内容
7. **字段验证** - 必要字段缺失的处理
8. **空内容响应** - API 返回空内容的处理
9. **收入交易** - 收入类型账单的处理

### 运行测试

#### 方法1：使用批处理脚本
```bash
run_tests.bat
```

#### 方法2：手动运行
```bash
# 激活虚拟环境
f:\Project\RagAgent\.venv\Scripts\activate

# 安装测试依赖
pip install pytest pytest-mock

# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_bill_parser_service.py -v

# 运行特定测试方法
pytest tests/test_bill_parser_service.py::TestParseBillImageWithDashscope::test_successful_parsing -v
```

### 测试依赖
- `pytest` - 测试框架
- `pytest-mock` - Mock 支持

### 注意事项
- 所有外部 API 调用都被 mock，不需要真实的 DashScope API 密钥
- 测试使用模拟数据，确保快速执行
- 测试覆盖了正常和异常情况的处理