@echo off
REM 运行单元测试脚本

echo 激活虚拟环境...
call f:\Project\RagAgent\.venv\Scripts\activate.bat

echo 安装测试依赖...
pip install pytest pytest-mock

echo 运行单元测试...
pytest tests/ -v

echo 测试完成
pause