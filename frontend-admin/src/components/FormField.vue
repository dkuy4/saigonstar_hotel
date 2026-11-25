<template>
  <div class="space-y-1">
    <label v-if="label" class="block text-sm font-medium text-slate-700">
      {{ label }}
      <span v-if="required" class="text-rose-500">*</span>
    </label>
    <slot />
    <p v-if="error" class="text-xs text-rose-600 mt-1">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-slate-500 mt-1">{{ hint }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  hint: {
    type: String,
    default: ''
  }
});
</script>
