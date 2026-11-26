<template>
  <div class="max-w-xl mx-auto py-12 px-4">
    <div class="bg-white dark:bg-darkbeige-850 rounded-2xl shadow-xl border border-beige-300 dark:border-darkbeige-800 p-8 text-center transition-colors">
      
      <!-- 1. XAC_NHAN -->
      <div v-if="result === 'XAC_NHAN'">
        <h2 class="font-display text-2xl font-bold text-stone-900 dark:text-white mb-2">{{ t('paymentResult.successTitle') }}</h2>
        <p class="text-stone-600 dark:text-stone-400 text-sm mb-6 leading-relaxed">
          {{ t('paymentResult.successSub') }}
        </p>
      </div>

      <!-- 2. XAC_NHAN_MUON -->
      <div v-else-if="result === 'XAC_NHAN_MUON'">
        <h2 class="font-display text-2xl font-bold text-stone-900 dark:text-white mb-2">{{ t('paymentResult.lateSuccessTitle') }}</h2>
        <p class="text-stone-600 dark:text-stone-400 text-sm mb-6 leading-relaxed">
          {{ t('paymentResult.lateSuccessSub') }}
        </p>
      </div>

      <!-- 3. HOAN_TIEN -->
      <div v-else-if="result === 'HOAN_TIEN'">
        <h2 class="font-display text-2xl font-bold text-stone-900 dark:text-white mb-2">{{ t('paymentResult.refundTitle') }}</h2>
        <p class="text-stone-600 dark:text-stone-400 text-sm mb-6 leading-relaxed">
          {{ t('paymentResult.refundSub') }}
        </p>
      </div>

      <!-- 4. THAT_BAI -->
      <div v-else-if="result === 'THAT_BAI'">
        <h2 class="font-display text-2xl font-bold text-rose-600 dark:text-rose-400 mb-2">{{ t('paymentResult.failedTitle') }}</h2>
        <p class="text-stone-600 dark:text-stone-400 text-sm mb-6 leading-relaxed">
          {{ t('paymentResult.failedSub') }}
        </p>
      </div>

      <!-- 5. DA_XU_LY -->
      <div v-else>
        <h2 class="font-display text-2xl font-bold text-stone-900 dark:text-white mb-2">{{ t('paymentResult.recordedTitle') }}</h2>
        <p class="text-stone-600 dark:text-stone-400 text-sm mb-6 leading-relaxed">
          {{ t('paymentResult.recordedSub') }}
        </p>
      </div>

      <!-- Details Block -->
      <div v-if="bookingCode || refCode" class="bg-beige-50/70 dark:bg-darkbeige-900 rounded-xl p-4 text-left text-sm mb-6 space-y-2 border border-beige-200 dark:border-darkbeige-800">
        <div v-if="bookingCode" class="flex justify-between">
          <span class="text-stone-500 dark:text-stone-400">{{ t('paymentResult.bookingCode') }}</span>
          <span class="font-mono font-bold text-amberbrown-600 dark:text-amberbrown-400">{{ bookingCode }}</span>
        </div>
        <div v-if="refCode" class="flex justify-between">
          <span class="text-stone-500 dark:text-stone-400">{{ t('paymentResult.refCode') }}</span>
          <span class="font-mono text-stone-700 dark:text-stone-300">{{ refCode }}</span>
        </div>
      </div>

      <!-- Navigation Actions -->
      <div class="flex flex-col sm:flex-row gap-3 justify-center">
        <router-link
          v-if="bookingCode && result !== 'THAT_BAI'"
          :to="`/don/${bookingCode}`"
          class="px-6 py-3 bg-amberbrown-500 hover:bg-amberbrown-600 text-white font-medium rounded-xl shadow transition"
        >
          {{ t('paymentResult.viewDetail') }}
        </router-link>

        <router-link
          to="/"
          class="px-6 py-3 bg-beige-200 dark:bg-darkbeige-800 hover:bg-beige-300 dark:hover:bg-darkbeige-700 text-stone-700 dark:text-stone-200 font-medium rounded-xl transition"
        >
          {{ t('paymentResult.home') }}
        </router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const route = useRoute();

const result = computed(() => route.query.result || 'UNKNOWN');
const bookingCode = computed(() => route.query.booking_code || '');
const refCode = computed(() => route.query.ref || '');
</script>
