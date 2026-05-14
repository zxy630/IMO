"""
单元测试 - 账单解析服务
测试 parse_bill_image_with_dashscope 函数的各种场景
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.services.bill_parser_service import parse_bill_image_with_dashscope
from app.config import settings


class TestParseBillImageWithDashscope:
    """测试 DashScope 账单图片解析功能"""

    def test_missing_api_key(self):
        """测试 API 密钥未配置的情况"""
        with patch.object(settings, 'DASHSCOPE_API_KEY', None):
            result = parse_bill_image_with_dashscope("fake_base64")

            assert result["success"] is False
            assert "未配置 DASHSCOPE_API_KEY" in result["message"]

    @patch('app.services.bill_parser_service.requests.post')
    def test_successful_parsing(self, mock_post):
        """测试成功的账单解析"""
        # 模拟成功的 API 响应
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": "200",
            "output": {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "transaction_time": "2024-01-15 14:30:00",
                            "merchant_name": "星巴克",
                            "amount": 25.0,
                            "transaction_type": "expense",
                            "payment_method": "支付宝",
                            "account_type": "余额宝",
                            "counterparty": "星巴克咖啡",
                            "actual_amount": 25.0,
                            "status": "completed"
                        })
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        # 设置 API 密钥
        with patch.object(settings, 'DASHSCOPE_API_KEY', 'fake_key'):
            result = parse_bill_image_with_dashscope("fake_base64_image")

        assert result["success"] is True
        assert result["message"] == "账单识别成功"
        assert result["data"]["merchant_name"] == "星巴克"
        assert result["data"]["amount"] == 25.0
        assert result["data"]["transaction_type"] == "expense"

    @patch('app.services.bill_parser_service.requests.post')
    def test_api_call_failure(self, mock_post):
        """测试 API 调用失败的情况"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Connection timeout")
        mock_post.return_value = mock_response

        with patch.object(settings, 'DASHSCOPE_API_KEY', 'fake_key'):
            result = parse_bill_image_with_dashscope("fake_base64_image")

        assert result["success"] is False
        assert "图片解析失败" in result["message"]

    @patch('app.services.bill_parser_service.requests.post')
    def test_api_error_response(self, mock_post):
        """测试 API 返回错误码的情况"""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": "400",
            "message": "Invalid request"
        }
        mock_post.return_value = mock_response

        with patch.object(settings, 'DASHSCOPE_API_KEY', 'fake_key'):
            result = parse_bill_image_with_dashscope("fake_base64_image")

        assert result["success"] is False
        assert "API调用失败" in result["message"]

    @patch('app.services.bill_parser_service.requests.post')
    def test_json_parsing_from_markdown(self, mock_post):
        """测试从 markdown 代码块中解析 JSON"""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": "200",
            "output": {
                "choices": [{
                    "message": {
                        "content": """```json
{
    "transaction_time": "2024-01-15 14:30:00",
    "merchant_name": "麦当劳",
    "amount": 15.5,
    "transaction_type": "expense",
    "payment_method": "微信",
    "account_type": "零钱",
    "counterparty": "麦当劳餐厅",
    "actual_amount": 15.5,
    "status": "completed"
}
```"""
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        with patch.object(settings, 'DASHSCOPE_API_KEY', 'fake_key'):
            result = parse_bill_image_with_dashscope("fake_base64_image")

        assert result["success"] is True
        assert result["data"]["merchant_name"] == "麦当劳"
        assert result["data"]["amount"] == 15.5

    @patch('app.services.bill_parser_service.requests.post')
    def test_json_parsing_from_plain_text(self, mock_post):
        """测试从纯文本中解析 JSON"""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": "200",
            "output": {
                "choices": [{
                    "message": {
                        "content": """根据图片分析，结果如下：
{
    "transaction_time": "2024-01-15 14:30:00",
    "merchant_name": "肯德基",
    "amount": 30.0,
    "transaction_type": "expense",
    "payment_method": "支付宝",
    "account_type": "花呗",
    "counterparty": "KFC餐厅",
    "actual_amount": 30.0,
    "status": "completed"
}
这是解析结果。"""
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        with patch.object(settings, 'DASHSCOPE_API_KEY', 'fake_key'):
            result = parse_bill_image_with_dashscope("fake_base64_image")

        assert result["success"] is True
        assert result["data"]["merchant_name"] == "肯德基"
        assert result["data"]["amount"] == 30.0

    @patch('app.services.bill_parser_service.requests.post')
    def test_invalid_json_response(self, mock_post):
        """测试无效的 JSON 响应"""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": "200",
            "output": {
                "choices": [{
                    "message": {
                        "content": "这是一张支付账单，金额25元。"
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        with patch.object(settings, 'DASHSCOPE_API_KEY', 'fake_key'):
            result = parse_bill_image_with_dashscope("fake_base64_image")

        assert result["success"] is False
        assert "无法解析返回的数据格式" in result["message"]

    @patch('app.services.bill_parser_service.requests.post')
    def test_missing_required_fields(self, mock_post):
        """测试返回数据缺少必要字段"""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": "200",
            "output": {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "merchant_name": "星巴克",
                            "amount": 25.0
                            # 缺少 transaction_time 和 transaction_type
                        })
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        with patch.object(settings, 'DASHSCOPE_API_KEY', 'fake_key'):
            result = parse_bill_image_with_dashscope("fake_base64_image")

        assert result["success"] is False
        assert "返回数据缺少必要字段" in result["message"]

    @patch('app.services.bill_parser_service.requests.post')
    def test_empty_content_response(self, mock_post):
        """测试 API 返回空内容"""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": "200",
            "output": {
                "choices": [{
                    "message": {
                        "content": ""
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        with patch.object(settings, 'DASHSCOPE_API_KEY', 'fake_key'):
            result = parse_bill_image_with_dashscope("fake_base64_image")

        assert result["success"] is False
        assert result["message"] == "API返回内容为空"

    @patch('app.services.bill_parser_service.requests.post')
    def test_income_transaction(self, mock_post):
        """测试收入类型交易"""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": "200",
            "output": {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "transaction_time": "2024-01-15 14:30:00",
                            "merchant_name": "支付宝",
                            "amount": 100.0,
                            "transaction_type": "income",
                            "payment_method": "支付宝",
                            "account_type": "余额宝",
                            "counterparty": "用户转账",
                            "actual_amount": 100.0,
                            "status": "completed"
                        })
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        with patch.object(settings, 'DASHSCOPE_API_KEY', 'fake_key'):
            result = parse_bill_image_with_dashscope("fake_base64_image")

        assert result["success"] is True
        assert result["data"]["transaction_type"] == "income"
        assert result["data"]["amount"] == 100.0