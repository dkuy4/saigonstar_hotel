<template>
  <span :class="badgeClasses" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  status: {
    type: String,
    required: true
  }
});

const { t, te } = useI18n();

const label = computed(() => {
  const key = `status.${props.status}`;
  return te(key) ? t(key) : props.status;
});

const badgeClasses = computed(() => {
  switch (props.status) {
    case 'TRONG':
    case 'CONFIRMED':
      return 'bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-200 dark:border-emerald-800';
    case 'DANG_O':
    case 'CHECKED_IN':
      return 'bg-blue-100 text-blue-800 border border-blue-300 dark:bg-blue-950/40 dark:text-blue-200 dark:border-blue-800';
    case 'HOLD':
      return 'bg-amber-100 text-amber-800 border border-amber-300 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800';
    case 'DANG_DON':
      return 'bg-purple-100 text-purple-800 border border-purple-300 dark:bg-purple-950/40 dark:text-purple-200 dark:border-purple-800';
    case 'BAO_TRI':
    case 'CANCELLED':
    case 'EXPIRED':
      return 'bg-rose-100 text-rose-800 border border-rose-300 dark:bg-rose-950/40 dark:text-rose-200 dark:border-rose-800';
    case 'CHECKED_OUT':
    case 'NO_SHOW':
      return 'bg-stone-100 text-stone-700 border border-stone-300 dark:bg-darkbeige-800 dark:text-stone-300 dark:border-darkbeige-700';
    default:
      return 'bg-stone-100 text-stone-700 border border-stone-300 dark:bg-darkbeige-800 dark:text-stone-300 dark:border-darkbeige-700';
  }
});
</script>
