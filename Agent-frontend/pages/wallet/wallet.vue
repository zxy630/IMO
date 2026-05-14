<template>
  <view class="wallet-page">
    <!-- 顶部导航栏 -->
    <view class="wallet-header">
      <view class="header-left" @click="handleBack">
        <text class="back-btn"><</text>
      </view>
      <view class="header-title">我的钱包</view>
      <view class="header-right"></view>
    </view>

    <!-- 余额卡片区域 -->
    <view class="balance-section">
      <!-- 零钱余额 -->
      <view class="balance-card cash-card">
        <text class="balance-label">零钱余额</text>
        <text class="balance-amount">¥ {{ formatMoney(walletInfo.cash_balance) }}</text>
        <view class="card-bottom">
          <text class="card-desc">可直接使用</text>
        </view>
      </view>

      <!-- 银行卡余额 -->
      <view class="balance-card bank-card">
        <text class="balance-label">银行卡余额</text>
        <text class="balance-amount">¥ {{ formatMoney(walletInfo.bank_balance) }}</text>
        <view class="card-bottom">
          <text class="card-desc">预留资金</text>
        </view>
      </view>

      <!-- 欠贷金额 -->
      <view class="balance-card debt-card">
        <text class="balance-label">欠贷金额</text>
        <text class="balance-amount">¥ {{ formatMoney(walletInfo.debt_amount) }}</text>
        <view class="card-bottom">
          <text class="card-desc">待偿还</text>
        </view>
      </view>
    </view>

    <!-- 账单列表区域 -->
    <view class="bill-section">
      <view class="section-header">
        <text class="section-title">账单记录</text>
        <view class="filter-tabs">
          <view 
            class="filter-tab" 
            :class="{ active: billFilter === 'all' }"
            @click="billFilter = 'all'"
          >
            全部
          </view>
          <view 
            class="filter-tab" 
            :class="{ active: billFilter === 'income' }"
            @click="billFilter = 'income'"
          >
            收入
          </view>
          <view 
            class="filter-tab" 
            :class="{ active: billFilter === 'expense' }"
            @click="billFilter = 'expense'"
          >
            支出
          </view>
        </view>
      </view>

      <!-- 账单列表 -->
      <scroll-view 
        class="bill-list" 
        scroll-y 
        @scrolltolower="loadMoreBills"
        :lower-threshold="100"
      >
        <view v-if="billLoading && bills.length === 0" class="bill-loading">
          <text>加载中...</text>
        </view>

        <view v-if="!billLoading && bills.length === 0" class="bill-empty">
          <text>暂无账单记录</text>
        </view>

        <view v-for="(bill, index) in bills" :key="index" class="bill-item">
          <view class="bill-left">
            <view class="bill-type" :class="bill.type">
              <text class="bill-icon">{{ bill.type === 'income' ? '➕' : '➖' }}</text>
            </view>
            <view class="bill-info">
              <text class="bill-title">{{ bill.description }}</text>
              <text class="bill-time">{{ formatTime(bill.created_at) }}</text>
            </view>
          </view>
          <text class="bill-amount" :class="bill.type">
            {{ bill.type === 'income' ? '+' : '-' }}¥ {{ formatMoney(bill.amount) }}
          </text>
        </view>

        <!-- 加载更多 -->
        <view v-if="bills.length > 0 && !billsNoMore" class="bill-loadmore">
          <text v-if="billLoading">加载中...</text>
          <text v-else @click="loadMoreBills">加载更多</text>
        </view>

        <view v-if="bills.length > 0 && billsNoMore" class="bill-end">
          <text>已加载全部账单</text>
        </view>

        <view style="height: 20rpx;"></view>
      </scroll-view>
    </view>

    <!-- 底部操作按钮 -->
    <!-- <view class="action-buttons">
      <button class="btn btn-recharge">充值</button>
      <button class="btn btn-withdraw">提现</button>
    </view> -->
  </view>
</template>

<script>
import { API_BASE_URL, buildApiUrl } from '../../config/api'

export default {
  data() {
    return {
      walletInfo: {
        cash_balance: 0,
        bank_balance: 0,
        debt_amount: 0
      },
      bills: [],
      billFilter: 'all',
      billPage: 1,
      billPageSize: 20,
      billLoading: false,
      billsNoMore: false,
      walletLoading: false
    }
  },
  onShow() {
    this.fetchWalletInfo()
    this.fetchBills(true)
  },
  methods: {
    handleBack() {
      uni.navigateBack()
    },
    
    // 获取钱包信息
    fetchWalletInfo() {
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

    // 获取账单记录
    fetchBills(isNew = false) {
      if (this.billsNoMore && !isNew) return
      if (this.billLoading) return

      this.billLoading = true
      const token = uni.getStorageSync('token')
      const username = uni.getStorageSync('username') || ''
      
      if (isNew) {
        this.billPage = 1
        this.billsNoMore = false
        this.bills = []
      }

      const params = {
        page: this.billPage,
        page_size: this.billPageSize
      }
      
      if (username) {
        params.username = username
      }
      if (this.billFilter !== 'all') {
        params.type = this.billFilter
      }

      const queryString = Object.keys(params)
        .map(k => `${k}=${params[k]}`)
        .join('&')

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
      if (username) {
        headers['X-Username'] = username
      }

      uni.request({
        url: buildApiUrl(`/api/wallet/bills?${queryString}`),
        method: 'GET',
        header: headers,
        success: (res) => {
          if (res.statusCode === 200 && res.data.code === 0) {
            const newBills = res.data.data.bills || []
            if (newBills.length < this.billPageSize) {
              this.billsNoMore = true
            }
            this.bills = this.bills.concat(newBills)
            this.billPage++
          } else {
            uni.showToast({
              title: res.data.msg || '获取账单失败',
              icon: 'none'
            })
          }
        },
        fail: (err) => {
          uni.showToast({
            title: '网络错误',
            icon: 'none'
          })
          console.error('Bills fetch error:', err)
        },
        complete: () => {
          this.billLoading = false
        }
      })
    },

    // 加载更多账单
    loadMoreBills() {
      this.fetchBills(false)
    },

    // 格式化金额
    formatMoney(amount) {
      if (!amount) return '0.00'
      const num = parseFloat(amount)
      if (isNaN(num)) return '0.00'
      return num.toFixed(2)
    },

    // 格式化时间
    formatTime(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      
      return `${month}-${day} ${hours}:${minutes}`
    }
  },
  watch: {
    billFilter(val) {
      this.fetchBills(true)
    }
  }
}
</script>

<style lang="scss" scoped>
page {
  background-color: #ffffff;
}

.wallet-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #ffffff;
}

