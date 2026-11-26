<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <!-- Notice Card -->
    <div class="bg-amberbrown-500 text-white rounded-2xl p-6 sm:p-8 text-center space-y-4 shadow-lg">
      <div class="w-14 h-14 bg-white/20 backdrop-blur-md rounded-2xl flex items-center justify-center text-3xl mx-auto">
        ⏳
      </div>
      <div>
        <span class="text-xs uppercase tracking-widest font-bold opacity-80">{{ t('bookingHold.status') }}</span>
        <h2 class="font-display text-2xl sm:text-3xl font-bold mt-1">{{ t('bookingHold.title') }}</h2>
        <p class="text-xs sm:text-sm text-beige-100 max-w-md mx-auto mt-1 leading-relaxed">
          {{ t('bookingHold.subtitle') }}
        </p>
      </div>

      <!-- Countdown Timer Box (Clean, no pulsing) -->
      <div class="inline-flex items-center space-x-3 bg-white text-stone-900 px-6 py-3 rounded-2xl shadow-md">
        <span class="text-xs text-stone-500 font-semibold uppercase">{{ t('bookingHold.timeRemaining') }}</span>
        <span class="text-2xl font-black font-mono" :class="remainingSeconds < 180 ? 'text-rose-600' : 'text-amberbrown-600'">
          {{ formatCountdown(remainingSeconds) }}
        </span>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-rose-800 dark:text-rose-300 rounded-xl text-xs font-semibold flex items-center space-x-2">
      <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0" />
      <span>{{ errorMessage }}</span>
    </div>

    <!-- Booking Details Card -->
    <div v-if="booking" class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-6 sm:p-8 shadow-sm space-y-6 transition-colors">
      <div class="flex items-center justify-between border-b border-beige-200 dark:border-darkbeige-800 pb-4">
        <div>
          <span class="text-xs text-stone-400 dark:text-stone-500">{{ t('bookingHold.lookupCode') }}</span>
          <p class="text-xl font-bold font-mono text-amberbrown-600 dark:text-amberbrown-400">{{ booking.booking_code }}</p>
        </div>
        <StatusBadge :status="booking.status" />
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
        <div>
          <span class="text-stone-400 dark:text-stone-500 block">{{ t('bookingHold.roomType') }}</span>
          <span class="font-bold text-stone-800 dark:text-stone-200 text-sm">{{ getRoomTypeLabel(booking) }}</span>
        </div>
        <div>
          <span class="text-stone-400 dark:text-stone-500 block">{{ t('bookingHold.roomNumber') }}</span>
          <span class="font-bold text-amberbrown-700 dark:text-amberbrown-300 text-sm">
            {{ getRoomNumber(booking) }}
          </span>
        </div>
        <div>
          <span class="text-stone-400 dark:text-stone-500 block">{{ t('bookingHold.guestsCount') }}</span>
          <span class="font-semibold text-stone-800 dark:text-stone-200">{{ booking.guests }} {{ t('bookingHold.personUnit') }}</span>
        </div>
        <div>
          <span class="text-stone-400 dark:text-stone-500 block">{{ t('bookingHold.checkin') }}</span>
          <span class="font-semibold text-stone-800 dark:text-stone-200">{{ formatDateTime(booking.checkin) }}</span>
        </div>
        <div>
          <span class="text-stone-400 dark:text-stone-500 block">{{ t('bookingHold.checkout') }}</span>
          <span class="font-semibold text-stone-800 dark:text-stone-200">{{ formatDateTime(booking.checkout) }}</span>
        </div>
      </div>

      <!-- Customer info block -->
      <div class="p-4 bg-beige-50/70 dark:bg-darkbeige-900 rounded-xl text-xs text-stone-600 dark:text-stone-300 space-y-1 border border-beige-200 dark:border-darkbeige-800">
        <span class="text-stone-400 dark:text-stone-500 uppercase text-[10px] font-bold block">{{ t('bookingHold.customer') }}</span>
        <div class="font-semibold text-stone-800 dark:text-stone-200">{{ booking.customer?.fullName }}</div>
        <div>Email: <strong class="text-stone-700 dark:text-stone-300">{{ booking.customer?.email }}</strong></div>
      </div>

      <!-- Price Breakdown -->
      <div class="pt-4 border-t border-beige-200 dark:border-darkbeige-800 space-y-2 text-xs">
        <div class="flex justify-between text-stone-600 dark:text-stone-400">
          <span>{{ t('bookingHold.roomAmount') }}</span>
          <MoneyText :value="booking.room_amount" currency="VND" />
        </div>
        <div class="flex justify-between text-stone-600 dark:text-stone-400">
          <span>{{ t('bookingHold.vat') }}</span>
          <MoneyText :value="booking.vat_amount" currency="VND" />
        </div>
        <div class="pt-3 border-t border-beige-200 dark:border-darkbeige-800 flex justify-between items-baseline">
          <span class="font-bold text-stone-800 dark:text-stone-200 text-sm">{{ t('bookingHold.totalAmount') }}</span>
          <div class="text-2xl font-black text-amberbrown-600 dark:text-amberbrown-400">
            <MoneyText :value="booking.total_amount" currency="VND" />
          </div>
        </div>
      </div>

      <!-- CTA Payment Button -->
      <div class="pt-2">
        <button
          type="button"
          :disabled="loading || remainingSeconds <= 0"
          @click="proceedToPayment"
          class="w-full py-4 bg-amberbrown-500 hover:bg-amberbrown-600 text-white font-semibold text-sm rounded-xl shadow-md transition disabled:opacity-50 flex items-center justify-center space-x-2"
        >
          <CreditCard class="w-4 h-4" />
          <span>{{ loading ? t('bookingHold.connecting') : t('bookingHold.payBtn') }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { AlertCircle, CreditCard } from 'lucide-vue-next';
import apiClient from '../api/client';
import StatusBadge from '../components/StatusBadge.vue';
import MoneyText from '../components/MoneyText.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const booking = ref(null);
const remainingSeconds = ref(900);
const loading = ref(false);
const errorMessage = ref('');
let timer = null;

const formatDateTime = (iso) => {
  if (!iso) return '';
  return new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
};

const getRoomTypeLabel = (b) => {
  if (!b) return '';
  const code = b.room_type || b.segments?.[0]?.roomType || '';
  switch (code) {
    case 'STANDARD': return 'Standard';
    case 'SUPERIOR': return 'Superior';
    case 'DELUXE': return 'Deluxe';
    case 'SUITE': return 'Suite';
    default: return code || t('myTrips.roomFallback');
  }
};

const getRoomNumber = (b) => {
  if (!b) return t('bookingHold.pendingRoom');
  const seg = b.segments?.[0];
  if (seg?.roomNumber) {
    return `${t('myTrips.roomPrefix')} ${seg.roomNumber}` + (seg.floor ? ` (Tầng ${seg.floor})` : '');
  }
  return b.room_number ? `${t('myTrips.roomPrefix')} ${b.room_number}` : t('bookingHold.pendingRoom');
};

const formatCountdown = (secs) => {
  if (secs <= 0) return '00:00';
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

const loadBooking = async () => {
  try {
    const res = await apiClient.get(`/bookings/${route.params.code}`);
    booking.value = res;

    if (booking.value.hold_expires_at) {
      let str = String(booking.value.hold_expires_at).trim();
      if (!str.endsWith('Z') && !str.includes('+')) {
        str += 'Z';
      }
      const expires = new Date(str).getTime();
      const now = new Date().getTime();
      const diff = Math.floor((expires - now) / 1000);
      remainingSeconds.value = Math.max(0, diff);
    }

    timer = setInterval(() => {
      if (remainingSeconds.value > 0) {
        remainingSeconds.value--;
      } else {
        clearInterval(timer);
      }
    }, 1000);
  } catch (err) {
    console.error('Failed to load booking:', err);
  }
};

const proceedToPayment = async () => {
  if (!booking.value) return;
  loading.value = true;
  errorMessage.value = '';

  try {
    const res = await apiClient.post('/payments/online', {
      bookingCode: booking.value.booking_code,
      email: booking.value.customer.email,
      returnUrl: '/thanh-toan/ket-qua'
    });
    const url = res.paymentUrl || res.payment_url;
    router.push(url);
  } catch (err) {
    errorMessage.value = err.message || t('errors.INTERNAL_SERVER_ERROR');
  } finally {
    loading.value = false;
  }
};

onMounted(loadBooking);
onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>
