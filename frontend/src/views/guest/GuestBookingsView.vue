<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <h1 class="text-xl font-semibold text-slate-900 tracking-tight">Chuyến đi của quý khách</h1>
        <p class="text-xs text-slate-500 mt-1">Danh sách phòng đã đặt và lịch sử lưu trú tại Khách sạn Sài Gòn Star</p>
      </div>

      <div class="flex items-center space-x-3">
        <router-link
          to="/"
          class="px-3.5 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-medium rounded-xl shadow-sm transition flex items-center space-x-1.5"
        >
          <Plus class="w-3.5 h-3.5" />
          <span>Đặt thêm phòng</span>
        </router-link>
        <button
          @click="fetchBookings"
          :disabled="loading"
          class="p-2 border border-slate-200 hover:bg-slate-100 text-slate-600 rounded-xl transition"
          title="Làm mới danh sách"
        >
          <RotateCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="py-16 text-center text-slate-400">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-sky-600 border-t-transparent mx-auto mb-3"></div>
      <p class="text-xs">Đang tải thông tin chuyến đi...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-2xl text-xs flex items-center space-x-3">
      <AlertCircle class="w-5 h-5 flex-shrink-0" />
      <span>{{ error }}</span>
    </div>

    <!-- Empty State -->
    <div v-else-if="bookings.length === 0" class="py-16 text-center bg-white rounded-2xl border border-slate-200/80 p-8 space-y-3">
      <div class="w-12 h-12 rounded-2xl bg-slate-50 text-slate-400 mx-auto flex items-center justify-center border border-slate-100">
        <CalendarX2 class="w-6 h-6" />
      </div>
      <h3 class="text-sm font-semibold text-slate-800">Quý khách chưa có chuyến đi nào</h3>
      <p class="text-xs text-slate-500 max-w-sm mx-auto">
        Khám phá các hạng phòng sang trọng tại Sài Gòn Star và tận hưởng kỳ nghỉ trọn vẹn ngay hôm nay.
      </p>
      <div class="pt-2">
        <router-link
          to="/"
          class="inline-block px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-medium rounded-xl transition shadow-sm"
        >
          Tìm kiếm phòng ngay
        </router-link>
      </div>
    </div>

    <!-- Bookings List -->
    <div v-else class="space-y-4">
      <div
        v-for="b in bookings"
        :key="b.dat_phong_id"
        class="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-sm hover:border-slate-300 transition"
      >
        <div class="p-5 sm:p-6 space-y-4">
          <!-- Top Row: Code & Status Badge -->
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center space-x-3">
              <span class="text-xs font-mono font-bold text-slate-900 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200">
                {{ b.ma_tra_cuu }}
              </span>
              <span class="text-xs font-medium text-slate-500">
                {{ formatDateTime(b.ngay_tao) }}
              </span>
            </div>

            <!-- Natural Friendly Status Badge -->
            <span
              class="px-3 py-1 rounded-full text-xs font-semibold inline-flex items-center space-x-1.5"
              :class="getStatusStyle(b.trang_thai)"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
              <span>{{ getStatusLabel(b.trang_thai) }}</span>
            </span>
          </div>

          <!-- Middle Row: Stay Details & Room Info -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-slate-100">
            <div>
              <p class="text-[11px] font-medium text-slate-400">Hạng phòng & Số phòng</p>
              <p class="text-xs font-semibold text-slate-800 mt-0.5">
                {{ b.ten_hang || b.ma_hang || 'Phòng nghỉ' }}
                <span v-if="b.so_phong" class="ml-1 text-sky-700 font-bold bg-sky-50 px-1.5 py-0.5 rounded text-[10px]">
                  Phòng {{ b.so_phong }}
                </span>
                <span v-else class="text-slate-400 font-normal text-[11px] ml-1">(Chờ xếp phòng)</span>
              </p>
            </div>

            <div>
              <p class="text-[11px] font-medium text-slate-400">Thời gian lưu trú</p>
              <p class="text-xs font-medium text-slate-800 mt-0.5">
                {{ formatDateTime(b.tu_luc) }} → {{ formatDateTime(b.den_luc) }}
              </p>
            </div>

            <div>
              <p class="text-[11px] font-medium text-slate-400">Tổng tiền thanh toán</p>
              <p class="text-sm font-bold text-slate-900 mt-0.5">
                {{ formatVND(b.tong_tien) }}
              </p>
            </div>
          </div>

          <!-- Actions Row -->
          <div class="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <p class="text-[11px] text-slate-400">
              Số khách lưu trú: <strong class="text-slate-700 font-medium">{{ b.so_khach }} người</strong>
            </p>

            <div class="flex items-center space-x-2">
              <!-- Payment Action if HOLD -->
              <router-link
                v-if="b.trang_thai === 'HOLD'"
                :to="`/giu-cho/${b.ma_tra_cuu}`"
                class="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium rounded-lg transition shadow-sm"
              >
                Thanh toán ngay
              </router-link>

              <!-- View details / Lookup -->
              <router-link
                :to="`/don/${b.ma_tra_cuu}`"
                class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-medium rounded-lg transition"
              >
                Xem chi tiết & Hủy phòng
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Plus, RotateCw, CalendarX2, AlertCircle } from 'lucide-vue-next';
import apiClient from '../../api/client';
import { useGuestAuthStore } from '../../stores/guestAuth';

