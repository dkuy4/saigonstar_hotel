<template>
  <div class="max-w-4xl mx-auto space-y-8">
    <!-- Header -->
    <div class="border-b border-beige-300 dark:border-darkbeige-800 pb-4">
      <router-link to="/ket-qua" class="text-xs text-amberbrown-600 dark:text-amberbrown-400 hover:underline flex items-center gap-1 mb-2">
        <span>←</span>
        <span>{{ t('bookingView.back') }}</span>
      </router-link>
      <h2 class="font-display text-3xl font-bold text-stone-900 dark:text-white tracking-tight">{{ t('bookingView.title') }}</h2>
      <p class="text-xs text-stone-500 dark:text-stone-400 mt-1">{{ t('bookingView.subtitle') }}</p>
    </div>

    <!-- Error Banner -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-rose-800 dark:text-rose-200 rounded-xl text-sm flex items-start space-x-3">
      <AlertCircle class="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
      <div class="flex-1">
        <p class="font-semibold">{{ errorTitle }}</p>
        <p class="text-xs mt-0.5">{{ errorMessage }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left: Form Input (2 cols) -->
      <div class="lg:col-span-2 space-y-6">
        <form @submit.prevent="handleBooking" class="space-y-6">
          <!-- Customer Info Card -->
          <div class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-6 shadow-sm space-y-4 transition-colors">
            <h3 class="font-display text-base font-bold text-stone-900 dark:text-white flex items-center gap-2">
              <User class="w-4 h-4 text-amberbrown-500" />
              <span>{{ t('bookingView.customerInfo') }}</span>
            </h3>

            <div class="space-y-4">
              <div>
                <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">
                  {{ t('bookingView.fullName') }} <span class="text-rose-500">*</span>
                </label>
                <input
                  v-model="customer.fullName"
                  type="text"
                  required
                  :placeholder="t('bookingView.fullNamePlaceholder')"
                  class="w-full px-3.5 py-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl text-sm text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-amberbrown-500 outline-none"
                />
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">
                    {{ t('bookingView.phone') }} <span class="text-rose-500">*</span>
                  </label>
                  <input
                    v-model="customer.phone"
                    type="tel"
                    required
                    :placeholder="t('bookingView.phonePlaceholder')"
                    class="w-full px-3.5 py-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl text-sm text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-amberbrown-500 outline-none"
                  />
                </div>

                <div>
                  <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">
                    {{ t('bookingView.email') }} <span class="text-rose-500">*</span>
                  </label>
                  <input
                    v-model="customer.email"
                    type="email"
                    required
                    :placeholder="t('bookingView.emailPlaceholder')"
                    class="w-full px-3.5 py-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl text-sm text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-amberbrown-500 outline-none"
                  />
                </div>
              </div>

              <div>
                <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">
                  {{ t('bookingView.nationality') }}
                </label>
                <select
                  v-model="customer.nationality"
                  class="w-full px-3.5 py-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl text-sm text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-amberbrown-500 outline-none"
                >
                  <option value="VN">Việt Nam (VN)</option>
                  <option value="US">United States (US)</option>
                  <option value="JP">Japan (JP)</option>
                  <option value="KR">Korea (KR)</option>
                  <option value="CN">China (CN)</option>
                  <option value="GB">United Kingdom (GB)</option>
                  <option value="FR">France (FR)</option>
                  <option value="ES">Spain (ES)</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Room Selection Card -->
          <div class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-6 shadow-sm space-y-4 transition-colors">
            <div class="flex items-center justify-between">
              <h3 class="font-display text-base font-bold text-stone-900 dark:text-white flex items-center gap-2">
                <DoorOpen class="w-4 h-4 text-amberbrown-500" />
                <span>{{ t('bookingView.roomSelect') }}</span>
              </h3>
              <span class="text-xs text-stone-400 dark:text-stone-500 font-normal">{{ t('bookingView.availableRoomsCount', { count: availableRooms.length }) }}</span>
            </div>

            <!-- Loading rooms -->
            <div v-if="loadingRooms" class="py-4 text-center text-xs text-stone-400 flex items-center justify-center space-x-2">
              <div class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-amberbrown-500 border-t-transparent"></div>
              <span>{{ t('common.loading') }}</span>
            </div>

            <!-- Room selection list -->
            <div v-else class="space-y-3">
              <!-- Default Option: Auto Assign -->
              <label
                class="flex items-center justify-between p-3.5 border rounded-xl cursor-pointer transition"
                :class="selectedRoomId === null ? 'border-amberbrown-500 bg-amberbrown-50/40 dark:bg-darkbeige-800 ring-1 ring-amberbrown-500' : 'border-beige-300 dark:border-darkbeige-700 hover:bg-beige-100/50 dark:hover:bg-darkbeige-800'"
              >
                <div class="flex items-center space-x-3">
                  <input
                    type="radio"
                    :checked="selectedRoomId === null"
                    @change="selectedRoomId = null"
                    class="text-amberbrown-600 focus:ring-amberbrown-500 h-4 w-4"
                  />
                  <div>
                    <span class="text-xs font-semibold text-stone-900 dark:text-stone-100">{{ t('bookingView.autoAssign') }}</span>
                  </div>
                </div>
              </label>

              <!-- Custom Room Pick Option -->
              <div v-if="availableRooms.length > 0" class="pt-2">
                <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5 max-h-56 overflow-y-auto p-1">
                  <button
                    v-for="r in availableRooms"
                    :key="r.room_id"
                    type="button"
                    @click="selectedRoomId = (selectedRoomId === r.room_id ? null : r.room_id)"
                    class="p-2.5 rounded-xl border text-left transition flex flex-col justify-between"
                    :class="selectedRoomId === r.room_id ? 'border-amberbrown-500 bg-amberbrown-50 dark:bg-darkbeige-800 ring-2 ring-amberbrown-500 text-stone-900 dark:text-white shadow-sm' : 'border-beige-300 dark:border-darkbeige-700 hover:border-amberbrown-400 bg-beige-50/40 dark:bg-darkbeige-900 text-stone-700 dark:text-stone-300'"
                  >
                    <div class="flex items-center justify-between">
                      <span class="font-bold text-xs">{{ t('myTrips.roomPrefix') }} {{ r.room_number }}</span>
                      <CheckCircle2 v-if="selectedRoomId === r.room_id" class="w-3.5 h-3.5 text-amberbrown-600" />
                    </div>
                    <span class="text-[10px] text-stone-500 dark:text-stone-400 mt-1">Tầng {{ r.floor }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Payment Options Card -->
          <div class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-6 shadow-sm space-y-4 transition-colors">
            <h3 class="font-display text-base font-bold text-stone-900 dark:text-white flex items-center gap-2">
              <CreditCard class="w-4 h-4 text-amberbrown-500" />
              <span>{{ t('bookingView.paymentMethod') }}</span>
            </h3>

            <div class="space-y-3">
              <!-- Online Payment (HOLD) -->
              <label
                class="flex items-start p-4 border rounded-xl cursor-pointer transition"
                :class="paymentMethod === 'TRUC_TUYEN' ? 'border-amberbrown-500 bg-amberbrown-50/40 dark:bg-darkbeige-800 ring-1 ring-amberbrown-500' : 'border-beige-300 dark:border-darkbeige-700 hover:bg-beige-100/50 dark:hover:bg-darkbeige-800'"
              >
                <input
                  v-model="paymentMethod"
                  type="radio"
                  value="TRUC_TUYEN"
                  class="mt-1 text-amberbrown-600 focus:ring-amberbrown-500 h-4 w-4"
                />
                <div class="ml-3">
                  <div class="font-semibold text-sm text-stone-900 dark:text-white">{{ t('bookingView.payOnline') }}</div>
                  <p class="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
                    {{ t('bookingView.payOnlineSub') }}
                  </p>
                </div>
              </label>

              <!-- Pay at Hotel (CONFIRMED) -->
              <label
                class="flex items-start p-4 border rounded-xl cursor-pointer transition"
                :class="paymentMethod === 'KHI_NHAN_PHONG' ? 'border-amberbrown-500 bg-amberbrown-50/40 dark:bg-darkbeige-800 ring-1 ring-amberbrown-500' : 'border-beige-300 dark:border-darkbeige-700 hover:bg-beige-100/50 dark:hover:bg-darkbeige-800'"
              >
                <input
                  v-model="paymentMethod"
                  type="radio"
                  value="KHI_NHAN_PHONG"
                  class="mt-1 text-amberbrown-600 focus:ring-amberbrown-500 h-4 w-4"
                />
                <div class="ml-3">
                  <div class="font-semibold text-sm text-stone-900 dark:text-white">{{ t('bookingView.payCounter') }}</div>
                  <p class="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
                    {{ t('bookingView.payCounterSub') }}
                  </p>
                </div>
              </label>
            </div>
          </div>

          <!-- Policy Agreement -->
          <div class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-6 shadow-sm space-y-3 transition-colors">
            <div class="flex items-start">
              <input
                id="agree-checkbox"
                v-model="agreeTerms"
                type="checkbox"
                required
                class="mt-1 h-4 w-4 text-amberbrown-600 focus:ring-amberbrown-500 border-beige-300 rounded"
              />
              <label for="agree-checkbox" class="ml-3 text-xs text-stone-700 dark:text-stone-300 leading-relaxed cursor-pointer">
                {{ t('bookingView.terms') }} <span class="text-rose-500">*</span>
              </label>
            </div>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="loading || !isFormValid"
            class="w-full py-4 px-6 bg-amberbrown-500 hover:bg-amberbrown-600 text-white font-bold text-base rounded-xl shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            <span>{{ loading ? t('bookingView.submitting') : t('bookingView.submit') }}</span>
            <span>→</span>
          </button>
        </form>
      </div>

      <!-- Right: Booking Summary (1 col) -->
      <div class="space-y-6">
        <div class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-6 shadow-sm sticky top-24 space-y-5 transition-colors">
          <h3 class="font-display text-base font-bold text-stone-900 dark:text-white pb-3 border-b border-beige-200 dark:border-darkbeige-800">
            {{ t('bookingView.summaryTitle') }}
          </h3>

          <div class="space-y-3 text-xs text-stone-600 dark:text-stone-300">
            <div class="flex justify-between items-center">
              <span class="text-stone-500 dark:text-stone-400">{{ t('bookingHold.roomType') }}</span>
              <span class="font-bold text-stone-900 dark:text-stone-100 bg-beige-100 dark:bg-darkbeige-800 px-2 py-0.5 rounded">{{ roomType }}</span>
            </div>

            <div class="flex justify-between items-center">
              <span class="text-stone-500 dark:text-stone-400">{{ t('bookingDetail.guests') }}:</span>
              <span class="font-medium text-stone-800 dark:text-stone-200">{{ guests }}</span>
            </div>

            <div class="flex justify-between items-center pt-2 border-t border-beige-200 dark:border-darkbeige-800">
              <span class="text-stone-500 dark:text-stone-400">{{ t('bookingHold.roomNumber') }}</span>
              <span class="font-semibold text-xs text-amberbrown-600 dark:text-amberbrown-400">
                {{ selectedRoomNumber ? `${t('myTrips.roomPrefix')} ${selectedRoomNumber}` : t('bookingView.autoAssign') }}
              </span>
            </div>

            <div class="pt-2 border-t border-beige-200 dark:border-darkbeige-800 space-y-2">
              <div>
                <span class="text-stone-400 dark:text-stone-500 block text-[10px] uppercase">{{ t('bookingDetail.checkin') }}:</span>
                <span class="font-semibold text-stone-800 dark:text-stone-200">{{ formatDateTime(checkin) }}</span>
              </div>
              <div>
                <span class="text-stone-400 dark:text-stone-500 block text-[10px] uppercase">{{ t('bookingDetail.checkout') }}:</span>
                <span class="font-semibold text-stone-800 dark:text-stone-200">{{ formatDateTime(checkout) }}</span>
              </div>
            </div>
          </div>

          <!-- Price Calculation Box -->
          <div v-if="priceInfo" class="pt-4 border-t border-beige-200 dark:border-darkbeige-800 space-y-2 text-xs">
            <div class="flex justify-between text-stone-600 dark:text-stone-400">
              <span>{{ t('bookingView.roomTotal') }}:</span>
              <MoneyText :value="priceInfo.room_amount" currency="VND" />
            </div>
            <div class="flex justify-between text-stone-600 dark:text-stone-400">
              <span>{{ t('bookingView.vatAmount') }}:</span>
              <MoneyText :value="priceInfo.vat_amount" currency="VND" />
            </div>
            <div class="pt-3 border-t border-beige-200 dark:border-darkbeige-800 flex justify-between items-baseline">
              <div>
                <span class="text-xs uppercase font-bold text-stone-700 dark:text-stone-200 block">{{ t('bookingView.grandTotal') }}:</span>
                <span class="text-[10px] text-stone-400 dark:text-stone-500">{{ t('pricing.totalWithVat') }}</span>
              </div>
              <div class="text-xl font-black text-amberbrown-600 dark:text-amberbrown-400">
                <MoneyText :value="priceInfo.total_amount" currency="VND" />
              </div>
            </div>
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
import { AlertCircle, User, CreditCard, DoorOpen, CheckCircle2 } from 'lucide-vue-next';
import apiClient from '../api/client';
import MoneyText from '../components/MoneyText.vue';
import { useGuestAuthStore } from '../stores/guestAuth';

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const guestAuth = useGuestAuthStore();

const stayType = computed(() => route.query.type || 'NGAY');
const roomType = computed(() => route.query.room_type || 'STANDARD');
const checkin = computed(() => route.query.checkin || '');
const checkout = computed(() => route.query.checkout || '');
const guests = computed(() => Number(route.query.guests || 2));

const customer = ref({
  fullName: guestAuth.isLoggedIn ? guestAuth.guestName : '',
  phone: guestAuth.isLoggedIn ? guestAuth.guestPhone : '',
  email: guestAuth.isLoggedIn ? guestAuth.guestEmail : '',
  nationality: 'VN'
});

const paymentMethod = ref('TRUC_TUYEN');
const agreeTerms = ref(false);
const loading = ref(false);
const errorMessage = ref('');
const errorTitle = ref('');
const priceInfo = ref(null);

const availableRooms = ref([]);
const selectedRoomId = ref(null);
const loadingRooms = ref(false);

const selectedRoomNumber = computed(() => {
  if (!selectedRoomId.value) return null;
  const found = availableRooms.value.find(r => r.room_id === selectedRoomId.value);
  return found ? found.room_number : null;
});

const loadAvailableRooms = async () => {
  if (!checkin.value || !checkout.value || !roomType.value) return;
  loadingRooms.value = true;
  try {
    const res = await apiClient.get('/availability/rooms', {
      params: {
        roomType: roomType.value,
        checkin: checkin.value,
        checkout: checkout.value
      }
    });
    availableRooms.value = res.rooms || res.data?.rooms || [];
  } catch (err) {
    console.error('Không thể tải danh sách phòng khả dụng:', err);
    availableRooms.value = [];
  } finally {
    loadingRooms.value = false;
  }
};

const isFormValid = computed(() => {
  return (
    customer.value.fullName.trim().length >= 2 &&
    customer.value.phone.trim().length >= 8 &&
    customer.value.email.includes('@') &&
    agreeTerms.value
  );
});

const formatDateTime = (isoStr) => {
  if (!isoStr) return '';
  return new Date(isoStr).toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const loadPriceInfo = async () => {
  if (!checkin.value || !checkout.value) {
    router.replace('/');
    return;
  }
  try {
    const res = await apiClient.get('/availability', {
      params: {
        type: stayType.value,
        checkin: checkin.value,
        checkout: checkout.value,
        guests: guests.value,
        room_type: roomType.value,
        lang: locale.value
      }
    });
    if (res.items && res.items.length > 0) {
      priceInfo.value = res.items[0];
    } else {
      errorMessage.value = t('search.noRooms');
      errorTitle.value = t('errors.NO_AVAILABILITY');
    }
  } catch (err) {
    errorMessage.value = err.message || t('errors.INTERNAL_SERVER_ERROR');
    errorTitle.value = t('errors.INTERNAL_SERVER_ERROR');
  }
};

const handleBooking = async () => {
  if (!isFormValid.value) return;

  loading.value = true;
  errorMessage.value = '';
  errorTitle.value = '';

  try {
    const payload = {
      loaiDat: stayType.value,
      maHang: roomType.value,
      phongId: selectedRoomId.value || null,
      nhanLuc: checkin.value,
      traLuc: checkout.value,
      soKhach: guests.value,
      thanhToan: paymentMethod.value,
      dongYChinhSach: agreeTerms.value,
      customer: {
        fullName: customer.value.fullName,
        phone: customer.value.phone,
        email: customer.value.email,
        nationality: customer.value.nationality
      },
      ngonNgu: locale.value
    };

    const res = await apiClient.post('/bookings', payload);
    const booking = res.data || res;

    if (booking.status === 'HOLD') {
      router.push(`/giu-cho/${booking.booking_code}`);
    } else {
      router.push(`/don/${booking.booking_code}`);
    }
  } catch (err) {
    errorTitle.value = t('errors.BOOKING_STATE_INVALID');
    if (err.code === 'NO_AVAILABILITY') {
      errorMessage.value = t('errors.NO_AVAILABILITY');
    } else if (err.code === 'PENDING_LIMIT_EXCEEDED') {
      errorMessage.value = t('errors.PENDING_LIMIT_EXCEEDED');
    } else if (err.code === 'ROOM_CONFLICT') {
      errorMessage.value = t('errors.ROOM_CONFLICT');
    } else {
      errorMessage.value = err.message || t('errors.INTERNAL_SERVER_ERROR');
    }
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadPriceInfo();
  loadAvailableRooms();
});
</script>
