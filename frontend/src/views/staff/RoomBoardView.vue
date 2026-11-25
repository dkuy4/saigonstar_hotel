<template>
  <div class="space-y-6 pb-12">
    <!-- Header & Live Bar -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight">Sơ đồ phòng</h1>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 text-sky-800">
            Lễ tân & Quản lý
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Trực quan hóa ma trận 50 phòng theo tầng và thời gian thực (FR-12, US-15, BR-40)
        </p>
      </div>

      <!-- Controls: Time selector & Auto refresh -->
      <div class="flex flex-wrap items-center gap-3">
        <!-- Datetime picker -->
        <div class="flex items-center space-x-1.5 bg-white border border-slate-200 rounded-xl px-3 py-1.5 shadow-sm text-xs">
          <span class="text-slate-400 font-medium">Thời điểm:</span>
          <input
            v-model="atTimeInput"
            @change="handleTimeChange"
            type="datetime-local"
            class="bg-transparent text-slate-800 font-medium outline-none text-xs"
          />
          <button
            v-if="isCustomTime"
            @click="resetToNow"
            title="Quay lại thời gian thực"
            class="px-2 py-0.5 bg-sky-50 text-sky-600 rounded font-bold hover:bg-sky-100 text-[11px]"
          >
            Hiện tại
          </button>
        </div>

        <!-- Auto refresh toggle -->
        <button
          @click="toggleAutoRefresh"
          :class="autoRefresh ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-50 text-slate-500 border-slate-200'"
          class="border px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition"
        >
          <span class="relative flex h-2 w-2">
            <span v-if="autoRefresh" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span :class="autoRefresh ? 'bg-emerald-500' : 'bg-slate-400'" class="relative inline-flex rounded-full h-2 w-2"></span>
          </span>
          <span>Tự làm mới (30s)</span>
        </button>

        <!-- Manual refresh button -->
        <button
          @click="fetchBoard"
          :disabled="loading"
          class="p-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-slate-600 shadow-sm transition disabled:opacity-50"
          title="Làm mới ngay"
        >
          <svg :class="{ 'animate-spin': loading }" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Stats Summary Cards -->
    <div v-if="stats" class="grid grid-cols-2 sm:grid-cols-5 gap-3">
      <div
        @click="filterStatus = 'ALL'"
        :class="filterStatus === 'ALL' ? 'ring-2 ring-slate-800' : ''"
        class="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm cursor-pointer hover:border-slate-300 transition"
      >
        <div class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Tổng phòng</div>
        <div class="text-2xl font-black text-slate-900 mt-0.5">{{ stats.total }}</div>
      </div>

      <div
        @click="filterStatus = 'TRONG'"
        :class="filterStatus === 'TRONG' ? 'ring-2 ring-emerald-500' : ''"
        class="bg-emerald-50/50 p-3.5 rounded-2xl border border-emerald-100 shadow-sm cursor-pointer hover:border-emerald-300 transition"
      >
        <div class="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">Trống sẵn sàng</div>
        <div class="text-2xl font-black text-emerald-800 mt-0.5">{{ stats.available }}</div>
      </div>

      <div
        @click="filterStatus = 'DANG_O'"
        :class="filterStatus === 'DANG_O' ? 'ring-2 ring-blue-500' : ''"
        class="bg-blue-50/50 p-3.5 rounded-2xl border border-blue-100 shadow-sm cursor-pointer hover:border-blue-300 transition"
      >
        <div class="text-[11px] font-bold text-blue-700 uppercase tracking-wider">Đang có khách</div>
        <div class="text-2xl font-black text-blue-800 mt-0.5">{{ stats.occupied }}</div>
      </div>

      <div
        @click="filterStatus = 'DANG_DON'"
        :class="filterStatus === 'DANG_DON' ? 'ring-2 ring-purple-500' : ''"
        class="bg-purple-50/50 p-3.5 rounded-2xl border border-purple-100 shadow-sm cursor-pointer hover:border-purple-300 transition"
      >
        <div class="text-[11px] font-bold text-purple-700 uppercase tracking-wider">Cần dọn dẹp</div>
        <div class="text-2xl font-black text-purple-800 mt-0.5">{{ stats.cleaning }}</div>
      </div>

      <div
        @click="filterStatus = 'BAO_TRI'"
        :class="filterStatus === 'BAO_TRI' ? 'ring-2 ring-red-500' : ''"
        class="bg-red-50/50 p-3.5 rounded-2xl border border-red-100 shadow-sm cursor-pointer hover:border-red-300 transition"
      >
        <div class="text-[11px] font-bold text-red-700 uppercase tracking-wider">Đang bảo trì</div>
        <div class="text-2xl font-black text-red-800 mt-0.5">{{ stats.maintenance }}</div>
      </div>
    </div>

    <!-- Filter Buttons Bar -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200 text-xs">
      <!-- Status Pills -->
      <div class="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0">
        <span class="text-slate-400 font-semibold px-2">Trạng thái:</span>
        <button
          v-for="st in statusOptions"
          :key="st.key"
          @click="filterStatus = st.key"
          :class="filterStatus === st.key ? 'bg-slate-900 text-white font-bold' : 'bg-slate-100 text-slate-600 hover:bg-slate-200 font-medium'"
          class="px-2.5 py-1 rounded-lg transition"
        >
          {{ st.label }}
        </button>
      </div>

      <!-- Room Type Pills -->
      <div class="flex items-center space-x-1.5 overflow-x-auto">
        <span class="text-slate-400 font-semibold px-2">Hạng:</span>
        <button
          v-for="rt in roomTypeOptions"
          :key="rt.key"
          @click="filterType = rt.key"
          :class="filterType === rt.key ? 'bg-sky-600 text-white font-bold' : 'bg-slate-100 text-slate-600 hover:bg-slate-200 font-medium'"
          class="px-2.5 py-1 rounded-lg transition"
        >
          {{ rt.label }}
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center space-x-2">
      <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0" />
      <span>{{ error }}</span>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading && !boardData" class="py-16 text-center text-slate-400">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-sky-600 border-t-transparent mb-3"></div>
      <p class="text-sm font-medium">Đang tải sơ đồ phòng...</p>
    </div>

    <!-- Room Matrix Floors -->
    <div v-else class="space-y-6">
      <div
        v-for="floorGroup in filteredFloors"
        :key="floorGroup.floor"
        class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3"
      >
        <!-- Floor Header -->
        <div class="flex items-center justify-between border-b border-slate-100 pb-2">
          <div class="flex items-center space-x-2">
            <span class="w-7 h-7 bg-slate-900 text-white rounded-lg flex items-center justify-center font-bold text-xs">
              {{ floorGroup.floor }}
            </span>
            <h3 class="text-base font-bold text-slate-800">Tầng {{ floorGroup.floor }}</h3>
          </div>
          <span class="text-xs text-slate-400 font-medium">
            {{ floorGroup.rooms.length }} phòng hiển thị
          </span>
        </div>

        <!-- Room Tiles Grid -->
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 xl:grid-cols-10 gap-3">
          <RoomTile
            v-for="room in floorGroup.rooms"
            :key="room.roomId"
            :room="room"
            :isSelected="selectedRoom?.roomId === room.roomId"
            @select="handleSelectRoom"
          />
        </div>
      </div>
    </div>

    <!-- RIGHT SLIDE-OVER DRAWER (Details & Quick Actions) -->
    <div
      v-if="selectedRoom"
      class="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-white shadow-2xl border-l border-slate-200 p-6 flex flex-col justify-between overflow-y-auto animate-fade-in"
    >
      <div class="space-y-6">
        <!-- Drawer Header -->
        <div class="flex items-start justify-between border-b border-slate-100 pb-4">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-3xl font-black font-mono text-slate-900">{{ selectedRoom.roomNumber }}</span>
              <StatusBadge :status="selectedRoom.status" />
            </div>
            <div class="text-xs text-slate-500 mt-1">
              Tầng {{ selectedRoom.floor }} - Hạng <strong class="text-sky-700">{{ selectedRoom.roomType }}</strong>
            </div>
          </div>
          <button
            @click="selectedRoom = null"
            class="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            ✕
          </button>
        </div>

        <!-- Current Booking Section -->
        <div v-if="selectedRoom.currentBooking" class="bg-blue-50/60 rounded-xl p-4 border border-blue-100 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold uppercase tracking-wider text-blue-800">Lượt đang ở / Giữ chỗ</span>
            <span class="font-mono text-xs font-bold text-blue-900">{{ selectedRoom.currentBooking.bookingCode }}</span>
          </div>
          <div class="space-y-1.5 text-xs text-slate-600">
            <div class="flex justify-between">
              <span class="text-slate-400">Trạng thái:</span>
              <strong class="text-slate-800">{{ selectedRoom.currentBooking.bookingStatus }}</strong>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Nhận phòng:</span>
              <span class="font-medium text-slate-800">{{ formatDateTime(selectedRoom.currentBooking.from) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">Trả phòng:</span>
              <span class="font-medium text-slate-800">{{ formatDateTime(selectedRoom.currentBooking.to) }}</span>
            </div>
          </div>

          <router-link
            :to="`/nv/don/${selectedRoom.currentBooking.bookingCode}`"
            class="w-full mt-2 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow transition flex items-center justify-center space-x-1"
          >
            <span>Quản lý đơn này</span>
            <span>→</span>
          </router-link>
        </div>

        <!-- Empty Room: Quick booking button -->
        <div v-else-if="selectedRoom.status === 'TRONG'" class="bg-emerald-50 rounded-xl p-4 border border-emerald-100 space-y-3">
          <div class="text-xs font-semibold text-emerald-800">
            Phòng đang trống và sẵn sàng đón khách.
          </div>
          <router-link
            :to="`/nv/don/moi?roomId=${selectedRoom.roomId}&roomType=${selectedRoom.roomType}`"
            class="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow transition flex items-center justify-center space-x-1.5"
          >
            <span>Tạo đơn tại quầy cho phòng này</span>
          </router-link>
        </div>

        <!-- Room under Maintenance: End Maintenance Action (F15) -->
        <div v-else-if="selectedRoom.status === 'BAO_TRI'" class="bg-rose-50 rounded-xl p-4 border border-rose-100 space-y-3">
          <div class="text-xs font-semibold text-rose-800 flex items-center gap-1.5">
            <Wrench class="w-4 h-4 text-rose-600" />
            <span>Phòng đang trong trạng thái bảo trì kỹ thuật</span>
          </div>
          <p v-if="selectedRoom.notes" class="text-xs text-slate-600 bg-white/80 p-2.5 rounded-lg border border-rose-200/60">
            <strong class="text-rose-900">Lý do:</strong> {{ selectedRoom.notes }}
          </p>
          <button
            type="button"
            @click="handleEndMaintenance(selectedRoom)"
            :disabled="maintenanceActionLoading"
            class="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow transition flex items-center justify-center space-x-1.5 active:scale-95 disabled:opacity-50"
          >
            <RefreshCw v-if="maintenanceActionLoading" class="w-4 h-4 animate-spin" />
            <Check v-else class="w-4 h-4 stroke-[3]" />
            <span>Kết thúc bảo trì (Đưa về phòng trống)</span>
          </button>
        </div>

        <!-- Maintenance Trigger for TRONG and DANG_DON rooms (F15, BR-40, BR-41) -->
        <div v-if="['TRONG', 'DANG_DON'].includes(selectedRoom.status)" class="pt-2">
          <button
            type="button"
            @click="openMaintenanceModal(selectedRoom)"
            class="w-full py-2 bg-slate-50 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 transition flex items-center justify-center space-x-1.5"
          >
            <Wrench class="w-3.5 h-3.5 text-slate-500" />
            <span>Đưa phòng vào bảo trì...</span>
          </button>
        </div>

        <!-- Next Booking Section -->
        <div v-if="selectedRoom.nextBooking" class="bg-slate-50 rounded-xl p-4 border border-slate-100 space-y-2 text-xs">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">Lượt kế tiếp</span>
            <span class="font-mono font-bold text-slate-800">{{ selectedRoom.nextBooking.bookingCode }}</span>
          </div>
          <div class="text-slate-600">
            Dự kiến nhận: <strong class="text-slate-900">{{ formatDateTime(selectedRoom.nextBooking.from) }}</strong>
          </div>
        </div>
      </div>

      <!-- Drawer Footer -->
      <div class="pt-4 border-t border-slate-100 flex justify-end">
        <button
          @click="selectedRoom = null"
          class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition"
        >
          Đóng ngăn
        </button>
      </div>
    </div>

    <!-- MODAL BẢO TRÌ PHÒNG (BR-40, BR-41) -->
    <div
      v-if="showMaintenanceModal"
      class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-fadeIn">
        <!-- Header -->
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-rose-100 text-rose-600 flex items-center justify-center">
              <Wrench class="w-4 h-4" />
            </div>
            <div>
              <h2 class="text-sm font-bold text-slate-900">Đưa phòng {{ maintenanceRoom?.roomNumber }} vào bảo trì</h2>
              <p class="text-[11px] text-slate-500">Chuyển trạng thái phòng sang BAO_TRI (BR-40, BR-41)</p>
            </div>
          </div>
          <button @click="closeMaintenanceModal" class="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <!-- Body -->
        <div class="p-6 space-y-4 text-xs">
          <!-- Error Alert -->
          <div v-if="maintenanceError" class="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl flex items-center gap-2">
            <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{{ maintenanceError }}</span>
          </div>

          <!-- Reason Input -->
          <div>
            <label class="block font-semibold text-slate-700 mb-1">
              Lý do bảo trì <span class="text-rose-500">*</span>
            </label>
            <textarea
              v-model="maintenanceReason"
              rows="3"
              placeholder="Nhập lý do chi tiết (VD: Hỏng điều hòa, sơn tường, sửa vòi sen...)"
              class="w-full px-3 py-2 border border-slate-300 rounded-xl bg-white text-xs outline-none focus:ring-2 focus:ring-rose-500 placeholder:text-slate-400"
            ></textarea>
          </div>

          <!-- Loading Affected Bookings -->
          <div v-if="loadingAffected" class="p-3 bg-slate-50 rounded-xl text-center text-slate-400 flex items-center justify-center gap-2">
            <RefreshCw class="w-3.5 h-3.5 animate-spin text-slate-500" />
            <span>Đang kiểm tra đơn tương lai bị ảnh hưởng...</span>
          </div>

          <!-- Affected Bookings Warning (BR-41) -->
          <div v-else-if="affectedBookings.length > 0" class="p-3.5 bg-amber-50 border border-amber-200 rounded-xl space-y-3">
            <div class="flex items-center gap-2 text-amber-800 font-bold">
              <AlertTriangle class="w-4 h-4 text-amber-600 flex-shrink-0" />
              <span>Cảnh báo: Có {{ affectedBookings.length }} đơn đặt tương lai bị ảnh hưởng!</span>
            </div>
            <p class="text-slate-600 text-[11px]">
              Phòng này đã có khách đặt trong tương lai. Bạn cần xử lý chuyển phòng cùng hạng cho khách (BR-41).
            </p>
            <div class="max-h-40 overflow-y-auto border border-amber-200/80 rounded-lg bg-white divide-y divide-slate-100">
              <div v-for="b in affectedBookings" :key="b.bookingId" class="p-2.5 text-[11px] space-y-1">
                <div class="flex items-center justify-between">
                  <span class="font-mono font-bold text-slate-800">{{ b.bookingCode }}</span>
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">{{ b.status }}</span>
                </div>
                <div class="text-slate-500 flex justify-between">
                  <span>{{ formatDateTime(b.from) }} → {{ formatDateTime(b.to) }}</span>
                  <span class="font-medium text-slate-700">{{ b.customerName }} ({{ b.customerPhone }})</span>
                </div>
              </div>
            </div>

            <label class="flex items-start gap-2 pt-1 cursor-pointer">
              <input
                type="checkbox"
                v-model="confirmIgnoreAffected"
                class="mt-0.5 rounded border-slate-300 text-rose-600 focus:ring-rose-500"
              />
              <span class="text-[11px] font-semibold text-slate-800">
                Tôi xác nhận tiếp tục đưa phòng vào bảo trì (sẽ xử lý chuyển phòng cho khách sau).
              </span>
            </label>
          </div>

          <div v-else class="p-3 bg-emerald-50 border border-emerald-100 rounded-xl text-emerald-800 flex items-center gap-2">
            <CheckCircle2 class="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>Phòng không có đơn tương lai nào bị ảnh hưởng.</span>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end gap-2">
          <button
            type="button"
            @click="closeMaintenanceModal"
            class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition"
          >
            Hủy bỏ
          </button>
          <button
            type="button"
            @click="submitMaintenance"
            :disabled="maintenanceSubmitting || !maintenanceReason.trim() || (affectedBookings.length > 0 && !confirmIgnoreAffected)"
            class="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-xl text-xs shadow-sm transition disabled:opacity-50 flex items-center gap-1.5"
          >
            <RefreshCw v-if="maintenanceSubmitting" class="w-3.5 h-3.5 animate-spin" />
            <Wrench v-else class="w-3.5 h-3.5" />
            <span>Xác nhận bảo trì</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import {
  AlertCircle,
  Wrench,
  Check,
  RefreshCw,
  AlertTriangle,
  CheckCircle2
} from 'lucide-vue-next';
import apiClient from '../../api/client';
import StatusBadge from '../../components/StatusBadge.vue';
import RoomTile from '../../components/RoomTile.vue';

const boardData = ref(null);
const loading = ref(false);
const error = ref('');
const selectedRoom = ref(null);

// Maintenance State (F15)
const showMaintenanceModal = ref(false);
const maintenanceRoom = ref(null);
const maintenanceReason = ref('');
const confirmIgnoreAffected = ref(false);
const affectedBookings = ref([]);
const loadingAffected = ref(false);
const maintenanceSubmitting = ref(false);
const maintenanceActionLoading = ref(false);
const maintenanceError = ref('');

const atTimeInput = ref('');
const isCustomTime = ref(false);
const autoRefresh = ref(true);
let refreshTimer = null;

const filterStatus = ref('ALL');
const filterType = ref('ALL');

const statusOptions = [
  { key: 'ALL', label: 'Tất cả' },
  { key: 'TRONG', label: 'Trống' },
  { key: 'DANG_O', label: 'Đang ở' },
  { key: 'DANG_DON', label: 'Đang dọn' },
  { key: 'BAO_TRI', label: 'Bảo trì' }
];

const roomTypeOptions = [
  { key: 'ALL', label: 'Tất cả' },
  { key: 'STANDARD', label: 'Standard' },
  { key: 'SUPERIOR', label: 'Superior' },
  { key: 'DELUXE', label: 'Deluxe' },
  { key: 'SUITE', label: 'Suite' }
];

const stats = computed(() => boardData.value?.stats);

const formatToInputTime = (date) => {
  const pad = (n) => String(n).padStart(2, '0');
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const mins = pad(date.getMinutes());
  return `${year}-${month}-${day}T${hours}:${mins}`;
};

const formatDateTime = (iso) => {
  if (!iso) return '';
  return new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit', month: '2-digit',
    hour: '2-digit', minute: '2-digit'
  });
};

