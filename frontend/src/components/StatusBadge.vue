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
      return 'bg-emerald-100 text-emerald-800 border border-emerald-200';
    case 'DANG_O':
    case 'CHECKED_IN':
      return 'bg-blue-100 text-blue-800 border border-blue-200';
    case 'HOLD':
      return 'bg-amber-100 text-amber-800 border border-amber-200 animate-pulse';
    case 'DANG_DON':
      return 'bg-purple-100 text-purple-800 border border-purple-200';
    case 'BAO_TRI':
    case 'CANCELLED':
    case 'EXPIRED':
      return 'bg-red-100 text-red-800 border border-red-200';
    case 'CHECKED_OUT':
    case 'NO_SHOW':
      return 'bg-gray-100 text-gray-800 border border-gray-200';
    default:
      return 'bg-slate-100 text-slate-800 border border-slate-200';
  }
});
</script>
