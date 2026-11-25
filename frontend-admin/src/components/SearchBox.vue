<template>
  <div class="bg-white rounded-2xl shadow-xl border border-slate-200/80 p-6 md:p-8">
    <!-- Mode Selection Tabs -->
    <div class="flex items-center space-x-2 border-b border-slate-200 pb-4 mb-6">
      <button
        type="button"
        @click="searchType = 'NGAY'"
        class="flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium text-sm transition"
        :class="searchType === 'NGAY' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
      >
        <Calendar class="w-4 h-4" />
        <span>{{ t('search.daily') }}</span>
      </button>

      <button
        type="button"
        @click="searchType = 'GIO'"
        class="flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium text-sm transition"
        :class="searchType === 'GIO' ? 'bg-sky-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
      >
        <Clock class="w-4 h-4" />
        <span>{{ t('search.hourly') }}</span>
      </button>
    </div>

    <!-- Form -->
    <form @submit.prevent="handleSubmit" class="space-y-6">
      <!-- Daily Fields -->
      <div v-if="searchType === 'NGAY'" class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Checkin Date -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">
            {{ t('search.checkinDate') }} (14:00)
          </label>
          <input
            v-model="dailyCheckinDate"
            type="date"
            :min="todayStr"
            required
            class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none shadow-sm"
          />
        </div>

        <!-- Checkout Date -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">
            {{ t('search.checkoutDate') }} (12:00)
          </label>
          <input
            v-model="dailyCheckoutDate"
            type="date"
            :min="dailyCheckinDate || todayStr"
            required
            class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none shadow-sm"
          />
        </div>

        <!-- Guests -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">
            {{ t('search.guests') }}
          </label>
          <select
            v-model="guests"
            class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none shadow-sm"
          >
            <option :value="1">{{ t('search.guestsCount', { count: 1 }) }}</option>
            <option :value="2">{{ t('search.guestsCount', { count: 2 }) }}</option>
            <option :value="3">{{ t('search.guestsCount', { count: 3 }) }}</option>
            <option :value="4">{{ t('search.guestsCount', { count: 4 }) }}</option>
          </select>
        </div>
      </div>

      <!-- Hourly Fields -->
      <div v-else class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <!-- Hourly Date -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              {{ t('search.hourlyDate') }}
            </label>
            <input
              v-model="hourlyDate"
              type="date"
              :min="todayStr"
              required
              class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none shadow-sm"
            />
          </div>

          <!-- Hourly Start Time (15-min interval) -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              {{ t('search.checkinTime') }} ({{ t('search.step15m') }})
            </label>
            <select
              v-model="hourlyTime"
              required
              class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none shadow-sm"
            >
              <option v-for="tSlot in timeSlots" :key="tSlot" :value="tSlot">
                {{ tSlot }}
              </option>
            </select>
          </div>

          <!-- Duration Hours -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              {{ t('search.durationHours') }}
            </label>
            <select
              v-model="hourlyDuration"
              class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none shadow-sm"
            >
              <option :value="1">{{ t('search.hourCount', { count: 1 }) }}</option>
              <option :value="2">{{ t('search.hourCount', { count: 2 }) }}</option>
              <option :value="3">{{ t('search.hourCount', { count: 3 }) }} (240.000 ₫)</option>
              <option :value="4">{{ t('search.hourCount', { count: 4 }) }} (320.000 ₫)</option>
              <option :value="5">{{ t('search.hourCount', { count: 5 }) }} (400.000 ₫)</option>
              <option :value="6">{{ t('search.hourCount', { count: 6 }) }} ({{ t('search.dailyCap', { price: '550.000 ₫' }) }})</option>
              <option :value="8">{{ t('search.hourCount', { count: 8 }) }} (550.000 ₫)</option>
              <option :value="12">{{ t('search.hourCount', { count: 12 }) }} (550.000 ₫)</option>
              <option :value="24">{{ t('search.hourCount', { count: 24 }) }} (550.000 ₫)</option>
            </select>
          </div>

          <!-- Guests -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              {{ t('search.guests') }}
            </label>
            <select
              v-model="guests"
              class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none shadow-sm"
            >
              <option :value="1">{{ t('search.guestsCount', { count: 1 }) }}</option>
              <option :value="2">{{ t('search.guestsCount', { count: 2 }) }} ({{ t('search.maxGuests') }})</option>
            </select>
          </div>
        </div>

        <div class="text-xs text-amber-800 bg-amber-50 border border-amber-200 px-3.5 py-2.5 rounded-xl flex items-center space-x-2.5">
          <Info class="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>{{ t('search.hourlyNote', { rank: 'Standard' }) }}</span>
        </div>
      </div>

      <!-- Action Button -->
      <div class="flex justify-end pt-2">
        <button
          type="submit"
          class="w-full md:w-auto px-8 py-3 bg-sky-600 hover:bg-sky-700 text-white font-semibold text-sm rounded-xl shadow-md hover:shadow-lg transition flex items-center justify-center space-x-2"
        >
          <Search class="w-4 h-4" />
          <span>{{ t('search.searchButton') }}</span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { Calendar, Clock, Search, Info } from 'lucide-vue-next';

