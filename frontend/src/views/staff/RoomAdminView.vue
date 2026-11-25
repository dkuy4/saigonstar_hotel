<template>
  <div class="space-y-6 pb-12">
    <!-- Header & Action Toolbar -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight">Quản lý danh mục phòng</h1>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 text-sky-800">
            F16.1 Admin
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Thêm, cập nhật thông tin phòng, ghi chú và bật/tắt trạng thái hoạt động (FR-26)
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <router-link
          to="/nv/quan-ly/hang-phong"
          class="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Hạng phòng (16.2)
        </router-link>
        <router-link
          to="/nv/quan-ly/bang-gia"
          class="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Bảng giá (16.3)
        </router-link>
        <router-link
          to="/nv/quan-ly/tham-so"
          class="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Tham số & VAT (16.4)
        </router-link>
        <router-link
          to="/nv/quan-ly/ban-dich"
          class="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Bản dịch & Email (16.5)
        </router-link>
        <router-link
          to="/nv/quan-ly/tai-khoan"
          class="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Tài khoản (F17)
        </router-link>
        <button
          @click="openCreateModal"
          class="px-4 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold transition flex items-center space-x-1.5 shadow-sm self-start sm:self-auto"
        >
          <Plus class="w-4 h-4" />
          <span>Thêm phòng mới</span>
        </button>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
        <!-- Search -->
        <div>
          <label class="block text-[11px] font-semibold text-slate-500 uppercase mb-1">Tìm kiếm</label>
          <div class="relative">
            <Search class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              v-model="searchQuery"
              @keyup.enter="handleFilter"
              type="text"
              placeholder="Mã phòng, ghi chú..."
              class="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
            />
          </div>
        </div>

        <!-- Floor Filter -->
        <div>
          <label class="block text-[11px] font-semibold text-slate-500 uppercase mb-1">Tầng</label>
          <select
            v-model="filterFloor"
            @change="handleFilter"
            class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
          >
            <option value="">Tất cả các tầng</option>
            <option v-for="f in 5" :key="f" :value="f">Tầng {{ f }}</option>
          </select>
        </div>

        <!-- Room Type Filter -->
        <div>
          <label class="block text-[11px] font-semibold text-slate-500 uppercase mb-1">Hạng phòng</label>
          <select
            v-model="filterType"
            @change="handleFilter"
            class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
          >
            <option value="">Tất cả hạng</option>
            <option value="STANDARD">Standard</option>
            <option value="SUPERIOR">Superior</option>
            <option value="DELUXE">Deluxe</option>
            <option value="SUITE">Suite</option>
          </select>
        </div>

        <!-- Status Filter -->
        <div>
          <label class="block text-[11px] font-semibold text-slate-500 uppercase mb-1">Trạng thái phòng</label>
          <select
            v-model="filterStatus"
            @change="handleFilter"
            class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
          >
            <option value="">Tất cả trạng thái</option>
            <option value="TRONG">Trống</option>
            <option value="DANG_O">Đang ở</option>
            <option value="DANG_DON">Đang dọn</option>
            <option value="BAO_TRI">Bảo trì</option>
          </select>
        </div>

        <!-- Active Filter -->
        <div>
          <label class="block text-[11px] font-semibold text-slate-500 uppercase mb-1">Hoạt động</label>
          <select
            v-model="filterActive"
            @change="handleFilter"
            class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
          >
            <option value="">Tất cả</option>
            <option value="true">Đang hoạt động</option>
            <option value="false">Ngưng dùng</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0" />
        <span>{{ errorMessage }}</span>
      </div>
      <button @click="errorMessage = ''" class="font-bold text-rose-600 hover:text-rose-800">✕</button>
    </div>

    <!-- Table Card -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <!-- Loading indicator -->
      <div v-if="loading" class="py-16 text-center text-slate-400">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-sky-600 border-t-transparent mb-3"></div>
        <p class="text-xs font-medium">Đang tải danh sách phòng...</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="!rooms.length" class="py-16 text-center text-slate-400 space-y-2">
        <div class="w-12 h-12 bg-slate-100 text-slate-400 rounded-2xl mx-auto flex items-center justify-center">
          <Building2 class="w-6 h-6" />
        </div>
        <h3 class="text-sm font-semibold text-slate-700">Không tìm thấy phòng nào phù hợp</h3>
        <p class="text-xs text-slate-400">Thử thay đổi điều kiện lọc hoặc từ khóa tìm kiếm</p>
      </div>

      <!-- Rooms Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
            <tr>
              <th class="py-3 px-4">Mã phòng</th>
              <th class="py-3 px-4">Tầng</th>
              <th class="py-3 px-4">Hạng phòng</th>
              <th class="py-3 px-4">Trạng thái phòng</th>
              <th class="py-3 px-4 text-center">Hoạt động</th>
              <th class="py-3 px-4">Ghi chú</th>
              <th class="py-3 px-4 text-center">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="r in rooms" :key="r.roomId" class="hover:bg-slate-50/75 transition">
              <td class="py-3 px-4 font-mono font-bold text-slate-900 text-sm">
                {{ r.roomNumber }}
              </td>
              <td class="py-3 px-4 font-medium text-slate-600">
                Tầng {{ r.floor }}
              </td>
              <td class="py-3 px-4">
                <span class="font-semibold text-slate-800">{{ r.roomTypeName }}</span>
                <span class="text-[10px] text-slate-400 block font-mono">{{ r.roomType }}</span>
              </td>
              <td class="py-3 px-4">
                <StatusBadge :status="r.status" />
              </td>
              <td class="py-3 px-4 text-center">
                <span
                  class="px-2.5 py-0.5 rounded-full text-[10px] font-semibold"
                  :class="r.isActive ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500 border border-slate-200'"
                >
                  {{ r.isActive ? 'Hoạt động' : 'Ngưng dùng' }}
                </span>
              </td>
              <td class="py-3 px-4 text-slate-500 max-w-xs truncate">
                {{ r.notes || '-' }}
              </td>
              <td class="py-3 px-4 text-center">
                <button
                  @click="openEditModal(r)"
                  class="px-3 py-1 bg-slate-100 hover:bg-sky-50 hover:text-sky-700 text-slate-700 rounded-lg text-xs font-medium transition"
                >
                  Sửa
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <div>
          Hiển thị trang <strong>{{ currentPage }}</strong> / <strong>{{ totalPages }}</strong> (Tổng {{ totalRooms }} phòng)
        </div>
        <div class="flex items-center space-x-1">
          <button
            @click="goToPage(currentPage - 1)"
            :disabled="currentPage <= 1"
            class="px-3 py-1 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40"
          >
            Trước
          </button>
          <button
            @click="goToPage(currentPage + 1)"
            :disabled="currentPage >= totalPages"
            class="px-3 py-1 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40"
          >
            Sau
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Create / Edit Room -->
    <div v-if="showModal" class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="text-base font-bold text-slate-900 flex items-center space-x-2">
            <Building2 class="w-5 h-5 text-sky-600" />
            <span>{{ isEditing ? 'Cập nhật phòng: ' + formRoomNumber : 'Thêm phòng mới' }}</span>
          </h3>
          <button @click="showModal = false" class="text-slate-400 hover:text-slate-600 font-bold">✕</button>
        </div>

        <form @submit.prevent="handleSaveRoom" class="space-y-4 text-xs">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Mã phòng *</label>
              <input
                v-model="formRoomNumber"
                type="text"
                required
                maxlength="10"
                placeholder="VD: 511"
                class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl font-mono uppercase text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>

            <div>
              <label class="block font-semibold text-slate-700 mb-1">Tầng *</label>
              <input
                v-model.number="formFloor"
                type="number"
                min="1"
                max="50"
                required
                class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Hạng phòng *</label>
            <select
              v-model.number="formRoomTypeId"
              required
              class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
            >
              <option :value="1">Standard (Phổ thông)</option>
              <option :value="2">Superior (Cao cấp)</option>
              <option :value="3">Deluxe (Sang trọng)</option>
              <option :value="4">Suite (Thượng hạng)</option>
            </select>
          </div>

          <div v-if="isEditing" class="flex items-center space-x-2 pt-1">
            <input
              v-model="formIsActive"
              type="checkbox"
              id="isActiveToggle"
              class="w-4 h-4 text-sky-600 rounded border-slate-300 focus:ring-sky-500"
            />
            <label for="isActiveToggle" class="font-medium text-slate-700 cursor-pointer">
              Đang hoạt động (Bỏ tick để ngưng dùng phòng)
            </label>
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Ghi chú tiện nghi / vị trí</label>
            <textarea
              v-model="formNotes"
              rows="2"
              placeholder="VD: Gần thang máy, view công viên..."
              class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
            ></textarea>
          </div>

          <!-- Affected Bookings Warning if Conflict -->
          <div v-if="conflictBookings.length" class="p-3.5 bg-rose-50 border border-rose-200 rounded-xl space-y-2 text-rose-800">
            <div class="font-bold flex items-center space-x-1.5">
              <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>Không thể ngưng dùng / đổi hạng phòng (ROOM_HAS_BOOKINGS)</span>
            </div>
            <p class="text-[11px] leading-relaxed">
              Phòng hiện còn <strong>{{ conflictBookings.length }} đơn tương lai</strong>. Vui lòng chuyển các đơn này sang phòng khác trước khi thực hiện.
            </p>
            <div class="space-y-1 pt-1 border-t border-rose-200/70 font-mono text-[10px]">
              <div v-for="cb in conflictBookings" :key="cb.bookingId" class="flex justify-between">
                <span>{{ cb.bookingCode }} ({{ cb.customerName }})</span>
                <span>{{ cb.from?.slice(0, 10) }}</span>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              @click="showModal = false"
              class="px-4 py-2 border border-slate-300 text-slate-700 rounded-xl font-medium hover:bg-slate-50 transition"
            >
              Hủy
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-5 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl font-semibold shadow transition disabled:opacity-50 flex items-center space-x-1.5"
            >
              <div v-if="saving" class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
              <span>{{ saving ? 'Đang lưu...' : 'Lưu thông tin' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Plus, Search, Building2, AlertCircle } from 'lucide-vue-next';
import apiClient from '../../api/client';
import StatusBadge from '../../components/StatusBadge.vue';

const rooms = ref([]);
const totalRooms = ref(0);
const totalPages = ref(1);
const currentPage = ref(1);
const pageSize = ref(15);
const loading = ref(false);
const errorMessage = ref('');

// Filters
const searchQuery = ref('');
const filterFloor = ref('');
const filterType = ref('');
const filterStatus = ref('');
const filterActive = ref('');

// Modal Form
const showModal = ref(false);
const isEditing = ref(false);
const editingRoomId = ref(null);
const formRoomNumber = ref('');
const formFloor = ref(1);
const formRoomTypeId = ref(1);
const formIsActive = ref(true);
const formNotes = ref('');
const saving = ref(false);
const conflictBookings = ref([]);

const fetchRooms = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value
    };
    if (searchQuery.value.trim()) params.q = searchQuery.value.trim();
    if (filterFloor.value !== '') params.floor = Number(filterFloor.value);
    if (filterType.value) params.roomType = filterType.value;
    if (filterStatus.value) params.status = filterStatus.value;
    if (filterActive.value !== '') params.isActive = filterActive.value === 'true';

    const res = await apiClient.get('/rooms', { params });
    rooms.value = res.items || [];
    totalRooms.value = res.total || 0;
    totalPages.value = Math.ceil(totalRooms.value / pageSize.value) || 1;
  } catch (err) {
    errorMessage.value = err.message || 'Không thể tải danh sách phòng';
  } finally {
    loading.value = false;
  }
};

