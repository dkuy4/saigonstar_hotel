import { createI18n } from 'vue-i18n';
import vi from './vi.json';
import en from './en.json';

const savedLang = localStorage.getItem('hotel_lang') || 'vi';

const i18n = createI18n({
  legacy: false,
  locale: savedLang,
  fallbackLocale: 'vi',
  messages: {
    vi,
    en
  }
});

export default i18n;
