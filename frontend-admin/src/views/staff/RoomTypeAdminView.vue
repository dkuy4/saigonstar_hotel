<template>
  <div class="space-y-6 pb-12">
    <!-- Header & Subtitle -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight">Quản lý hạng phòng & Nội dung đa ngôn ngữ</h1>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 text-sky-800">
            F16.2 Admin
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Cập nhật sức chứa, hình ảnh đại diện và bản dịch 7 ngôn ngữ (Tiếng Việt, Anh, Trung, Hàn, Nhật, Tây Ban Nha, Pháp)
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <router-link
          to="/nv/quan-ly/phong"
          class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Danh mục phòng (16.1)
        </router-link>
        <router-link
          to="/nv/quan-ly/bang-gia"
          class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Bảng giá (16.3)
        </router-link>
        <router-link
          to="/nv/quan-ly/tham-so"
          class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Tham số & VAT (16.4)
        </router-link>
        <router-link
          to="/nv/quan-ly/ban-dich"
          class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Bản dịch & Email (16.5)
        </router-link>
        <router-link
          to="/nv/quan-ly/tai-khoan"
          class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Tài khoản (F17)
        </router-link>
      </div>
    </div>

    <!-- Alert Messages -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0" />
        <span>{{ errorMessage }}</span>
      </div>
      <button @click="errorMessage = ''" class="font-bold text-rose-600 hover:text-rose-800">✕</button>
    </div>

    <div v-if="successMessage" class="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <CheckCircle2 class="w-4 h-4 text-emerald-600 flex-shrink-0" />
        <span>{{ successMessage }}</span>
      </div>
      <button @click="successMessage = ''" class="font-bold text-emerald-600 hover:text-emerald-800">✕</button>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading && !roomTypes.length" class="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
      <div v-for="i in 4" :key="i" class="bg-white rounded-2xl border border-slate-200 p-6 h-96"></div>
    </div>

    <!-- 4 Room Types Cards Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div
        v-for="rt in roomTypes"
        :key="rt.id"
        class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col justify-between"
      >
        <div class="p-6 space-y-5">
          <!-- Card Header -->
          <div class="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
            <div class="flex items-center space-x-3">
              <div class="w-12 h-12 bg-sky-50 text-sky-600 rounded-xl flex items-center justify-center font-bold text-base shadow-sm border border-sky-100">
                {{ rt.code.slice(0, 3) }}
              </div>
              <div>
                <h3 class="text-lg font-bold text-slate-900">{{ rt.translations?.vi?.name || rt.code }}</h3>
                <span class="text-xs font-mono font-semibold text-sky-600 block">Mã hạng: {{ rt.code }}</span>
              </div>
            </div>

            <div class="flex flex-col items-end space-y-1">
              <span
                class="px-2.5 py-0.5 rounded-full text-[10px] font-semibold"
                :class="rt.hourly_allowed ? 'bg-purple-50 text-purple-700 border border-purple-200' : 'bg-slate-100 text-slate-600'"
              >
                {{ rt.hourly_allowed ? 'Thuê ngày & giờ' : 'Chỉ thuê ngày' }}
              </span>
              <span class="text-[11px] text-slate-500 font-medium">
                Sức chứa: <strong>{{ rt.capacity }} khách</strong>
              </span>
            </div>
          </div>

          <!-- Image Preview & URL -->
          <div class="flex flex-col sm:flex-row gap-4">
            <div class="sm:w-36 h-28 bg-slate-100 rounded-xl overflow-hidden border border-slate-200 flex-shrink-0">
              <img
                :src="editForms[rt.id]?.image_url || getFallbackImage(rt.code)"
                :alt="rt.code"
                @error="(e) => (e.target.src = getFallbackImage(rt.code))"
                class="w-full h-full object-cover"
              />
            </div>
            <div class="flex-1 space-y-2 text-xs">
              <div>
                <label class="block font-semibold text-slate-700 mb-1">Đường dẫn ảnh đại diện (URL)</label>
                <input
                  v-model="editForms[rt.id].image_url"
                  type="text"
                  placeholder="https://images.unsplash.com/..."
                  class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
                />
              </div>
              <div>
                <label class="block font-semibold text-slate-700 mb-1">Sức chứa tối đa (khách) *</label>
                <input
                  v-model.number="editForms[rt.id].capacity"
                  type="number"
                  min="1"
                  max="20"
                  required
                  class="w-24 px-3 py-1.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none font-bold"
                />
              </div>
            </div>
          </div>

          <!-- Language Tabs -->
          <div class="space-y-3 pt-2 border-t border-slate-100">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-700">Nội dung 7 ngôn ngữ</span>
              <span class="text-[11px] text-slate-400">
                Đã dịch: {{ getFilledLangsCount(editForms[rt.id].translations) }}/7
              </span>
            </div>

            <!-- Tab Pills -->
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="l in availableLanguages"
                :key="l.code"
                type="button"
                @click="activeTabs[rt.id] = l.code"
                class="px-2.5 py-1 rounded-lg text-xs font-medium transition flex items-center space-x-1"
                :class="activeTabs[rt.id] === l.code ? 'bg-sky-600 text-white shadow-sm' : 'bg-slate-100 hover:bg-slate-200 text-slate-700'"
              >
                <span>{{ l.flag }}</span>
                <span>{{ l.name }}</span>
                <span v-if="editForms[rt.id].translations[l.code]?.name" class="w-1.5 h-1.5 rounded-full bg-emerald-400 ml-1"></span>
              </button>
            </div>

            <!-- Active Tab Content Fields -->
            <div class="p-4 bg-slate-50/80 rounded-xl border border-slate-200/80 space-y-3 text-xs">
              <div>
                <div class="flex justify-between items-center mb-1">
                  <label class="font-semibold text-slate-700">
                    Tên hạng phòng ({{ availableLanguages.find(x => x.code === activeTabs[rt.id])?.name }})
                    <span v-if="['vi', 'en'].includes(activeTabs[rt.id])" class="text-rose-600">*</span>
                  </label>
                  <span v-if="['vi', 'en'].includes(activeTabs[rt.id])" class="text-[10px] text-slate-400 uppercase font-semibold">Bắt buộc</span>
                </div>
                <input
                  v-model="editForms[rt.id].translations[activeTabs[rt.id]].name"
                  type="text"
                  placeholder="Nhập tên hạng phòng theo ngôn ngữ này"
                  class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
                />
              </div>

              <div>
                <label class="block font-semibold text-slate-700 mb-1">Đoạn mô tả giới thiệu</label>
                <textarea
                  v-model="editForms[rt.id].translations[activeTabs[rt.id]].description"
                  rows="2"
                  placeholder="Mô tả không gian, tầm nhìn, trang trí..."
                  class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
                ></textarea>
              </div>

              <div>
                <label class="block font-semibold text-slate-700 mb-1">Tiện nghi nổi bật (phân cách bằng dấu phẩy)</label>
                <input
                  v-model="editForms[rt.id].translations[activeTabs[rt.id]].amenities"
                  type="text"
                  placeholder="Wifi, Smart TV 50 inch, Minibar, Ban công ngắm cảnh..."
                  class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Footer / Save Action -->
        <div class="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
          <span class="text-[11px] text-slate-500">
            Lưu thay đổi sẽ áp dụng ngay lên toàn bộ hệ thống
          </span>
          <button
            @click="handleSaveRoomType(rt.id)"
            :disabled="savingId === rt.id"
            class="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow transition disabled:opacity-50 flex items-center space-x-1.5"
          >
            <div v-if="savingId === rt.id" class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
            <span>{{ savingId === rt.id ? 'Đang lưu...' : 'Lưu hạng phòng' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { AlertCircle, CheckCircle2 } from 'lucide-vue-next';
import apiClient from '../../api/client';

const roomTypes = ref([]);
const loading = ref(false);
const savingId = ref(null);
const errorMessage = ref('');
const successMessage = ref('');

const availableLanguages = [
  { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' }
];

const activeTabs = reactive({});
const editForms = reactive({});

const getFallbackImage = (code) => {
  const images = {
    STANDARD: 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80',
    SUPERIOR: 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80',
    DELUXE: 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80',
    SUITE: 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80'
  };
  return images[code] || images.STANDARD;
};

const getFilledLangsCount = (translationsMap) => {
  if (!translationsMap) return 0;
  return Object.values(translationsMap).filter(t => t?.name?.trim()).length;
};

const fetchRoomTypesAdmin = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const res = await apiClient.get('/room-types', { params: { lang: 'all' } });
    roomTypes.value = res || [];

    // Initialize state
    res.forEach(rt => {
      activeTabs[rt.id] = activeTabs[rt.id] || 'vi';

      // Prepopulate form for 7 languages
      const transObj = {};
      availableLanguages.forEach(l => {
        const existing = rt.translations?.[l.code];
        transObj[l.code] = {
          lang: l.code,
          name: existing?.name || '',
          description: existing?.description || '',
          amenities: existing?.amenities || ''
        };
      });

      editForms[rt.id] = {
        capacity: rt.capacity || 2,
        image_url: rt.image_url || '',
        translations: transObj
      };
    });
  } catch (err) {
    errorMessage.value = err.message || 'Không thể tải danh sách hạng phòng';
  } finally {
    loading.value = false;
  }
};

const handleSaveRoomType = async (rtId) => {
  savingId.value = rtId;
  errorMessage.value = '';
  successMessage.value = '';

  const form = editForms[rtId];
  if (!form) return;

  const transList = Object.values(form.translations).map(t => ({
    lang: t.lang,
    name: t.name.trim(),
    description: t.description.trim() || null,
    amenities: t.amenities.trim() || null
  }));

  try {
    await apiClient.put(`/room-types/${rtId}`, {
      capacity: form.capacity,
      image_url: form.image_url.trim() || null,
      translations: transList
    });
    successMessage.value = 'Cập nhật hạng phòng và bản dịch thành công';
    await fetchRoomTypesAdmin();
  } catch (err) {
    errorMessage.value = err.message || 'Cập nhật thất bại';
  } finally {
    savingId.value = null;
  }
};

onMounted(fetchRoomTypesAdmin);
</script>
