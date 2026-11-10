<template>
  <div class="max-w-4xl mx-auto space-y-6 py-6 px-4">
    <!-- Lookup Form Header / Card -->
    <div v-if="!booking || isLookupRoute" class="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
      <div class="text-center max-w-lg mx-auto space-y-1">
        <div class="w-12 h-12 bg-sky-100 text-sky-600 rounded-full flex items-center justify-center mx-auto mb-2">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-slate-900">Tra cứu đơn đặt phòng</h2>
        <p class="text-xs text-slate-500">Vui lòng cung cấp mã đơn (ví dụ: DP0006053) và email đăng ký để bảo mật thông tin lưu trú</p>
      </div>

      <form @submit.prevent="handleLookup" class="max-w-md mx-auto space-y-3 pt-2">
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Mã đơn đặt phòng</label>
          <input
            v-model="lookupCode"
            type="text"
            required
            placeholder="DP0000001"
            class="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-sm font-mono uppercase focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Email đăng ký đặt phòng</label>
          <input
            v-model="lookupEmail"
            type="email"
            required
            placeholder="guest@example.com"
            class="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
          />
        </div>

        <button
          type="submit"
          :disabled="loadingLookup"
          class="w-full py-3 bg-sky-600 hover:bg-sky-700 text-white font-semibold text-sm rounded-xl shadow transition flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          <div v-if="loadingLookup" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
          <span>{{ loadingLookup ? 'Đang kiểm tra...' : 'Tra cứu đơn' }}</span>
        </button>
      </form>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm flex items-center space-x-3">
      <span class="text-lg">⚠️</span>
      <span class="text-xs font-medium">{{ errorMessage }}</span>
    </div>

    <!-- Success Message Alert -->
    <div v-if="successMessage" class="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="text-lg">✅</span>
        <span class="text-xs font-medium">{{ successMessage }}</span>
      </div>
      <button @click="successMessage = ''" class="text-emerald-600 hover:text-emerald-800 text-xs font-bold">Đóng</button>
    </div>

    <!-- Booking Details Card -->
    <div v-if="booking" class="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
      <!-- Card Header -->
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <span class="text-xs uppercase tracking-wide font-semibold text-slate-400">Mã đơn đặt phòng</span>
          <h3 class="text-3xl font-black font-mono text-slate-900 mt-0.5">{{ booking.booking_code }}</h3>
          <p class="text-xs text-slate-500 mt-0.5">Đặt qua kênh: <strong class="text-slate-700">{{ booking.channel }}</strong></p>
        </div>
        <div class="flex items-center space-x-3">
          <StatusBadge :status="booking.status" />
        </div>
      </div>

      <!-- Action Banners -->
      <div v-if="booking.status === 'HOLD'" class="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between">
        <div class="text-xs text-amber-800">
          <span class="font-bold">Đơn đang trong thời hạn giữ chỗ 15 phút.</span>
          Vui lòng thanh toán để xác nhận phòng.
        </div>
        <router-link
          :to="`/giu-cho/${booking.booking_code}`"
          class="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold shadow"
        >
          Thanh toán ngay
        </router-link>
      </div>

      <!-- Guest and Stay Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
        <!-- Guest Box -->
        <div class="bg-slate-50 rounded-xl p-5 space-y-2 border border-slate-100">
          <span class="font-bold text-slate-700 block uppercase text-[10px] tracking-wider border-b border-slate-200 pb-1.5">
            Thông tin người đặt
          </span>
          <div class="text-sm font-semibold text-slate-900">{{ booking.customer?.fullName }}</div>
          <div class="text-slate-600">SĐT: <span class="font-medium text-slate-800">{{ booking.customer?.phone }}</span></div>
          <div class="text-slate-600">Email: <span class="font-medium text-slate-800">{{ booking.customer?.email }}</span></div>
          <div class="text-slate-600">Quốc tịch: <span class="font-medium text-slate-800">{{ booking.customer?.nationality }}</span></div>
        </div>

        <!-- Stay Details Box -->
        <div class="bg-slate-50 rounded-xl p-5 space-y-2 border border-slate-100">
          <span class="font-bold text-slate-700 block uppercase text-[10px] tracking-wider border-b border-slate-200 pb-1.5">
            Thông tin lưu trú
          </span>
          <div class="text-sm font-bold text-sky-600">Hạng {{ booking.room_type }}</div>
          <div class="text-slate-600">Số khách: <span class="font-medium text-slate-800">{{ booking.guests }} người</span></div>
          <div class="text-slate-600">Nhận phòng: <strong class="text-slate-900">{{ formatDateTime(booking.checkin) }}</strong></div>
          <div class="text-slate-600">Trả phòng: <strong class="text-slate-900">{{ formatDateTime(booking.checkout) }}</strong></div>
        </div>
      </div>

      <!-- Financial Breakdown (BR-59) -->
      <div class="pt-4 border-t border-slate-200 space-y-2.5 text-xs">
        <div class="flex justify-between text-slate-600">
          <span>Tiền phòng niêm yết:</span>
          <MoneyText :amount="booking.room_amount" />
        </div>
        <div class="flex justify-between text-slate-600">
          <span>Thuế VAT ({{ (booking.vat_rate * 100).toFixed(0) }}%):</span>
          <MoneyText :amount="booking.vat_amount" />
        </div>
        <div class="pt-3 border-t border-slate-100 flex justify-between items-baseline">
          <div>
            <span class="font-bold text-slate-800 text-sm">Tổng thanh toán:</span>
            <span class="text-[10px] text-slate-400 block">Đã gồm thuế VAT & phí dịch vụ (BR-59)</span>
          </div>
          <div class="text-2xl font-black text-sky-600">
            <MoneyText :amount="booking.total_amount" />
          </div>
        </div>
      </div>

      <!-- Policy Reminder (BR-24) -->
      <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 text-xs text-blue-900 space-y-1">
        <div class="font-bold uppercase text-[10px] tracking-wider text-blue-700">Chính sách hủy & đổi phòng (BR-24, BR-27)</div>
        <p class="text-blue-800 leading-relaxed">
          Quý khách được hoàn tiền 100% nếu hủy trước 24 giờ so với thời điểm nhận phòng. Hủy dưới 24 giờ không hoàn tiền.
          Đổi ngày lưu trú cùng hạng phòng được giữ nguyên đơn giá đã chốt.
        </p>
      </div>

      <!-- Action Buttons for CONFIRMED Booking -->
      <div v-if="booking.status === 'CONFIRMED'" class="pt-4 border-t border-slate-200 flex flex-wrap gap-3 justify-end">
        <button
          @click="openRescheduleModal"
          class="px-5 py-2.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold rounded-xl text-xs transition border border-indigo-200 flex items-center space-x-1.5"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>Đổi ngày / giờ lưu trú</span>
        </button>

        <button
          @click="openCancelModal"
          class="px-5 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold rounded-xl text-xs transition border border-rose-200 flex items-center space-x-1.5"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <span>Hủy đơn đặt phòng</span>
        </button>
      </div>
    </div>

    <!-- CANCEL MODAL (FR-09, BR-24) -->
    <div v-if="showCancelModal" class="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl animate-fade-in">
        <div class="flex items-center justify-between border-b pb-3">
          <h3 class="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <span class="text-rose-600">⚠️</span>
            <span>Xác nhận hủy đơn đặt phòng</span>
          </h3>
          <button @click="showCancelModal = false" class="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <div v-if="loadingPreview" class="py-8 text-center text-slate-500 text-xs">
          <div class="animate-spin rounded-full h-6 w-6 border-2 border-sky-600 border-t-transparent mx-auto mb-2"></div>
          Đang tính toán chính sách hoàn tiền...
        </div>

        <div v-else-if="refundPreview" class="space-y-4 text-xs">
          <!-- Refund Preview Box -->
          <div :class="refundPreview.isEligible ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-amber-50 border-amber-200 text-amber-900'" class="p-4 rounded-xl border space-y-2">
            <div class="font-bold text-sm flex justify-between items-center">
              <span>Số tiền hoàn dự kiến:</span>
              <span class="text-lg font-black font-mono">
                <MoneyText :amount="refundPreview.expectedRefund" />
              </span>
            </div>
            <div class="text-[11px] leading-relaxed">{{ refundPreview.reason }}</div>
            <div class="text-[11px] text-slate-500">
              Tổng tiền đã thanh toán: <strong class="text-slate-700"><MoneyText :amount="refundPreview.paidAmount" /></strong>
            </div>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Lý do hủy phòng (tùy chọn)</label>
            <textarea
              v-model="cancelReason"
              rows="3"
              placeholder="Thay đổi lịch trình, bận việc đột xuất..."
              class="w-full p-2.5 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500"
            ></textarea>
          </div>

          <div class="flex justify-end space-x-2 pt-2 border-t">
            <button
              @click="showCancelModal = false"
              class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-medium"
            >
              Giữ lại đơn
            </button>
            <button
              @click="confirmCancelBooking"
              :disabled="cancelling"
              class="px-5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-semibold shadow disabled:opacity-50 flex items-center space-x-1"
            >
              <div v-if="cancelling" class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
              <span>Xác nhận hủy</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- RESCHEDULE MODAL (FR-09, BR-15, D-29) -->
    <div v-if="showRescheduleModal" class="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl animate-fade-in">
        <div class="flex items-center justify-between border-b pb-3">
          <h3 class="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <span class="text-indigo-600">📅</span>
            <span>Đổi lịch / Hạng phòng</span>
          </h3>
          <button @click="showRescheduleModal = false" class="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <form @submit.prevent="confirmRescheduleBooking" class="space-y-4 text-xs">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Ngày nhận phòng mới</label>
              <input
                v-model="rescheduleCheckinDate"
                type="date"
                required
                class="w-full p-2.5 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Ngày trả phòng mới</label>
              <input
                v-model="rescheduleCheckoutDate"
                type="date"
                required
                class="w-full p-2.5 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Hạng phòng</label>
            <select
              v-model="rescheduleRoomType"
              class="w-full p-2.5 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500 bg-white"
            >
              <option value="STANDARD">Standard (Phổ thông)</option>
              <option value="SUPERIOR">Superior (Cao cấp)</option>
              <option value="DELUXE">Deluxe (Sang trọng)</option>
              <option value="SUITE">Suite (Tổng thống)</option>
            </select>
            <p class="text-[11px] text-slate-400 mt-1">
              Đổi cùng hạng giữ nguyên đơn giá cũ (D-29). Đổi sang hạng khác tính theo giá hiện hành.
            </p>
          </div>

          <div v-if="rescheduleError" class="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs">
            {{ rescheduleError }}
          </div>

          <div class="flex justify-end space-x-2 pt-3 border-t">
            <button
              type="button"
              @click="showRescheduleModal = false"
              class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-medium"
            >
              Đóng
            </button>
            <button
              type="submit"
              :disabled="rescheduling"
              class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold shadow disabled:opacity-50 flex items-center space-x-1"
            >
              <div v-if="rescheduling" class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
              <span>Xác nhận đổi lịch</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '../api/client';
