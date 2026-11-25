import { defineStore } from 'pinia';
import apiClient from '../api/client';

export const useGuestAuthStore = defineStore('guestAuth', {
  state: () => ({
    token: localStorage.getItem('guest_token') || '',
    user: JSON.parse(localStorage.getItem('guest_user') || 'null'),
    loading: false
  }),

  getters: {
    isLoggedIn: (state) => !!state.token && !!state.user,
    guestName: (state) => state.user?.ho_ten || 'Quý khách',
    guestEmail: (state) => state.user?.email || '',
    guestPhone: (state) => state.user?.sdt || ''
  },

  actions: {
    setAuth(token, user) {
      this.token = token;
      this.user = user;
      localStorage.setItem('guest_token', token);
      localStorage.setItem('guest_user', JSON.stringify(user));
      // Remove any stale staff token from this client to avoid header collisions
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    },

    logout() {
      this.token = '';
      this.user = null;
      localStorage.removeItem('guest_token');
      localStorage.removeItem('guest_user');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    },

    async fetchProfile() {
      if (!this.token) return;
      try {
        const res = await apiClient.get('/guest/me');
        this.user = res?.data || res;
        localStorage.setItem('guest_user', JSON.stringify(this.user));
      } catch (err) {
        if (err.response?.status === 401 || err.response?.status === 403) {
          this.logout();
        }
      }
    }
  }
});