const { t } = useI18n();
const router = useRouter();

const props = defineProps({
  initialType: { type: String, default: 'NGAY' },
  initialCheckin: { type: String, default: '' },
  initialCheckout: { type: String, default: '' },
  initialGuests: { type: Number, default: 2 }
});

const searchType = ref(props.initialType);
const guests = ref(props.initialGuests || 2);

// Dates calculation
const now = new Date();
const pad = (n) => String(n).padStart(2, '0');
const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

const tomorrow = new Date(now);
tomorrow.setDate(now.getDate() + 1);
const tomorrowStr = `${tomorrow.getFullYear()}-${pad(tomorrow.getMonth() + 1)}-${pad(tomorrow.getDate())}`;

const nextTwoDays = new Date(now);
nextTwoDays.setDate(now.getDate() + 3);
const nextTwoDaysStr = `${nextTwoDays.getFullYear()}-${pad(nextTwoDays.getMonth() + 1)}-${pad(nextTwoDays.getDate())}`;

// Extract YYYY-MM-DD from ISO or date string
const parseDatePart = (str, fallback) => {
  if (!str) return fallback;
  const match = str.match(/^\d{4}-\d{2}-\d{2}/);
  return match ? match[0] : fallback;
};

// Daily fields (initialized with props if provided)
const dailyCheckinDate = ref(parseDatePart(props.initialCheckin, tomorrowStr));
const dailyCheckoutDate = ref(parseDatePart(props.initialCheckout, nextTwoDaysStr));

// Hourly fields
const hourlyDate = ref(parseDatePart(props.initialCheckin, tomorrowStr));
const hourlyTime = ref(props.initialCheckin && props.initialCheckin.includes('T') ? props.initialCheckin.split('T')[1].substring(0, 5) : '10:00');
const hourlyDuration = ref(3);

// Generate 15-minute time slots
const timeSlots = computed(() => {
  const slots = [];
  for (let h = 0; h < 24; h++) {
    for (let m = 0; m < 60; m += 15) {
      slots.push(`${pad(h)}:${pad(m)}`);
    }
  }
  return slots;
});

const handleSubmit = () => {
  let checkinIso = '';
  let checkoutIso = '';

  if (searchType.value === 'NGAY') {
    // 14:00 checkin, 12:00 checkout (+07:00)
    checkinIso = `${dailyCheckinDate.value}T14:00:00+07:00`;
    checkoutIso = `${dailyCheckoutDate.value}T12:00:00+07:00`;
  } else {
    // Hourly calculation
    const [h, m] = hourlyTime.value.split(':').map(Number);
    const startDate = new Date(`${hourlyDate.value}T${pad(h)}:${pad(m)}:00`);
    const endDate = new Date(startDate.getTime() + hourlyDuration.value * 3600 * 1000);

    const formatOffsetIso = (d) => {
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00+07:00`;
    };

    checkinIso = formatOffsetIso(startDate);
    checkoutIso = formatOffsetIso(endDate);
  }

  router.push({
    path: '/ket-qua',
    query: {
      type: searchType.value,
      checkin: checkinIso,
      checkout: checkoutIso,
      guests: guests.value
    }
  });
};
</script>
