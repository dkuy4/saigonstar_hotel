<template>
  <div class="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
    <div class="font-display text-5xl font-bold text-amberbrown-500 mb-2">
      404
    </div>
    <h2 class="font-display text-2xl font-bold text-stone-900 dark:text-white tracking-tight">{{ t('notFound.title') }}</h2>
    <p class="text-sm text-stone-500 dark:text-stone-400 mt-2 max-w-md">
      {{ t('notFound.sub') }}
    </p>
    <router-link
      to="/"
      class="mt-6 inline-flex items-center px-5 py-2.5 text-sm font-semibold rounded-xl text-white bg-amberbrown-500 hover:bg-amberbrown-600 transition shadow-sm"
    >
      {{ t('notFound.backHome') }}
    </router-link>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>
