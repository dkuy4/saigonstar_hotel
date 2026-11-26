import { createI18n } from 'vue-i18n';
import vi from './vi.json';
import en from './en.json';
import zhCN from './zh-CN.json';
import ko from './ko.json';
import ja from './ja.json';
import es from './es.json';
import fr from './fr.json';

const savedLang = localStorage.getItem('hotel_lang') || 'vi';

const i18n = createI18n({
  legacy: false,
  locale: savedLang,
  fallbackLocale: 'vi',
  messages: {
    vi,
    en,
    'zh-CN': zhCN,
    ko,
    ja,
    es,
    fr
  }
});

export default i18n;
