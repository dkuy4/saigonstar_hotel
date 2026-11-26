<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-beige-300 dark:border-darkbeige-800">
      <div>
        <h1 class="font-display font-bold text-2xl text-stone-900 dark:text-white tracking-tight">{{ t('myTrips.title') }}</h1>
        <p class="text-xs text-stone-500 dark:text-stone-400 mt-1">{{ t('myTrips.subtitle') }}</p>
      </div>

      <div class="flex items-center space-x-3">
        <router-link
          to="/"
          class="px-4 py-2 bg-amberbrown-500 hover:bg-amberbrown-600 text-white text-xs font-semibold rounded-xl shadow-sm transition flex items-center space-x-1.5"
        >
          <Plus class="w-3.5 h-3.5" />
          <span>{{ t('myTrips.bookMore') }}</span>
        </router-link>
        <button
          @click="fetchBookings"
          :disabled="loading"
          class="p-2 border border-beige-300 dark:border-darkbeige-700 hover:bg-beige-200/60 dark:hover:bg-darkbeige-800 text-stone-600 dark:text-stone-300 rounded-xl transition"
          :title="t('myTrips.refresh')"
        >
          <RotateCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="py-16 text-center text-stone-400">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-amberbrown-500 border-t-transparent mx-auto mb-3"></div>
      <p class="text-xs">{{ t('myTrips.loading') }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-rose-700 dark:text-rose-300 rounded-2xl text-xs flex items-center space-x-3">
      <AlertCircle class="w-5 h-5 flex-shrink-0" />
      <span>{{ error }}</span>
    </div>

    <!-- Empty State -->
    <div v-else-if="bookings.length === 0" class="py-16 text-center bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-8 space-y-3">
      <div class="w-12 h-12 rounded-2xl bg-beige-100 dark:bg-darkbeige-800 text-stone-400 mx-auto flex items-center justify-center border border-beige-200 dark:border-darkbeige-700">
        <CalendarX2 class="w-6 h-6" />
      </div>
      <h3 class="font-display font-semibold text-base text-stone-900 dark:text-white">{{ t('myTrips.emptyTitle') }}</h3>
      <p class="text-xs text-stone-500 dark:text-stone-400 max-w-sm mx-auto leading-relaxed">
        {{ t('myTrips.emptySubtitle') }}
      </p>
      <div class="pt-2">
        <router-link
          to="/"
          class="inline-block px-4 py-2 bg-amberbrown-500 hover:bg-amberbrown-600 text-white text-xs font-semibold rounded-xl transition shadow-sm"
        >
          {{ t('myTrips.searchNow') }}
        </router-link>
      </div>
    </div>

    <!-- Bookings List -->
    <div v-else class="space-y-4">
      <div
        v-for="b in bookings"
        :key="b.dat_phong_id"
        class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 overflow-hidden shadow-sm hover:border-amberbrown-500/40 transition"
      >
        <div class="p-5 sm:p-6 space-y-4">
          <!-- Top Row: Code & Status Badge (Clean, No decorative dots) -->
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center space-x-3">
              <span class="text-xs font-mono font-bold text-stone-900 dark:text-stone-100 bg-beige-200/70 dark:bg-darkbeige-800 px-2.5 py-1 rounded-lg border border-beige-300 dark:border-darkbeige-700">
                {{ b.ma_tra_cuu }}
              </span>
              <span class="text-xs font-medium text-stone-500 dark:text-stone-400">
                {{ formatDateTime(b.ngay_tao) }}
              </span>
            </div>

            <!-- Natural Friendly Status Badge - Dot Removed per unslop & user request -->
            <span
              class="px-3 py-1 rounded-full text-xs font-semibold inline-flex items-center"
              :class="getStatusStyle(b.trang_thai)"
            >
              {{ getStatusLabel(b.trang_thai) }}
            </span>
          </div>

          <!-- Middle Row: Stay Details & Room Info -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-beige-200 dark:border-darkbeige-800">
            <div>
              <p class="text-[11px] font-medium text-stone-400 dark:text-stone-500">{{ t('myTrips.roomAndNumber') }}</p>
              <p class="text-xs font-semibold text-stone-800 dark:text-stone-200 mt-0.5">
                {{ b.ten_hang || b.ma_hang || t('myTrips.roomFallback') }}
                <span v-if="b.so_phong" class="ml-1 text-amberbrown-700 dark:text-amberbrown-300 font-bold bg-amberbrown-50 dark:bg-darkbeige-800 px-1.5 py-0.5 rounded text-[10px]">
                  {{ t('myTrips.roomPrefix') }} {{ b.so_phong }}
                </span>
                <span v-else class="text-stone-400 dark:text-stone-500 font-normal text-[11px] ml-1">{{ t('myTrips.waitingRoom') }}</span>
              </p>
            </div>

            <div>
              <p class="text-[11px] font-medium text-stone-400 dark:text-stone-500">{{ t('myTrips.stayDuration') }}</p>
              <p class="text-xs font-medium text-stone-800 dark:text-stone-200 mt-0.5">
                {{ formatDateTime(b.tu_luc) }} - {{ formatDateTime(b.den_luc) }}
              </p>
            </div>

            <div>
              <p class="text-[11px] font-medium text-stone-400 dark:text-stone-500">{{ t('myTrips.totalPayment') }}</p>
              <p class="text-sm font-bold text-stone-900 dark:text-white mt-0.5">
                {{ formatVND(b.tong_tien) }}
              </p>
            </div>
          </div>

          <!-- Actions Row -->
          <div class="pt-3 border-t border-beige-200 dark:border-darkbeige-800 flex flex-wrap items-center justify-between gap-3">
            <p class="text-[11px] text-stone-500 dark:text-stone-400">
              {{ t('bookingDetail.guests') }}: <strong class="text-stone-700 dark:text-stone-200 font-medium">{{ b.so_khach }}</strong>
            </p>

            <div class="flex items-center space-x-2">
              <!-- Payment Action if HOLD -->
              <router-link
                v-if="b.trang_thai === 'HOLD'"
                :to="`/giu-cho/${b.ma_tra_cuu}`"
                class="px-3.5 py-1.5 bg-amberbrown-500 hover:bg-amberbrown-600 text-white text-xs font-medium rounded-xl transition shadow-sm"
              >
                {{ t('myTrips.payNow') }}
              </router-link>

              <!-- View details / Lookup -->
              <router-link
                :to="`/don/${b.ma_tra_cuu}`"
                class="px-3.5 py-1.5 bg-beige-200/70 hover:bg-beige-300 dark:bg-darkbeige-800 dark:hover:bg-darkbeige-700 text-stone-800 dark:text-stone-200 text-xs font-medium rounded-xl transition"
              >
                {{ t('myTrips.viewDetail') }}
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
import { useI18n } from 'vue-i18n';
import { Plus, RotateCw, CalendarX2, AlertCircle } from 'lucide-vue-next';
import apiClient from '../../api/client';
import { useGuestAuthStore } from '../../stores/guestAuth';

const { t, te } = useI18n();
const guestAuth = useGuestAuthStore();

const bookings = ref([]);
const loading = ref(false);
const error = ref('');

const fetchBookings = async () => {
  const token = guestAuth.token || localStorage.getItem('guest_token');
  if (!token) {
    error.value = t('myTrips.authRequired');
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
    error.value = err.detail || err.message || t('myTrips.errorLoad');
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
    case 'HOLD': return t('myTrips.statusHold');
    case 'CONFIRMED': return t('myTrips.statusConfirmed');
    case 'CHECKED_IN': return t('myTrips.statusCheckedIn');
    case 'CHECKED_OUT': return t('myTrips.statusCheckedOut');
    case 'CANCELLED': return t('myTrips.statusCancelled');
    case 'NO_SHOW': return t('myTrips.statusNoShow');
    case 'EXPIRED': return t('myTrips.statusExpired');
    default:
      return te(`status.${st}`) ? t(`status.${st}`) : st;
  }
};

const getStatusStyle = (st) => {
  switch (st) {
    case 'HOLD':
      return 'bg-amber-100 text-amber-800 border border-amber-300 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800';
    case 'CONFIRMED':
      return 'bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-200 dark:border-emerald-800';
    case 'CHECKED_IN':
      return 'bg-teal-100 text-teal-800 border border-teal-300 dark:bg-teal-950/40 dark:text-teal-200 dark:border-teal-800';
    case 'CHECKED_OUT':
      return 'bg-stone-100 text-stone-700 border border-stone-300 dark:bg-darkbeige-800 dark:text-stone-300 dark:border-darkbeige-700';
    case 'CANCELLED':
      return 'bg-rose-100 text-rose-800 border border-rose-300 dark:bg-rose-950/40 dark:text-rose-200 dark:border-rose-800';
    default:
      return 'bg-stone-100 text-stone-600 border border-stone-300 dark:bg-darkbeige-800 dark:text-stone-400 dark:border-darkbeige-700';
  }
};

onMounted(() => {
  fetchBookings();
});
</script>
