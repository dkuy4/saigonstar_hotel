import { defineStore } from 'pinia';
import i18n from '../i18n';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: sessionStorage.getItem('hotel_token') || '',
    user: JSON.parse(sessionStorage.getItem('hotel_user') || 'null'),
    language: localStorage.getItem('hotel_lang') || 'vi'
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    role: (state) => state.user?.role || 'KHACH',
    isStaff: (state) => ['LE_TAN', 'BUONG_PHONG', 'QUAN_LY'].includes(state.user?.role),
    isManager: (state) => state.user?.role === 'QUAN_LY',
    isReceptionist: (state) => state.user?.role === 'LE_TAN',
    isHousekeeping: (state) => state.user?.role === 'BUONG_PHONG'
  },
  actions: {
    setAuth(token, user) {
      this.token = token;
      this.user = user;
      sessionStorage.setItem('hotel_token', token);
      sessionStorage.setItem('hotel_user', JSON.stringify(user));
    },
    logout() {
      this.token = '';
      this.user = null;
      sessionStorage.removeItem('hotel_token');
      sessionStorage.removeItem('hotel_user');
    },
    setLanguage(lang) {
      this.language = lang;
      localStorage.setItem('hotel_lang', lang);
      i18n.global.locale.value = lang;
    }
  }
});
