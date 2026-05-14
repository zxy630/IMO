<template>
  <view class="profile-page">
    <view class="profile-container">
      <view class="profile-header">
        <view class="nav-back" @click="goBack"><text>‹</text></view>
        <text class="profile-title">个人中心</text>
        <view class="nav-space"></view>
      </view>

      <scroll-view class="profile-content" scroll-y :scroll-top="0">
        <view class="section card-section">
          <text class="section-title">头像与昵称</text>
          <view class="avatar-panel">
            <image
              class="avatar-preview"
              :src="avatarPreview || defaultAvatar"
              mode="aspectFill"
              @click="chooseAvatar"
            ></image>
            <view class="avatar-details">
              <text class="label">点击头像更换</text>
              <text class="hint">支持本地上传并实时预览</text>
              <view class="action-row">
                <view class="button" @click="chooseAvatar">上传头像</view>
                <view class="button secondary" @click="removeAvatar">移除头像</view>
              </view>
            </view>
          </view>

          <view class="field-row">
            <text class="field-label">昵称 / 用户名</text>
            <input
              class="field-input"
              v-model="username"
              placeholder="请输入昵称或用户名"
              placeholder-style="color: #999"
            />
          </view>

          <view class="button primary" :class="{disabled: isSaving}" @click="saveProfile">
            <text>{{ isSaving ? '保存中...' : '保存设置' }}</text>
          </view>
        </view>

        <view class="section member-section">
          <text class="section-title">会员升级</text>
          <view class="member-status">
            <text class="member-label">当前身份</text>
            <text class="member-value" :class="{active: isMember}">{{ roleLabel }}</text>
          </view>
          <text class="member-desc">
            升级为会员后，可解锁并使用 DeepSeek 系列模型，获得更高级的对话能力与服务权限。
          </text>
          <view class="button upgrade" :class="{disabled: isMember || isUpgrading}" @click="upgradeMembership">
            <text>{{ isMember ? '已是顶级会员' : isUpgrading ? '升级中...' : '立即升级' }}</text>
          </view>

          <view class="benefits-panel">
            <text class="benefits-title">会员权益说明</text>
            <view class="benefit-item" v-for="(item, index) in memberBenefits" :key="index">
              <text class="bullet">·</text>
              <text class="benefit-text">{{ item }}</text>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
import { API_BASE_URL, buildApiUrl } from '../../config/api'