import StatusBadge from '../components/StatusBadge.vue';
import MoneyText from '../components/MoneyText.vue';

const route = useRoute();
const router = useRouter();

const booking = ref(null);
const lookupCode = ref('');
const lookupEmail = ref('');
const loadingLookup = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

// Modals
const showCancelModal = ref(false);
const loadingPreview = ref(false);
const refundPreview = ref(null);
const cancelReason = ref('');
const cancelling = ref(false);

const showRescheduleModal = ref(false);
const rescheduleCheckinDate = ref('');
const rescheduleCheckoutDate = ref('');
const rescheduleRoomType = ref('STANDARD');
const rescheduling = ref(false);
const rescheduleError = ref('');

const isLookupRoute = computed(() => route.path === '/don/tra-cuu');
const routeCode = computed(() => route.params.code || '');

const formatDateTime = (iso) => {
  if (!iso) return '';
  return new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
};

const handleLookup = async () => {
  if (!lookupCode.value || !lookupEmail.value) return;
  loadingLookup.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    const res = await apiClient.post('/bookings/lookup', {
      bookingCode: lookupCode.value.trim().toUpperCase(),
      email: lookupEmail.value.trim()
    });

    sessionStorage.setItem('booking_token', res.token);
    sessionStorage.setItem('booking_code', res.booking.booking_code);
    sessionStorage.setItem('booking_email', lookupEmail.value.trim());

    booking.value = res.booking;
    if (route.params.code !== res.booking.booking_code) {
      router.push(`/don/${res.booking.booking_code}`);
    }
  } catch (err) {
    errorMessage.value = err.message || 'Mã đặt phòng hoặc email không chính xác';
    booking.value = null;
  } finally {
    loadingLookup.value = false;
  }
};

