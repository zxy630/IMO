<template>
  <view class="about-page">
    <view class="nav-bar" @click.stop>
      <view class="nav-left" @click="goBack">
        <text class="back-icon"><</text>
      </view>
      <view class="nav-title">关于</view>
      <view class="nav-right"></view>
    </view>

    <view class="content">
      <view class="hero">
        <image class="logo" src="/static/ailogo.jpg" mode="aspectFill"></image>
        <view class="hero-text">
          <text class="app-name">钱宝</text>
          <text class="tagline">你的随身智能家庭账本小助手</text>
        </view>
      </view>

      <view class="card">
        <text class="card-title">功能介绍</text>
        <view class="feature">
          <text class="dot">•</text>
          <text class="txt">支持多模型对话（可在聊天页切换模型）</text>
        </view>
        <view class="feature">
          <text class="dot">•</text>
          <text class="txt">支持新对话/续聊（会话管理）</text>
        </view>
        <view class="feature">
          <text class="dot">•</text>
          <text class="txt">历史会话列表与会话消息查看</text>
        </view>
        <view class="feature">
          <text class="dot">•</text>
          <text class="txt">账号体系：注册、登录、找回密码</text>
        </view>
      </view>

      <view class="card">
        <text class="card-title">开发版本</text>
        <view class="kv">
          <text class="k">版本号</text>
          <text class="v">{{ version }}</text>
        </view>
        <view class="kv">
          <text class="k">构建时间</text>
          <text class="v">{{ buildTime }}</text>
        </view>
        <view class="kv">
          <text class="k">运行环境</text>
          <text class="v">{{ platform }}</text>
        </view>
      </view>

      <view class="footer">
        <text class="footer-text">© {{ new Date().getFullYear() }} AI Agent</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      version: 'v0.1.0-dev',
      buildTime: '2026-04-14',
      platform: ''
    }
  },
  onLoad() {
    const sys = uni.getSystemInfoSync()
    this.platform = `${sys.platform || ''} ${sys.system || ''}`.trim()
  },
  methods: {
    goBack() {
      uni.navigateBack()
    }
  }
}
</script>

<style lang="scss" scoped>
.about-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.nav-bar {
  height: 90rpx;
  padding-top: var(--status-bar-height);
  background: #fff;
  display: flex;
  align-items: center;
  padding-left: 20rpx;
  padding-right: 20rpx;
  border-bottom: 1px solid #f0f0f0;
}
.nav-left {
  width: 80rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
}
.back-icon {
  font-size: 40rpx;
  color: #A9A9A9;
}
.nav-title {
  flex: 1;
  text-align: center;
  font-size: 34rpx;
  font-weight: 700;
  color: #111827;
}
.nav-right {
  width: 80rpx;
}

.content {
  padding: 24rpx 24rpx 40rpx;
}

.hero {
  background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
  border-radius: 22rpx;
  padding: 26rpx;
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}
.logo {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  margin-right: 20rpx;
  background: rgba(255, 255, 255, 0.12);
}
.hero-text {
  display: flex;
  flex-direction: column;
}
.app-name {
  color: #fff;
  font-size: 38rpx;
  font-weight: 800;
}
.tagline {
  margin-top: 6rpx;
  color: rgba(255, 255, 255, 0.8);
  font-size: 24rpx;
}

.card {
  background: #fff;
  border-radius: 22rpx;
  padding: 22rpx;
  margin-bottom: 18rpx;
  border: 1px solid rgba(15, 23, 42, 0.06);
}
.card-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 14rpx;
}
.feature {
  display: flex;
  align-items: flex-start;
  margin-top: 10rpx;
}
.dot {
  width: 24rpx;
  color: #111827;
  line-height: 1.5;
}
.txt {
  flex: 1;
  color: rgba(15, 23, 42, 0.82);
  font-size: 26rpx;
  line-height: 1.5;
}

.kv {
  display: flex;
  align-items: center;
  padding: 10rpx 0;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
}
.kv:first-of-type {
  border-top: none;
}
.k {
  width: 160rpx;
  color: rgba(15, 23, 42, 0.62);
  font-size: 24rpx;
}
.v {
  flex: 1;
  color: #0f172a;
  font-size: 24rpx;
  font-weight: 600;
}

.footer {
  padding-top: 10rpx;
  display: flex;
  justify-content: center;
}
.footer-text {
  color: rgba(15, 23, 42, 0.5);
  font-size: 22rpx;
}
</style>

