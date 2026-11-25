<template>
  <div class="space-y-6 pb-16 max-w-7xl mx-auto">
    <!-- Header & Action Toolbar -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Sparkles class="w-7 h-7 text-emerald-600" />
            <span>Nhiệm vụ buồng phòng & Vệ sinh</span>
          </h1>
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
            F15 Vận hành
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Theo dõi trạng thái buồng phòng, bắt đầu dọn và nghiệm thu phòng sạch sẵn sàng đón khách (FR-24, FR-25, AC-16)
        </p>
      </div>

      <!-- Action Bar: Role indicator & Refresh -->
      <div class="flex items-center gap-3">
        <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-slate-100 border border-slate-200 rounded-xl text-xs text-slate-700 font-medium">
          <ShieldCheck class="w-4 h-4 text-emerald-600" />
          <span>Vai trò: <strong class="text-slate-900">{{ currentRoleName }}</strong></span>
        </div>

        <button
          @click="fetchTasks"
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

    <!-- KPI & Summary Cards (Touch-Friendly filter buttons) -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      <!-- Cần dọn (DANG_DON) -->
      <div
        @click="filterStatus = 'DANG_DON'"
        class="p-4 rounded-2xl border transition-all cursor-pointer shadow-sm hover:shadow"
        :class="filterStatus === 'DANG_DON' ? 'bg-purple-50 border-purple-300 ring-2 ring-purple-500/30' : 'bg-white border-slate-200 hover:border-purple-200'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-purple-700">Cần dọn dẹp</span>
          <div class="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center text-purple-600">
            <Sparkles class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-black text-purple-900">{{ stats.cleaning }}</span>
          <span class="text-xs font-medium text-slate-400">phòng</span>
        </div>
      </div>

      <!-- Đang bảo trì (BAO_TRI) -->
      <div
        @click="filterStatus = 'BAO_TRI'"
        class="p-4 rounded-2xl border transition-all cursor-pointer shadow-sm hover:shadow"
        :class="filterStatus === 'BAO_TRI' ? 'bg-rose-50 border-rose-300 ring-2 ring-rose-500/30' : 'bg-white border-slate-200 hover:border-rose-200'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-rose-700">Đang bảo trì</span>
          <div class="w-8 h-8 rounded-lg bg-rose-100 flex items-center justify-center text-rose-600">
            <Wrench class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-black text-rose-900">{{ stats.maintenance }}</span>
          <span class="text-xs font-medium text-slate-400">phòng</span>
        </div>
      </div>

      <!-- Trống sẵn sàng (TRONG) -->
      <div
        @click="filterStatus = 'TRONG'"
        class="p-4 rounded-2xl border transition-all cursor-pointer shadow-sm hover:shadow"
        :class="filterStatus === 'TRONG' ? 'bg-emerald-50 border-emerald-300 ring-2 ring-emerald-500/30' : 'bg-white border-slate-200 hover:border-emerald-200'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-emerald-700">Sẵn sàng</span>
          <div class="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600">
            <CheckCircle2 class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-black text-emerald-900">{{ stats.available }}</span>
          <span class="text-xs font-medium text-slate-400">phòng</span>
        </div>
      </div>

      <!-- Tất cả phòng -->
      <div
        @click="filterStatus = 'ALL'"
        class="p-4 rounded-2xl border transition-all cursor-pointer shadow-sm hover:shadow"
        :class="filterStatus === 'ALL' ? 'bg-slate-100 border-slate-300 ring-2 ring-slate-400/30' : 'bg-white border-slate-200 hover:border-slate-300'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-600">Tổng buồng phòng</span>
          <div class="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600">
            <Layers class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-black text-slate-900">{{ allRooms.length }}</span>
          <span class="text-xs font-medium text-slate-400">phòng</span>
        </div>
      </div>
    </div>

    <!-- Filters & Search Toolbar -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
      <!-- Status Tabs -->
      <div class="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
        <button
          v-for="st in statusTabOptions"
          :key="st.key"
          @click="filterStatus = st.key"
          class="px-3 py-1.5 rounded-xl font-semibold transition flex items-center gap-1.5 whitespace-nowrap"
          :class="filterStatus === st.key ? 'bg-slate-900 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        >
          <span>{{ st.label }}</span>
          <span class="px-1.5 py-0.2 rounded-full text-[10px]" :class="filterStatus === st.key ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'">
            {{ getCountByStatus(st.key) }}
          </span>
        </button>
      </div>

      <!-- Floor Filter & Search -->
      <div class="flex items-center gap-2">
        <select
          v-model="filterFloor"
          class="px-3 py-1.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium text-slate-700 outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option :value="null">Tất cả các tầng</option>
          <option v-for="fl in availableFloors" :key="fl" :value="fl">
            Tầng {{ fl }}
          </option>
        </select>

        <div class="relative min-w-[140px]">
          <Search class="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            v-model="searchQuery"
            placeholder="Tìm số phòng..."
            class="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-300 rounded-xl text-xs outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && allRooms.length === 0" class="py-16 text-center text-slate-400 space-y-3">
      <RefreshCw class="w-8 h-8 mx-auto animate-spin text-emerald-500" />
      <p class="text-sm">Đang tải danh sách nhiệm vụ buồng phòng...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredRooms.length === 0" class="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3 shadow-sm">
      <div class="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center">
        <CheckCircle2 class="w-6 h-6" />
      </div>
      <h3 class="text-sm font-bold text-slate-800">Không có phòng nào trong danh sách lọc</h3>
      <p class="text-xs text-slate-500 max-w-sm mx-auto">
        Hiện tại không có phòng nào phù hợp với bộ lọc đã chọn. Hãy thử chọn tầng khác hoặc trạng thái "Tất cả".
      </p>
    </div>

    <!-- Grouped Room List by Floor -->
    <div v-else class="space-y-6">
      <div
        v-for="group in groupedRooms"
        :key="group.floor"
        class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
      >
        <!-- Floor Header -->
        <div class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Layers class="w-4 h-4 text-slate-500" />
            <h2 class="text-sm font-bold text-slate-900 tracking-wide">
              Tầng {{ group.floor }}
            </h2>
            <span class="text-xs text-slate-400">({{ group.rooms.length }} phòng)</span>
          </div>

          <!-- Quick counts on floor -->
          <div class="flex items-center gap-2 text-[11px] font-semibold">
            <span v-if="group.cleaningCount > 0" class="px-2 py-0.5 rounded-md bg-purple-100 text-purple-800">
              {{ group.cleaningCount }} cần dọn
            </span>
            <span v-if="group.maintenanceCount > 0" class="px-2 py-0.5 rounded-md bg-rose-100 text-rose-800">
              {{ group.maintenanceCount }} bảo trì
            </span>
            <span class="px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800">
              {{ group.availableCount }} sẵn sàng
            </span>
          </div>
        </div>

        <!-- Rooms Grid -->
        <div class="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          <div
            v-for="room in group.rooms"
            :key="room.roomId"
            class="p-4 rounded-xl border transition-all flex flex-col justify-between"
            :class="getRoomCardBorderClass(room.status)"
          >
            <!-- Card Header: Room Number & Type -->
            <div>
              <div class="flex items-start justify-between">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="text-xl font-black text-slate-900 tracking-tight">Phòng {{ room.roomNumber }}</span>
                    <span class="text-[11px] px-2 py-0.5 rounded-md font-semibold bg-slate-100 text-slate-700">
                      {{ room.roomTypeName }}
                    </span>
                  </div>
                  <div class="text-[11px] text-slate-400 mt-0.5">
                    Mã hạng: <span class="font-mono text-slate-600">{{ room.roomType }}</span>
                  </div>
                </div>

                <!-- Status Badge -->
                <span
                  class="px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider flex items-center gap-1"
                  :class="getStatusBadgeClass(room.status)"
                >
                  <span class="w-1.5 h-1.5 rounded-full" :class="getStatusDotClass(room.status)"></span>
                  {{ getStatusText(room.status) }}
                </span>
              </div>

              <!-- Notes (Ghi chú bảo dưỡng / dọn) -->
              <div v-if="room.notes" class="mt-3 p-2 bg-slate-50 rounded-lg text-xs text-slate-600 border border-slate-100">
                <span class="font-semibold text-slate-700">Ghi chú:</span> {{ room.notes }}
              </div>

              <!-- Last Action Timestamp -->
              <div class="mt-3 flex items-center gap-1.5 text-[11px] text-slate-400">
                <Clock class="w-3.5 h-3.5" />
                <span v-if="room.lastActionAt">
                  Hoạt động gần nhất: <strong class="text-slate-600">{{ formatDateTime(room.lastActionAt) }}</strong>
                </span>
                <span v-else>Chưa có nhật ký gần đây</span>
              </div>
            </div>

            <!-- Card Actions: Large Touch Buttons for Mobile -->
            <div class="mt-4 pt-3 border-t border-slate-100">
              <!-- When Room is DANG_DON: Show 'Bắt đầu dọn' and 'Dọn xong' buttons -->
              <div v-if="room.status === 'DANG_DON'" class="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  @click="handleStartCleaning(room)"
                  :disabled="actionLoading[room.roomId]"
                  class="py-2.5 px-3 bg-sky-50 hover:bg-sky-100 text-sky-700 font-bold rounded-xl text-xs transition border border-sky-200 flex items-center justify-center gap-1.5 active:scale-95 disabled:opacity-50"
                >
                  <Play class="w-3.5 h-3.5 fill-current" />
                  <span>Bắt đầu dọn</span>
                </button>

                <button
                  type="button"
                  @click="handleFinishCleaning(room)"
                  :disabled="actionLoading[room.roomId]"
                  class="py-2.5 px-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center justify-center gap-1.5 active:scale-95 disabled:opacity-50"
                >
                  <Check class="w-4 h-4 stroke-[3]" />
                  <span>Dọn xong</span>
                </button>
              </div>

              <!-- When Room is BAO_TRI -->
              <div v-else-if="room.status === 'BAO_TRI'" class="flex items-center justify-between text-xs py-1">
                <span class="text-rose-700 font-semibold flex items-center gap-1">
                  <Wrench class="w-3.5 h-3.5" />
                  <span>Đang sửa chữa kỹ thuật</span>
                </span>
                <span class="text-slate-400 text-[11px]">Chỉ quản lý/lễ tân kết thúc</span>
              </div>

              <!-- When Room is TRONG -->
              <div v-else-if="room.status === 'TRONG'" class="flex items-center justify-between text-xs py-1">
                <span class="text-emerald-700 font-semibold flex items-center gap-1">
                  <CheckCircle2 class="w-4 h-4" />
                  <span>Phòng sạch, sẵn sàng đón khách</span>
                </span>
                <span class="text-slate-400 text-[11px]">Sẵn sàng</span>
              </div>

              <!-- When Room is DANG_O -->
              <div v-else-if="room.status === 'DANG_O'" class="flex items-center justify-between text-xs py-1">
                <span class="text-blue-700 font-semibold flex items-center gap-1">
                  <BedDouble class="w-3.5 h-3.5" />
                  <span>Khách đang lưu trú</span>
                </span>
                <span class="text-slate-400 text-[11px]">Đang sử dụng</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import {
  Sparkles,
  RefreshCw,
  CheckCircle2,
  Wrench,
  Clock,
  Search,
  BedDouble,
  AlertTriangle,
  Play,
  Check,
  Layers,
  ShieldCheck
} from 'lucide-vue-next'
import apiClient from '../../api/client'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

