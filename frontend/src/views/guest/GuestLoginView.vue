<template>
  <div class="max-w-md mx-auto my-12 bg-white p-8 rounded-2xl border border-slate-200/80 shadow-sm">
    <div class="text-center mb-8">
      <div class="w-12 h-12 bg-sky-50 text-sky-700 rounded-xl mx-auto flex items-center justify-center mb-3 border border-sky-100">
        <UserCircle2 class="w-6 h-6" />
      </div>
      <h2 class="text-2xl font-semibold text-slate-900 tracking-tight">Chào mừng quý khách</h2>
      <p class="text-xs text-slate-500 mt-1">Đăng nhập tài khoản thành viên Khách sạn Sài Gòn Star</p>
    </div>

    <form @submit.prevent="handleLogin" class="space-y-4">
      <div v-if="errorMessage" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 flex-shrink-0" />
        <span>{{ errorMessage }}</span>
      </div>

      <div>
        <label class="block text-xs font-medium text-slate-700 mb-1.5">Email hoặc Số điện thoại</label>
        <input
          v-model="account"
          type="text"
          required
          autocomplete="username"
          placeholder="Ví dụ: khachhang@email.com hoặc 0901234567"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <div>
        <div class="flex items-center justify-between mb-1.5">
          <label class="block text-xs font-medium text-slate-700">Mật khẩu</label>
          <router-link to="/quen-mat-khau" class="text-xs text-sky-600 hover:text-sky-700 font-medium transition">
            Quên mật khẩu?
          </router-link>
        </div>
        <input
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
          placeholder="Nhập mật khẩu của quý khách"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs rounded-xl shadow-sm transition disabled:opacity-50 flex items-center justify-center space-x-2"
      >
        <div v-if="loading" class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
        <span>{{ loading ? 'Đang kiểm tra...' : 'Đăng nhập' }}</span>
      </button>
    </form>

    <div class="mt-6 pt-6 border-t border-slate-100 text-center">
      <p class="text-xs text-slate-500">
        Quý khách chưa có tài khoản?
        <router-link to="/dang-ky" class="text-sky-600 hover:text-sky-700 font-semibold ml-1 transition">
          Đăng ký thành viên
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { UserCircle2, AlertCircle } from 'lucide-vue-next';
import apiClient from '../../api/client';
import { useGuestAuthStore } from '../../stores/guestAuth';

const router = useRouter();
const route = useRoute();
const guestAuth = useGuestAuthStore();

const account = ref('');
const password = ref('');
const errorMessage = ref('');
const loading = ref(false);

const handleLogin = async () => {
  errorMessage.value = '';
  loading.value = true;
  try {
    const res = await apiClient.post('/guest/login', {
      tai_khoan: account.value,
      mat_khau: password.value
    });

    const token = res?.access_token || res?.data?.access_token;
    const user = res?.user || res?.data?.user;
    if (token) {
      guestAuth.setAuth(token, user);
      const redirectPath = route.query.redirect || '/chuyen-di-cua-toi';
      router.push(redirectPath);
    } else {
      throw new Error('Dữ liệu đăng nhập không hợp lệ');
    }
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || err.message || 'Thông tin đăng nhập chưa chính xác. Xin quý khách kiểm tra lại.';
  } finally {
    loading.value = false;
  }
};
</script>
