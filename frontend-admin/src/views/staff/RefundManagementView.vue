<template>
  <div class="space-y-6 pb-16 max-w-7xl mx-auto">
    <!-- Header & Action Toolbar -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Undo2 class="w-7 h-7 text-amber-600" />
            <span>Quản lý hoàn tiền & Phê duyệt</span>
          </h1>
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
            F12 Tài chính
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Quy trình phê duyệt hoàn tiền hai bước (Lễ tân đề xuất → Quản lý duyệt → Xác nhận chi tiền) (FR-37, BR-25, BR-26)
        </p>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-3">
        <button
          v-if="isManager"
          type="button"
          @click="openOverrideModal"
          class="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition active:scale-95"
        >
          <ShieldAlert class="w-4 h-4 text-white" />
          <span>Hoàn ngoại lệ (BR-26)</span>
        </button>

        <button
          type="button"
          @click="fetchRefunds"
          :disabled="loading"
          class="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shadow-sm transition active:scale-95 disabled:opacity-50"
        >
          <RefreshCw class="w-4 h-4 text-slate-500" :class="{ 'animate-spin': loading }" />
          <span>Làm mới</span>
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
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      <div
        @click="filterStatus = 'CHO_DUYET'"
        class="p-4 rounded-2xl border transition-all cursor-pointer shadow-sm hover:shadow"
        :class="filterStatus === 'CHO_DUYET' ? 'bg-amber-50 border-amber-300 ring-2 ring-amber-500/30' : 'bg-white border-slate-200 hover:border-amber-200'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-amber-700">Chờ duyệt</span>
          <div class="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center text-amber-600">
            <Clock class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-black text-amber-900">{{ stats.pending }}</span>
          <span class="text-xs font-medium text-slate-400">yêu cầu</span>
        </div>
      </div>

      <div
        @click="filterStatus = 'DA_DUYET'"
        class="p-4 rounded-2xl border transition-all cursor-pointer shadow-sm hover:shadow"
        :class="filterStatus === 'DA_DUYET' ? 'bg-sky-50 border-sky-300 ring-2 ring-sky-500/30' : 'bg-white border-slate-200 hover:border-sky-200'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-sky-700">Đã duyệt (Chờ chi)</span>
          <div class="w-8 h-8 rounded-lg bg-sky-100 flex items-center justify-center text-sky-600">
            <CheckCircle2 class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-black text-sky-900">{{ stats.approved }}</span>
          <span class="text-xs font-medium text-slate-400">yêu cầu</span>
        </div>
      </div>

      <div
        @click="filterStatus = 'DA_HOAN'"
        class="p-4 rounded-2xl border transition-all cursor-pointer shadow-sm hover:shadow"
        :class="filterStatus === 'DA_HOAN' ? 'bg-emerald-50 border-emerald-300 ring-2 ring-emerald-500/30' : 'bg-white border-slate-200 hover:border-emerald-200'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-emerald-700">Đã chi hoàn tất</span>
          <div class="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600">
            <Banknote class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-black text-emerald-900">{{ stats.completed }}</span>
          <span class="text-xs font-medium text-slate-400">yêu cầu</span>
        </div>
      </div>

      <div
        @click="filterStatus = 'ALL'"
        class="p-4 rounded-2xl border transition-all cursor-pointer shadow-sm hover:shadow"
        :class="filterStatus === 'ALL' ? 'bg-slate-100 border-slate-300 ring-2 ring-slate-400/30' : 'bg-white border-slate-200 hover:border-slate-300'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-600">Tổng yêu cầu</span>
          <div class="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600">
            <Layers class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-black text-slate-900">{{ totalItems }}</span>
          <span class="text-xs font-medium text-slate-400">khoản</span>
        </div>
      </div>
    </div>

    <!-- Filters Bar -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
      <!-- Status Tabs -->
      <div class="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
        <button
          v-for="st in statusTabOptions"
          :key="st.key"
          @click="changeTab(st.key)"
          class="px-3 py-1.5 rounded-xl font-semibold transition flex items-center gap-1.5 whitespace-nowrap"
          :class="filterStatus === st.key ? 'bg-slate-900 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        >
          <span>{{ st.label }}</span>
        </button>
      </div>

      <!-- Search Box -->
      <div class="relative min-w-[200px]">
        <Search class="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
        <input
          type="text"
          v-model="searchQuery"
          @keyup.enter="fetchRefunds"
          placeholder="Lọc mã đơn, người nhận..."
          class="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-300 rounded-xl text-xs outline-none focus:ring-2 focus:ring-amber-500"
        />
      </div>
    </div>

    <!-- Refunds Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div v-if="loading && refunds.length === 0" class="py-16 text-center text-slate-400 space-y-3">
        <RefreshCw class="w-8 h-8 mx-auto animate-spin text-amber-500" />
        <p class="text-sm">Đang tải danh sách hoàn tiền...</p>
      </div>

      <div v-else-if="refunds.length === 0" class="p-12 text-center text-slate-400 italic text-xs">
        Không có yêu cầu hoàn tiền nào phù hợp với bộ lọc.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-xs text-slate-600">
          <thead class="bg-slate-50 text-slate-700 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
            <tr>
              <th class="py-3 px-4">Mã đơn</th>
              <th class="py-3 px-4">Khách hàng</th>
              <th class="py-3 px-4">Phương thức / Kênh</th>
              <th class="py-3 px-4 text-right">Số tiền hoàn</th>
              <th class="py-3 px-4">Lý do</th>
              <th class="py-3 px-4">Người đề nghị / Duyệt</th>
              <th class="py-3 px-4">Ngày tạo</th>
              <th class="py-3 px-4 text-center">Trạng thái</th>
              <th class="py-3 px-4 text-center">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="r in refunds" :key="r.refundId" class="hover:bg-slate-50/80 transition">
              <td class="py-3 px-4">
                <router-link
                  :to="`/nv/don/${r.bookingCode}`"
                  class="font-mono font-bold text-sky-700 hover:underline"
                >
                  {{ r.bookingCode }}
                </router-link>
              </td>
              <td class="py-3 px-4">
                <div class="font-medium text-slate-800">{{ r.customerName || 'N/A' }}</div>
                <div class="text-[11px] text-slate-400 font-mono">{{ r.customerPhone || '' }}</div>
              </td>
              <td class="py-3 px-4">
                <span class="font-semibold text-slate-700">{{ formatMethod(r.method) }}</span>
                <span class="text-[10px] px-1.5 py-0.2 rounded ml-1 bg-slate-100 text-slate-500 font-bold uppercase">
                  {{ r.channel }}
                </span>
              </td>
              <td class="py-3 px-4 text-right font-mono font-bold text-rose-700">
                {{ formatCurrency(r.amount) }}
              </td>
              <td class="py-3 px-4 max-w-xs truncate" :title="r.reason">
                {{ r.reason || '-' }}
              </td>
              <td class="py-3 px-4 text-[11px]">
                <div class="text-slate-700">Đề nghị: <strong>{{ r.requesterName || 'Hệ thống' }}</strong></div>
                <div v-if="r.approverName" class="text-slate-500">Duyệt: <strong>{{ r.approverName }}</strong></div>
              </td>
              <td class="py-3 px-4 font-mono text-[11px] text-slate-500">
                {{ formatDateTime(r.createdAt) }}
              </td>
              <td class="py-3 px-4 text-center">
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                  :class="getStatusBadgeClass(r.status)"
                >
                  {{ getStatusText(r.status) }}
                </span>
              </td>
              <td class="py-3 px-4 text-center whitespace-nowrap">
                <!-- Action for CHO_DUYET: Quản lý Duyệt / Từ chối -->
                <div v-if="r.status === 'CHO_DUYET'" class="flex items-center justify-center gap-1.5">
                  <button
                    type="button"
                    v-if="isManager"
                    @click="handleApprove(r, true)"
                    :disabled="actionLoading[r.refundId]"
                    class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg text-[11px] transition shadow-sm disabled:opacity-50"
                  >
                    Duyệt
                  </button>
                  <button
                    type="button"
                    v-if="isManager"
                    @click="handleApprove(r, false)"
                    :disabled="actionLoading[r.refundId]"
                    class="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold rounded-lg text-[11px] transition disabled:opacity-50"
                  >
                    Từ chối
                  </button>
                  <span v-if="!isManager" class="text-[11px] text-amber-700 font-medium">Chờ Quản lý duyệt</span>
                </div>

                <!-- Action for DA_DUYET: Xác nhận đã chi tiền (Lễ tân/Quản lý) -->
                <div v-else-if="r.status === 'DA_DUYET'" class="flex items-center justify-center">
                  <button
                    type="button"
                    @click="handleComplete(r)"
                    :disabled="actionLoading[r.refundId]"
                    class="px-3 py-1 bg-sky-600 hover:bg-sky-700 text-white font-bold rounded-lg text-[11px] transition shadow-sm disabled:opacity-50 flex items-center gap-1"
                  >
                    <Check class="w-3.5 h-3.5 stroke-[3]" />
                    <span>Đã chi tiền</span>
                  </button>
                </div>

                <div v-else class="text-slate-400 text-[11px] italic">
                  Đã hoàn tất
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Hoàn tiền ngoại lệ (BR-26, chỉ Quản lý) -->
    <div
      v-if="showOverrideModal"
      class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-fadeIn">
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center">
              <ShieldAlert class="w-4 h-4" />
            </div>
            <div>
              <h2 class="text-sm font-bold text-slate-900">Hoàn tiền ngoại lệ (BR-26)</h2>
              <p class="text-[11px] text-slate-500">Chỉ dành cho Quản lý khách sạn - Bắt buộc nhập lý do chi tiết</p>
            </div>
          </div>
          <button @click="showOverrideModal = false" class="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <div class="p-6 space-y-4 text-xs">
          <div v-if="overrideError" class="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl flex items-center gap-2">
            <AlertTriangle class="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{{ overrideError }}</span>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Mã ID đơn đặt phòng *</label>
            <input
              type="number"
              v-model.number="overrideForm.bookingId"
              placeholder="VD: 14487"
              class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-mono font-bold focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Số tiền muốn hoàn (VND) *</label>
            <input
              type="number"
              v-model.number="overrideForm.amount"
              min="1000"
              step="1000"
              placeholder="VD: 500000"
              class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-mono font-bold focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Lý do hoàn ngoại lệ (bắt buộc) *</label>
            <textarea
              v-model="overrideForm.reason"
              rows="3"
              placeholder="Nhập lý do cụ thể theo quy định BR-26 (VD: Khiếu nại dịch vụ VIP, sự cố điện nước...)"
              class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-indigo-500 outline-none"
            ></textarea>
          </div>
        </div>

        <div class="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end gap-2">
          <button
            type="button"
            @click="showOverrideModal = false"
            class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition"
          >
            Hủy
          </button>
          <button
            type="button"
            @click="submitOverride"
            :disabled="overrideSubmitting || overrideForm.bookingId <= 0 || overrideForm.amount <= 0 || !overrideForm.reason.trim()"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs shadow-sm transition disabled:opacity-50 flex items-center gap-1.5"
          >
            <RefreshCw v-if="overrideSubmitting" class="w-3.5 h-3.5 animate-spin" />
            <span>Xác nhận hoàn ngoại lệ</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import {
  Undo2,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Banknote,
  Layers,
  Search,
  Check,
  ShieldAlert
} from 'lucide-vue-next'
import apiClient from '../../api/client'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const isManager = computed(() => authStore.user?.role === 'QUAN_LY')