const loading = ref(false)
const allRooms = ref([])
const filterStatus = ref('DANG_DON')
const filterFloor = ref(null)
const searchQuery = ref('')
const actionLoading = reactive({})

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

const currentRoleName = computed(() => {
  const role = authStore.user?.role
  if (role === 'BUONG_PHONG') return 'Buồng phòng'
  if (role === 'LE_TAN') return 'Lễ tân'
  if (role === 'QUAN_LY') return 'Quản lý'
  return role || 'Nhân viên'
})

const statusTabOptions = [
  { key: 'DANG_DON', label: 'Cần dọn dẹp' },
  { key: 'BAO_TRI', label: 'Đang bảo trì' },
  { key: 'TRONG', label: 'Sẵn sàng' },
  { key: 'ALL', label: 'Tất cả phòng' }
]

const stats = computed(() => {
  let cleaning = 0
  let maintenance = 0
  let available = 0
  let occupied = 0

  for (const r of allRooms.value) {
    if (r.status === 'DANG_DON') cleaning++
    else if (r.status === 'BAO_TRI') maintenance++
    else if (r.status === 'TRONG') available++
    else if (r.status === 'DANG_O') occupied++
  }

  return { cleaning, maintenance, available, occupied }
})

function getCountByStatus(st) {
  if (st === 'ALL') return allRooms.value.length
  if (st === 'DANG_DON') return stats.value.cleaning
  if (st === 'BAO_TRI') return stats.value.maintenance
  if (st === 'TRONG') return stats.value.available
  return 0
}

