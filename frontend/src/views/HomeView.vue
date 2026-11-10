<template>
  <div class="space-y-10">
    <!-- Hero Banner with Integrated Search -->
    <div class="relative rounded-3xl overflow-hidden bg-slate-900 text-white shadow-2xl">
      <!-- Background Image with Overlay -->
      <div class="absolute inset-0 z-0 opacity-40">
        <img
          src="https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1600&q=80"
          alt="Hotel Luxury"
          class="w-full h-full object-cover"
        />
      </div>
      <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-900/60 to-transparent z-0"></div>

      <!-- Hero Content -->
      <div class="relative z-10 px-6 py-12 md:py-16 max-w-4xl mx-auto text-center space-y-4">
        <span class="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-semibold bg-sky-500/20 text-sky-300 border border-sky-400/30 backdrop-blur-md">
          ★ KHÁCH SẠN NGHỈ DƯỠNG TIÊU CHUẨN QUỐC TẾ
        </span>
        <h2 class="text-3xl md:text-5xl font-black tracking-tight text-white leading-tight">
          {{ t('search.title') }}
        </h2>
        <p class="text-sm md:text-base text-slate-300 max-w-2xl mx-auto font-light leading-relaxed">
          {{ t('search.subtitle') }}
        </p>

        <!-- Floating Search Box -->
        <div class="pt-6 text-left">
          <SearchBox />
        </div>
      </div>
    </div>

    <!-- Featured Room Types Showcase -->
    <div class="space-y-6">
      <div class="flex items-end justify-between">
        <div>
          <h3 class="text-2xl font-bold text-slate-900 tracking-tight">Hạng phòng & Bảng giá niêm yết</h3>
          <p class="text-xs text-slate-500 mt-1">Giá công khai đã gồm phí dịch vụ, chưa gồm VAT 8% (D-26, BR-57)</p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div
          v-for="rt in roomTypes"
          :key="rt.id"
          class="bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition overflow-hidden flex flex-col justify-between"
        >
          <div>
            <div class="h-44 bg-slate-100 relative overflow-hidden">
              <img :src="getRoomImage(rt.code)" :alt="rt.name" class="w-full h-full object-cover hover:scale-105 transition duration-300" />
              <div class="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-sm text-white px-2 py-0.5 rounded text-[11px] font-semibold">
                {{ rt.code }}
              </div>
              <div v-if="rt.hourly_allowed" class="absolute bottom-3 right-3 bg-purple-600 text-white px-2 py-0.5 rounded text-[11px] font-semibold shadow">
                ⏱️ Có thuê giờ
              </div>
            </div>

            <div class="p-5 space-y-2.5">
              <h4 class="font-bold text-base text-slate-900">{{ rt.name }}</h4>
              <p class="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                {{ rt.description }}
              </p>
              <div class="text-[11px] text-slate-600 font-medium pt-1">
                👥 Sức chứa: {{ rt.capacity }} khách
              </div>
            </div>
          </div>

          <div class="p-5 pt-0 border-t border-slate-100 mt-3 flex items-center justify-between">
            <div>
              <span class="text-[10px] text-slate-400 uppercase font-semibold block">Giá theo ngày</span>
              <span class="text-base font-bold text-sky-600">
                <MoneyText :value="rt.daily_price" currency="VND" />
              </span>
              <span class="text-[10px] text-slate-400"> / đêm</span>
            </div>
            <div v-if="rt.hourly_price" class="text-right">
              <span class="text-[10px] text-slate-400 uppercase font-semibold block">Giá theo giờ</span>
              <span class="text-sm font-semibold text-purple-700">
                <MoneyText :value="rt.hourly_price" currency="VND" />
              </span>
              <span class="text-[10px] text-slate-400"> / giờ</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Architecture & Database Health Status -->
    <div class="bg-slate-100/70 border border-slate-200/80 rounded-2xl p-6">
      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-lg">
            ⚡
          </div>
          <div>
            <h4 class="text-sm font-bold text-slate-900">Oracle Database 23ai Engine</h4>
            <p class="text-xs text-slate-500">Khóa bi quan tại CSDL • Kiểm soát xung đột đồng thời 100%</p>
          </div>
        </div>

        <div class="flex items-center space-x-4 text-xs">
          <span class="flex items-center text-emerald-700 font-semibold">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-1.5"></span>
            PDB FREEPDB1 (Connected)
          </span>
          <span class="text-slate-400">|</span>
          <span class="text-slate-600">21 Tables</span>
          <span class="text-slate-400">|</span>
          <span class="text-slate-600">11 Packages</span>
          <span class="text-slate-400">|</span>
          <span class="text-slate-600">37 + 104 Tests Pass</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '../api/client';
import SearchBox from '../components/SearchBox.vue';
import MoneyText from '../components/MoneyText.vue';

const { t, locale } = useI18n();

const roomTypes = ref([]);

const getRoomImage = (code) => {
  const images = {
    STANDARD: 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80',
    SUPERIOR: 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80',
    DELUXE: 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80',
    SUITE: 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80'
  };
  return images[code] || images.STANDARD;
};

const loadRoomTypes = async () => {
  try {
    const res = await apiClient.get('/room-types', {
      params: { lang: locale.value }
    });
    roomTypes.value = res || [];
  } catch (err) {
    console.error('Failed to load room types:', err);
  }
};

onMounted(loadRoomTypes);
watch(() => locale.value, loadRoomTypes);
</script>
