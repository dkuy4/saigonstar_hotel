<template>
  <div class="space-y-8">
    <!-- Top Search Summary & Bar -->
    <div class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-6 shadow-sm transition-colors">
      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center space-x-2">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase"
              :class="searchType === 'NGAY' ? 'bg-amberbrown-100 text-amberbrown-800 dark:bg-amberbrown-950/40 dark:text-amberbrown-200' : 'bg-purple-100 text-purple-800 dark:bg-purple-950/40 dark:text-purple-200'">
              {{ searchType === 'NGAY' ? t('search.daily') : t('search.hourly') }}
            </span>
            <span class="text-xs text-stone-400 dark:text-stone-500">-</span>
            <span class="text-xs text-stone-600 dark:text-stone-300 font-medium">{{ guestsCount }} {{ t('bookingHold.personUnit') }}</span>
          </div>

          <h2 class="font-display text-xl font-bold text-stone-900 dark:text-white mt-1">
            {{ formatDateTime(checkinStr) }} - {{ formatDateTime(checkoutStr) }}
          </h2>
          <p class="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
            {{ stayDurationDescription }}
          </p>
        </div>

        <button
          @click="showSearchBox = !showSearchBox"
          class="px-4 py-2 border border-beige-300 dark:border-darkbeige-700 hover:bg-beige-100/60 dark:hover:bg-darkbeige-800 text-stone-700 dark:text-stone-200 text-xs font-semibold rounded-xl transition flex items-center space-x-1.5"
        >
          <SlidersHorizontal class="w-3.5 h-3.5 text-stone-500" />
          <span>{{ showSearchBox ? t('common.close') : t('search.modifySearch') }}</span>
        </button>
      </div>

      <!-- Collapsible Search Box -->
      <div v-if="showSearchBox" class="mt-6 pt-6 border-t border-beige-200 dark:border-darkbeige-800">
        <SearchBox
          :initial-type="searchType"
          :initial-checkin="checkinStr"
          :initial-checkout="checkoutStr"
          :initial-guests="Number(guestsCount)"
        />
      </div>
    </div>

    <!-- Error Alert Banner -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-rose-800 dark:text-rose-200 rounded-xl text-sm flex items-start space-x-3">
      <AlertCircle class="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
      <div>
        <p class="font-semibold">{{ t('errors.INTERNAL_SERVER_ERROR') }}</p>
        <p class="text-xs mt-0.5">{{ errorMessage }}</p>
      </div>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-6 animate-pulse flex flex-col md:flex-row gap-6">
        <div class="w-full md:w-64 h-48 bg-stone-200 dark:bg-darkbeige-800 rounded-xl"></div>
        <div class="flex-1 space-y-3">
          <div class="h-6 bg-stone-200 dark:bg-darkbeige-800 rounded w-1/3"></div>
          <div class="h-4 bg-stone-200 dark:bg-darkbeige-800 rounded w-2/3"></div>
          <div class="h-4 bg-stone-200 dark:bg-darkbeige-800 rounded w-1/2"></div>
        </div>
      </div>
    </div>

    <!-- No Availability Notice -->
    <div v-else-if="!loading && rooms.length === 0 && !errorMessage" class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-12 text-center max-w-xl mx-auto space-y-4">
      <div class="w-16 h-16 bg-amber-50 dark:bg-amber-950/30 text-amber-600 rounded-full flex items-center justify-center mx-auto">
        <Building2 class="w-8 h-8 text-amber-600" />
      </div>
      <h3 class="font-display text-lg font-bold text-stone-900 dark:text-white">{{ t('search.noRooms') }}</h3>
      <p class="text-sm text-stone-500 dark:text-stone-400 leading-relaxed">
        {{ t('search.suggestInterval') }}
      </p>
      <button
        @click="showSearchBox = true"
        class="px-5 py-2.5 bg-amberbrown-500 hover:bg-amberbrown-600 text-white text-xs font-semibold rounded-xl transition"
      >
        {{ t('search.modifySearch') }}
      </button>
    </div>

    <!-- Room Results List (2-Column Responsive Layout) -->
    <div v-else-if="!loading && rooms.length > 0" class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <!-- Left Sidebar: Filter & Summary -->
      <aside class="lg:col-span-4 bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 p-5 space-y-4 lg:sticky lg:top-24 transition-colors">
        <div class="border-b border-beige-200 dark:border-darkbeige-800 pb-3">
          <h3 class="font-display text-lg font-bold text-stone-900 dark:text-white">
            {{ t('results.title') }}
          </h3>
          <p class="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
            {{ t('results.foundCount', { count: filteredRooms.length }) }}
          </p>
        </div>

        <div class="space-y-2">
          <button
            type="button"
            @click="rentalFilter = 'ALL'"
            class="w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-medium transition border"
            :class="rentalFilter === 'ALL' ? 'bg-amberbrown-500 text-white border-amberbrown-500' : 'bg-beige-50/50 dark:bg-darkbeige-900 text-stone-700 dark:text-stone-300 border-beige-200 dark:border-darkbeige-700 hover:bg-beige-100 dark:hover:bg-darkbeige-800'"
          >
            {{ t('results.title') }} ({{ rooms.length }})
          </button>
          <button
            type="button"
            @click="rentalFilter = 'HOURLY'"
            class="w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-medium transition border"
            :class="rentalFilter === 'HOURLY' ? 'bg-amberbrown-500 text-white border-amberbrown-500' : 'bg-beige-50/50 dark:bg-darkbeige-900 text-stone-700 dark:text-stone-300 border-beige-200 dark:border-darkbeige-700 hover:bg-beige-100 dark:hover:bg-darkbeige-800'"
          >
            {{ t('results.hourlyAndDaily') }}
          </button>
          <button
            type="button"
            @click="rentalFilter = 'DAILY'"
            class="w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-medium transition border"
            :class="rentalFilter === 'DAILY' ? 'bg-amberbrown-500 text-white border-amberbrown-500' : 'bg-beige-50/50 dark:bg-darkbeige-900 text-stone-700 dark:text-stone-300 border-beige-200 dark:border-darkbeige-700 hover:bg-beige-100 dark:hover:bg-darkbeige-800'"
          >
            {{ t('results.dailyOnly') }}
          </button>
        </div>

        <p class="text-[11px] text-stone-500 dark:text-stone-400 pt-2 border-t border-beige-200 dark:border-darkbeige-800">
          {{ t('home.showcaseSubtitle') }}
        </p>
      </aside>

      <!-- Right Column: Room Cards -->
      <div class="lg:col-span-8 grid grid-cols-1 gap-6">
        <div
          v-for="room in filteredRooms"
          :key="room.room_type_id"
          class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 shadow-sm transition overflow-hidden flex flex-col md:flex-row"
        >
          <!-- Room Thumbnail / Image (Unslop: no random hover scaling) -->
          <div class="lg:w-80 h-56 lg:h-auto bg-beige-100 dark:bg-darkbeige-900 relative overflow-hidden flex-shrink-0">
            <img
              :src="getRoomImage(room.code)"
              :alt="room.name"
              class="w-full h-full object-cover"
            />
            <div class="absolute top-3 left-3 bg-stone-900/80 backdrop-blur-sm text-white px-2.5 py-1 rounded-md text-xs font-semibold">
              {{ room.code }}
            </div>
            <div class="absolute bottom-3 left-3 bg-emerald-700 text-white px-2.5 py-1 rounded-md text-xs font-semibold shadow">
              {{ t('results.roomsLeft', { count: room.available_rooms }) }}
            </div>
          </div>

          <!-- Room Details -->
          <div class="p-6 flex-1 flex flex-col justify-between">
            <div class="space-y-3">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h4 class="font-display text-xl font-bold text-stone-900 dark:text-white">{{ room.name }}</h4>
                  <p class="text-xs text-stone-500 dark:text-stone-400 flex items-center gap-2 mt-1">
                    <span class="flex items-center space-x-1">
                      <Users class="w-3.5 h-3.5 text-stone-400" />
                      <span>{{ t('results.maxGuests', { count: room.capacity }) }}</span>
                    </span>
                    <span>-</span>
                    <span v-if="room.hourly_allowed" class="text-amberbrown-600 dark:text-amberbrown-400 font-medium flex items-center space-x-1">
                      <Clock class="w-3.5 h-3.5" />
                      <span>{{ t('results.hourlyAndDaily') }}</span>
                    </span>
                    <span v-else class="text-stone-500 dark:text-stone-400 flex items-center space-x-1">
                      <Calendar class="w-3.5 h-3.5 text-stone-400" />
                      <span>{{ t('results.dailyOnly') }}</span>
                    </span>
                  </p>
                </div>
              </div>

              <!-- Description -->
              <p class="text-xs text-stone-600 dark:text-stone-300 leading-relaxed">
                {{ room.description }}
              </p>

              <!-- Amenities Tags -->
              <div v-if="room.amenities" class="flex flex-wrap gap-1.5 pt-1">
                <span
                  v-for="(amenity, idx) in room.amenities.split(',')"
                  :key="idx"
                  class="px-2.5 py-1 bg-beige-100 dark:bg-darkbeige-800 text-stone-700 dark:text-stone-300 text-[11px] rounded-lg font-medium flex items-center space-x-1"
                >
                  <Check class="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                  <span>{{ amenity.trim() }}</span>
                </span>
              </div>
            </div>

            <!-- Pricing & Action Section -->
            <div class="mt-6 pt-4 border-t border-beige-200 dark:border-darkbeige-800 flex flex-col sm:flex-row items-end sm:items-center justify-between gap-4">
              <!-- Price Breakdown -->
              <div class="space-y-1">
                <div class="text-[11px] uppercase tracking-wider font-semibold text-stone-500 dark:text-stone-400">
                  {{ t('pricing.totalWithVat') }}
                </div>
                <!-- Prominent Grand Total -->
                <div class="text-2xl font-black text-amberbrown-600 dark:text-amberbrown-400">
                  <MoneyText :value="room.total_amount" currency="VND" />
                </div>
                <!-- Breakdown note -->
                <div class="text-[11px] text-stone-500 dark:text-stone-400 flex items-center space-x-2">
                  <span>{{ t('pricing.roomAmount') }}: <MoneyText :value="room.room_amount" currency="VND" /></span>
                  <span>+</span>
                  <span>VAT ({{ (room.vat_rate * 100).toFixed(0) }}%): <MoneyText :value="room.vat_amount" currency="VND" /></span>
                </div>
              </div>

              <!-- Booking CTA Button -->
              <button
                @click="goToBooking(room)"
                class="w-full sm:w-auto px-6 py-3 bg-amberbrown-500 hover:bg-amberbrown-600 text-white font-bold text-sm rounded-xl shadow-md transition flex items-center justify-center space-x-2"
              >
                <span>{{ t('results.bookNow') }}</span>
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
import { SlidersHorizontal, AlertCircle, Building2, Users, Clock, Calendar, Check } from 'lucide-vue-next';
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
const rentalFilter = ref('ALL');

const filteredRooms = computed(() => {
  if (rentalFilter.value === 'HOURLY') {
    return rooms.value.filter(r => r.hourly_allowed);
  }
  if (rentalFilter.value === 'DAILY') {
    return rooms.value.filter(r => !r.hourly_allowed);
  }
  return rooms.value;
});

const searchType = computed(() => route.query.type || 'NGAY');
const checkinStr = computed(() => route.query.checkin || '');
const checkoutStr = computed(() => route.query.checkout || '');
const guestsCount = computed(() => route.query.guests || '2');

const formatDateTime = (isoStr) => {
  if (!isoStr) return '';
  const match = isoStr.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  if (match) {
    const [_, y, m, d, hh, mm] = match;
    return `${hh}:${mm} - ${d}/${m}/${y}`;
  }
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
    return `${nights} ${t('pricing.night')} (Check-in 14:00 - Check-out 12:00)`;
  } else {
    return `${diffHours} ${t('pricing.hour')}`;
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
