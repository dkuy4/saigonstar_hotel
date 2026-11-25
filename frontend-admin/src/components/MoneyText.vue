<template>
  <span class="font-medium tabular-nums">{{ formattedMoney }}</span>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  amount: {
    type: [Number, String],
    default: null
  },
  value: {
    type: [Number, String],
    default: null
  },
  currency: {
    type: String,
    default: 'VND'
  }
});

const formattedMoney = computed(() => {
  const raw = props.amount !== null && props.amount !== undefined ? props.amount : props.value;
  const num = Number(raw) || 0;
  if (props.currency === 'VND') {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(num);
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: props.currency
  }).format(num);
});
</script>