const handleFilter = () => {
  currentPage.value = 1;
  fetchRooms();
};

const goToPage = (p) => {
  if (p < 1 || p > totalPages.value) return;
  currentPage.value = p;
  fetchRooms();
};

const openCreateModal = () => {
  isEditing.value = false;
  editingRoomId.value = null;
  formRoomNumber.value = '';
  formFloor.value = 1;
  formRoomTypeId.value = 1;
  formIsActive.value = true;
  formNotes.value = '';
  conflictBookings.value = [];
  showModal.value = true;
};

const openEditModal = (room) => {
  isEditing.value = true;
  editingRoomId.value = room.roomId;
  formRoomNumber.value = room.roomNumber;
  formFloor.value = room.floor;
  formRoomTypeId.value = room.roomTypeId;
  formIsActive.value = room.isActive;
  formNotes.value = room.notes || '';
  conflictBookings.value = [];
  showModal.value = true;
};

const handleSaveRoom = async () => {
  saving.value = true;
  errorMessage.value = '';
  conflictBookings.value = [];

  try {
    if (isEditing.value) {
      await apiClient.put(`/rooms/${editingRoomId.value}`, {
        roomNumber: formRoomNumber.value,
        floor: formFloor.value,
        roomTypeId: formRoomTypeId.value,
        isActive: formIsActive.value,
        notes: formNotes.value
      });
    } else {
      await apiClient.post('/rooms', {
        roomNumber: formRoomNumber.value,
        floor: formFloor.value,
        roomTypeId: formRoomTypeId.value,
        notes: formNotes.value
      });
    }
    showModal.value = false;
    await fetchRooms();
  } catch (err) {
    errorMessage.value = err.message || 'Lưu thông tin phòng thất bại';
    if (err.data?.length) {
      conflictBookings.value = err.data;
    }
  } finally {
    saving.value = false;
  }
};

onMounted(fetchRooms);
</script>
