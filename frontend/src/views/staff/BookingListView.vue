<template>
  <div class="space-y-6 pb-12">
    <!-- Top Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight">Quản lý đơn đặt phòng</h1>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 text-sky-800">
            Lễ tân & Quản lý
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">Tìm kiếm, tra cứu và thực hiện các nghiệp vụ lưu trú tại quầy (F07)</p>
      </div>

      <router-link
        to="/nv/don/moi"
        class="px-4 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold shadow-md hover:shadow-lg transition flex items-center space-x-2"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span>Tạo đơn tại quầy</span>
      </router-link>
    </div>

    <!-- Filters & Search Toolbar -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
        <!-- Search input -->
        <div class="md:col-span-2 relative">
          <input
            v-model="searchQuery"
            @keyup.enter="handleSearch"
            type="text"
            placeholder="Tìm theo mã đơn (DP...), tên, SĐT, email, số phòng..."
            class="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
          />
          <svg class="w-4 h-4 text-slate-400 absolute left-3 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        <!-- Status filter -->
        <div>
          <select
            v-model="filterStatus"
            @change="handleSearch"
            class="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition"
          >
            <option value="ALL">Tất cả trạng thái</option>
            <option value="CONFIRMED">Đã xác nhận (CONFIRMED)</option>
            <option value="CHECKED_IN">Đang ở (CHECKED_IN)</option>
            <option value="CHECKED_OUT">Đã trả phòng (CHECKED_OUT)</option>
            <option value="HOLD">Giữ chỗ (HOLD)</option>
            <option value="CANCELLED">Đã hủy (CANCELLED)</option>
            <option value="EXPIRED">Hết hạn (EXPIRED)</option>
            <option value="NO_SHOW">Vắng mặt (NO_SHOW)</option>
          </select>
        </div>

        <!-- Filter Action Button -->
        <div class="flex items-center space-x-2">
          <button
            @click="handleSearch"
            :disabled="loading"
            class="flex-1 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-semibold shadow transition disabled:opacity-50"
          >
            Tìm kiếm
          </button>
          <button
            @click="resetFilters"
            class="px-3 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl font-medium transition"
            title="Đặt lại bộ lọc"
          >
            Đặt lại
          </button>
        </div>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="error" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center space-x-2">
      <span>⚠️</span>
      <span>{{ error }}</span>
    </div>

    <!-- Bookings Table Card -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <!-- Loading indicator -->
      <div v-if="loading" class="py-16 text-center text-slate-400">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-sky-600 border-t-transparent mb-3"></div>
        <p class="text-xs font-medium">Đang tải danh sách đơn đặt phòng...</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="!bookings.length" class="py-16 text-center text-slate-400 space-y-2">
        <div class="text-3xl">📋</div>
        <h3 class="text-sm font-semibold text-slate-700">Không tìm thấy đơn đặt phòng nào</h3>
        <p class="text-xs text-slate-400">Thử thay đổi từ khóa tìm kiếm hoặc bỏ chọn các bộ lọc trạng thái</p>
      </div>

      <!-- Table View -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
            <tr>
              <th class="py-3 px-4">Mã đơn</th>
              <th class="py-3 px-4">Khách hàng</th>
              <th class="py-3 px-4">Phòng / Hạng</th>
              <th class="py-3 px-4">Thời gian lưu trú</th>
              <th class="py-3 px-4">Trạng thái</th>
              <th class="py-3 px-4 text-right">Tổng tiền</th>
              <th class="py-3 px-4 text-center">Kênh</th>
              <th class="py-3 px-4 text-center">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="b in bookings"
              :key="b.id"
              @click="goToDetail(b.bookingCode)"
              class="hover:bg-slate-50/80 transition cursor-pointer"
            >
              <!-- Booking code -->
              <td class="py-3.5 px-4 font-mono font-bold text-sky-700 whitespace-nowrap">
                {{ b.bookingCode }}
              </td>

              <!-- Customer info -->
              <td class="py-3.5 px-4">
                <div class="font-bold text-slate-800">{{ b.customerName }}</div>
                <div class="text-[11px] text-slate-400">{{ b.customerPhone }} • {{ b.customerEmail }}</div>
              </td>

              <!-- Room info -->
              <td class="py-3.5 px-4 whitespace-nowrap">
                <div class="font-bold text-slate-800">
                  <span v-if="b.roomNumber" class="text-sky-700">P.{{ b.roomNumber }}</span>
                  <span v-else class="text-slate-400 italic">Chưa gán</span>
                </div>
                <div class="text-[11px] text-slate-500">{{ b.roomType || 'Standard' }}</div>
              </td>

              <!-- Dates -->
              <td class="py-3.5 px-4 whitespace-nowrap text-slate-600">
                <div>{{ formatDateTime(b.checkin) }}</div>
                <div class="text-slate-400 text-[10px]">đến {{ formatDateTime(b.checkout) }}</div>
              </td>

              <!-- Status -->
              <td class="py-3.5 px-4 whitespace-nowrap">
                <StatusBadge :status="b.status" />
              </td>

              <!-- Financial -->
              <td class="py-3.5 px-4 text-right whitespace-nowrap">
                <div class="font-bold text-slate-900">
                  <MoneyText :amount="b.totalAmount" />
                </div>
                <div class="text-[10px]" :class="b.paidAmount >= b.totalAmount ? 'text-emerald-600' : 'text-amber-600'">
                  Đã thu: <MoneyText :amount="b.paidAmount" />
                </div>
              </td>

              <!-- Channel -->
              <td class="py-3.5 px-4 text-center whitespace-nowrap">
                <span
                  :class="b.channel === 'QUAY' ? 'bg-purple-100 text-purple-800' : 'bg-slate-100 text-slate-700'"
                  class="px-2 py-0.5 rounded text-[10px] font-bold"
                >
                  {{ b.channel }}
                </span>
              </td>

              <!-- Actions button -->
              <td class="py-3.5 px-4 text-center whitespace-nowrap" @click.stop>
                <router-link
                  :to="`/nv/don/${b.bookingCode}`"
                  class="px-3 py-1 bg-slate-100 hover:bg-sky-50 hover:text-sky-700 text-slate-600 rounded-lg font-semibold transition"
                >
                  Chi tiết →
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Footer -->
      <div v-if="totalPages > 1" class="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <div>
          Hiển thị trang <strong>{{ currentPage }}</strong> / <strong>{{ totalPages }}</strong> (Tổng {{ totalItems }} đơn)
        </div>
        <div class="flex items-center space-x-1">
          <button
            @click="changePage(currentPage - 1)"
            :disabled="currentPage <= 1"
            class="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 disabled:opacity-40"
          >
            ← Trước
          </button>
          <button
            @click="changePage(currentPage + 1)"
            :disabled="currentPage >= totalPages"
            class="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 disabled:opacity-40"
          >
            Sau →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import apiClient from '../../api/client';
