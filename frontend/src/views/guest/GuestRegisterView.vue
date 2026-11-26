<template>
  <div class="max-w-md mx-auto my-12 bg-white dark:bg-darkbeige-850 p-8 rounded-2xl border border-beige-300 dark:border-darkbeige-800 shadow-sm transition-colors">
    <div class="text-center mb-8">
      <h2 class="font-display font-bold text-3xl text-stone-900 dark:text-white tracking-tight">{{ t('auth.registerTitle') }}</h2>
      <p class="text-xs text-stone-500 dark:text-stone-400 mt-1.5">{{ t('auth.registerSubtitle') }}</p>
    </div>

    <form @submit.prevent="handleRegister" class="space-y-4">
      <div v-if="errorMessage" class="p-3.5 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-rose-700 dark:text-rose-300 text-xs rounded-xl flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 flex-shrink-0" />
        <span>{{ errorMessage }}</span>
      </div>

      <div>
        <label class="block text-xs font-medium text-stone-700 dark:text-stone-300 mb-1.5">{{ t('auth.fullName') }}</label>
        <input
          v-model="fullName"
          type="text"
          required
          :placeholder="t('auth.fullNamePlaceholder')"
          class="w-full px-3.5 py-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl text-xs text-stone-900 dark:text-stone-100 focus:bg-white dark:focus:bg-darkbeige-800 focus:ring-2 focus:ring-amberbrown-500 outline-none transition"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-stone-700 dark:text-stone-300 mb-1.5">{{ t('auth.phone') }}</label>
        <input
          v-model="phone"
          type="tel"
          required
          :placeholder="t('auth.phonePlaceholder')"
          class="w-full px-3.5 py-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl text-xs text-stone-900 dark:text-stone-100 focus:bg-white dark:focus:bg-darkbeige-800 focus:ring-2 focus:ring-amberbrown-500 outline-none transition"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-stone-700 dark:text-stone-300 mb-1.5">{{ t('auth.email') }}</label>
        <input
          v-model="email"
          type="email"
          required
          :placeholder="t('auth.emailPlaceholder')"
          class="w-full px-3.5 py-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl text-xs text-stone-900 dark:text-stone-100 focus:bg-white dark:focus:bg-darkbeige-800 focus:ring-2 focus:ring-amberbrown-500 outline-none transition"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-stone-700 dark:text-stone-300 mb-1.5">{{ t('auth.password') }}</label>
        <input
          v-model="password"
          type="password"
          required
          minlength="6"
          :placeholder="t('auth.newPasswordPlaceholder')"
          class="w-full px-3.5 py-2.5 bg-beige-50/50 dark:bg-darkbeige-900 border border-beige-300 dark:border-darkbeige-700 rounded-xl text-xs text-stone-900 dark:text-stone-100 focus:bg-white dark:focus:bg-darkbeige-800 focus:ring-2 focus:ring-amberbrown-500 outline-none transition"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full py-2.5 px-4 bg-amberbrown-500 hover:bg-amberbrown-600 text-white font-semibold text-xs rounded-xl shadow-sm transition disabled:opacity-50 flex items-center justify-center space-x-2"
      >
        <div v-if="loading" class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
        <span>{{ loading ? t('auth.registering') : t('auth.registerBtn') }}</span>
      </button>
    </form>

    <div class="mt-6 pt-6 border-t border-beige-200 dark:border-darkbeige-800 text-center">
      <p class="text-xs text-stone-500 dark:text-stone-400">
        {{ t('auth.haveAccount') }}
        <router-link to="/dang-nhap" class="text-amberbrown-600 dark:text-amberbrown-400 hover:text-amberbrown-700 dark:hover:text-amberbrown-300 font-semibold ml-1 transition">
          {{ t('auth.loginNow') }}
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { AlertCircle } from 'lucide-vue-next';
import apiClient from '../../api/client';
import { useGuestAuthStore } from '../../stores/guestAuth';

const { t } = useI18n();
const router = useRouter();
const guestAuth = useGuestAuthStore();

const fullName = ref('');
const phone = ref('');
const email = ref('');
const password = ref('');
const errorMessage = ref('');
const loading = ref(false);

const handleRegister = async () => {
  errorMessage.value = '';
  loading.value = true;
  try {
    const res = await apiClient.post('/guest/register', {
      ho_ten: fullName.value,
      so_dien_thoai: phone.value,
      email: email.value,
      mat_khau: password.value
    });

    const token = res?.access_token || res?.data?.access_token;
    const user = res?.user || res?.data?.user;
    if (token) {
      guestAuth.setAuth(token, user);
      router.push('/chuyen-di-cua-toi');
    } else {
      router.push('/dang-nhap');
    }
  } catch (err) {
    errorMessage.value = err.detail || err.message || t('errors.VALIDATION_ERROR');
  } finally {
    loading.value = false;
  }
};
</script>
