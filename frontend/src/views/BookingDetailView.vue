<template>
  <div class="max-w-4xl mx-auto space-y-6 py-6 px-4">
    <!-- Lookup Form Header / Card -->
    <div v-if="!booking || isLookupRoute" class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-6 sm:p-8 shadow-sm space-y-4 transition-colors">
      <div class="text-center max-w-lg mx-auto space-y-1">
        <h2 class="font-display text-2xl font-bold text-stone-900 dark:text-white">{{ t('lookup.title') }}</h2>
        <p class="text-xs text-stone-500 dark:text-stone-400">{{ t('lookup.subtitle') }}</p>
      </div>

      <!-- Embedded Alerts inside Lookup Form Card -->
      <div v-if="errorMessage" class="max-w-md mx-auto p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-rose-800 dark:text-rose-200 rounded-xl text-xs flex items-center space-x-3">
        <AlertCircle class="w-5 h-5 text-rose-600 flex-shrink-0" />
        <span class="font-medium leading-relaxed">{{ errorMessage }}</span>
      </div>

      <div v-if="successMessage" class="max-w-md mx-auto p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/50 text-emerald-800 dark:text-emerald-200 rounded-xl text-xs flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <CheckCircle2 class="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span class="font-medium leading-relaxed">{{ successMessage }}</span>
        </div>
        <button @click="successMessage = ''" class="text-emerald-700 hover:text-emerald-900 dark:text-emerald-300 font-bold ml-2">{{ t('common.close') }}</button>
      </div>

      <form @submit.prevent="handleLookup" class="max-w-md mx-auto space-y-4 pt-1">
        <div>
          <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">{{ t('lookup.bookingCode') }}</label>
          <input
            v-model="lookupCode"
            type="text"
            required
            :placeholder="t('lookup.bookingCodePlaceholder')"
            class="w-full px-4 py-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl text-sm font-mono uppercase text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-amberbrown-500 outline-none"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">{{ t('lookup.email') }}</label>
          <input
            v-model="lookupEmail"
            type="email"
            required
            :placeholder="t('lookup.emailPlaceholder')"
            class="w-full px-4 py-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl text-sm text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-amberbrown-500 outline-none"
          />
        </div>

        <button
          type="submit"
          :disabled="loadingLookup"
          class="w-full py-3 bg-amberbrown-500 hover:bg-amberbrown-600 text-white font-semibold text-sm rounded-xl shadow transition flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          <div v-if="loadingLookup" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
          <span>{{ loadingLookup ? t('lookup.checking') : t('lookup.submit') }}</span>
        </button>
      </form>
    </div>

    <!-- Error Alert when booking is loaded but action fails -->
    <div v-if="booking && !isLookupRoute && errorMessage" class="p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-rose-800 dark:text-rose-200 rounded-xl text-xs flex items-center space-x-3">
      <AlertCircle class="w-5 h-5 text-rose-600 flex-shrink-0" />
      <span class="font-medium leading-relaxed">{{ errorMessage }}</span>
    </div>

    <!-- Success Message Alert when booking is loaded -->
    <div v-if="booking && !isLookupRoute && successMessage" class="p-4 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/50 text-emerald-800 dark:text-emerald-200 rounded-xl text-xs flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <CheckCircle2 class="w-5 h-5 text-emerald-600 flex-shrink-0" />
        <span class="font-medium leading-relaxed">{{ successMessage }}</span>
      </div>
      <button @click="successMessage = ''" class="text-emerald-700 hover:text-emerald-900 dark:text-emerald-300 font-bold ml-2">{{ t('common.close') }}</button>
    </div>

    <!-- Booking Details Card -->
    <div v-if="booking" class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-6 sm:p-8 shadow-sm space-y-6 transition-colors">
      <!-- Card Header -->
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-beige-200 dark:border-darkbeige-800 pb-5">
        <div>
          <span class="text-xs uppercase tracking-wide font-semibold text-stone-400 dark:text-stone-500">{{ t('bookingDetail.codeLabel') }}</span>
          <h3 class="text-3xl font-black font-mono text-stone-900 dark:text-white mt-0.5">{{ booking.booking_code }}</h3>
          <p class="text-xs text-stone-500 dark:text-stone-400 mt-0.5">{{ t('bookingDetail.channel') }} <strong class="text-stone-700 dark:text-stone-300">{{ booking.channel === 'WEB' ? t('bookingDetail.channelWeb') : t('bookingDetail.channelCounter') }}</strong></p>
        </div>
        <div class="flex items-center space-x-3">
          <StatusBadge :status="booking.status" />
        </div>
      </div>

      <!-- Action Banners -->
      <div v-if="booking.status === 'HOLD'" class="p-4 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl flex items-center justify-between">
        <div class="text-xs text-amber-800 dark:text-amber-200">
          <span class="font-bold">{{ t('bookingDetail.holdAlert') }}</span>
          {{ t('bookingDetail.holdAlertSub') }}
        </div>
        <router-link
          :to="`/giu-cho/${booking.booking_code}`"
          class="px-4 py-2 bg-amberbrown-500 hover:bg-amberbrown-600 text-white rounded-lg text-xs font-semibold shadow"
        >
          {{ t('bookingDetail.payNow') }}
        </router-link>
      </div>

      <!-- Guest and Stay Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
        <!-- Guest Box -->
        <div class="bg-beige-50/70 dark:bg-darkbeige-900 rounded-xl p-5 space-y-2 border border-beige-200 dark:border-darkbeige-800">
          <span class="font-bold text-stone-700 dark:text-stone-300 block uppercase text-[10px] tracking-wider border-b border-beige-200 dark:border-darkbeige-800 pb-1.5">
            {{ t('bookingDetail.customerInfo') }}
          </span>
          <div class="text-sm font-semibold text-stone-900 dark:text-white">{{ booking.customer?.fullName }}</div>
          <div class="text-stone-600 dark:text-stone-400">{{ t('bookingView.phone') }}: <span class="font-medium text-stone-800 dark:text-stone-200">{{ booking.customer?.phone }}</span></div>
          <div class="text-stone-600 dark:text-stone-400">{{ t('bookingView.email') }}: <span class="font-medium text-stone-800 dark:text-stone-200">{{ booking.customer?.email }}</span></div>
          <div class="text-stone-600 dark:text-stone-400">{{ t('bookingView.nationality') }}: <span class="font-medium text-stone-800 dark:text-stone-200">{{ booking.customer?.nationality }}</span></div>
        </div>

        <!-- Stay Details Box -->
        <div class="bg-beige-50/70 dark:bg-darkbeige-900 rounded-xl p-5 space-y-2 border border-beige-200 dark:border-darkbeige-800">
          <span class="font-bold text-stone-700 dark:text-stone-300 block uppercase text-[10px] tracking-wider border-b border-beige-200 dark:border-darkbeige-800 pb-1.5">
            {{ t('bookingDetail.roomInfo') }}
          </span>
          <div class="text-sm font-bold text-amberbrown-600 dark:text-amberbrown-400">{{ getRoomTypeLabel(booking) }}</div>
          <div v-if="getRoomNumber(booking)" class="text-stone-600 dark:text-stone-400">
            {{ t('bookingDetail.assignedRoom') }}: <span class="font-bold text-stone-900 dark:text-stone-100 bg-amberbrown-50 dark:bg-darkbeige-800 text-amberbrown-800 dark:text-amberbrown-300 px-2 py-0.5 rounded-lg border border-amberbrown-200 dark:border-darkbeige-700">{{ t('myTrips.roomPrefix') }} {{ getRoomNumber(booking) }}</span>
          </div>
          <div class="text-stone-600 dark:text-stone-400">{{ t('bookingDetail.guests') }}: <span class="font-medium text-stone-800 dark:text-stone-200">{{ booking.guests }}</span></div>
          <div class="text-stone-600 dark:text-stone-400">{{ t('bookingDetail.checkin') }}: <strong class="text-stone-900 dark:text-stone-100">{{ formatDateTime(booking.checkin) }}</strong></div>
          <div class="text-stone-600 dark:text-stone-400">{{ t('bookingDetail.checkout') }}: <strong class="text-stone-900 dark:text-stone-100">{{ formatDateTime(booking.checkout) }}</strong></div>
        </div>
      </div>

      <!-- Financial Breakdown -->
      <div class="pt-4 border-t border-beige-200 dark:border-darkbeige-800 space-y-2.5 text-xs">
        <div class="flex justify-between text-stone-600 dark:text-stone-400">
          <span>{{ t('bookingDetail.roomRate') }}:</span>
          <MoneyText :amount="booking.room_amount" />
        </div>
        <div class="flex justify-between text-stone-600 dark:text-stone-400">
          <span>{{ t('bookingDetail.vat') }}:</span>
          <MoneyText :amount="booking.vat_amount" />
        </div>
        <div class="pt-3 border-t border-beige-200 dark:border-darkbeige-800 flex justify-between items-baseline">
          <div>
            <span class="font-bold text-stone-800 dark:text-stone-200 text-sm">{{ t('bookingDetail.total') }}:</span>
            <span class="text-[10px] text-stone-400 dark:text-stone-500 block">{{ t('pricing.totalWithVat') }}</span>
          </div>
          <div class="text-2xl font-black text-amberbrown-600 dark:text-amberbrown-400">
            <MoneyText :amount="booking.total_amount" />
          </div>
        </div>
      </div>

      <!-- Policy Reminder -->
      <div class="bg-beige-100/70 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-800 rounded-xl p-4 text-xs text-stone-800 dark:text-stone-300 space-y-1">
        <div class="font-bold uppercase text-[10px] tracking-wider text-amberbrown-700 dark:text-amberbrown-300">{{ t('bookingDetail.cancelPolicy') }}</div>
        <p class="text-stone-600 dark:text-stone-400 leading-relaxed">
          {{ t('bookingDetail.cancelPolicyDesc') }}
        </p>
      </div>

      <!-- Action Buttons for CONFIRMED Booking -->
      <div v-if="booking.status === 'CONFIRMED'" class="pt-4 border-t border-beige-200 dark:border-darkbeige-800 flex flex-wrap gap-3 justify-end">
        <button
          @click="openCancelModal"
          class="px-5 py-2.5 bg-rose-50 dark:bg-rose-950/30 hover:bg-rose-100 text-rose-700 dark:text-rose-300 font-semibold rounded-xl text-xs transition border border-rose-200 dark:border-rose-900/50 flex items-center space-x-1.5"
        >
          <X class="w-4 h-4" />
          <span>{{ t('bookingDetail.cancelBtn') }}</span>
        </button>
      </div>
    </div>

    <!-- CANCEL MODAL -->
    <div v-if="showCancelModal" class="fixed inset-0 z-50 bg-stone-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div class="bg-white dark:bg-darkbeige-850 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl border border-beige-300 dark:border-darkbeige-800">
        <div class="flex items-center justify-between border-b border-beige-200 dark:border-darkbeige-800 pb-3">
          <h3 class="text-lg font-bold text-stone-900 dark:text-white flex items-center space-x-2">
            <AlertCircle class="w-5 h-5 text-rose-600 flex-shrink-0" />
            <span>{{ t('bookingDetail.cancelBtn') }}</span>
          </h3>
          <button @click="showCancelModal = false" class="text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 p-1 rounded-lg">
            <X class="w-4 h-4" />
          </button>
        </div>

        <div v-if="loadingPreview" class="py-8 text-center text-stone-500 text-xs">
          <div class="animate-spin rounded-full h-6 w-6 border-2 border-amberbrown-500 border-t-transparent mx-auto mb-2"></div>
          {{ t('bookingDetail.cancelling') }}
        </div>

        <div v-else-if="refundPreview" class="space-y-4 text-xs">
          <div :class="refundPreview.isEligible ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 text-emerald-900 dark:text-emerald-200' : 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 text-amber-900 dark:text-amber-200'" class="p-4 rounded-xl border space-y-2">
            <div class="font-bold text-sm flex justify-between items-center">
              <span>{{ t('bookingDetail.total') }}:</span>
              <span class="text-lg font-black font-mono">
                <MoneyText :amount="refundPreview.expectedRefund" />
              </span>
            </div>
            <div class="text-[11px] leading-relaxed">{{ refundPreview.reason }}</div>
          </div>

          <div>
            <label class="block font-semibold text-stone-700 dark:text-stone-300 mb-1">{{ t('common.actions') }}</label>
            <textarea
              v-model="cancelReason"
              rows="3"
              class="w-full p-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl outline-none focus:ring-2 focus:ring-amberbrown-500 text-stone-900 dark:text-stone-100"
            ></textarea>
          </div>

          <div class="flex justify-end space-x-2 pt-2 border-t border-beige-200 dark:border-darkbeige-800">
            <button
              @click="showCancelModal = false"
              class="px-4 py-2 bg-beige-200 dark:bg-darkbeige-800 text-stone-700 dark:text-stone-300 rounded-xl font-medium"
            >
              {{ t('common.close') }}
            </button>
            <button
              @click="confirmCancelBooking"
              :disabled="cancelling"
              class="px-5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-semibold shadow disabled:opacity-50 flex items-center space-x-1"
            >
              <div v-if="cancelling" class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
              <span>{{ cancelling ? t('bookingDetail.cancelling') : t('bookingDetail.cancelBtn') }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { AlertCircle, CheckCircle2, X } from 'lucide-vue-next';
import apiClient from '../api/client';
import StatusBadge from '../components/StatusBadge.vue';
import MoneyText from '../components/MoneyText.vue';

const { t } = useI18n();
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

const isLookupRoute = computed(() => route.path === '/don/tra-cuu');
const routeCode = computed(() => route.params.code || '');

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
  if (!b) return null;
  return b.room_number || b.segments?.[0]?.room_number || b.segments?.[0]?.roomNumber || null;
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
    errorMessage.value = err.message || t('errors.BOOKING_NOT_FOUND');
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
    errorMessage.value = err.message || t('errors.BOOKING_NOT_FOUND');
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
    alert(err.message || t('errors.CANCEL_NOT_ALLOWED'));
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
      reason: cancelReason.value
    });
    showCancelModal.value = false;
    successMessage.value = res?.message || t('bookingDetail.cancelSuccess');
    fetchBookingPublic(booking.value.booking_code);
  } catch (err) {
    alert(err.message || t('errors.CANCEL_NOT_ALLOWED'));
  } finally {
    cancelling.value = false;
  }
};

onMounted(() => {
  if (routeCode.value) {
    fetchBookingPublic(routeCode.value);
  }
});
</script>
