<template>
  <view class="login-container">
    <view class="bg-circle circle-1"></view>
    <view class="bg-circle circle-2"></view>

    <view class="login-box">
      <view class="logo-area">
        <text class="app-name">AI Agent</text>
      </view>

      <view class="input-group">
        <view class="input-item">
          <text class="input-icon">👤</text>
          <input class="uni-input" type="text" v-model="username" placeholder="请输入账号" placeholder-class="placeholder" />
        </view>
        <view class="input-item">
          <text class="input-icon">🔒</text>
          <input class="uni-input" type="password" v-model="password" placeholder="请输入密码" placeholder-class="placeholder" />
        </view>
      </view>

      <!-- 登录按钮 -->
      <button class="login-btn" @click="handleLogin">登 录</button>

      <!-- 注册按钮（样式统一） -->
      <button class="register-btn" @click="handleRegister">注 册</button>

      <!-- 找回密码按钮 -->
      <button class="reset-btn" @click="showResetPasswordDialog">找回密码</button>
    </view>

    <!-- 找回密码弹窗 -->
    <view v-if="showResetDialog" class="dialog-overlay" @click="hideResetPasswordDialog">
      <view class="reset-dialog" @click.stop>
        <view class="dialog-header">
          <text class="dialog-title">忘记密码</text>
          <text class="close-btn" @click="hideResetPasswordDialog">×</text>
        </view>
        <view class="dialog-content">
          <view v-if="!showAnswerInput">
            <view class="input-item">
              <text class="input-icon">👤</text>
              <input class="uni-input" type="text" v-model="resetUsername" placeholder="请输入用户名" placeholder-class="placeholder" />
            </view>
            <button class="submit-btn" @click="getSecurityQuestion">获取密保问题</button>
          </view>
          <view v-else>
            <view class="security-question">{{ securityQuestion }}</view>
            <view class="input-item">
              <text class="input-icon">🔑</text>
              <input class="uni-input" type="text" v-model="securityAnswer" placeholder="请输入密保答案" placeholder-class="placeholder" />
            </view>
            <view class="input-item">
              <text class="input-icon">🔒</text>
              <input class="uni-input" type="password" v-model="newPassword" placeholder="请输入新密码" placeholder-class="placeholder" />
            </view>
            <button class="submit-btn" @click="resetPassword">重置密码</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { buildApiUrl } from '../../config/api'

export default {
  data() {
    return {
      username: '',
      password: '',
      // 找回密码相关数据
      showResetDialog: false,
      resetUsername: '',
      securityQuestion: '',
      securityAnswer: '',
      newPassword: '',
      showAnswerInput: false
    }
  },
  methods: {
    // ------------------------------
    // 登录功能（原逻辑不动）
    // ------------------------------
    async handleLogin() {
      if (!this.username || !this.password) {
        uni.showToast({ title: '请输入账号和密码', icon: 'none' })
        return
      }

      uni.showLoading({ title: '登录中...' })

      uni.request({
        url: buildApiUrl('/auth/login'),
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: { username: this.username, password: this.password },
        success: (res) => {
          console.log('login response:', res.statusCode, res.data)
          const data = res.data || {}
          if (data.success) {
            const nickname = data.nickname
            const avatar = data.avatar
			console.log(avatar)
            uni.setStorageSync('username', this.username)
            uni.setStorageSync('nickname', nickname)
            uni.setStorageSync('avatar', avatar)
            setTimeout(() => {
              uni.showToast({ title: '登录成功', icon: 'success' })
              uni.reLaunch({ url: '/pages/index/index' })
            }, 500)
          } else {
            uni.showToast({ title: data.message || '用户名或密码错误', icon: 'none' })
          }
        },
        fail: () => {
          uni.showToast({ title: '网络异常，请稍后重试', icon: 'none' })
        },
        complete: () => {
          try { uni.hideLoading() } catch (e) {}
        }
      })
    },

    // ------------------------------
    // 注册功能（跳转到注册页面）
    // ------------------------------
    async handleRegister() {
      uni.navigateTo({ url: '/pages/register/register' });
    },

    // ------------------------------
    // 找回密码功能
    // ------------------------------
    showResetPasswordDialog() {
      this.resetUsername = '';
      this.securityQuestion = '';
      this.securityAnswer = '';
      this.newPassword = '';
      this.showAnswerInput = false;
      this.showResetDialog = true;
    },

    hideResetPasswordDialog() {
      this.showResetDialog = false;
    },

    async getSecurityQuestion() {
      if (!this.resetUsername) {
        uni.showToast({ title: '请输入用户名', icon: 'none' });
        return;
      }

      uni.showLoading({ title: '获取密保问题...' });

      uni.request({
        url: buildApiUrl('/auth/get-security-question'), // 如果后端没有此接口，可以用现有接口测试
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: { username: this.resetUsername },
        success: (res) => {
          console.log('get security question response:', res.statusCode, res.data);
          const data = res.data || {};
          if (data.success && data.question) {
            this.securityQuestion = data.question;
            this.showAnswerInput = true; // 这行是关键，应切换视图显示密保问题和答案输入框
          } else {
            uni.showToast({ title: data.message || '该用户未设置密保问题', icon: 'none' });
          }
        },
        fail: (error) => {
          console.error('获取密保问题失败:', error);
          // 如果后端没有提供获取密保问题的接口，可以暂时用注册接口来测试
          // 模拟返回一个测试密保问题
          uni.showToast({ title: '该用户未设置密保问题或服务不可用', icon: 'none' });
        },
        complete: () => {
          try { uni.hideLoading() } catch (e) {}
        }
      });
    },

    async resetPassword() {
      if (!this.resetUsername || !this.securityAnswer || !this.newPassword) {
        uni.showToast({ title: '请填写完整信息', icon: 'none' });
        return;
      }

      uni.showLoading({ title: '重置密码...' });

      uni.request({
        url: buildApiUrl('/auth/reset-password'),
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: {
          username: this.resetUsername,
          security_answer: this.securityAnswer,
          new_password: this.newPassword
        },
        success: (res) => {
          console.log('reset password response:', res.statusCode, res.data);
          const data = res.data || {};
          if (data.success) {
            uni.showToast({ title: '密码重置成功', icon: 'success' });
            setTimeout(() => {
              this.hideResetPasswordDialog();
            }, 1500);
          } else {
            uni.showToast({ title: data.message || '密码重置失败', icon: 'none' });
          }
        },
        fail: () => {
          uni.showToast({ title: '网络异常，请稍后重试', icon: 'none' });
        },
        complete: () => {
          try { uni.hideLoading() } catch (e) {}
        }
      });
    }
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  position: relative;
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  overflow: hidden;
}
.bg-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
  z-index: 1;
}
.circle-1 { width: 300rpx; height: 300rpx; top: -100rpx; left: -100rpx; }
.circle-2 { width: 400rpx; height: 400rpx; bottom: -150rpx; right: -100rpx; }

