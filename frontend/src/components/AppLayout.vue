<template>
  <div class="min-h-screen flex flex-col bg-beige-100 dark:bg-darkbeige-950 text-stone-900 dark:text-stone-100 antialiased font-sans transition-colors duration-200">
    <!-- Top Header for Guests (Quiet Chrome, Unslop) -->
    <header class="bg-white/95 dark:bg-darkbeige-900/95 backdrop-blur-sm border-b border-beige-300 dark:border-darkbeige-800 sticky top-0 z-30 shadow-sm transition-colors duration-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Logo / Brand -->
        <router-link to="/" class="flex items-center space-x-3 text-stone-900 dark:text-white group">
          <div class="w-9 h-9 rounded-xl bg-amberbrown-500 flex items-center justify-center text-white shadow-sm group-hover:bg-amberbrown-600 transition">
            <Star class="w-4 h-4 fill-white" />
          </div>
          <div>
            <h1 class="font-display font-bold text-lg leading-tight tracking-tight text-stone-900 dark:text-white">SaigonStar</h1>
            <p class="hidden sm:block text-[11px] text-stone-500 dark:text-stone-400 font-normal">{{ t('app.subtitle') }}</p>
          </div>
        </router-link>

        <!-- Guest Navigation Links -->
        <nav class="hidden md:flex items-center space-x-1">
          <router-link
            to="/"
            class="px-3 py-2 rounded-xl text-xs font-medium transition"
            :class="$route.path === '/' ? 'text-amberbrown-600 dark:text-amberbrown-300 bg-amberbrown-50 dark:bg-darkbeige-800 font-semibold' : 'text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white hover:bg-beige-200/50 dark:hover:bg-darkbeige-800'"
          >
            {{ t('nav.search') }}
          </router-link>

          <router-link
            v-if="guestAuth.isLoggedIn"
            to="/chuyen-di-cua-toi"
            class="px-3 py-2 rounded-xl text-xs font-medium transition"
            :class="$route.path.includes('chuyen-di') ? 'text-amberbrown-600 dark:text-amberbrown-300 bg-amberbrown-50 dark:bg-darkbeige-800 font-semibold' : 'text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white hover:bg-beige-200/50 dark:hover:bg-darkbeige-800'"
          >
            {{ t('nav.myTrips') }}
          </router-link>

          <router-link
            to="/don/tra-cuu"
            class="px-3 py-2 rounded-xl text-xs font-medium transition"
            :class="$route.path.startsWith('/don') ? 'text-amberbrown-600 dark:text-amberbrown-300 bg-amberbrown-50 dark:bg-darkbeige-800 font-semibold' : 'text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white hover:bg-beige-200/50 dark:hover:bg-darkbeige-800'"
          >
            {{ t('nav.lookup') }}
          </router-link>
        </nav>

        <!-- Right Actions: Language Selector + Theme Toggle + Guest Account + Link to Staff Portal -->
        <div class="flex items-center space-x-2.5">
          <!-- Dark / Light Mode Toggle Button -->
          <button
            @click="themeStore.toggleTheme"
            class="p-2 text-stone-600 dark:text-stone-300 hover:bg-beige-200/60 dark:hover:bg-darkbeige-800 rounded-xl border border-beige-300 dark:border-darkbeige-800 transition"
            :title="themeStore.isDark ? (locale === 'vi' ? 'Chuyển sang giao diện Sáng' : 'Switch to Light mode') : (locale === 'vi' ? 'Chuyển sang giao diện Tối' : 'Switch to Dark mode')"
          >
            <Sun v-if="themeStore.isDark" class="w-4 h-4 text-amber-400" />
            <Moon v-else class="w-4 h-4 text-stone-600" />
          </button>

          <!-- 7 Languages Selector -->
          <select
            v-model="currentLang"
            @change="changeLanguage"
            class="bg-white dark:bg-darkbeige-800 border border-beige-300 dark:border-darkbeige-700 text-stone-700 dark:text-stone-200 text-xs rounded-xl px-2.5 py-1.5 focus:ring-2 focus:ring-amberbrown-500 outline-none"
          >
            <option value="vi">🇻🇳 Tiếng Việt</option>
            <option value="en">🇬🇧 English</option>
            <option value="zh-CN">🇨🇳 中文</option>
            <option value="ko">🇰🇷 한국어</option>
            <option value="ja">🇯🇵 日本語</option>
            <option value="es">🇪🇸 Español</option>
            <option value="fr">🇫🇷 Français</option>
          </select>

          <!-- Guest Account Area -->
          <template v-if="guestAuth.isLoggedIn">
            <div class="flex items-center space-x-2 border-l border-beige-300 dark:border-darkbeige-800 pl-2.5">
              <router-link
                to="/chuyen-di-cua-toi"
                class="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl hover:bg-beige-200/60 dark:hover:bg-darkbeige-800 text-xs font-medium text-stone-800 dark:text-stone-200 transition"
              >
                <User class="w-3.5 h-3.5 text-amberbrown-500" />
                <span class="max-w-[120px] truncate">{{ guestAuth.guestName }}</span>
              </router-link>
              <button
                @click="handleLogout"
                class="px-2.5 py-1.5 text-xs text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 rounded-xl transition font-medium"
                :title="t('nav.logout')"
              >
                {{ t('nav.logout') }}
              </button>
            </div>
          </template>

          <template v-else>
            <div class="flex items-center space-x-1.5 border-l border-beige-300 dark:border-darkbeige-800 pl-2.5">
              <router-link
                to="/dang-nhap"
                class="px-3 py-1.5 text-xs font-medium text-stone-700 dark:text-stone-200 hover:text-stone-900 dark:hover:text-white hover:bg-beige-200/60 dark:hover:bg-darkbeige-800 rounded-xl transition"
              >
                {{ t('nav.login') }}
              </router-link>
              <router-link
                to="/dang-ky"
                class="px-3 py-1.5 text-xs font-semibold text-white bg-amberbrown-500 hover:bg-amberbrown-600 rounded-xl shadow-sm transition"
              >
                {{ t('nav.register') }}
              </router-link>
            </div>
          </template>
        </div>
      </div>

      <!-- Mobile Navigation Bar -->
      <nav class="md:hidden border-t border-beige-200 dark:border-darkbeige-800 px-4 py-2 flex items-center justify-around bg-beige-50/80 dark:bg-darkbeige-900/80">
        <router-link
          to="/"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition"
          :class="$route.path === '/' ? 'text-amberbrown-600 dark:text-amberbrown-300 bg-amberbrown-50 dark:bg-darkbeige-800 font-semibold' : 'text-stone-600 dark:text-stone-300'"
        >
          {{ t('nav.search') }}
        </router-link>

        <router-link
          v-if="guestAuth.isLoggedIn"
          to="/chuyen-di-cua-toi"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition"
          :class="$route.path.includes('chuyen-di') ? 'text-amberbrown-600 dark:text-amberbrown-300 bg-amberbrown-50 dark:bg-darkbeige-800 font-semibold' : 'text-stone-600 dark:text-stone-300'"
        >
          {{ t('nav.myTrips') }}
        </router-link>

        <router-link
          to="/don/tra-cuu"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition"
          :class="$route.path.startsWith('/don') ? 'text-amberbrown-600 dark:text-amberbrown-300 bg-amberbrown-50 dark:bg-darkbeige-800 font-semibold' : 'text-stone-600 dark:text-stone-300'"
        >
          {{ t('nav.lookup') }}
        </router-link>
      </nav>
    </header>

    <!-- Main Content Slot -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="bg-white dark:bg-darkbeige-900 border-t border-beige-300 dark:border-darkbeige-800 py-8 text-center text-xs text-stone-500 dark:text-stone-400 transition-colors duration-200">
      <div class="max-w-7xl mx-auto px-4 space-y-2">
        <div class="flex items-center justify-center space-x-2 text-stone-800 dark:text-stone-200 font-medium">
          <Star class="w-4 h-4 fill-amberbrown-500 text-amberbrown-500" />
          <span class="font-display font-bold text-sm">SaigonStar</span>
        </div>
        <p class="text-xs text-stone-500 dark:text-stone-400">{{ t('footer.address') }}</p>
        <p class="text-[11px] text-stone-400 dark:text-stone-500 pt-1">
          {{ t('footer.tagline') }}
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { Star, User, Sun, Moon } from 'lucide-vue-next';
import { useGuestAuthStore } from '../stores/guestAuth';
import { useAuthStore } from '../stores/auth';
import { useThemeStore } from '../stores/theme';

const { t, locale } = useI18n();
const router = useRouter();
const guestAuth = useGuestAuthStore();
const themeStore = useThemeStore();

const currentLang = ref(locale.value);

const changeLanguage = () => {
  locale.value = currentLang.value;
  localStorage.setItem('hotel_lang', currentLang.value);
  localStorage.setItem('lang', currentLang.value);
  // Cập nhật lang trên authStore nếu có
  try {
    const authStore = useAuthStore();
    authStore.setLanguage(currentLang.value);
  } catch (e) {}
};

const handleLogout = () => {
  guestAuth.logout();
  router.push('/');
};
</script>