const guestAuth = useGuestAuthStore();

const bookings = ref([]);
const loading = ref(false);
const error = ref('');

const fetchBookings = async () => {
  const token = guestAuth.token || localStorage.getItem('guest_token');
  if (!token) {
    error.value = 'Phiên đăng nhập đã hết hạn. Quý khách vui lòng đăng nhập lại để xem chuyến đi.';
    return;
  }
  loading.value = true;
  error.value = '';
  try {
    const res = await apiClient.get('/guest/my-bookings', {
      headers: { Authorization: `Bearer ${token}` }
    });
    bookings.value = Array.isArray(res) ? res : (res?.data || []);
  } catch (err) {
    error.value = err.detail || err.message || 'Không thể tải danh sách chuyến đi. Xin quý khách vui lòng thử lại.';
  } finally {
    loading.value = false;
  }
};

const formatVND = (num) => {
  if (num == null) return '0 đ';
  return new Intl.NumberFormat('vi-VN').format(Math.round(num)) + ' đ';
};

const formatDateTime = (isoStr) => {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getStatusLabel = (st) => {
  switch (st) {
    case 'HOLD': return 'Đang giữ phòng 15 phút';
    case 'CONFIRMED': return 'Đã xác nhận thành công';
    case 'CHECKED_IN': return 'Đang lưu trú tại khách sạn';
    case 'CHECKED_OUT': return 'Đã hoàn tất trả phòng';
    case 'CANCELLED': return 'Đã hủy chuyến đi';
    case 'NO_SHOW': return 'Không đến nhận phòng';
    case 'EXPIRED': return 'Đã hết hạn giữ phòng';
    default: return st;
  }
};

const getStatusStyle = (st) => {
  switch (st) {
    case 'HOLD':
      return 'bg-amber-50 text-amber-800 border border-amber-200';
    case 'CONFIRMED':
      return 'bg-sky-50 text-sky-800 border border-sky-200';
    case 'CHECKED_IN':
      return 'bg-emerald-50 text-emerald-800 border border-emerald-200';
    case 'CHECKED_OUT':
      return 'bg-slate-100 text-slate-700 border border-slate-200';
    case 'CANCELLED':
      return 'bg-rose-50 text-rose-800 border border-rose-200';
    default:
      return 'bg-slate-50 text-slate-600 border border-slate-200';
  }
};

onMounted(() => {
  fetchBookings();
});
</script>