const fetchBoard = async () => {
  loading.value = true;
  error.value = '';
  try {
    const params = {};
    if (isCustomTime.value && atTimeInput.value) {
      // Build ISO with local offset
      const d = new Date(atTimeInput.value);
      params.at = d.toISOString();
    }
    const res = await apiClient.get('/rooms/board', { params });
    boardData.value = res;

    // Keep selected room fresh if opened
    if (selectedRoom.value) {
      for (const fl of res.floors || []) {
        const found = fl.rooms.find(r => r.roomId === selectedRoom.value.roomId);
        if (found) {
          selectedRoom.value = found;
          break;
        }
      }
    }
  } catch (err) {
    error.value = err.message || 'Không thể tải sơ đồ phòng';
  } finally {
    loading.value = false;
  }
};

const handleTimeChange = () => {
  isCustomTime.value = Boolean(atTimeInput.value);
  fetchBoard();
};

const resetToNow = () => {
  isCustomTime.value = false;
  atTimeInput.value = formatToInputTime(new Date());
  fetchBoard();
};

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value;
  if (autoRefresh.value) {
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
};

const startAutoRefresh = () => {
  stopAutoRefresh();
  refreshTimer = setInterval(() => {
    if (!isCustomTime.value) {
      atTimeInput.value = formatToInputTime(new Date());
    }
    fetchBoard();
  }, 30000);
};

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
};

