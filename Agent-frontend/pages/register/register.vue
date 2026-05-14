<template>
  <view class="register-container">
    <view class="bg-circle circle-1"></view>
    <view class="bg-circle circle-2"></view>

    <view class="register-box">
      <view class="logo-area">
        <text class="app-name">AI Agent</text>
      </view>

      <view class="input-group">
        <view class="avatar-upload">
          <image class="avatar-preview" :src="avatarPreview || defaultAvatar" mode="aspectFill"></image>
          <button class="avatar-btn" @click="chooseAvatar">上传头像</button>
        </view>

        <view class="input-item">
          <text class="input-icon">👤</text>
          <input class="uni-input" type="text" v-model="username" placeholder="请输入用户名" placeholder-class="placeholder" />
        </view>

        <view class="input-item">
          <text class="input-icon">🔒</text>
          <input class="uni-input" type="password" v-model="password" placeholder="请输入密码" placeholder-class="placeholder" />
        </view>

        <view class="input-item">
          <text class="input-icon">📛</text>
          <input class="uni-input" type="text" v-model="nickname" placeholder="请输入昵称（可选）" placeholder-class="placeholder" />
        </view>

        <view class="input-item">
          <text class="input-icon">❓</text>
          <input class="uni-input" type="text" v-model="securityQuestion" placeholder="请输入密保问题" placeholder-class="placeholder" />
        </view>

        <view class="input-item">
          <text class="input-icon">🔑</text>
          <input class="uni-input" type="text" v-model="securityAnswer" placeholder="请输入密保答案" placeholder-class="placeholder" />
        </view>
      </view>

      <!-- 注册按钮 -->
      <button class="register-btn" @click="handleRegister">注 册</button>

      <!-- 返回登录按钮 -->
      <button class="login-btn" @click="goToLogin">返回登录</button>
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
      nickname: '',
      avatarFilePath: '',
      avatarPreview: '',
      defaultAvatar: '/static/logo.png',
      securityQuestion: '',
      securityAnswer: ''
    }
  },
  methods: {
    chooseAvatar() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          const filePath = (res.tempFilePaths && res.tempFilePaths[0]) || ''
          this.avatarFilePath = filePath
          this.avatarPreview = filePath
        }
      })
    },
    async handleRegister() {
      if (!this.username || !this.password || !this.securityQuestion || !this.securityAnswer) {
        uni.showToast({ title: '请填写所有必填项', icon: 'none' })
        return
      }

      uni.showLoading({ title: '注册中...' })

      const handleSuccess = (data) => {
        if (data.success) {
          uni.showToast({ title: '注册成功，请登录', icon: 'success' })
          setTimeout(() => {
            uni.navigateTo({ url: '/pages/login/login' })
          }, 1500)
        } else {
          uni.showToast({ title: data.message || '注册失败', icon: 'none' })
        }
      }

      const handleFail = () => {
        uni.showToast({ title: '网络异常，注册失败', icon: 'none' })
      }

      if (this.avatarFilePath) {
        uni.uploadFile({
          url: buildApiUrl('/auth/register'),
          filePath: this.avatarFilePath,
          name: 'avatar',
          formData: {
            username: this.username,
            password: this.password,
            nickname: this.nickname || '',
            security_question: this.securityQuestion,
            security_answer: this.securityAnswer
          },
          success: (uploadRes) => {
            let data = {}
            try {
              data = JSON.parse(uploadRes.data || '{}')
            } catch (e) {
              data = {}
            }
            handleSuccess(data)
          },
          fail: handleFail,
          complete: () => {
            try { uni.hideLoading() } catch (e) {}
          }
        })
        return
      }

      uni.request({
        url: buildApiUrl('/auth/register'),
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: {
          username: this.username,
          password: this.password,
          nickname: this.nickname || '',
          avatar: '',
          security_question: this.securityQuestion,
          security_answer: this.securityAnswer
        },
        success: (res) => {
          const data = res.data || {}
          handleSuccess(data)
        },
        fail: handleFail,
        complete: () => {
          try { uni.hideLoading() } catch (e) {}
        }
      })
    },

    goToLogin() {
      uni.navigateTo({ url: '/pages/login/login' })
    }
  }
}
</script>

<style lang="scss" scoped>
.register-container {
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

.register-box {
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
.logo-area { display: flex; flex-direction: column; align-items: center; margin-bottom: 40rpx; }
.app-name { font-size: 40rpx; color: #fff; font-weight: bold; letter-spacing: 2rpx; }

.input-group { margin-bottom: 40rpx; }
.avatar-upload {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
}
.avatar-preview {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  margin-right: 24rpx;
  border: 1px solid rgba(255, 255, 255, 0.2);
}
.avatar-btn {
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 28rpx;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  border-radius: 36rpx;
  font-size: 26rpx;
}
.avatar-btn::after {
  border: none;
}
.input-item {
  display: flex; align-items: center; height: 90rpx;
  background: rgba(255, 255, 255, 0.05); border-radius: 12rpx;
  margin-bottom: 24rpx; padding: 0 24rpx;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.uni-input { flex: 1; margin-left: 20rpx; color: #fff; font-size: 28rpx; }
.placeholder { color: rgba(255, 255, 255, 0.4); }

/* 注册按钮 */
.register-btn {
  width: 100%; height: 90rpx;
  background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
  border-radius: 12rpx; color: #fff; font-size: 32rpx; font-weight: bold;
  display: flex; justify-content: center; align-items: center; border: none;
  box-shadow: 0 10rpx 20rpx rgba(0, 242, 254, 0.3);
  margin-bottom: 20rpx;
}
.register-btn::after { border: none; }

/* 返回登录按钮 */
.login-btn {
  width: 100%; height: 90rpx;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12rpx; color: #fff; font-size: 32rpx;
  display: flex; justify-content: center; align-items: center;
}
.login-btn::after { border: none; }
</style>