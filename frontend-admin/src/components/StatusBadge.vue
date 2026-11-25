<template>
  <span :class="badgeClasses" class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-tight border">
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
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    case 'DANG_O':
    case 'CHECKED_IN':
      return 'bg-sky-50 text-sky-700 border-sky-200';
    case 'HOLD':
      return 'bg-amber-50 text-amber-700 border-amber-200';
    case 'DANG_DON':
      return 'bg-purple-50 text-purple-700 border-purple-200';
    case 'BAO_TRI':
    case 'CANCELLED':
    case 'EXPIRED':
      return 'bg-rose-50 text-rose-700 border-rose-200';
    case 'CHECKED_OUT':
    case 'NO_SHOW':
      return 'bg-slate-50 text-slate-600 border-slate-200';
    default:
      return 'bg-slate-50 text-slate-700 border-slate-200';
  }
});
</script>