const loading = ref(false)
const refunds = ref([])
const totalItems = ref(0)
const filterStatus = ref('CHO_DUYET')
const searchQuery = ref('')
const actionLoading = reactive({})

const stats = reactive({
  pending: 0,
  approved: 0,
  completed: 0
})

const toast = reactive({
  show: false,
  message: '',
  isError: false,
  timer: null
})

function showToast(message, isError = false) {
  if (toast.timer) clearTimeout(toast.timer)
  toast.message = message
  toast.isError = isError
  toast.show = true
  toast.timer = setTimeout(() => {
    toast.show = false
  }, 4000)
}

const statusTabOptions = [
  { key: 'CHO_DUYET', label: 'Chờ duyệt' },
  { key: 'DA_DUYET', label: 'Đã duyệt (Chờ chi)' },
  { key: 'DA_HOAN', label: 'Đã hoàn tất' },
  { key: 'TU_CHOI', label: 'Đã từ chối' },
  { key: 'ALL', label: 'Tất cả' }
]

function changeTab(st) {
  filterStatus.value = st
  fetchRefunds()
}

async function fetchStats() {
  try {
    const resPending = await apiClient.get('/refunds', { params: { status: 'CHO_DUYET', pageSize: 1 } })
    stats.pending = resPending.total || 0

    const resApproved = await apiClient.get('/refunds', { params: { status: 'DA_DUYET', pageSize: 1 } })
    stats.approved = resApproved.total || 0

    const resCompleted = await apiClient.get('/refunds', { params: { status: 'DA_HOAN', pageSize: 1 } })
    stats.completed = resCompleted.total || 0
  } catch (err) {
    console.error('Lỗi tải thống kê hoàn tiền:', err)
  }
}

