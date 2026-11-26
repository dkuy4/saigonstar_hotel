<template>
  <div class="max-w-xl mx-auto py-10 px-4">
    <div class="bg-white dark:bg-darkbeige-850 rounded-2xl shadow-xl border border-beige-300 dark:border-darkbeige-800 overflow-hidden transition-colors">
      <!-- Header -->
      <div class="bg-amberbrown-500 text-white p-6 text-center">
        <h1 class="font-display text-2xl font-bold tracking-tight">{{ t('mockPay.title') }}</h1>
        <p class="text-beige-100 text-xs mt-1 uppercase tracking-wider font-semibold">{{ t('mockPay.subtitle') }}</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="p-12 text-center text-stone-500">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-amberbrown-500 border-t-transparent mb-3"></div>
        <p class="text-sm">{{ t('mockPay.loading') }}</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="p-8 text-center">
        <h3 class="font-display text-lg font-bold text-stone-900 dark:text-white mb-2">{{ t('mockPay.error') }}</h3>
        <p class="text-stone-600 dark:text-stone-400 text-sm mb-6">{{ error }}</p>
        <router-link to="/" class="px-5 py-2.5 bg-amberbrown-500 text-white rounded-xl text-sm font-medium hover:bg-amberbrown-600 transition">
          {{ t('mockPay.backHome') }}
        </router-link>
      </div>

      <!-- Content -->
      <div v-else-if="info" class="p-6">
        <!-- Amount Banner -->
        <div class="bg-amberbrown-50 dark:bg-darkbeige-900 border border-amberbrown-200 dark:border-darkbeige-700 rounded-xl p-4 text-center mb-6">
          <div class="text-xs text-amberbrown-700 dark:text-amberbrown-300 font-semibold uppercase tracking-wider">{{ t('mockPay.amount') }}</div>
          <div class="text-3xl font-extrabold text-amberbrown-900 dark:text-amberbrown-100 mt-1">
            <MoneyText :amount="info.so_tien || info.amount" />
          </div>
        </div>

        <!-- Details -->
        <div class="space-y-3 mb-6 text-sm">
          <div class="flex justify-between py-2 border-b border-beige-200 dark:border-darkbeige-800">
            <span class="text-stone-500 dark:text-stone-400">{{ t('mockPay.refCode') }}</span>
            <span class="font-mono font-medium text-stone-800 dark:text-stone-200">{{ info.reference_code }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-beige-200 dark:border-darkbeige-800">
            <span class="text-stone-500 dark:text-stone-400">{{ t('mockPay.bookingCode') }}</span>
            <span class="font-mono font-bold text-amberbrown-600 dark:text-amberbrown-400">{{ info.ma_dat_phong }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-beige-200 dark:border-darkbeige-800">
            <span class="text-stone-500 dark:text-stone-400">{{ t('mockPay.customer') }}</span>
            <span class="font-medium text-stone-800 dark:text-stone-200">{{ info.ten_khach || t('myTrips.roomFallback') }}</span>
          </div>
          <div class="flex justify-between py-2">
            <span class="text-stone-500 dark:text-stone-400">{{ t('mockPay.status') }}</span>
            <span class="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
              {{ info.trang_thai }}
            </span>
          </div>
        </div>

        <div class="bg-beige-50/70 dark:bg-darkbeige-900 rounded-xl p-4 mb-6 border border-beige-200 dark:border-darkbeige-800">
          <p class="text-xs text-stone-500 dark:text-stone-400 leading-relaxed">
            {{ t('mockPay.sandboxNote') }}
          </p>
        </div>

        <!-- Action Buttons -->
        <div class="space-y-3">
          <button
            @click="submitPayment(true)"
            :disabled="processing"
            class="w-full py-3.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl shadow transition flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            <div v-if="processing" class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
            <span>{{ t('mockPay.paySuccessBtn') }}</span>
          </button>

          <button
            @click="submitPayment(false)"
            :disabled="processing"
            class="w-full py-3.5 px-4 bg-beige-200 dark:bg-darkbeige-800 hover:bg-beige-300 dark:hover:bg-darkbeige-700 text-stone-700 dark:text-stone-300 font-semibold rounded-xl transition flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            <span>{{ t('mockPay.payFailBtn') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import apiClient from '../api/client';
import MoneyText from '../components/MoneyText.vue';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const info = ref(null);
const loading = ref(true);
const processing = ref(false);
const error = ref('');

const fetchInfo = async () => {
  loading.value = true;
  try {
    const res = await apiClient.get(`/payments/mock-info/${route.params.ref}`);
    info.value = res;
  } catch (err) {
    error.value = err.message || t('mockPay.error');
  } finally {
    loading.value = false;
  }
};

const submitPayment = async (isSuccess) => {
  processing.value = true;
  try {
    const res = await apiClient.post('/payments/mock-submit', {
      reference_code: info.value.reference_code,
      success: isSuccess
    });
    router.push({
      path: '/thanh-toan/ket-qua',
      query: {
        result: res.code,
        booking_code: res.booking_code,
        ref: info.value.reference_code
      }
    });
  } catch (err) {
    alert(err.message || t('errors.INTERNAL_SERVER_ERROR'));
  } finally {
    processing.value = false;
  }
};

onMounted(fetchInfo);
</script>
