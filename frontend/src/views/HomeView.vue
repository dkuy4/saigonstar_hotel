<template>
  <div class="space-y-10">
    <!-- Hero Banner with Integrated Search -->
    <div class="relative rounded-3xl overflow-hidden bg-stone-950 text-white shadow-2xl">
      <!-- Background Image with Overlay -->
      <div class="absolute inset-0 z-0 opacity-40">
        <img
          src="https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1600&q=80"
          alt="Hotel Luxury"
          class="w-full h-full object-cover"
        />
      </div>
      <div class="absolute inset-0 bg-gradient-to-t from-stone-950 via-stone-900/60 to-transparent z-0"></div>

      <!-- Hero Content -->
      <div class="relative z-10 px-6 py-12 md:py-16 max-w-4xl mx-auto text-center space-y-4">
        <span class="inline-flex items-center space-x-1.5 px-3.5 py-1 rounded-full text-xs font-semibold bg-amberbrown-500/20 text-amber-200 border border-amberbrown-400/30 backdrop-blur-md">
          <Star class="w-3.5 h-3.5 fill-amber-300 text-amber-300" />
          <span>{{ t('home.badge') }}</span>
        </span>
        <h2 class="font-display text-3xl md:text-5xl font-bold tracking-tight text-white leading-tight">
          {{ t('search.title') }}
        </h2>
        <p class="text-sm md:text-base text-stone-300 max-w-2xl mx-auto font-light leading-relaxed">
          {{ t('search.subtitle') }}
        </p>

        <!-- Floating Search Box -->
        <div class="pt-6 text-left">
          <SearchBox />
        </div>
      </div>
    </div>

    <!-- Featured Room Types Showcase -->
    <div class="space-y-6">
      <div class="flex items-end justify-between">
        <div>
          <h3 class="font-display text-2xl font-bold text-stone-900 dark:text-white tracking-tight">{{ t('home.showcaseTitle') }}</h3>
          <p class="text-xs text-stone-500 dark:text-stone-400 mt-1">{{ t('home.showcaseSubtitle') }}</p>
        </div>
      </div>

      <!-- Loading Skeletons -->
      <div v-if="loadingRoomTypes" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div v-for="i in 4" :key="i" class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 shadow-sm overflow-hidden flex flex-col justify-between animate-pulse">
          <div>
            <div class="h-44 bg-stone-200 dark:bg-darkbeige-800"></div>
            <div class="p-5 space-y-3">
              <div class="h-5 bg-stone-200 dark:bg-darkbeige-800 rounded w-3/4"></div>
              <div class="space-y-1.5">
                <div class="h-3 bg-stone-200 dark:bg-darkbeige-800 rounded w-full"></div>
                <div class="h-3 bg-stone-200 dark:bg-darkbeige-800 rounded w-5/6"></div>
              </div>
              <div class="h-3.5 bg-stone-200 dark:bg-darkbeige-800 rounded w-1/3 pt-1"></div>
            </div>
          </div>
          <div class="p-5 pt-0 border-t border-beige-200 dark:border-darkbeige-800 mt-3 flex items-center justify-between">
            <div class="space-y-1">
              <div class="h-2.5 bg-stone-200 dark:bg-darkbeige-800 rounded w-12"></div>
              <div class="h-4 bg-stone-200 dark:bg-darkbeige-800 rounded w-20"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Loaded Room Cards -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div
          v-for="rt in roomTypes"
          :key="rt.id"
          class="bg-white dark:bg-darkbeige-850 rounded-2xl border border-beige-300 dark:border-darkbeige-800 shadow-sm transition overflow-hidden flex flex-col justify-between"
        >
          <div>
            <!-- Room Image (Unslop: no random hover scaling) -->
            <div class="h-44 bg-beige-100 dark:bg-darkbeige-900 relative overflow-hidden">
              <img :src="getRoomImage(rt.code)" :alt="rt.name" class="w-full h-full object-cover" />
              <div class="absolute top-3 left-3 bg-stone-900/80 backdrop-blur-sm text-white px-2 py-0.5 rounded text-[11px] font-semibold">
                {{ rt.code }}
              </div>
              <div v-if="rt.hourly_allowed" class="absolute bottom-3 right-3 bg-stone-900/80 backdrop-blur-sm text-white px-2 py-0.5 rounded text-[11px] font-semibold shadow flex items-center space-x-1">
                <Clock class="w-3 h-3 text-amber-300" />
                <span>{{ t('home.hourlyAllowed') }}</span>
              </div>
            </div>

            <div class="p-5 space-y-2.5">
              <h4 class="font-display font-bold text-base text-stone-900 dark:text-white">{{ rt.name }}</h4>
              <p class="text-xs text-stone-500 dark:text-stone-400 line-clamp-3 leading-relaxed">
                {{ rt.description }}
              </p>
              <div class="text-[11px] text-stone-600 dark:text-stone-300 font-medium pt-1 flex items-center space-x-1.5">
                <Users class="w-3.5 h-3.5 text-stone-400" />
                <span>{{ t('home.capacity', { count: rt.capacity }) }}</span>
              </div>
            </div>
          </div>

          <div class="p-5 pt-0 border-t border-beige-200 dark:border-darkbeige-800 mt-3 flex items-center justify-between">
            <div>
              <span class="text-[10px] text-stone-400 dark:text-stone-500 uppercase font-semibold block">{{ t('home.dailyPrice') }}</span>
              <span class="text-base font-bold text-amberbrown-600 dark:text-amberbrown-400">
                <MoneyText :amount="rt.daily_price || defaultDailyPrices[rt.code]" currency="VND" />
              </span>
              <span class="text-[10px] text-stone-400 dark:text-stone-500">{{ t('home.perNight') }}</span>
            </div>
            <div v-if="rt.hourly_price || rt.hourly_allowed" class="text-right">
              <span class="text-[10px] text-stone-400 dark:text-stone-500 uppercase font-semibold block">{{ t('home.hourlyPrice') }}</span>
              <span class="text-sm font-semibold text-amber-700 dark:text-amber-300">
                <MoneyText :amount="rt.hourly_price || defaultHourlyPrices[rt.code] || 80000" currency="VND" />
              </span>
              <span class="text-[10px] text-stone-400 dark:text-stone-500">{{ t('home.perHour') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Star, Clock, Users } from 'lucide-vue-next';
import apiClient from '../api/client';
import SearchBox from '../components/SearchBox.vue';
import MoneyText from '../components/MoneyText.vue';

const { t, locale } = useI18n();

const roomTypes = ref([]);
const loadingRoomTypes = ref(true);

const defaultDailyPrices = {
  STANDARD: 550000,
  SUPERIOR: 950000,
  DELUXE: 1450000,
  SUITE: 1950000
};

const defaultHourlyPrices = {
  STANDARD: 80000,
  SUPERIOR: 0,
  DELUXE: 0,
  SUITE: 0
};

const getRoomImage = (code) => {
  const images = {
    STANDARD: 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80',
    SUPERIOR: 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80',
    DELUXE: 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80',
    SUITE: 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80'
  };
  return images[code] || images.STANDARD;
};

const loadRoomTypes = async () => {
  loadingRoomTypes.value = true;
  try {
    const res = await apiClient.get('/room-types', {
      params: { lang: locale.value }
    });
    roomTypes.value = res || [];
  } catch (err) {
    console.error('Failed to load room types:', err);
  } finally {
    loadingRoomTypes.value = false;
  }
};

onMounted(loadRoomTypes);
watch(() => locale.value, loadRoomTypes);
</script>
