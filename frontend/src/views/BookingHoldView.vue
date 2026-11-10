<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <!-- Notice Card -->
    <div class="bg-amber-500 text-white rounded-2xl p-6 sm:p-8 text-center space-y-4 shadow-lg">
      <div class="w-14 h-14 bg-white/20 backdrop-blur-md rounded-2xl flex items-center justify-center text-3xl mx-auto">
        ⏳
      </div>
      <div>
        <span class="text-xs uppercase tracking-widest font-bold opacity-80">Trạng thái: Giữ chỗ trực tuyến (HOLD)</span>
        <h2 class="text-2xl sm:text-3xl font-extrabold mt-1">Đơn đặt phòng đang được giữ</h2>
        <p class="text-xs sm:text-sm text-amber-100 max-w-md mx-auto mt-1">
          Phòng của quý khách đã được khóa trên hệ thống. Vui lòng hoàn tất thanh toán trước khi hết giờ (BR-17).
        </p>
      </div>

      <!-- Countdown Timer Box -->
      <div class="inline-flex items-center space-x-3 bg-white text-slate-900 px-6 py-3 rounded-2xl shadow-md">
        <span class="text-xs text-slate-500 font-semibold uppercase">Thời gian còn lại:</span>
        <span class="text-2xl font-black font-mono" :class="remainingSeconds < 180 ? 'text-rose-600 animate-pulse' : 'text-sky-600'">
          {{ formatCountdown(remainingSeconds) }}
        </span>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs font-semibold">
      ⚠️ {{ errorMessage }}
    </div>

    <!-- Booking Details Card -->
    <div v-if="booking" class="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
      <div class="flex items-center justify-between border-b pb-4">
        <div>
          <span class="text-xs text-slate-400">Mã tra cứu đơn:</span>
          <p class="text-xl font-bold font-mono text-sky-600">{{ booking.booking_code }}</p>
        </div>
        <StatusBadge :status="booking.status" />
      </div>

      <div class="grid grid-cols-2 gap-4 text-xs">
        <div>
          <span class="text-slate-400 block">Hạng phòng:</span>
          <span class="font-bold text-slate-800 text-sm">{{ booking.room_type }}</span>
        </div>
        <div>
          <span class="text-slate-400 block">Số lượng khách:</span>
          <span class="font-semibold text-slate-800">{{ booking.guests }} người</span>
        </div>
        <div>
          <span class="text-slate-400 block">Thời gian nhận phòng:</span>
          <span class="font-semibold text-slate-800">{{ formatDateTime(booking.checkin) }}</span>
        </div>
        <div>
          <span class="text-slate-400 block">Thời gian trả phòng:</span>
          <span class="font-semibold text-slate-800">{{ formatDateTime(booking.checkout) }}</span>
        </div>
      </div>

      <!-- Customer email check -->
      <div class="p-4 bg-slate-50 rounded-xl text-xs text-slate-600 space-y-1">
        <span class="text-slate-400 uppercase text-[10px] font-bold block">Người đặt phòng:</span>
        <div class="font-semibold text-slate-800">{{ booking.customer?.fullName }}</div>
        <div>Email: <strong class="text-slate-700">{{ booking.customer?.email }}</strong></div>
      </div>

      <!-- Price Breakdown -->
      <div class="pt-4 border-t border-slate-100 space-y-2 text-xs">
        <div class="flex justify-between text-slate-600">
          <span>Tiền phòng:</span>
          <MoneyText :value="booking.room_amount" currency="VND" />
        </div>
        <div class="flex justify-between text-slate-600">
          <span>Thuế VAT (8%):</span>
          <MoneyText :value="booking.vat_amount" currency="VND" />
        </div>
        <div class="pt-3 border-t border-slate-100 flex justify-between items-baseline">
          <span class="font-bold text-slate-800 text-sm">Tổng thanh toán:</span>
          <div class="text-2xl font-black text-sky-600">
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
          class="w-full py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-xl shadow-md hover:shadow-lg transition disabled:opacity-50 flex items-center justify-center space-x-2"
        >
          <span>💳</span>
          <span>{{ loading ? 'Đang kết nối cổng...' : 'Chuyển đến Cổng thanh toán trực tuyến' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '../api/client';
import StatusBadge from '../components/StatusBadge.vue';
import MoneyText from '../components/MoneyText.vue';

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
      const expires = new Date(booking.value.hold_expires_at).getTime();
      const now = new Date().getTime();
      const diff = Math.max(0, Math.floor((expires - now) / 1000));
      remainingSeconds.value = diff;
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
    errorMessage.value = err.message || 'Không thể khởi tạo cổng thanh toán';
  } finally {
    loading.value = false;
  }
};

onMounted(loadBooking);
onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>
