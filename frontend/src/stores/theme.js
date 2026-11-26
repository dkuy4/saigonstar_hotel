import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useThemeStore = defineStore('theme', () => {
  // Check localStorage or system prefers-color-scheme
  const savedTheme = localStorage.getItem('hotel_theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = ref(savedTheme ? savedTheme === 'dark' : prefersDark);

  const applyTheme = (dark) => {
    isDark.value = dark;
    if (dark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('hotel_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('hotel_theme', 'light');
    }
  };

  const toggleTheme = () => {
    applyTheme(!isDark.value);
  };

  const initTheme = () => {
    applyTheme(isDark.value);
    // Listen for system changes if user hasn't explicitly set a preference
    if (!savedTheme && window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('hotel_theme')) {
          applyTheme(e.matches);
        }
      });
    }
  };

  return {
    isDark,
    toggleTheme,
    applyTheme,
    initTheme
  };
});
