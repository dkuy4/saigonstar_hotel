<template>
  <div class="space-y-8">
    <!-- Top Search Summary & Bar -->
    <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center space-x-2">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase"
              :class="searchType === 'NGAY' ? 'bg-sky-100 text-sky-800' : 'bg-purple-100 text-purple-800'">
              {{ searchType === 'NGAY' ? t('search.daily') : t('search.hourly') }}
            </span>
            <span class="text-xs text-slate-500">•</span>
            <span class="text-xs text-slate-600 font-medium">{{ guestsCount }} khách</span>
          </div>

          <h2 class="text-xl font-bold text-slate-900 mt-1">
            {{ formatDateTime(checkinStr) }} → {{ formatDateTime(checkoutStr) }}
          </h2>
          <p class="text-xs text-slate-500 mt-0.5">
            {{ stayDurationDescription }}
          </p>
        </div>

        <button
          @click="showSearchBox = !showSearchBox"
          class="px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-xl transition flex items-center space-x-1.5"
        >
          <span>✏️</span>
          <span>{{ showSearchBox ? 'Ẩn bộ tìm kiếm' : t('search.modifySearch') }}</span>
        </button>
      </div>

      <!-- Collapsible Search Box -->
      <div v-if="showSearchBox" class="mt-6 pt-6 border-t border-slate-100">
        <SearchBox
          :initial-type="searchType"
          :initial-checkin="checkinStr"
          :initial-checkout="checkoutStr"
          :initial-guests="Number(guestsCount)"
        />
      </div>
    </div>

    <!-- Error Alert Banner -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm flex items-start space-x-3">
      <span class="text-lg">⚠️</span>
      <div>
        <p class="font-semibold">Không thể tải danh sách phòng</p>
        <p class="text-xs mt-0.5">{{ errorMessage }}</p>
      </div>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-white rounded-2xl border border-slate-200 p-6 animate-pulse flex flex-col md:flex-row gap-6">
        <div class="w-full md:w-64 h-48 bg-slate-200 rounded-xl"></div>
        <div class="flex-1 space-y-3">
          <div class="h-6 bg-slate-200 rounded w-1/3"></div>
          <div class="h-4 bg-slate-200 rounded w-2/3"></div>
          <div class="h-4 bg-slate-200 rounded w-1/2"></div>
        </div>
      </div>
    </div>

    <!-- No Availability Notice -->
    <div v-else-if="!loading && rooms.length === 0 && !errorMessage" class="bg-white rounded-2xl border border-slate-200 p-12 text-center max-w-xl mx-auto space-y-4">
      <div class="w-16 h-16 bg-amber-50 text-amber-600 rounded-full flex items-center justify-center text-3xl mx-auto">
        🏨
      </div>
      <h3 class="text-lg font-bold text-slate-800">{{ t('search.noRooms') }}</h3>
      <p class="text-sm text-slate-500 leading-relaxed">
        {{ t('search.suggestInterval') }}
      </p>
      <button
        @click="showSearchBox = true"
        class="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded-xl transition"
      >
        {{ t('search.modifySearch') }}
      </button>
    </div>

    <!-- Room Results List -->
    <div v-else-if="!loading && rooms.length > 0" class="space-y-6">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-bold text-slate-900">
          {{ t('search.resultsTitle') }} ({{ rooms.length }} hạng phòng)
        </h3>
        <span class="text-xs text-slate-500 italic">Giá đã bao gồm toàn bộ thuế VAT và phí dịch vụ (BR-59)</span>
      </div>

      <div class="grid grid-cols-1 gap-6">
        <div
          v-for="room in rooms"
          :key="room.room_type_id"
          class="bg-white rounded-2xl border border-slate-200/90 shadow-sm hover:shadow-md transition overflow-hidden flex flex-col lg:flex-row"
        >
          <!-- Room Thumbnail / Image -->
          <div class="lg:w-80 h-56 lg:h-auto bg-slate-100 relative overflow-hidden flex-shrink-0">
            <img
              :src="getRoomImage(room.code)"
              :alt="room.name"
              class="w-full h-full object-cover group-hover:scale-105 transition duration-300"
            />
            <div class="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-sm text-white px-2.5 py-1 rounded-md text-xs font-semibold">
              {{ room.code }}
            </div>
            <div class="absolute bottom-3 left-3 bg-emerald-600 text-white px-2.5 py-1 rounded-md text-xs font-semibold shadow">
              {{ t('search.roomsLeft', { count: room.available_rooms }) }}
            </div>
          </div>

          <!-- Room Details -->
          <div class="p-6 flex-1 flex flex-col justify-between">
            <div class="space-y-3">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h4 class="text-xl font-bold text-slate-900">{{ room.name }}</h4>
                  <p class="text-xs text-slate-500 flex items-center gap-2 mt-1">
                    <span>👥 Tối đa {{ room.capacity }} người</span>
                    <span>•</span>
                    <span v-if="room.hourly_allowed" class="text-sky-600 font-medium">⏱️ Cho thuê theo giờ & theo ngày</span>
                    <span v-else class="text-slate-500">📅 Chỉ thuê theo ngày</span>
                  </p>
                </div>
              </div>

              <!-- Description -->
              <p class="text-xs text-slate-600 leading-relaxed">
                {{ room.description }}
              </p>

              <!-- Amenities Tags -->
              <div v-if="room.amenities" class="flex flex-wrap gap-1.5 pt-1">
                <span
                  v-for="(amenity, idx) in room.amenities.split(',')"
                  :key="idx"
                  class="px-2.5 py-1 bg-slate-100 text-slate-700 text-[11px] rounded-lg font-medium"
                >
                  ✓ {{ amenity.trim() }}
                </span>
              </div>
            </div>

            <!-- Pricing & Action Section (BR-59 Compliant) -->
            <div class="mt-6 pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-end sm:items-center justify-between gap-4">
              <!-- Price Breakdown -->
              <div class="space-y-1">
                <div class="text-[11px] uppercase tracking-wider font-semibold text-slate-500">
                  {{ t('pricing.totalWithVat') }}
                </div>
                <!-- Prominent Grand Total -->
                <div class="text-2xl font-black text-sky-600">
                  <MoneyText :value="room.total_amount" currency="VND" />
                </div>
                <!-- Breakdown note -->
                <div class="text-[11px] text-slate-500 flex items-center space-x-2">
                  <span>Tiền phòng: <MoneyText :value="room.room_amount" currency="VND" /></span>
                  <span>+</span>
                  <span>VAT ({{ (room.vat_rate * 100).toFixed(0) }}%): <MoneyText :value="room.vat_amount" currency="VND" /></span>
                </div>
                <!-- Converted Foreign Currency Estimate (FR-10) -->
                <div v-if="room.converted_prices && room.converted_prices.USD" class="text-[11px] text-slate-400 font-mono">
                  {{ t('pricing.referencePrice', { amount: room.converted_prices.USD, currency: 'USD' }) }}
                </div>
              </div>

              <!-- Booking CTA Button -->
              <button
                @click="goToBooking(room)"
                class="w-full sm:w-auto px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white font-bold text-sm rounded-xl shadow-md hover:shadow-lg transition flex items-center justify-center space-x-2"
              >
                <span>{{ t('search.bookNow') }}</span>
                <span>→</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import apiClient from '../api/client';