/* 顶部导航栏 */
.wallet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100rpx;
  background-color: #1f2937;
  padding: 0 20rpx;
  padding-top: env(safe-area-inset-top);
  color: white;
  font-size: 32rpx;
  font-weight: bold;

  .header-left,
  .header-right {
    width: 60rpx;
    height: 60rpx;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .header-left {
    cursor: pointer;

    &:active {
      opacity: 0.7;
    }
  }

  .back-btn {
    font-size: 28rpx;
  }

  .header-title {
    flex: 1;
    text-align: center;
    font-size: 32rpx;
  }
}

/* 余额卡片区域 */
.balance-section {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12rpx;
  padding: 20rpx;
  background-color: #ffffff;

  .balance-card {
    padding: 20rpx;
    border-radius: 12rpx;
    color: white;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.08);
    transition: transform 0.2s ease;

    .balance-label {
      font-size: 14rpx;
      opacity: 0.85;
      margin-bottom: 8rpx;
    }

    .balance-amount {
      font-size: 32rpx;
      font-weight: 600;
      margin: 8rpx 0;
      word-break: break-all;
      line-height: 1.2;
    }

    .card-bottom {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 8rpx;

      .card-desc {
        font-size: 20rpx;
        opacity: 0.75;
      }
    }

    &.cash-card {
      background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
    }

    &.bank-card {
      background: linear-gradient(135deg, #10b981 0%, #047857 100%);
    }

    &.debt-card {
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
  }
}

/* 账单部分 */
.bill-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f9fafb;
  border-radius: 0;
  margin: 0 0;
  overflow: hidden;

  .section-header {
    padding: 20rpx;
    border-bottom: 1rpx solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .section-title {
      font-size: 28rpx;
      font-weight: 600;
      color: #1f2937;
    }

    .filter-tabs {
      display: flex;
      gap: 16rpx;

      .filter-tab {
        padding: 8rpx 16rpx;
        border-radius: 20rpx;
        background-color: #e5e7eb;
        font-size: 24rpx;
        color: #6b7280;
        transition: all 0.3s ease;

        &.active {
          background-color: #1f2937;
          color: white;
        }
      }
    }
  }

  .bill-list {
    flex: 1;
    overflow-y: auto;

    .bill-loading,
    .bill-empty {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 200rpx;
      color: #9ca3af;
      font-size: 28rpx;
    }

    .bill-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16rpx 20rpx;
      border-bottom: 1rpx solid #e5e7eb;
      background-color: white;
      transition: background-color 0.2s;

      &:active {
        background-color: #f3f4f6;
      }

      .bill-left {
        display: flex;
        gap: 12rpx;
        flex: 1;

        .bill-type {
          width: 60rpx;
          height: 60rpx;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24rpx;

          &.income {
            background-color: #dcfce7;
          }

          &.expense {
            background-color: #fee2e2;
          }
        }

        .bill-info {
          display: flex;
          flex-direction: column;
          justify-content: center;

          .bill-title {
            font-size: 26rpx;
            color: #1f2937;
            font-weight: 500;
          }

          .bill-time {
            font-size: 22rpx;
            color: #9ca3af;
            margin-top: 4rpx;
          }
        }
      }

      .bill-amount {
        font-size: 26rpx;
        font-weight: 600;
        min-width: 80rpx;
        text-align: right;

        &.income {
          color: #16a34a;
        }

        &.expense {
          color: #dc2626;
        }
      }
    }

    .bill-loadmore {
      padding: 20rpx;
      text-align: center;
      color: #3b82f6;
      font-size: 24rpx;
      cursor: pointer;

      &:active {
        opacity: 0.7;
      }
    }

    .bill-end {
      padding: 20rpx;
      text-align: center;
      color: #9ca3af;
      font-size: 22rpx;
    }
  }
}

/* 底部操作按钮 */
.action-buttons {
  display: flex;
  gap: 12rpx;
  padding: 16rpx 20rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background-color: #f9fafb;
  border-top: 1rpx solid #e5e7eb;

  .btn {
    flex: 1;
    padding: 14rpx 0;
    border-radius: 8rpx;
    font-size: 26rpx;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;

    &:active {
      transform: scale(0.98);
      opacity: 0.9;
    }

    &.btn-recharge {
      background-color: #3b82f6;
      color: white;
    }

    &.btn-withdraw {
      background-color: #f3f4f6;
      color: #1f2937;
      border: 1rpx solid #d1d5db;
    }
  }
}
</style>
