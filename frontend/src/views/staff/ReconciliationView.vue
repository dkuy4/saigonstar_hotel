<template>
  <div class="space-y-6 pb-16 max-w-7xl mx-auto">
    <!-- Header & Action Toolbar -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Coins class="w-7 h-7 text-sky-600" />
            <span>Đối soát doanh thu & Dòng tiền theo ngày</span>
          </h1>
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-sky-100 text-sky-800 border border-sky-200">
            F12 Báo cáo
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Đối soát tổng thu, tổng hoàn và thực thu ròng phân tách theo từng phương thức và kênh thanh toán (FR-39)
        </p>
      </div>

      <!-- Action: Export CSV & Refresh -->
      <div class="flex items-center gap-2.5">
        <button
          type="button"
          @click="exportCsv"
          :disabled="loading || items.length === 0"
          class="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm transition active:scale-95 disabled:opacity-50"
        >
          <Download class="w-4 h-4 text-white" />
          <span>Xuất file CSV</span>
        </button>

        <button
          type="button"
          @click="fetchReconciliation"
          :disabled="loading"
          class="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shadow-sm transition active:scale-95 disabled:opacity-50"
        >
          <RefreshCw class="w-4 h-4 text-slate-500" :class="{ 'animate-spin': loading }" />
          <span>Làm mới</span>
        </button>
      </div>
    </div>

    <!-- Date Filter Bar -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
      <div class="flex items-center gap-2">
        <Calendar class="w-4 h-4 text-slate-500" />
        <span class="font-bold text-slate-700">Ngày đối soát:</span>
        <input
          type="date"
          v-model="selectedDate"
          @change="fetchReconciliation"
          class="px-3 py-1.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold text-slate-800 outline-none focus:ring-2 focus:ring-sky-500"
        />
      </div>

      <!-- Quick Shortcuts -->
      <div class="flex items-center gap-1.5">
        <button
          type="button"
          @click="setQuickDate(0)"
          class="px-3 py-1.5 rounded-lg font-semibold transition"
          :class="isToday ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        >
          Hôm nay
        </button>
        <button
          type="button"
          @click="setQuickDate(-1)"
          class="px-3 py-1.5 rounded-lg font-semibold transition"
          :class="isYesterday ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        >
          Hôm qua
        </button>
      </div>
    </div>

    <!-- Alert / Toast Messages -->
    <div
      v-if="toast.show"
      class="p-4 rounded-xl text-xs font-medium flex items-center justify-between border shadow-sm transition-all"
      :class="toast.isError ? 'bg-rose-50 border-rose-200 text-rose-800' : 'bg-emerald-50 border-emerald-200 text-emerald-800'"
    >
      <div class="flex items-center gap-2">
        <AlertTriangle v-if="toast.isError" class="w-4 h-4 text-rose-600 flex-shrink-0" />
        <CheckCircle2 v-else class="w-4 h-4 text-emerald-600 flex-shrink-0" />
        <span>{{ toast.message }}</span>
      </div>
      <button @click="toast.show = false" class="text-slate-400 hover:text-slate-600">✕</button>
    </div>

    <!-- Summary KPI Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <!-- Tổng thu -->
      <div class="bg-white p-5 rounded-2xl border border-emerald-200 shadow-sm hover:shadow transition">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-emerald-700">Tổng thu thực nhận</span>
          <div class="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600">
            <ArrowDownLeft class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-3">
          <div class="text-2xl font-black text-emerald-800 font-mono">
            {{ formatCurrency(reconData?.grandTotalCollected || 0) }}
          </div>
          <p class="text-[11px] text-slate-400 mt-0.5">Tiền mặt, chuyển khoản, POS & cổng trực tuyến</p>
        </div>
      </div>

      <!-- Tổng hoàn -->
      <div class="bg-white p-5 rounded-2xl border border-rose-200 shadow-sm hover:shadow transition">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-rose-700">Tổng tiền đã hoàn</span>
          <div class="w-8 h-8 rounded-lg bg-rose-100 flex items-center justify-center text-rose-600">
            <ArrowUpRight class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-3">
          <div class="text-2xl font-black text-rose-800 font-mono">
            {{ formatCurrency(reconData?.grandTotalRefunded || 0) }}
          </div>
          <p class="text-[11px] text-slate-400 mt-0.5">Khoản hoàn khách hủy đơn hoặc trả phòng sớm</p>
        </div>
      </div>

      <!-- Thực thu ròng -->
      <div class="bg-white p-5 rounded-2xl border border-sky-200 shadow-sm hover:shadow transition">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-sky-700">Thực thu ròng (Net)</span>
          <div class="w-8 h-8 rounded-lg bg-sky-100 flex items-center justify-center text-sky-600">
            <Coins class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-3">
          <div class="text-2xl font-black text-sky-900 font-mono">
            {{ formatCurrency(reconData?.grandNetRevenue || 0) }}
          </div>
          <p class="text-[11px] text-slate-400 mt-0.5">Tổng thu thực nhận trừ đi các khoản đã hoàn</p>
        </div>
      </div>
    </div>

    <!-- Detailed Reconciliation Breakdown Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="px-5 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <h2 class="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
          <CreditCard class="w-4 h-4 text-slate-500" />
          <span>Bảng phân tích dòng tiền theo phương thức và kênh (Ngày: {{ selectedDate }})</span>
        </h2>
        <span class="text-xs text-slate-500 font-mono">{{ items.length }} luồng thanh toán</span>
      </div>

      <div v-if="loading" class="py-16 text-center text-slate-400 space-y-3">
        <RefreshCw class="w-8 h-8 mx-auto animate-spin text-sky-500" />
        <p class="text-sm">Đang tính toán số liệu đối soát...</p>
      </div>

      <div v-else-if="items.length === 0" class="p-12 text-center text-slate-400 italic text-xs">
        Không có phát sinh giao dịch thu/hoàn tiền nào trong ngày {{ selectedDate }}.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-xs text-slate-600">
          <thead class="bg-slate-100/75 text-slate-700 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
            <tr>
              <th class="py-3 px-5">Phương thức thanh toán</th>
              <th class="py-3 px-4">Kênh thực hiện</th>
              <th class="py-3 px-4 text-right">Tổng thu (+)</th>
              <th class="py-3 px-4 text-right">Tổng hoàn (-)</th>
              <th class="py-3 px-4 text-right">Thực thu ròng</th>
              <th class="py-3 px-4 text-right">Tỷ trọng thu</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="(it, idx) in items" :key="idx" class="hover:bg-slate-50/80 transition">
              <td class="py-3 px-5 font-bold text-slate-800 flex items-center gap-2">
                <span>{{ formatMethodIcon(it.paymentMethod) }}</span>
                <span>{{ formatMethodName(it.paymentMethod) }}</span>
              </td>
              <td class="py-3 px-4">
                <span
                  class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                  :class="it.channel === 'QUAY' ? 'bg-amber-100 text-amber-800' : 'bg-indigo-100 text-indigo-800'"
                >
                  {{ it.channel === 'QUAY' ? 'Tại quầy' : 'Cổng trực tuyến' }}
                </span>
              </td>
              <td class="py-3 px-4 text-right font-mono font-semibold text-emerald-700">
                +{{ formatCurrency(it.totalCollected) }}
              </td>
              <td class="py-3 px-4 text-right font-mono font-semibold text-rose-700">
                {{ it.totalRefunded > 0 ? '-' + formatCurrency(it.totalRefunded) : '0 ₫' }}
              </td>
              <td class="py-3 px-4 text-right font-mono font-black text-slate-900">
                {{ formatCurrency(it.netRevenue) }}
              </td>
              <td class="py-3 px-4 text-right font-mono text-slate-500 text-[11px]">
                {{ calculateShare(it.totalCollected) }}%
              </td>
            </tr>
          </tbody>
          <!-- Footer Totals Row -->
          <tfoot class="bg-slate-50/90 font-bold border-t-2 border-slate-200 text-slate-900">
            <tr>
              <td class="py-3.5 px-5 uppercase text-[11px] tracking-wider text-slate-800" colspan="2">
                Tổng cộng toàn khách sạn
              </td>
              <td class="py-3.5 px-4 text-right font-mono text-emerald-800 text-sm">
                +{{ formatCurrency(reconData?.grandTotalCollected || 0) }}
              </td>
              <td class="py-3.5 px-4 text-right font-mono text-rose-800 text-sm">
                -{{ formatCurrency(reconData?.grandTotalRefunded || 0) }}
              </td>
              <td class="py-3.5 px-4 text-right font-mono text-sky-900 text-base font-black">
                {{ formatCurrency(reconData?.grandNetRevenue || 0) }}
              </td>
              <td class="py-3.5 px-4 text-right font-mono text-slate-500 text-xs">
                100%
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Coins,
  RefreshCw,
  Download,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  ArrowDownLeft,
  ArrowUpRight,
  CreditCard
} from 'lucide-vue-next'
import apiClient from '../../api/client'