export default {
  data() {
    return {
      username: '',
      avatarPreview: '',
      avatarFilePath: '',
      roleCode: 1,
      isSaving: false,
      isUpgrading: false,
      defaultAvatar: '/static/logo.png',
      memberBenefits: [
        '解锁 DeepSeek 系列模型',
        '更高级对话理解与生成能力',
        '更快的响应速度与优先服务',
        '专属会员功能与权限扩展'
      ]
    }
  },
  computed: {
    roleLabel() {
      switch (this.roleCode) {
        case 2:
          return 'VIP'
        case 3:
          return 'SVIP'
        default:
          return '普通用户'
      }
    },
    isMember() {
      return this.roleCode == 3
    }
  },
  onShow() {
    this.loadProfile()
    this.fetchMembershipStatus()
  },
  methods: {
    goBack() {
      uni.navigateBack()
    },
    normalizeAvatarUrl(rawAvatar) {
      const avatar = (rawAvatar || '').trim()
      if (!avatar) return ''
      if (/^https?:\/\//i.test(avatar)) return avatar
      if (avatar.startsWith('/')) return `${API_BASE_URL}${avatar}`
      return `${API_BASE_URL}/${avatar}`
    },
    loadProfile() {
      const username = uni.getStorageSync('username') || ''
      const nickname = uni.getStorageSync('nickname') || ''
      const avatar = uni.getStorageSync('avatar') || ''
      const storedRoleCode = Number(uni.getStorageSync('role_code') || 1)

      this.username = nickname || username
      this.avatarPreview = this.normalizeAvatarUrl(avatar) || this.defaultAvatar
      this.roleCode = [1, 2, 3].includes(storedRoleCode) ? storedRoleCode : 1

      if (!username) return

      uni.request({
        url: buildApiUrl('/user/profile'),
        method: 'GET',
        header: {
          'X-Username': username
        },
        success: (res) => {
          const data = res.data || {}
          if (data.success === false) return
          const payload = data.data || data
          if (payload.nickname) {
            this.username = payload.nickname
            uni.setStorageSync('nickname', payload.nickname)
          }
          if (payload.avatar) {
            const resolved = this.normalizeAvatarUrl(payload.avatar)
            this.avatarPreview = resolved
            uni.setStorageSync('avatar', payload.avatar)
          }
          if (payload.role_code !== undefined) {
            const code = Number(payload.role_code) || 1
            this.roleCode = [1, 2, 3].includes(code) ? code : 1
            uni.setStorageSync('role_code', String(this.roleCode))
          }
        }
      })
    },
    chooseAvatar() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed', 'original'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          const filePath = (res.tempFilePaths && res.tempFilePaths[0]) || ''
          if (!filePath) return
          this.avatarFilePath = filePath
          this.avatarPreview = filePath
        }
      })
    },
    removeAvatar() {
      this.avatarFilePath = ''
      this.avatarPreview = this.defaultAvatar
      uni.removeStorageSync('avatar')
    },
    saveProfile() {
      const nickname = (this.username || '').trim()
      if (!nickname) {
        uni.showToast({ title: '请输入昵称或用户名', icon: 'none' })
        return
      }
      this.isSaving = true
      const username = uni.getStorageSync('username') || ''
      const requestData = {
        username,
        nickname
      }

      const finalize = (avatarUrl) => {
        if (avatarUrl) {
          uni.setStorageSync('avatar', avatarUrl)
          this.avatarPreview = this.normalizeAvatarUrl(avatarUrl)
        }
        uni.setStorageSync('nickname', nickname)
        this.isSaving = false
        uni.showToast({ title: '保存成功', icon: 'success' })
      }

      const requestUpdateProfile = () => {
        uni.request({
          url: buildApiUrl('/user/profile/update'),
          method: 'POST',
          header: {
            'Content-Type': 'application/json',
            'X-Username': username
          },
          data: requestData,
          success: (res) => {
            const data = res.data || {}
            if (data.success === false) {
              uni.showToast({ title: data.message || '保存失败', icon: 'none' })
              return
            }
            finalize(data.data?.avatar || '')
          },
          fail: () => {
            uni.showToast({ title: '保存失败，请检查网络', icon: 'none' })
          },
          complete: () => {
            this.isSaving = false
          }
        })
      }

      if (this.avatarFilePath) {
        uni.uploadFile({
          url: buildApiUrl('/user/avatar/upload'),
          filePath: this.avatarFilePath,
          name: 'file',
          formData: requestData,
          header: {
            'X-Username': username
          },
          success: (uploadRes) => {
			  console.log(uploadRes)
            let result = {}
            try {
              result = typeof uploadRes.data === 'string' ? JSON.parse(uploadRes.data) : uploadRes.data
            } catch (err) {
              result = {}
            }
            if (uploadRes.statusCode === 200 && result.success !== false) {
              requestData.avatar = result.data?.avatar || result.avatar || ''
              requestUpdateProfile()
            } else {
              uni.showToast({ title: result.message || '头像上传失败', icon: 'none' })
              this.isSaving = false
            }
          },
          fail: () => {
            uni.showToast({ title: '头像上传失败', icon: 'none' })
            this.isSaving = false
          }
        })
      } else {
        requestUpdateProfile()
      }
    },
    fetchMembershipStatus() {
      const username = uni.getStorageSync('username') || ''
      if (!username) return
      uni.request({
        url: buildApiUrl('/user/membership/status'),
        method: 'GET',
        header: {
          'X-Username': username
        },
        success: (res) => {
          const data = res.data || {}
          if (data.success === false) return
          const payload = data.data || data
          if (payload.role_code !== undefined) {
            const code = Number(payload.role_code) || 1
            this.roleCode = [1, 2, 3].includes(code) ? code : 1
            uni.setStorageSync('role_code', String(this.roleCode))
          }
        }
      })
    },
    upgradeMembership() {
      if (this.roleCode > 1) return
      const username = uni.getStorageSync('username') || ''
      if (!username) {
        uni.showToast({ title: '用户未登录', icon: 'none' })
        return
      }
      this.isUpgrading = true
      uni.request({
        url: buildApiUrl('/user/membership/upgrade'),
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          'X-Username': username
        },
        data: {
          username,
          plan: 'deepseek'
        },
        success: (res) => {
          const data = res.data || {}
          if (data.success === false) {
            uni.showToast({ title: data.message || '升级失败', icon: 'none' })
            return
          }
          const newCode = Number(data.data?.role_code || data.role_code || 2)
          this.roleCode = [1, 2, 3].includes(newCode) ? newCode : 2
          uni.setStorageSync('role_code', String(this.roleCode))
          uni.showToast({ title: '升级成功，DeepSeek 已解锁', icon: 'success' })
        },
        fail: () => {
          uni.showToast({ title: '升级请求失败', icon: 'none' })
        },
        complete: () => {
          this.isUpgrading = false
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.profile-page {
  width: 100vw;
  height: 100vh;
  background: #f5f7fa;
  display: flex;
  justify-content: center;
}
.profile-container {
  width: 100%;
  max-width: 750rpx;
  height: 100vh;
  background: #f5f7fa;
}
.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 24rpx 12rpx;
  background: #fff;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
}
.nav-back,
.nav-space {
  width: 70rpx;
  height: 70rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.nav-back {
  font-size: 40rpx;
  color: #333;
}
.profile-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #111;
}
.profile-content {
  height: calc(100vh - 140rpx);
  padding: 24rpx;
}
.section {
  margin-bottom: 24rpx;
  background: #fff;
  border-radius: 24rpx;
  padding: 24rpx;
}
.section-title {
  font-size: 28rpx;
  font-weight: 700;
  color: #111;
  margin-bottom: 24rpx;
}
.avatar-panel {
  flex-direction: row;
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.avatar-preview {
  width: 150rpx;
  height: 150rpx;
  border-radius: 50%;    /* 绝对圆形 */
  overflow: hidden;      /* 必须加，图片才会被裁成圆 */
  background: #f2f4f7;
}
.avatar-details {
  flex: 1;
}
.label {
  font-size: 24rpx;
  color: #333;
  margin-bottom: 12rpx;
}
.hint {
  font-size: 22rpx;
  color: #8f98a4;
  margin-bottom: 20rpx;
}
.action-row {
  display: flex;
  gap: 16rpx;
}
.field-row {
  margin-top: 30rpx;
}
.field-label {
  display: block;
  font-size: 24rpx;
  color: #666;
  margin-bottom: 14rpx;
}
.field-input {
  width: 90%;
  height: 80rpx;
  padding: 0 24rpx;
  border-radius: 40rpx;
  border: 1rpx solid #e5e7eb;
  background: #f8fafc;
  font-size: 26rpx;
  color: #2c3e50;
}
.section.card-section {
  width: 85%;
  margin: 0 auto 10rpx 10rpx;
}
.section.member-section {
  width: 85%;
  margin: 0 auto 10rpx 10rpx;
}
.button {
  min-width: 220rpx;
  padding: 18rpx 0;
  border-radius: 40rpx;
  text-align: center;
  background: #4facfe;
  color: #fff;
  font-size: 26rpx;
}
.button.secondary {
  background: #f5f7fa;
  color: #4a5568;
  border: 1rpx solid #d2d6dc;
}
.button.primary {
  margin-top: 30rpx;
  width: 100%;
  max-width: 300rpx;
  margin: 30rpx auto 0;
  display: block;
}
.button.upgrade {
  margin-top: 20rpx;
  width: 100%;
  max-width: 300rpx;
  margin: 30rpx auto 0;
  display: block;
}
.button.disabled {
  opacity: 0.55;
  pointer-events: none;
}
.member-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18rpx;
}
.member-value {
  font-size: 26rpx;
  font-weight: 700;
  color: #999;
}
.member-value.active {
  color: #0f8cff;
}
.member-desc {
  line-height: 1.6;
  color: #6b7280;
  font-size: 24rpx;
}
.benefits-panel {
  margin-top: 28rpx;
}
.benefits-title {
  font-size: 24rpx;
  color: #111;
  font-weight: 600;
  margin-bottom: 18rpx;
}
.benefit-item {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  margin-bottom: 16rpx;
}
.bullet {
  color: #4facfe;
  font-size: 32rpx;
  line-height: 32rpx;
}
.benefit-text {
  flex: 1;
  font-size: 24rpx;
  color: #4b5563;
  line-height: 1.6;
}
</style>