.login-box {
  position: relative;
  z-index: 10;
  width: 80%;
  padding: 60rpx 40rpx;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  border-radius: 24rpx;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20rpx 40rpx rgba(0, 0, 0, 0.3);
}
.logo-area { display: flex; flex-direction: column; align-items: center; margin-bottom: 60rpx; }
.app-name { font-size: 40rpx; color: #fff; font-weight: bold; letter-spacing: 2rpx; }

.input-group { margin-bottom: 40rpx; }
.input-item {
  display: flex; align-items: center; height: 90rpx;
  background: rgba(255, 255, 255, 0.05); border-radius: 12rpx;
  margin-bottom: 24rpx; padding: 0 24rpx;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.uni-input { flex: 1; margin-left: 20rpx; color: #fff; font-size: 28rpx; }
.placeholder { color: rgba(255, 255, 255, 0.4); }

/* 登录按钮 */
.login-btn {
  width: 100%; height: 90rpx;
  background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
  border-radius: 12rpx; color: #fff; font-size: 32rpx; font-weight: bold;
  display: flex; justify-content: center; align-items: center; border: none;
  box-shadow: 0 10rpx 20rpx rgba(0, 242, 254, 0.3);
  margin-bottom: 20rpx;
}
.login-btn::after { border: none; }

/* 注册按钮（新增样式） */
.register-btn {
  width: 100%; height: 90rpx;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12rpx; color: #fff; font-size: 32rpx;
  display: flex; justify-content: center; align-items: center;
  margin-bottom: 20rpx;
}
.register-btn::after { border: none; }

/* 找回密码按钮 */
.reset-btn {
  width: 100%; height: 90rpx;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12rpx; color: #fff; font-size: 32rpx;
  display: flex; justify-content: center; align-items: center;
}
.reset-btn::after { border: none; }

/* 对话框遮罩层 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

/* 重置密码对话框 */
.reset-dialog {
  width: 80%;
  background: rgba(30, 30, 46, 0.95); // 深色背景
  backdrop-filter: blur(10px);
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 20rpx 40rpx rgba(0, 0, 0, 0.3);
  max-height: 80vh;
  overflow-y: auto;
  color: #fff; // 白色文字
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.dialog-title {
  font-size: 36rpx;
  font-weight: bold;
}

.close-btn {
  font-size: 48rpx;
  cursor: pointer;
  width: 50rpx;
  height: 50rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.dialog-content {
  padding: 30rpx;
  color: #fff; // 确保内容区文字也是白色
}

.security-question {
  background: rgba(255, 255, 255, 0.1); // 浅色半透明背景
  padding: 20rpx;
  border-radius: 12rpx;
  margin-bottom: 30rpx;
  font-size: 28rpx;
  color: #fff; // 白色文字
  line-height: 1.5;
}

.submit-btn {
  width: 100%; height: 90rpx;
  background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
  border-radius: 12rpx; color: #fff; font-size: 32rpx; font-weight: bold;
  display: flex; justify-content: center; align-items: center; border: none;
  box-shadow: 0 10rpx 20rpx rgba(0, 242, 254, 0.3);
  margin-top: 20rpx;
}
.submit-btn::after { border: none; }
</style>