import SearchBox from '../components/SearchBox.vue';
import MoneyText from '../components/MoneyText.vue';

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();

const showSearchBox = ref(false);
const loading = ref(true);
const errorMessage = ref('');
const rooms = ref([]);

const searchType = computed(() => route.query.type || 'NGAY');
const checkinStr = computed(() => route.query.checkin || '');
const checkoutStr = computed(() => route.query.checkout || '');
const guestsCount = computed(() => route.query.guests || '2');

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

const stayDurationDescription = computed(() => {
  if (!checkinStr.value || !checkoutStr.value) return '';
  const ci = new Date(checkinStr.value);
  const co = new Date(checkoutStr.value);
  const diffHours = Math.round((co - ci) / (1000 * 3600));

  if (searchType.value === 'NGAY') {
    const nights = Math.round(diffHours / 24);
    return `${nights} đêm lưu trú (Nhận 14:00 - Trả 12:00)`;
  } else {
    return `${diffHours} giờ lưu trú theo giờ`;
  }
});

const getRoomImage = (code) => {
  const images = {
    STANDARD: 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80',
    SUPERIOR: 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80',
    DELUXE: 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80',
    SUITE: 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80'
  };
  return images[code] || images.STANDARD;
};

const fetchAvailability = async () => {
  if (!checkinStr.value || !checkoutStr.value) {
    router.replace('/');
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  try {
    const res = await apiClient.get('/availability', {
      params: {
        type: searchType.value,
        checkin: checkinStr.value,
        checkout: checkoutStr.value,
        guests: guestsCount.value,
        lang: locale.value
      }
    });
    rooms.value = res.items || [];
  } catch (err) {
    errorMessage.value = err.message || t('errors.INTERNAL_SERVER_ERROR');
    rooms.value = [];
  } finally {
    loading.value = false;
  }
};

const goToBooking = (room) => {
  router.push({
    path: '/dat-phong',
    query: {
      type: searchType.value,
      room_type: room.code,
      checkin: checkinStr.value,
      checkout: checkoutStr.value,
      guests: guestsCount.value
    }
  });
};

onMounted(fetchAvailability);
watch(() => [route.query, locale.value], fetchAvailability);
</script>
