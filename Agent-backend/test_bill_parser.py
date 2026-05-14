#!/usr/bin/env python3
"""
图片账单智能解析功能 - 测试脚本
用于验证所有API接口是否正常工作
"""

import requests
import json
import sys
from pathlib import Path
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "testuser"
HEADERS = {"X-Username": TEST_USERNAME}

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text: str):
    """打印测试头"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text: str):
    """打印信息"""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")

def print_data(title: str, data: Dict[str, Any]):
    """打印JSON数据"""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_health_check() -> bool:
    """测试服务器是否运行"""
    print_header("测试 1: 服务器健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print_success("服务器正在运行")
            print_info(f"API文档地址: {BASE_URL}/docs")
            return True
        else:
            print_error(f"服务器返回异常状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"无法连接到服务器: {BASE_URL}")
        print_info("请确保服务器已启动: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"健康检查失败: {str(e)}")
        return False

def test_get_profile() -> bool:
    """测试获取用户资料"""
    print_header("测试 2: 获取用户资料 (GET /user/profile)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/user/profile",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_success("用户资料获取成功")
                print_data("返回数据", data)
                return True
            else:
                print_error(f"请求失败: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP 状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False

def test_upload_bill_without_file() -> bool:
    """测试上传账单（无效请求）"""
    print_header("测试 3: 上传账单接口可用性 (POST /user/bills/parse-image)")
    
    try:
        # 发送无文件的请求来检查端点是否存在
        response = requests.post(
            f"{BASE_URL}/user/bills/parse-image",
            headers=HEADERS,
            timeout=10
        )
        
        # 预期会返回 422（验证错误）或类似错误
        if response.status_code in [200, 422, 400]:
            print_success("接口已注册并可响应")
            print_info(f"状态码: {response.status_code} (预期的验证错误)")
            return True
        else:
            print_error(f"意外的状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False

def test_get_bills_list() -> bool:
    """测试获取账单列表"""
    print_header("测试 4: 获取账单列表 (GET /user/bills/list)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/user/bills/list?limit=10",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("账单列表获取成功")
            print_data("返回数据", {
                "success": data.get("success"),
                "message": data.get("message"),
                "total_count": data.get("total_count"),
                "bills_count": len(data.get("bills", []))
            })
            
            if data.get("bills"):
                print_info(f"账单总数: {data.get('total_count')}")
                print("\n最近账单列表:")
                for i, bill in enumerate(data.get("bills", [])[:3], 1):
                    print(f"  {i}. {bill.get('merchant_name')} | "
                          f"¥{bill.get('amount')} | "
                          f"{bill.get('transaction_time')}")
            else:
                print_info("暂无账单记录")
            
            return True
        else:
            print_error(f"HTTP 状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False

def test_get_bills_report() -> bool:
    """测试获取账单报告"""
    print_header("测试 5: 获取账单统计报告 (GET /user/bills/report)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/user/bills/report?days=30",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_success("账单报告生成成功")
                
                summary = data.get("summary", {})
                print_data("统计汇总", {
                    "总收入": f"¥{summary.get('total_income', 0):.2f}",
                    "总支出": f"¥{summary.get('total_expense', 0):.2f}",
                    "净结余": f"¥{summary.get('net_change', 0):.2f}",
                    "账单数": summary.get('bill_count', 0),
                    "日均": f"¥{summary.get('daily_avg', 0):.2f}",
                    "当前余额": f"¥{data.get('wallet_balance', 0):.2f}"
                })
                
                if data.get("advice"):
                    print(f"\n💡 AI建议:")
                    for line in data.get("advice", "").split("\n"):
                        if line.strip():
                            print(f"   {line}")
                
                return True
            else:
                print_error(f"报告生成失败: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP 状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False

def test_imports() -> bool:
    """测试Python模块导入"""
    print_header("测试 0: Python模块检查")
    
    modules = [
        ("requests", "HTTP请求库"),
        ("chromadb", "向量数据库"),
        ("fastapi", "Web框架"),
        ("pydantic", "数据验证"),
    ]
    
    all_ok = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print_success(f"{module_name:15} - {description}")
        except ImportError:
            print_error(f"{module_name:15} - {description} (未安装)")
            all_ok = False
    
    return all_ok

def main():
    """主测试函数"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{'图片账单智能解析功能 - 综合测试':^60}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    results = {}
    
    # 测试顺序
    tests = [
        ("模块检查", test_imports),
        ("服务器健康", test_health_check),
        ("用户资料", test_get_profile),
        ("账单接口", test_upload_bill_without_file),
        ("账单列表", test_get_bills_list),
        ("统计报告", test_get_bills_report),
    ]
    
    # 执行测试
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print_error("\n测试被中断")
            sys.exit(1)
        except Exception as e:
            print_error(f"测试异常: {str(e)}")
            results[test_name] = False
    
    # 输出测试总结
    print_header("测试总结")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n总计: {total} 项测试")
    print(f"通过: {Colors.GREEN}{passed}{Colors.RESET}")
    print(f"失败: {Colors.RED}{total - passed}{Colors.RESET}\n")
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✅ 通过{Colors.RESET}" if result else f"{Colors.RED}❌ 失败{Colors.RESET}"
        print(f"  {test_name:15} {status}")
    
    print()
    
    if passed == total:
        print_success("所有测试通过！功能已就绪。")
        print_info("完整API文档: http://localhost:8000/docs")
        print_info("完整API文档: http://localhost:8000/redoc")
        return 0
    else:
        print_error("部分测试失败，请检查日志。")
        print_info("详见: BILL_PARSE_QUICKSTART.md")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_error("\n\n测试被用户中止")
        sys.exit(1)
