#!/usr/bin/env python3
"""
测试 DashScope API 调用的简单脚本
用于验证 API 调用是否正常工作
"""

import os
import base64
import requests
import json
from pathlib import Path

def test_dashscope_api():
    """测试 DashScope API 调用"""

    # 从环境变量获取 API Key
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("❌ 未设置 DASHSCOPE_API_KEY 环境变量")
        return False

    print("🔑 API Key 已配置")

    # 创建一个简单的测试图片 (1x1 像素的 PNG)
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    # API 请求
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-vl-plus",
        "messages": [
            {
                "role": "system",
                "content": "你是一个助手，请简要回答用户的问题。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{test_image_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "这是一张什么图片？请简要描述。"
                    }
                ]
            }
        ],
        "max_tokens": 100
    }

    try:
        print("📡 发送 API 请求...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"📊 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ API 调用成功!")
            print("📄 响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return True
        else:
            print("❌ API 调用失败")
            print(f"📄 错误响应: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 测试 DashScope API 调用")
    print("=" * 50)

    success = test_dashscope_api()

    print("=" * 50)
    if success:
        print("🎉 API 测试通过!")
    else:
        print("💥 API 测试失败，请检查配置和网络连接")