const handleSelectRoom = (room) => {
  selectedRoom.value = room;
};

const filteredFloors = computed(() => {
  if (!boardData.value?.floors) return [];
  return boardData.value.floors.map(floorGroup => {
    const matchingRooms = floorGroup.rooms.filter(room => {
      const matchStatus = filterStatus.value === 'ALL' || room.status === filterStatus.value;
      const matchType = filterType.value === 'ALL' || room.roomType === filterType.value;
      return matchStatus && matchType;
    });
    return {
      floor: floorGroup.floor,
      rooms: matchingRooms
    };
  });
});

const openMaintenanceModal = async (room) => {
  maintenanceRoom.value = room;
  maintenanceReason.value = '';
  confirmIgnoreAffected.value = false;
  affectedBookings.value = [];
  maintenanceError.value = '';
  showMaintenanceModal.value = true;
  loadingAffected.value = true;
  try {
    const res = await apiClient.get(`/rooms/${room.roomId}/affected-bookings`);
    affectedBookings.value = res || [];
  } catch (err) {
    console.error('Lỗi kiểm tra đơn ảnh hưởng:', err);
  } finally {
    loadingAffected.value = false;
  }
};

const closeMaintenanceModal = () => {
  showMaintenanceModal.value = false;
  maintenanceRoom.value = null;
  maintenanceReason.value = '';
  affectedBookings.value = [];
  maintenanceError.value = '';
};

const submitMaintenance = async () => {
  if (!maintenanceReason.value.trim() || !maintenanceRoom.value) return;
  maintenanceSubmitting.value = true;
  maintenanceError.value = '';
  try {
    await apiClient.post(`/rooms/${maintenanceRoom.value.roomId}/maintenance`, {
      reason: maintenanceReason.value.trim(),
      ignoreAffectedBookings: confirmIgnoreAffected.value
    });
    closeMaintenanceModal();
    await fetchBoard();
  } catch (err) {
    maintenanceError.value = err.response?.data?.detail || err.message || 'Không thể đưa phòng vào bảo trì';
  } finally {
    maintenanceSubmitting.value = false;
  }
};

const handleEndMaintenance = async (room) => {
  maintenanceActionLoading.value = true;
  try {
    await apiClient.post(`/rooms/${room.roomId}/end-maintenance`);
    await fetchBoard();
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Không thể kết thúc bảo trì';
  } finally {
    maintenanceActionLoading.value = false;
  }
};

onMounted(() => {
  atTimeInput.value = formatToInputTime(new Date());
  fetchBoard();
  startAutoRefresh();
});

onUnmounted(() => {
  stopAutoRefresh();
});
</script>