const fetchBookingPublic = async (code) => {
  if (!code) return;
  errorMessage.value = '';
  try {
    const res = await apiClient.get(`/bookings/${code}`);
    booking.value = res;
    lookupCode.value = res.booking_code;
    if (res.customer?.email) {
      lookupEmail.value = res.customer.email;
    }
  } catch (err) {
    errorMessage.value = err.message || 'Không tìm thấy thông tin đơn phòng';
    booking.value = null;
  }
};

const openCancelModal = async () => {
  if (!booking.value) return;
  showCancelModal.value = true;
  loadingPreview.value = true;
  refundPreview.value = null;
  cancelReason.value = '';

  try {
    const preview = await apiClient.get(`/bookings/${booking.value.booking_code}/refund-preview`);
    refundPreview.value = preview;
  } catch (err) {
    alert(err.message || 'Không thể tính toán số tiền hoàn');
    showCancelModal.value = false;
  } finally {
    loadingPreview.value = false;
  }
};

const confirmCancelBooking = async () => {
  if (!booking.value || cancelling.value) return;
  cancelling.value = true;
  try {
    const res = await apiClient.post(`/bookings/${booking.value.booking_code}/cancel`, {
      reason: cancelReason.value || 'Khách hủy trên website'
    });
    showCancelModal.value = false;
    successMessage.value = res.message || 'Hủy đơn đặt phòng thành công';
    await fetchBookingPublic(booking.value.booking_code);
  } catch (err) {
    alert(err.message || 'Hủy đơn thất bại');
  } finally {
    cancelling.value = false;
  }
};

