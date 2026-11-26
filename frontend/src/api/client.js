import axios from 'axios';
import { useAuthStore } from '../stores/auth';
import { useGuestAuthStore } from '../stores/guestAuth';
import i18n from '../i18n';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
});

// Request interceptor: attach Bearer token and current language
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    const guestToken = localStorage.getItem('guest_token');

    // If authorization is already explicitly set on this request, keep it
    if (!config.headers.Authorization) {
      // If calling guest APIs or if guest is logged in on guest portal, prioritize guest token
      if (config.url && config.url.includes('/guest')) {
        if (guestToken) {
          config.headers.Authorization = `Bearer ${guestToken}`;
        } else if (authStore.token) {
          config.headers.Authorization = `Bearer ${authStore.token}`;
        }
      } else if (guestToken && !authStore.token) {
        config.headers.Authorization = `Bearer ${guestToken}`;
      } else if (authStore.token) {
        config.headers.Authorization = `Bearer ${authStore.token}`;
      } else if (guestToken) {
        config.headers.Authorization = `Bearer ${guestToken}`;
      }
    }
    const bookingToken = sessionStorage.getItem('booking_token');
    if (bookingToken) {
      config.headers['X-Booking-Token'] = bookingToken;
    }
    // Append lang query parameter if not explicitly specified
    if (!config.params) {
      config.params = {};
    }
    if (config.params.lang === undefined) {
      config.params.lang = authStore.language;
    } else if (config.params.lang === null || config.params.lang === '') {
      delete config.params.lang;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle errors & map error codes
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const authStore = useAuthStore();
    
    // Auto logout if 401 Unauthorized
    if (error.response?.status === 401) {
      authStore.logout();
      try {
        const guestAuthStore = useGuestAuthStore();
        guestAuthStore.logout();
      } catch (e) {
        localStorage.removeItem('guest_token');
        localStorage.removeItem('guest_user');
      }
    }

    const data = error.response?.data;
    const code = data?.code || 'INTERNAL_SERVER_ERROR';
    
    // Translate error code using i18n
    const translationKey = `errors.${code}`;
    const localizedMessage = i18n.global.te(translationKey)
      ? i18n.global.t(translationKey)
      : (data?.detail || error.message || 'Lỗi không xác định');

    const enhancedError = new Error(localizedMessage);
    enhancedError.code = code;
    enhancedError.detail = data?.detail;
    enhancedError.status = error.response?.status;
    enhancedError.data = data?.data;
    enhancedError.raw = error;

    return Promise.reject(enhancedError);
  }
);

export default apiClient;