import StatusBadge from '../../components/StatusBadge.vue';
import MoneyText from '../../components/MoneyText.vue';

const router = useRouter();

const bookings = ref([]);
const totalItems = ref(0);
const totalPages = ref(1);
const currentPage = ref(1);
const pageSize = ref(15);

const searchQuery = ref('');
const filterStatus = ref('ALL');
const loading = ref(false);
const error = ref('');

const formatDateTime = (iso) => {
  if (!iso) return '';
  return new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit', month: '2-digit',
    hour: '2-digit', minute: '2-digit'
  });
};

const fetchBookings = async () => {
  loading.value = true;
  error.value = '';
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value
    };
    if (searchQuery.value.trim()) {
      params.q = searchQuery.value.trim();
    }
    if (filterStatus.value && filterStatus.value !== 'ALL') {
      params.status = filterStatus.value;
    }

    const res = await apiClient.get('/bookings', { params });
    bookings.value = res.items || [];
    totalItems.value = res.total || 0;
    totalPages.value = res.totalPages || 1;
  } catch (err) {
    error.value = err.message || 'Không thể tải danh sách đơn đặt phòng';
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  currentPage.value = 1;
  fetchBookings();
};

const resetFilters = () => {
  searchQuery.value = '';
  filterStatus.value = 'ALL';
  currentPage.value = 1;
  fetchBookings();
};

const changePage = (p) => {
  if (p < 1 || p > totalPages.value) return;
  currentPage.value = p;
  fetchBookings();
};

const goToDetail = (code) => {
  router.push(`/nv/don/${code}`);
};

onMounted(fetchBookings);
</script>
