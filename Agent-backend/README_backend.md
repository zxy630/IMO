# Python 后端登录示例（FastAPI）

## 环境准备

- 安装 Python 3.10+
- 在项目根目录安装依赖：

```bash
pip install -r requirements.txt
```

## 初始化数据库（ChromaDB）

```bash
python -m app.initial_data
```

初始化后会生成 ChromaDB 持久化目录 `chroma_data/`，并插入一个测试用户：

- 用户名：`test`
- 密码：`123456`

## 启动后端服务

在项目根目录执行：

```bash
run_server.bat
```

或直接使用命令：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

接口文档可访问：`http://127.0.0.1:8000/docs`

## 登录接口说明

- 请求方式：`POST /auth/login`
- 请求头：`Content-Type: application/json`
- 请求体示例：

```json
{
  "username": "test",
  "password": "123456"
}
```

- 响应示例（成功）：

```json
{
  "success": true,
  "message": "登录成功",
  "username": "test"
}
```

- 响应示例（失败）：

```json
{
  "success": false,
  "message": "用户名或密码错误",
  "username": null
}
```

## Uniapp 调用示例

```js
uni.request({
  url: 'http://127.0.0.1:8000/auth/login',
  method: 'POST',
  header: {
    'Content-Type': 'application/json'
  },
  data: {
    username: this.username,
    password: this.password
  },
  success: (res) => {
    if (res.data.success) {
      uni.showToast({
        title: '登录成功',
        icon: 'success'
      })
      // 在这里做登录后的跳转或状态保存
    } else {
      uni.showToast({
        title: res.data.message || '登录失败',
        icon: 'none'
      })
    }
  },
  fail: () => {
    uni.showToast({
      title: '网络错误',
      icon: 'none'
    })
  }
})
```

