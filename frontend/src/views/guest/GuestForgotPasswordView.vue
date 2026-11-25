<template>
  <div class="max-w-md mx-auto my-12 bg-white p-8 rounded-2xl border border-slate-200/80 shadow-sm">
    <div class="text-center mb-8">
      <div class="w-12 h-12 bg-slate-50 text-slate-700 rounded-xl mx-auto flex items-center justify-center mb-3 border border-slate-200">
        <KeyRound class="w-6 h-6" />
      </div>
      <h2 class="text-2xl font-semibold text-slate-900 tracking-tight">Đặt lại mật khẩu</h2>
      <p class="text-xs text-slate-500 mt-1">Xác nhận thông tin cá nhân để thiết lập mật khẩu mới</p>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl space-y-3">
      <p class="font-medium">{{ successMessage }}</p>
      <router-link
        to="/dang-nhap"
        class="inline-block py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition"
      >
        Đăng nhập với mật khẩu mới
      </router-link>
    </div>

    <!-- Form -->
    <form v-else @submit.prevent="handleResetPassword" class="space-y-4">
      <div v-if="errorMessage" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 flex-shrink-0" />
        <span>{{ errorMessage }}</span>
      </div>

      <div>
        <label class="block text-xs font-medium text-slate-700 mb-1.5">Địa chỉ Email đã đăng ký</label>
        <input
          v-model="email"
          type="email"
          required
          placeholder="Ví dụ: khachhang@email.com"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-slate-700 mb-1.5">Số điện thoại đã đăng ký</label>
        <input
          v-model="phone"
          type="tel"
          required
          placeholder="Ví dụ: 0912345678"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-slate-700 mb-1.5">Họ và tên của quý khách</label>
        <input
          v-model="fullName"
          type="text"
          required
          placeholder="Họ tên chính xác như lúc đăng ký"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <div class="pt-2 border-t border-slate-100">
        <label class="block text-xs font-medium text-slate-700 mb-1.5">Mật khẩu mới muốn đặt</label>
        <input
          v-model="newPassword"
          type="password"
          required
          minlength="6"
          placeholder="Tối thiểu 6 ký tự"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-slate-700 mb-1.5">Xác nhận mật khẩu mới</label>
        <input
          v-model="confirmPassword"
          type="password"
          required
          minlength="6"
          placeholder="Nhập lại mật khẩu mới"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs rounded-xl shadow-sm transition disabled:opacity-50 flex items-center justify-center space-x-2"
      >
        <div v-if="loading" class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
        <span>{{ loading ? 'Đang xác minh...' : 'Lưu mật khẩu mới' }}</span>
      </button>
    </form>

    <div class="mt-6 pt-6 border-t border-slate-100 text-center">
      <router-link to="/dang-nhap" class="text-xs text-slate-600 hover:text-slate-900 font-medium transition">
        Quay lại màn hình đăng nhập
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { KeyRound, AlertCircle } from 'lucide-vue-next';
import apiClient from '../../api/client';

const email = ref('');
const phone = ref('');
const fullName = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const errorMessage = ref('');
const successMessage = ref('');
const loading = ref(false);

const handleResetPassword = async () => {
  errorMessage.value = '';
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'Mật khẩu mới và xác nhận mật khẩu không trùng khớp.';
    return;
  }

  loading.value = true;
  try {
    const res = await apiClient.post('/guest/forgot-password', {
      email: email.value,
      sdt: phone.value,
      ho_ten: fullName.value,
      mat_khau_moi: newPassword.value
    });

    successMessage.value = res?.message || res?.data?.message || 'Mật khẩu của quý khách đã được cập nhật thành công. Quý khách có thể đăng nhập ngay.';
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || err.message || 'Thông tin không khớp. Quý khách vui lòng kiểm tra lại họ tên, email và số điện thoại.';
  } finally {
    loading.value = false;
  }
};
</script>