const availableFloors = computed(() => {
  const floors = new Set()
  for (const r of allRooms.value) {
    if (r.floor) floors.add(r.floor)
  }
  return Array.from(floors).sort((a, b) => a - b)
})

const filteredRooms = computed(() => {
  return allRooms.value.filter(r => {
    // Status filter
    if (filterStatus.value !== 'ALL' && r.status !== filterStatus.value) {
      return false
    }
    // Floor filter
    if (filterFloor.value !== null && r.floor !== filterFloor.value) {
      return false
    }
    // Search query
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.trim().toLowerCase()
      const matchNum = r.roomNumber?.toLowerCase().includes(q)
      const matchType = r.roomTypeName?.toLowerCase().includes(q)
      if (!matchNum && !matchType) return false
    }
    return true
  })
})

const groupedRooms = computed(() => {
  const groups = {}
  for (const room of filteredRooms.value) {
    const f = room.floor || 1
    if (!groups[f]) {
      groups[f] = {
        floor: f,
        rooms: [],
        cleaningCount: 0,
        maintenanceCount: 0,
        availableCount: 0
      }
    }
    groups[f].rooms.push(room)
    if (room.status === 'DANG_DON') groups[f].cleaningCount++
    else if (room.status === 'BAO_TRI') groups[f].maintenanceCount++
    else if (room.status === 'TRONG') groups[f].availableCount++
  }

  // Sort groups by floor ascending
  return Object.values(groups).sort((a, b) => a.floor - b.floor)
})