async function fetchRefunds() {
  loading.value = true
  try {
    const params = {
      status: filterStatus.value,
      pageSize: 50
    }
    const res = await apiClient.get('/refunds', { params })
    refunds.value = res.items || []
    totalItems.value = res.total || 0
    await fetchStats()
  } catch (err) {
    showToast(err.detail || err.message || 'Không thể tải danh sách hoàn tiền', true)
  } finally {
    loading.value = false
  }
}

async function handleApprove(refund, approved) {
  actionLoading[refund.refundId] = true
  try {
    await apiClient.post(`/refunds/${refund.refundId}/approve`, {
      approved: approved,
      reason: approved ? 'Quản lý chấp thuận' : 'Từ chối hoàn tiền'
    })
    showToast(approved ? `Đã phê duyệt hoàn tiền đơn ${refund.bookingCode}` : `Đã từ chối hoàn tiền đơn ${refund.bookingCode}`)
    await fetchRefunds()
  } catch (err) {
    showToast(err.detail || err.message || 'Không thể xử lý phê duyệt', true)
  } finally {
    actionLoading[refund.refundId] = false
  }
}

async function handleComplete(refund) {
  actionLoading[refund.refundId] = true
  try {
    await apiClient.post(`/refunds/${refund.refundId}/complete`)
    showToast(`Đã xác nhận chi tiền hoàn cho đơn ${refund.bookingCode}`)
    await fetchRefunds()
  } catch (err) {
    showToast(err.detail || err.message || 'Không thể xác nhận chi tiền', true)
  } finally {
    actionLoading[refund.refundId] = false
  }
}

