<template>
  <view class="page-container">
    <!-- 左侧侧边栏 -->
    <view class="sidebar" v-show="showSidebar" @click.stop>
      <view class="sidebar-content">
        <view class="user-header">
          <image class="avatar" :src="userAvatar || defaultAvatar" mode="aspectFill"></image>
          <view class="user-info">
            <view class="user-row">
              <text class="username">{{ displayName }}</text>
              <text class="role-badge" :class="roleTagClass">{{ roleLabel }}</text>
            </view>
          </view>
        </view>

        <view class="menu-list">
          <view class="menu-item" v-for="(item, index) in menuList" :key="index" @click="handleMenuClick(item)">
            <text class="menu-text">{{ item.name }}</text>
          </view>
        </view>

        <view class="logout-btn" @click="handleLogout">
          <text>退出登录</text>
        </view>
      </view>
    </view>

    <!-- 历史会话弹窗 -->
    <view v-if="showThreadsDialog" class="dialog-overlay" @click="closeThreadsDialog">
      <view class="threads-dialog" @click.stop>
        <view class="threads-header">
          <text class="threads-title">历史会话</text>
          <text class="threads-close" @click="closeThreadsDialog">×</text>
        </view>
        <view class="threads-content">
          <view v-if="threadsLoading" class="threads-loading">加载中...</view>
          <view v-else>
            <view v-if="!threads.length" class="threads-empty">暂无历史会话</view>
            <view
              v-for="(t, idx) in threads"
              :key="t.thread_id || idx"
              class="thread-item"
              @click="handleThreadClick(t)"
            >
              <view class="thread-main">
                <text class="thread-title">{{ t.title || '未命名会话' }}</text>
                <text class="thread-time">{{ formatTime(t.updated_at) }}</text>
              </view>
              <text class="thread-last">{{ t.last_message || '' }}</text>
            </view>
          </view>
        </view>
        <!-- <view class="threads-footer">
          <button class="threads-refresh" @click="fetchThreads">刷新</button>
        </view> -->
      </view>
    </view>

    <!-- 钱包弹窗 -->
    <view v-if="showWalletDialog" class="dialog-overlay" @click="closeWalletDialog">
      <view class="wallet-dialog" @click.stop>
        <view class="wallet-header">
          <text class="wallet-title">我的钱包</text>
          <text class="wallet-close" @click="closeWalletDialog">×</text>
        </view>
        <view class="wallet-content">
          <view v-if="walletLoading" class="wallet-loading">加载中...</view>
          <view v-else>
            <view class="wallet-row">
              <text class="wallet-k">零钱余额</text>
              <text class="wallet-v">{{ formatMoney(walletInfo.cash_balance) }}</text>
            </view>
            <view class="wallet-row">
              <text class="wallet-k">银行卡余额</text>
              <text class="wallet-v">{{ formatMoney(walletInfo.bank_balance) }}</text>
            </view>
            <view class="wallet-row debt">
              <text class="wallet-k">欠贷金额</text>
              <text class="wallet-v">{{ formatMoney(walletInfo.debt_amount) }}</text>
            </view>
          </view>
        </view>
        <view class="wallet-footer">
          <button class="wallet-refresh" @click="fetchWallet">刷新</button>
        </view>
      </view>
    </view>

    <!-- 主聊天页面 -->
    <view 
      class="main-content" 
      :style="{ transform: showSidebar ? 'translateX(75%)' : 'translateX(0)' }"
      @click="closeSidebar"
    >
      <!-- 导航栏 -->
      <view class="nav-bar" @click.stop>
        <view class="nav-left" @click="toggleSidebar">
          <text class="iconfont">☰</text>
        </view>
        <view class="nav-title"> </view>
        <view class="nav-right" @click="startNewChat">
          <text class="new-chat-btn">新对话</text>
        </view>
      </view>
      <view class="model-selector-wrap" @click.stop>
        <picker
          class="model-picker"
          mode="selector"
          :range="modelOptions"
          range-key="label"
          :value="currentModelIndex"
          @change="handleModelChange"
        >
          <view class="model-selector">
            <text class="model-label">模型：</text>
            <text class="model-value">{{ modelOptions[currentModelIndex].label }}</text>
            <text class="model-arrow">▼</text>
          </view>
        </picker>
      </view>

      <!-- 聊天列表 -->
      <scroll-view class="chat-list" scroll-y :scroll-into-view="scrollToView" scroll-with-animation>
        <view class="chat-item" :id="'msg-' + index" v-for="(msg, index) in chatList" :key="index" :class="msg.role === 'user' ? 'chat-user' : 'chat-ai'">
          <image class="chat-avatar" :src="msg.role === 'user' ? (userAvatar || defaultAvatar) : '/static/ailogo.jpg'"></image>
          <view class="msg-box">
            <image
              v-if="msg.image"
              class="chat-image"
              :src="msg.image"
              mode="aspectFit"
              @click.stop="previewImage(msg.image)"
            ></image>
            <view v-if="msg.thinking" class="thinking-wrap">
              <text class="msg-text">AI正在思考中</text>
              <view class="thinking-dots">
                <text class="dot dot-1">.</text>
                <text class="dot dot-2">.</text>
                <text class="dot dot-3">.</text>
              </view>
            </view>
            <view v-else class="msg-content">
              <block v-for="(part, partIndex) in renderMessageParts(msg.content)" :key="partIndex">
                <text v-if="part.type === 'text'" class="msg-text">{{ part.content }}</text>
                <view v-else class="markdown-image-card" @click.stop="previewImage(part.src)">
                  <image class="markdown-image" :src="part.src" mode="aspectFit"></image>
                  <view class="markdown-image-caption">
                    <text class="image-caption-text">{{ part.alt || getImageName(part.src) }}</text>
                  </view>
                </view>
              </block>
            </view>
          </view>
        </view>
        <view style="height:120rpx"></view>
      </scroll-view>

      <!-- 输入框 -->
      <view class="input-area" @click.stop>
        <input class="chat-input" v-model="inputMsg" placeholder="输入消息..." @confirm="sendMessage" />
        <view class="upload-btn" @click="chooseImage">
          <text>📷</text>
        </view>
        <view class="send-btn" @click="sendMessage">
          <text>发送</text>
        </view>
      </view>

      <!-- 钱包悬浮球（可拖拽） -->
      <view
        class="wallet-fab"
        :style="{ left: walletFabX + 'px', top: walletFabY + 'px' }"
        @touchstart.stop.prevent="onWalletFabTouchStart"
        @touchmove.stop.prevent="onWalletFabTouchMove"
        @touchend.stop="onWalletFabTouchEnd"
      >
        <text class="wallet-icon">💰</text>
      </view>
    </view>
  </view>