async function fetchTasks() {
  loading.value = true
  try {
    // Luôn lấy toàn bộ danh sách trạng thái để phân loại trên giao diện
    const res = await apiClient.get('/housekeeping/tasks', {
      params: { status: 'ALL' }
    })
    allRooms.value = res.items || res.data?.items || []
  } catch (err) {
    showToast(err.response?.data?.detail || 'Không thể tải danh sách buồng phòng', true)
  } finally {
    loading.value = false
  }
}

async function handleStartCleaning(room) {
  actionLoading[room.roomId] = true
  try {
    const res = await apiClient.post(`/housekeeping/${room.roomId}/start`)
    showToast(`Đã bắt đầu dọn phòng ${room.roomNumber}`)
    // Cập nhật lại danh sách phòng
    await fetchTasks()
  } catch (err) {
    showToast(err.response?.data?.detail || `Không thể bắt đầu dọn phòng ${room.roomNumber}`, true)
  } finally {
    actionLoading[room.roomId] = false
  }
}

async function handleFinishCleaning(room) {
  actionLoading[room.roomId] = true
  try {
    const res = await apiClient.post(`/housekeeping/${room.roomId}/done`)
    showToast(`Đã dọn xong phòng ${room.roomNumber}! Phòng đã sẵn sàng đón khách.`)
    await fetchTasks()
  } catch (err) {
    showToast(err.response?.data?.detail || `Không thể xác nhận dọn xong phòng ${room.roomNumber}`, true)
  } finally {
    actionLoading[room.roomId] = false
  }
}

function getStatusText(status) {
  switch (status) {
    case 'DANG_DON': return 'Cần dọn dẹp'
    case 'BAO_TRI': return 'Đang bảo trì'
    case 'TRONG': return 'Trống sẵn sàng'
    case 'DANG_O': return 'Đang có khách'
    default: return status
  }
}

function getStatusBadgeClass(status) {
  switch (status) {
    case 'DANG_DON': return 'bg-purple-100 text-purple-800 border border-purple-200'
    case 'BAO_TRI': return 'bg-rose-100 text-rose-800 border border-rose-200'
    case 'TRONG': return 'bg-emerald-100 text-emerald-800 border border-emerald-200'
    case 'DANG_O': return 'bg-blue-100 text-blue-800 border border-blue-200'
    default: return 'bg-slate-100 text-slate-700'
  }
}

function getStatusDotClass(status) {
  switch (status) {
    case 'DANG_DON': return 'bg-purple-600 animate-pulse'
    case 'BAO_TRI': return 'bg-rose-600'
    case 'TRONG': return 'bg-emerald-600'
    case 'DANG_O': return 'bg-blue-600'
    default: return 'bg-slate-400'
  }
}

function getRoomCardBorderClass(status) {
  switch (status) {
    case 'DANG_DON': return 'border-purple-200 bg-purple-50/20 hover:border-purple-300'
    case 'BAO_TRI': return 'border-rose-200 bg-rose-50/20 hover:border-rose-300'
    case 'TRONG': return 'border-emerald-200 bg-emerald-50/20 hover:border-emerald-300'
    case 'DANG_O': return 'border-blue-200 bg-blue-50/20 hover:border-blue-300'
    default: return 'border-slate-200 bg-white'
  }
}

function formatDateTime(isoStr) {
  if (!isoStr) return ''
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

let refreshInterval = null

onMounted(() => {
  fetchTasks()
  // Tự động làm mới mỗi 30 giây
  refreshInterval = setInterval(() => {
    fetchTasks()
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>