const loading = ref(false)
const selectedDate = ref(new Date().toISOString().slice(0, 10))
const reconData = ref(null)

const toast = ref({
  show: false,
  message: '',
  isError: false,
  timer: null
})

function showToast(message, isError = false) {
  if (toast.value.timer) clearTimeout(toast.value.timer)
  toast.value.message = message
  toast.value.isError = isError
  toast.value.show = true
  toast.value.timer = setTimeout(() => {
    toast.value.show = false
  }, 4000)
}

const items = computed(() => reconData.value?.items || [])

const isToday = computed(() => {
  return selectedDate.value === new Date().toISOString().slice(0, 10)
})

const isYesterday = computed(() => {
  const y = new Date()
  y.setDate(y.getDate() - 1)
  return selectedDate.value === y.toISOString().slice(0, 10)
})

function setQuickDate(offsetDays) {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  selectedDate.value = d.toISOString().slice(0, 10)
  fetchReconciliation()
}

async function fetchReconciliation() {
  loading.value = true
  try {
    const res = await apiClient.get('/reconciliation/daily', {
      params: { date: selectedDate.value }
    })
    reconData.value = res
  } catch (err) {
    showToast(err.detail || err.message || 'Không thể tải báo cáo đối soát', true)
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  const token = sessionStorage.getItem('token') || ''
  const exportUrl = `${import.meta.env.VITE_API_URL || '/api/v1'}/reconciliation/daily/export?date=${selectedDate.value}`
  window.open(exportUrl, '_blank')
}

function calculateShare(amount) {
  const total = reconData.value?.grandTotalCollected || 0
  if (total <= 0) return '0.0'
  return ((amount / total) * 100).toFixed(1)
}

function formatMethodName(method) {
  switch (method) {
    case 'TIEN_MAT': return 'Tiền mặt tại quầy'
    case 'CHUYEN_KHOAN': return 'Chuyển khoản ngân hàng'
    case 'THE': return 'Quẹt thẻ máy POS'
    case 'ONLINE': return 'Cổng thanh toán điện tử'
    default: return method
  }
}

function formatMethodIcon(method) {
  switch (method) {
    case 'TIEN_MAT': return '💵'
    case 'CHUYEN_KHOAN': return '🏦'
    case 'THE': return '💳'
    case 'ONLINE': return '🌐'
    default: return '💰'
  }
}

function formatCurrency(val) {
  if (val === undefined || val === null) return '0 ₫'
  return Number(val).toLocaleString('vi-VN') + ' ₫'
}

onMounted(() => {
  fetchReconciliation()
})
</script>