</template>

<script>
import { API_BASE_URL, buildApiUrl } from '../../config/api'

export default {
  data() {
    return {
      showSidebar: false,
      userAvatar: '',
      userNickname: '',
      roleCode: 1,
      defaultAvatar: '/static/logo.png',
      currentModelIndex: 0,
      currentModelId: 'qwen-turbo',
      modelOptions: [
        { label: 'Qwen Turbo', value: 'qwen-turbo' },
        { label: 'DeepSeek Chat', value: 'deepseek-chat' },
        { label: 'GPT', value: 'gpt-4o-mini' }
      ],
      threadId: null,
      newChatNext: false,
      showThreadsDialog: false,
      threadsLoading: false,
      threads: [],
      showWalletDialog: false,
      walletLoading: false,
      walletLoadedOnce: false,
      walletInfo: {
        cash_balance: 0,
        bank_balance: 0,
        debt_amount: 0
      },
      walletFabX: 0,
      walletFabY: 0,
      walletFabDragging: false,
      walletFabTouchOffsetX: 0,
      walletFabTouchOffsetY: 0,
      walletFabStartX: 0,
      walletFabStartY: 0,
      walletFabSizePx: 0,
      walletFabMarginPx: 0,
      walletFabClickGuard: false,
      isSending: false,
      inputMsg: "",
      scrollToView: "",
      chatList: [
        { role: "ai", content: "你好！我是你的AI助手" }
      ],
      menuList: [
        { name: "个人中心" },
		{ name: "我的钱包" },
        { name: "历史会话" },
        { name: "设置" },
        { name: "关于" }
      ]
    };
  },
  computed: {
    displayName() {
      const username = uni.getStorageSync('username') || ''
      return this.userNickname || username || '默认用户'
    },
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
    roleTagClass() {
      return {
        'role-badge-normal': this.roleCode === 1,
        'role-badge-vip': this.roleCode === 2,
        'role-badge-svip': this.roleCode === 3
      }
    }
  },
  onShow() {
    this.loadSidebarState()
    this.loadUserProfile()
    this.loadLatestChat()
    this.fetchWallet()
    this.initWalletFabPosition()
  },
  methods: {
    initWalletFabPosition() {
      if (this.walletFabX || this.walletFabY) return
      const info = uni.getSystemInfoSync()
      const sizePx = uni.upx2px(104)
      const marginPx = uni.upx2px(12)
      const bottomOffsetPx = uni.upx2px(160)
      this.walletFabSizePx = sizePx
      this.walletFabMarginPx = marginPx
      this.walletFabX = Math.max(marginPx, info.windowWidth - sizePx - marginPx)
      this.walletFabY = Math.max(marginPx, info.windowHeight - bottomOffsetPx - sizePx)
    },
    onWalletFabTouchStart(e) {
      const t = e.touches && e.touches[0]
      if (!t) return
      this.walletFabDragging = false
      this.walletFabClickGuard = false
      this.walletFabStartX = t.pageX
      this.walletFabStartY = t.pageY
      this.walletFabTouchOffsetX = t.pageX - this.walletFabX
      this.walletFabTouchOffsetY = t.pageY - this.walletFabY
    },
    onWalletFabTouchMove(e) {
      const t = e.touches && e.touches[0]
      if (!t) return
      const info = uni.getSystemInfoSync()
      const size = this.walletFabSizePx || uni.upx2px(104)
      const margin = this.walletFabMarginPx || uni.upx2px(12)
      const dx = Math.abs(t.pageX - this.walletFabStartX)
      const dy = Math.abs(t.pageY - this.walletFabStartY)
      if (dx > 3 || dy > 3) this.walletFabDragging = true
      let x = t.pageX - this.walletFabTouchOffsetX
      let y = t.pageY - this.walletFabTouchOffsetY
      x = Math.min(Math.max(margin, x), info.windowWidth - size - margin)
      y = Math.min(Math.max(margin, y), info.windowHeight - size - margin)
      this.walletFabX = x
      this.walletFabY = y
    },
    onWalletFabTouchEnd() {
      if (!this.walletFabDragging) {
        if (!this.walletFabClickGuard) this.openWalletDialog()
        return
      }
      const info = uni.getSystemInfoSync()
      const size = this.walletFabSizePx || uni.upx2px(104)
      const margin = this.walletFabMarginPx || uni.upx2px(12)
      const mid = info.windowWidth / 2
      this.walletFabX = this.walletFabX + size / 2 < mid ? margin : info.windowWidth - size - margin
      this.walletFabClickGuard = true
      setTimeout(() => {
        this.walletFabClickGuard = false
      }, 250)
    },
    normalizeAvatarUrl(rawAvatar) {
      const avatar = (rawAvatar || '').trim()
      if (!avatar) return ''
      if (/^https?:\/\//i.test(avatar)) return avatar
      if (avatar.startsWith('/')) return `${API_BASE_URL}${avatar}`
      return `${API_BASE_URL}/${avatar}`
    },
    normalizeMessageImageUrl(rawUrl) {
      const url = (rawUrl || '').trim()
      if (!url) return ''
      if (/^(https?:|blob:|data:)/i.test(url)) return url
      if (url.startsWith('/')) return `${API_BASE_URL}${url}`
      return `${API_BASE_URL}/${url}`
    },
    renderMessageParts(content) {
      const text = content == null ? '' : String(content)
      if (!text) return []

      const parts = []
      const imagePattern = /!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g
      let lastIndex = 0
      let match

      while ((match = imagePattern.exec(text)) !== null) {
        if (match.index > lastIndex) {
          const before = text.slice(lastIndex, match.index)
          if (before) parts.push({ type: 'text', content: before })
        }

        const src = this.normalizeMessageImageUrl(match[2])
        if (src) {
          parts.push({
            type: 'image',
            src,
            alt: (match[1] || '').trim()
          })
        }

        lastIndex = imagePattern.lastIndex
      }

      if (lastIndex < text.length) {
        const rest = text.slice(lastIndex)
        if (rest) parts.push({ type: 'text', content: rest })
      }

      if (!parts.some((part) => part.type === 'image')) {
        const plainParts = []
        const plainImagePattern = /((?:https?:\/\/|\/|[\w.-]+\/)?[^\s，。；：:]+?\.(?:png|jpe?g|gif|bmp|webp))(?:\?[^ \n\r]*)?/gi
        let plainLastIndex = 0
        let plainMatch

        while ((plainMatch = plainImagePattern.exec(text)) !== null) {
          if (plainMatch.index > plainLastIndex) {
            const before = text.slice(plainLastIndex, plainMatch.index)
            if (before) plainParts.push({ type: 'text', content: before })
          }

          const src = this.normalizeMessageImageUrl(plainMatch[0])
          if (src) {
            plainParts.push({
              type: 'image',
              src,
              alt: this.getImageName(plainMatch[0])
            })
          }

          plainLastIndex = plainImagePattern.lastIndex
        }

        if (plainLastIndex < text.length) {
          const rest = text.slice(plainLastIndex)
          if (rest) plainParts.push({ type: 'text', content: rest })
        }

        if (plainParts.some((part) => part.type === 'image')) return plainParts
      }

      return parts.length ? parts : [{ type: 'text', content: text }]
    },
    getImageName(src) {
      const clean = String(src || '').split('?')[0].split('#')[0]
      const name = clean.split('/').pop()
      return name || 'image'
    },
    previewImage(src) {
      if (!src) return
      uni.previewImage({
        urls: [src],
        current: src
      })
    },
    loadUserProfile() {
      const avatar = uni.getStorageSync('avatar') || ''
      const storedRoleCode = Number(uni.getStorageSync('role_code') || 1)
      this.userAvatar = this.normalizeAvatarUrl(avatar)
      this.userNickname = uni.getStorageSync('nickname') || ''
      this.roleCode = [1, 2, 3].includes(storedRoleCode) ? storedRoleCode : 1
      if (this.chatList.length && this.chatList[0].role === 'ai') {
        this.$set(this.chatList, 0, {
          ...this.chatList[0],
          content: this.buildGreetingMessage()
        })
      }
    },
    getGreetName() {
      return this.userNickname || uni.getStorageSync('nickname') || uni.getStorageSync('username') || '用户'
    },
    loadSidebarState() {
      const stored = uni.getStorageSync('sidebarOpen')
      this.showSidebar = stored === 'true'
    },
    saveSidebarState(open) {
      uni.setStorageSync('sidebarOpen', open ? 'true' : 'false')
    },
    buildGreetingMessage() {
      const greetName = this.getGreetName()
      return `你好，${greetName}！我是你的AI助手钱宝~`
    },
    getCurrentGreetingMessage() {
      const firstMessage = this.chatList && this.chatList[0]
      if (firstMessage && firstMessage.role === 'ai' && firstMessage.content) {
        return firstMessage.content
      }
      return this.buildGreetingMessage()
    },
    getPendingGreetingMessage() {
      const firstMessage = this.chatList && this.chatList[0]
      if (this.chatList.length === 1 && firstMessage && firstMessage.role === 'ai') {
        return firstMessage.content || this.buildGreetingMessage()
      }
      return ''
    },
    setGreetingAsFirstMessage() {
      this.chatList = [{ role: 'ai', content: this.buildGreetingMessage() }]
      this.$nextTick(() => {
        this.scrollToView = 'msg-0'
      })
    },
    loadLatestChat() {
      const username = uni.getStorageSync('username') || ''
      if (!username) {
        this.threadId = null
        this.newChatNext = true
        this.setGreetingAsFirstMessage()
        return
      }

      uni.request({
        url: buildApiUrl(`/user/chat/latest?username=${encodeURIComponent(username)}`),
        method: 'GET',
        success: (res) => {
			// console.log(res)
          const data = res.data
		  console.log(data)
          // 无会话：null
          if (!data) {
            this.threadId = null
            this.newChatNext = true
            this.setGreetingAsFirstMessage()
            return
          }

          const messages = Array.isArray(data.messages) ? data.messages : []
          this.threadId = data.thread_id || null
          this.newChatNext = false

          const rendered = messages.map((m) => {
            const role = m.role === 'assistant' ? 'ai' : 'user'
            return {
              role,
              content: m.content || ''
            }
          })

          if (!rendered.length) {
            this.newChatNext = true
            this.setGreetingAsFirstMessage()
            return
          }

          this.chatList = rendered

          // 同步模型选择为最近一次消息的模型（如果能取到）
          const lastModel = (messages[messages.length - 1] && messages[messages.length - 1].model) || ''
          if (lastModel) {
            const idx = this.modelOptions.findIndex((x) => x.value === lastModel)
            if (idx >= 0) {
              this.currentModelIndex = idx
              this.currentModelId = lastModel
            }
          }

          this.$nextTick(() => {
            this.scrollToView = `msg-${this.chatList.length - 1}`
          })
        },
        fail: () => {
          // 拉取失败时不打断使用，默认开启新对话
          this.threadId = null
          this.newChatNext = true
          this.setGreetingAsFirstMessage()
        }
      })
    },
    startNewChat() {
      this.threadId = null
      this.newChatNext = true
      this.setGreetingAsFirstMessage()
      uni.showToast({ title: '已开启新对话', icon: 'none' })
    },
    openThreadsDialog() {
      this.showThreadsDialog = true
      this.fetchThreads()
    },
    closeThreadsDialog() {
      this.showThreadsDialog = false
    },
    fetchThreads() {
      const username = uni.getStorageSync('username') || ''
      if (!username) {
        this.threads = []
        return
      }
      this.threadsLoading = true
      uni.request({
        url: buildApiUrl('/user/chat/threads'),
        method: 'GET',
        header: {
          'X-Username': username
        },
        success: (res) => {
          const data = res.data
          this.threads = Array.isArray(data) ? data : []
        },
        fail: () => {
          this.threads = []
          uni.showToast({ title: '获取历史会话失败', icon: 'none' })
        },
        complete: () => {
          this.threadsLoading = false
        }
      })
    },
    openWalletDialog() {
      this.showWalletDialog = true
      if (!this.walletLoadedOnce && !this.walletLoading) this.fetchWallet()
    },
    closeWalletDialog() {
      this.showWalletDialog = false
    },
    fetchWallet() {
      const username = uni.getStorageSync('username') || ''
      if (!username) return
      this.walletLoading = true
      uni.request({
        url: buildApiUrl('/user/wallet'),
        method: 'GET',
        header: {
          'X-Username': username
        },
        success: (res) => {
          const data = res.data || {}
		  console.log(data)
          if (data.success === false) {
            uni.showToast({ title: data.message || '获取钱包失败', icon: 'none' })
            return
          }
          const payload = data.data || data
          this.walletInfo = {
            cash_balance: payload.cash_balance ?? payload.cash ?? 0,
            bank_balance: payload.bank_balance ?? payload.bank ?? 0,
            debt_amount: payload.debt_amount ?? payload.debt ?? 0
          }
          this.walletLoadedOnce = true
        },
        fail: () => {
          uni.showToast({ title: '获取钱包失败', icon: 'none' })
        },
        complete: () => {
          this.walletLoading = false
        }
      })
    },
    formatMoney(v) {
      const n = Number(v)
      const safe = Number.isFinite(n) ? n : 0
      return `¥ ${safe.toFixed(2)}`
    },
    handleThreadClick(t) {
      const username = uni.getStorageSync('username') || ''
      const threadId = t.thread_id || null
      if (!username || !threadId) return

      this.threadsLoading = true
      uni.request({
        url: buildApiUrl(`/user/chat/threads/${encodeURIComponent(threadId)}/messages`),
        method: 'GET',
        header: {
          'X-Username': username
        },
        success: (res) => {
          const data = res.data
          const messages = Array.isArray(data) ? data : []
          this.threadId = threadId
          this.newChatNext = false

          const rendered = messages.map((m) => {
            const role = m.role === 'assistant' ? 'ai' : 'user'
            return {
              role,
              content: m.content || ''
            }
          })

          this.chatList = rendered.length ? rendered : [{ role: 'ai', content: this.buildGreetingMessage() }]

          const lastModelId = (messages[messages.length - 1] && messages[messages.length - 1].model_id) || ''
          if (lastModelId) {
            const idx = this.modelOptions.findIndex((x) => x.value === lastModelId)
            if (idx >= 0) {
              this.currentModelIndex = idx
              this.currentModelId = lastModelId
            }
          }

          this.closeThreadsDialog()
          this.$nextTick(() => {
            this.scrollToView = `msg-${this.chatList.length - 1}`
          })
        },
        fail: () => {
          uni.showToast({ title: '拉取会话消息失败', icon: 'none' })
        },
        complete: () => {
          this.threadsLoading = false
        }
      })
    },
    formatTime(iso) {
      if (!iso) return ''
      const s = String(iso).replace('T', ' ')
      return s.length > 16 ? s.slice(0, 16) : s
    },
    toggleSidebar() {
      this.showSidebar = !this.showSidebar;
      this.saveSidebarState(this.showSidebar)
    },
    closeSidebar() {
      this.showSidebar = false;
      this.saveSidebarState(false)
    },
    handleModelChange(e) {
      const idx = Number(e.detail.value || 0)
      this.currentModelIndex = idx
      this.currentModelId = this.modelOptions[idx].value
      uni.showToast({
        title: `已切换到${this.modelOptions[idx].label}`,
        icon: 'none'
      })
    },
    sendMessage() {
      const message = (this.inputMsg || '').trim()
      if (!message) return;
      if (this.isSending) {
        uni.showToast({ title: 'AI正在回复，请稍候', icon: 'none' })
        return
      }
      const pendingGreetingMessage = this.getPendingGreetingMessage()
      this.chatList.push({ role: "user", content: message });
      const thinkingIndex = this.chatList.length
      this.chatList.push({ role: "ai", content: "", thinking: true });
      this.inputMsg = "";
      this.isSending = true
      this.$nextTick(() => {
        this.scrollToView = "msg-" + (this.chatList.length - 1);
      });

      uni.request({
        url: buildApiUrl('/user/chat/send'),
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: (() => {
          const shouldNewChat = this.newChatNext || !this.threadId
          const payload = {
            username: uni.getStorageSync('username') || '',
            message,
            model_id: this.currentModelId,
            thread_id: shouldNewChat ? null : this.threadId,
            new_chat: shouldNewChat
          }
		  console.log("发消息", payload);
          if (pendingGreetingMessage) {
            payload.greeting_message = pendingGreetingMessage
          }
          return payload
        })(),
        success: (res) => {
          const data = res.data || {}
		  console.log("AI回复", data);
          if (data.thread_id) {
            this.threadId = data.thread_id
            this.newChatNext = false
          }
          if (data.success === false) {
            const errorMessage = data.message || (data.data && data.data.message) || ''
            this.$set(this.chatList, thinkingIndex, {
              role: 'ai',
              content: errorMessage ? `${errorMessage}，快去升级体验吧~` : '抱歉，AI暂时没有返回内容。',
              thinking: false
            })
            return
          }
          const answer = data.answer || (data.data && data.data.answer) || ''
          this.$set(this.chatList, thinkingIndex, {
            role: 'ai',
            content: answer || '抱歉，AI暂时没有返回内容。',
            thinking: false
          })
        },
        fail: () => {
          this.$set(this.chatList, thinkingIndex, {
            role: 'ai',
            content: '请求失败，请稍后重试。',
            thinking: false
          })
        },
        complete: () => {
          this.isSending = false
          this.$nextTick(() => {
            this.scrollToView = "msg-" + (this.chatList.length - 1);
          });
        }
      })
    },
    chooseImage() {
      uni.chooseImage({
        count: 1,
        sizeType: ['original', 'compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          const tempFilePath = res.tempFilePaths[0]
          const tempFiles = res.tempFiles[0]
          // 检查文件大小，最大10MB
          if (tempFiles.size > 10 * 1024 * 1024) {
            uni.showToast({ title: '文件大小超过10MB', icon: 'none' })
            return
          }
          // 检查文件格式
          const allowedMimeTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
          if (!allowedMimeTypes.includes(tempFiles.type)) {
            uni.showToast({ title: '不支持的文件格式', icon: 'none' })
            return
          }
          // 添加用户图片消息
          this.chatList.push({ role: "user", content: "", image: tempFilePath })
          // 添加AI思考消息
          const thinkingIndex = this.chatList.length
          this.chatList.push({ role: "ai", content: "", thinking: true })
          this.$nextTick(() => {
            this.scrollToView = "msg-" + (this.chatList.length - 1)
          })
          this.uploadImage(tempFilePath, thinkingIndex)
        },
        fail: () => {
          uni.showToast({ title: '选择图片失败', icon: 'none' })
        }
      })
    },
    uploadImage(tempFilePath, thinkingIndex) {
      const username = uni.getStorageSync('username') || ''
      if (!username) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }

      const pendingGreetingMessage = this.getPendingGreetingMessage()
      const uploadUrl = buildApiUrl(`/user/bills/parse-image${this.threadId ? `?thread_id=${encodeURIComponent(this.threadId)}` : ''}`)
      uni.uploadFile({
        url: uploadUrl,
        filePath: tempFilePath,
        name: 'file',
        header: {
          'X-Username': username
        },
        formData: pendingGreetingMessage ? {
          greeting_message: pendingGreetingMessage
        } : {},
        success: (res) => {
          try {
            const data = JSON.parse(res.data)
            if (data.thread_id) {
              this.threadId = data.thread_id
              this.newChatNext = false
            }
            if (Array.isArray(data.chat_messages) && data.chat_messages.length) {
              const messages = data.chat_messages.map((item) => {
                if (typeof item === 'string') {
                  return { role: 'ai', content: item }
                }
                const content = item.content || item.message || ''
                return {
                  role: item.role === 'user' ? 'user' : 'ai',
                  content
                }
              }).filter((msg) => msg.content)

              if (messages.length) {
                const replaceIndex = Math.max(thinkingIndex - 1, 0)
                this.chatList.splice(replaceIndex, 2, ...messages)
                if (data.wallet_balance !== undefined) {
                  this.walletInfo.cash_balance = data.wallet_balance
                  this.walletLoadedOnce = false
                }
                this.$nextTick(() => {
                  this.scrollToView = "msg-" + (this.chatList.length - 1)
                })
                return
              }
            }
            if (data.success) {
              const parsedData = data.parsed_data || {}
              const billId = data.bill_id || ''
              let content = `账单解析成功！\n`
              if (billId) content += `账单ID: ${billId}\n`
              if (parsedData.amount) content += `金额: ¥${parsedData.amount}\n`
              if (parsedData.type) content += `类型: ${parsedData.type}\n`
              if (parsedData.merchant) content += `商户: ${parsedData.merchant}\n`
              if (parsedData.description) content += `描述: ${parsedData.description}\n`
              if (!content.trim()) content = '账单解析成功，但未返回具体内容。'
              this.$set(this.chatList, thinkingIndex, {
                role: 'ai',
                content,
                thinking: false
              })
              if (data.wallet_balance !== undefined) {
                this.walletInfo.cash_balance = data.wallet_balance
                this.walletLoadedOnce = false
              }
              this.$nextTick(() => {
                this.scrollToView = "msg-" + (this.chatList.length - 1)
              })
            } else {
              this.$set(this.chatList, thinkingIndex, {
                role: 'ai',
                content: data.message || '解析失败',
                thinking: false
              })
            }
          } catch (e) {
            this.$set(this.chatList, thinkingIndex, {
              role: 'ai',
              content: '响应解析失败',
              thinking: false
            })
          }
        },
        fail: () => {
          this.$set(this.chatList, thinkingIndex, {
            role: 'ai',
            content: '上传失败',
            thinking: false
          })
        },
        complete: () => {
        }
      })
    },
    handleMenuClick(item) {
      if (item.name === '个人中心') {
        uni.navigateTo({ url: '/pages/profile/profile' })
        return
      }
      if (item.name === '历史会话') {
        this.showSidebar = false
        this.saveSidebarState(false)
        this.openThreadsDialog()
        return
      }
      if (item.name === '我的钱包') {
        uni.navigateTo({ url: '/pages/wallet/wallet' })
        return
      }
      if (item.name === '关于') {
        uni.navigateTo({ url: '/pages/about/about' })
        return
      }
      uni.showToast({ title: item.name, icon: "none" })
    },
    handleLogout() {
      uni.showModal({
        title: "提示",
        content: "确定退出？",
        success: (res) => {
          if (res.confirm) {
            uni.removeStorageSync('username')
            uni.removeStorageSync('nickname')
            uni.removeStorageSync('avatar')
            uni.reLaunch({ url: "/pages/login/login" })
          }
        }
      });
    }
  }
};
</script>