// Override Modal State
const showOverrideModal = ref(false)
const overrideSubmitting = ref(false)
const overrideError = ref('')
const overrideForm = reactive({
  bookingId: 0,
  amount: 0,
  reason: ''
})

function openOverrideModal() {
  overrideError.value = ''
  overrideForm.bookingId = 0
  overrideForm.amount = 0
  overrideForm.reason = ''
  showOverrideModal.value = true
}

async function submitOverride() {
  if (overrideForm.bookingId <= 0 || overrideForm.amount <= 0 || !overrideForm.reason.trim()) return
  overrideSubmitting.value = true
  overrideError.value = ''
  try {
    await apiClient.post('/refunds/override', {
      bookingId: overrideForm.bookingId,
      amount: overrideForm.amount,
      reason: overrideForm.reason.trim()
    })
    showToast('Đã tạo hoàn tiền ngoại lệ thành công!')
    showOverrideModal.value = false
    await fetchRefunds()
  } catch (err) {
    overrideError.value = err.detail || err.message || 'Lỗi khi tạo hoàn tiền ngoại lệ'
  } finally {
    overrideSubmitting.value = false
  }
}

function formatMethod(method) {
  switch (method) {
    case 'TIEN_MAT': return 'Tiền mặt'
    case 'CHUYEN_KHOAN': return 'Chuyển khoản'
    case 'THE': return 'Quẹt thẻ'
    case 'ONLINE': return 'Cổng trực tuyến'
    default: return method || 'Khác'
  }
}

function getStatusText(status) {
  switch (status) {
    case 'CHO_DUYET': return 'Chờ duyệt'
    case 'DA_DUYET': return 'Đã duyệt (Chờ chi)'
    case 'DA_HOAN': return 'Đã hoàn tất'
    case 'TU_CHOI': return 'Đã từ chối'
    default: return status
  }
}

function getStatusBadgeClass(status) {
  switch (status) {
    case 'CHO_DUYET': return 'bg-amber-100 text-amber-800 border border-amber-200'
    case 'DA_DUYET': return 'bg-sky-100 text-sky-800 border border-sky-200'
    case 'DA_HOAN': return 'bg-emerald-100 text-emerald-800 border border-emerald-200'
    case 'TU_CHOI': return 'bg-rose-100 text-rose-800 border border-rose-200'
    default: return 'bg-slate-100 text-slate-700'
  }
}

function formatCurrency(val) {
  if (val === undefined || val === null) return '0 ₫'
  return Number(val).toLocaleString('vi-VN') + ' ₫'
}

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  try {
    const d = new Date(isoStr)
    return d.toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return isoStr
  }
}

onMounted(() => {
  fetchRefunds()
})
</script>
