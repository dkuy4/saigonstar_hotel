<template>
  <div class="max-w-md mx-auto mt-12 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
    <div class="text-center mb-6">
      <div class="w-12 h-12 bg-sky-100 text-sky-600 rounded-xl mx-auto flex items-center justify-center font-bold text-xl mb-3">
        🔐
      </div>
      <h2 class="text-2xl font-bold text-slate-800">Đăng nhập nhân viên</h2>
      <p class="text-xs text-slate-500 mt-1">Dành cho Lễ tân, Buồng phòng và Quản lý</p>
    </div>

    <form @submit.prevent="handleLogin" class="space-y-4">
      <div v-if="errorMessage" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
        {{ errorMessage }}
      </div>

      <div>
        <label class="block text-xs font-semibold text-slate-700 mb-1">Tên đăng nhập</label>
        <input
          v-model="username"
          type="text"
          required
          autocomplete="username"
          class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
          placeholder="Nhập tên đăng nhập"
        />
      </div>

      <div>
        <label class="block text-xs font-semibold text-slate-700 mb-1">Mật khẩu</label>
        <input
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
          class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
          placeholder="Nhập mật khẩu"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-700 text-white font-medium text-sm rounded-lg shadow-sm transition disabled:opacity-50"
      >
        {{ loading ? 'Đang xác thực...' : 'Đăng nhập' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import apiClient from '../../api/client';

const router = useRouter();
const authStore = useAuthStore();

const username = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');

const handleLogin = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const res = await apiClient.post('/auth/login', {
      username: username.value,
      password: password.value
    });
    const userObj = res.user || res.data?.user;
    const tokenStr = res.token || res.data?.token;
    authStore.setAuth(tokenStr, userObj);
    // Redirect based on role
    if (userObj.role === 'BUONG_PHONG') {
      router.push('/nv/don-phong');
    } else {
      router.push('/nv/so-do-phong');
    }
  } catch (err) {
    errorMessage.value = err.message || 'Sai tên đăng nhập hoặc mật khẩu';
  } finally {
    loading.value = false;
  }
};
</script>