<style lang="scss" scoped>
page {
  margin: 0;
  padding: 0;
  background: #f5f7fa;
}
.page-container {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 75%;
  height: 100vh;
  background: #2c3e50;
  z-index: 999;
}
.sidebar-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  color: #fff;
}
.user-header {
  padding: 60rpx 40rpx 40rpx;
  background: rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
}
.avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  margin-right: 20rpx;
}
.user-info {
  display: flex;
  flex-direction: column;
}
.user-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.username {
  font-size: 32rpx;
  font-weight: bold;
}
.role-badge {
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
  font-weight: 600;
  color: #fff;
}
.role-badge-normal {
  background: #6b7280;
}
.role-badge-vip {
  background: #288deb;
}
.role-badge-svip {
  background: #d97706;
}
.menu-list {
  flex: 1;
  padding: 20rpx 0;
}
.menu-item {
  height: 100rpx;
  line-height: 100rpx;
  padding-left: 40rpx;
  font-size: 30rpx;
}
.logout-btn {
  height: 100rpx;
  line-height: 100rpx;
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: #ff6b6b;
}

/* 弹窗遮罩 */
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
  z-index: 2000;
}
.threads-dialog {
  width: 86%;
  max-height: 80vh;
  background: #2c3e50;
  border-radius: 20rpx;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.threads-header {
  padding: 26rpx 26rpx;
  background: linear-gradient(135deg, #2c3e50 0%, #111827 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
}
.threads-title {
  font-size: 32rpx;
  font-weight: 700;
}
.threads-close {
  font-size: 44rpx;
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.9;
}
.threads-content {
  padding: 20rpx 22rpx;
  overflow-y: auto;
  flex: 1;
}
.threads-loading,
.threads-empty {
  padding: 40rpx 0;
  text-align: center;
  color: #666;
  font-size: 26rpx;
}
.thread-item {
  padding: 18rpx 18rpx;
  border-radius: 16rpx;
  background: #f8fafc;
  margin-bottom: 16rpx;
  border: 1px solid rgba(15, 23, 42, 0.06);
}
.thread-item:active {
  transform: scale(0.99);
  opacity: 0.95;
}
.thread-main {
  display: flex;
  align-items: center;
}
.thread-title {
  flex: 1;
  font-size: 28rpx;
  font-weight: 700;
  color: #0f172a;
}
.thread-time {
  font-size: 22rpx;
  color: rgba(15, 23, 42, 0.5);
  margin-left: 12rpx;
}
.thread-last {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: rgba(15, 23, 42, 0.72);
  line-height: 1.4;
}
.threads-footer {
  padding: 18rpx 22rpx 22rpx;
  border-top: 1px solid #f0f0f0;
}
.threads-refresh {
  width: 100%;
  height: 74rpx;
  line-height: 74rpx;
  background: #2c3e50;
  color: #fff;
  border-radius: 14rpx;
  font-size: 28rpx;
}
.threads-refresh:active {
  opacity: 0.92;
}

/* 钱包弹窗 */
.wallet-dialog {
  width: 86%;
  max-height: 70vh;
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.wallet-header {
  padding: 26rpx 26rpx;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #111827;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}
.wallet-title {
  font-size: 32rpx;
  font-weight: 800;
}
.wallet-close {
  font-size: 44rpx;
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.7;
}
.wallet-content {
  padding: 18rpx 22rpx 10rpx;
}
.wallet-loading {
  padding: 36rpx 0;
  text-align: center;
  color: #666;
  font-size: 26rpx;
}
.wallet-row {
  display: flex;
  align-items: center;
  padding: 18rpx 16rpx;
  border-radius: 16rpx;
  background: #f6f7f9;
  border: 1px solid rgba(15, 23, 42, 0.05);
  margin-bottom: 14rpx;
}
.wallet-row.debt .wallet-v {
  color: #b91c1c;
}
.wallet-k {
  flex: 1;
  font-size: 26rpx;
  color: rgba(17, 24, 39, 0.62);
}
.wallet-v {
  font-size: 28rpx;
  font-weight: 800;
  color: #111827;
}
.wallet-footer {
  padding: 18rpx 22rpx 22rpx;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
}
.wallet-refresh {
  width: 100%;
  height: 74rpx;
  line-height: 74rpx;
  background: #e5e7eb;
  color: #111827;
  border-radius: 14rpx;
  font-size: 28rpx;
}
.wallet-refresh::after {
  border: none;
}
.wallet-refresh:active {
  opacity: 0.92;
}

/* 钱包悬浮球 */
.wallet-fab {
  position: fixed;
  width: 104rpx;
  height: 104rpx;
  border-radius: 52rpx;
  background: rgba(17, 4, 5, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 18rpx 34rpx rgba(0, 0, 0, 0.25);
  z-index: 1500;
  transition: left 0.18s ease, top 0.18s ease;
}
.wallet-fab:active {
  transform: scale(0.98);
  opacity: 0.95;
}
.wallet-icon {
  font-size: 42rpx;
}
.threads-refresh::after {
  border: none;
}

/* 主内容 */
.main-content {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  transition: transform 0.3s ease;
  z-index: 100;
}

/* 导航栏 */
.nav-bar {
  height: 90rpx;
  padding-top: var(--status-bar-height);
  background: #fff;
  display: flex;
  align-items: center;
  padding-left: 20rpx;
  padding-right: 20rpx;
}
.nav-left {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
}
.nav-title {
  flex: 1;
  text-align: center;
  font-size: 36rpx;
  font-weight: 600;
}
.nav-right {
  width: 140rpx;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
.new-chat-btn {
  padding: 10rpx 18rpx;
  background: #f5f7fa;
  border-radius: 18rpx;
  font-size: 22rpx;
  color: #2d8cf0;
}
.model-selector-wrap {
  padding: 12rpx 24rpx;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}
.model-picker {
  width: 100%;
}
.model-selector {
  height: 62rpx;
  display: flex;
  align-items: center;
  background: #f5f7fa;
  border-radius: 32rpx;
  padding: 0 20rpx;
}
.model-label {
  color: #666;
  font-size: 24rpx;
}
.model-value {
  flex: 1;
  margin-left: 8rpx;
  color: #2d8cf0;
  font-size: 24rpx;
  font-weight: 600;
}
.model-arrow {
  color: #999;
  font-size: 20rpx;
}

/* 聊天区域修复 */
.chat-list {
  flex: 1;
  min-height: 0;
  padding: 20rpx 30rpx; /* 左右增加内边距，防止贴边 */
}
.chat-item {
  display: flex;
  margin-bottom: 30rpx;
  align-items: flex-start;
}
.chat-avatar {
  width: 70rpx;
  height: 70rpx;
  border-radius: 12rpx;
  flex-shrink: 0;
}

/* 用户消息（右侧）修复 */
.chat-user {
  flex-direction: row-reverse;
  justify-content: flex-start; /* 关键：不要顶到最右 */
}
.chat-user .chat-avatar {
  margin-left: 15rpx; /* 头像和消息之间留空隙 */
  margin-right: 40rpx; /* 增大这个值 → 头像更靠左 */
}
.chat-user .msg-box {
  background: #4facfe;
  color: #fff;
  border-radius: 20rpx 4rpx 20rpx 20rpx;
  margin-left: 0;
}

/* AI消息（左侧） */
.chat-ai .chat-avatar {
  margin-right: 15rpx;
}
.chat-ai .msg-box {
  background: #fff;
  border-radius: 4rpx 20rpx 20rpx 20rpx;
  box-shadow: 0 4rpx 10rpx rgba(0, 0, 0, 0.05);
}
.msg-box {
  max-width: 70%;
  padding: 20rpx;
  font-size: 28rpx;
  line-height: 1.5;
}
.msg-content {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.msg-text {
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
}
.chat-image {
  width: 360rpx;
  max-width: 100%;
  height: 300rpx;
  border-radius: 12rpx;
  display: block;
  background: rgba(255, 255, 255, 0.3);
}
.markdown-image-card {
  width: 360rpx;
  max-width: 100%;
  overflow: hidden;
  border-radius: 14rpx;
  background: #f7f8fa;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}
.chat-user .markdown-image-card {
  background: rgba(255, 255, 255, 0.18);
  box-shadow: none;
}
.markdown-image {
  width: 100%;
  height: 300rpx;
  display: block;
  background: #eef1f5;
}
.markdown-image-caption {
  padding: 10rpx 14rpx;
}
.image-caption-text {
  display: block;
  color: #606266;
  font-size: 22rpx;
  line-height: 1.35;
  word-break: break-all;
}
.chat-user .image-caption-text {
  color: rgba(255, 255, 255, 0.9);
}
.thinking-wrap {
  display: flex;
  align-items: center;
}
.thinking-dots {
  display: flex;
}
.dot {
  opacity: 0.2;
  animation: blink 1.2s infinite;
}
.dot-2 {
  animation-delay: 0.2s;
}
.dot-3 {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.2;
  }
  40% {
    opacity: 1;
  }
}

/* 输入框 */
.input-area {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  background: #fff;
  display: flex;
  align-items: center;
  padding: 10rpx 20rpx 20rpx 20rpx;
  border-top: 1px solid #eee;
}
.chat-input {
  flex: 1;
  height: 70rpx;
  background: #f0f2f5;
  border-radius: 35rpx;
  padding: 0 30rpx;
  font-size: 28rpx;
  margin-right: 20rpx;
}
.upload-btn {
  width: 70rpx;
  height: 70rpx;
  background: #f0f2f5;
  border-radius: 35rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  font-size: 28rpx;
}
.send-btn {
  padding: 0 30rpx;
  height: 70rpx;
  background: #4facfe;
  color: #fff;
  border-radius: 35rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
