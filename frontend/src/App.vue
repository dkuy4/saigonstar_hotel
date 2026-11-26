<template>
  <AppLayout>
    <router-view />
  </AppLayout>
</template>

<script setup>
import { onMounted } from 'vue';
import AppLayout from './components/AppLayout.vue';
import { useThemeStore } from './stores/theme';

const themeStore = useThemeStore();
onMounted(() => {
  themeStore.initTheme();
});
</script>