const openRescheduleModal = () => {
  if (!booking.value) return;
  rescheduleRoomType.value = booking.value.room_type || 'STANDARD';
  rescheduleError.value = '';

  // Default to current dates in YYYY-MM-DD
  if (booking.value.checkin) {
    const d = new Date(booking.value.checkin);
    rescheduleCheckinDate.value = d.toISOString().split('T')[0];
  }
  if (booking.value.checkout) {
    const d = new Date(booking.value.checkout);
    rescheduleCheckoutDate.value = d.toISOString().split('T')[0];
  }
  showRescheduleModal.value = true;
};

const confirmRescheduleBooking = async () => {
  if (!booking.value || rescheduling.value) return;
  rescheduling.value = true;
  rescheduleError.value = '';

  const checkinIso = `${rescheduleCheckinDate.value}T14:00:00+07:00`;
  const checkoutIso = `${rescheduleCheckoutDate.value}T12:00:00+07:00`;

  try {
    const res = await apiClient.put(`/bookings/${booking.value.booking_code}`, {
      nhanLuc: checkinIso,
      traLuc: checkoutIso,
      maHang: rescheduleRoomType.value
    });
    showRescheduleModal.value = false;
    successMessage.value = res.message || 'Đổi ngày thành công';
    await fetchBookingPublic(booking.value.booking_code);
  } catch (err) {
    rescheduleError.value = err.message || 'Đổi ngày lưu trú thất bại';
  } finally {
    rescheduling.value = false;
  }
};

onMounted(() => {
  const savedToken = sessionStorage.getItem('booking_token');
  const savedCode = sessionStorage.getItem('booking_code');
  const savedEmail = sessionStorage.getItem('booking_email');

  if (savedEmail) lookupEmail.value = savedEmail;

  if (routeCode.value) {
    lookupCode.value = routeCode.value;
    fetchBookingPublic(routeCode.value);
  } else if (savedCode && !isLookupRoute.value) {
    lookupCode.value = savedCode;
    fetchBookingPublic(savedCode);
  }
});
</script>
