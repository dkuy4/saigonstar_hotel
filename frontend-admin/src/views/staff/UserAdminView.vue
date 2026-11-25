<template>
  <div class="space-y-6 pb-12">
    <!-- Header & Subtitle -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight">Tài khoản nhân viên</h1>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 text-sky-800">
            F17 Quản trị
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Quản lý tài khoản, cấp phát quyền hạn, khóa an toàn và đặt lại mật khẩu nhân viên (FR-30, US-26, NFR-11, NFR-12)
        </p>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex flex-wrap items-center gap-2">
        <router-link
          to="/nv/quan-ly/phong"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Danh mục phòng (16.1)
        </router-link>
        <router-link
          to="/nv/quan-ly/hang-phong"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Hạng phòng (16.2)
        </router-link>
        <router-link
          to="/nv/quan-ly/bang-gia"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Bảng giá (16.3)
        </router-link>
        <router-link
          to="/nv/quan-ly/tham-so"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Tham số & VAT (16.4)
        </router-link>
        <router-link
          to="/nv/quan-ly/ban-dich"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Bản dịch & Email (16.5)
        </router-link>
        <span class="px-3 py-2 bg-sky-600 text-white rounded-xl text-xs font-semibold shadow-sm">
          Tài khoản nhân viên (F17)
        </span>
      </div>
    </div>

    <!-- Alert Notifications -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between shadow-sm">
      <div class="flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0" />
        <span>{{ errorMessage }}</span>
      </div>
      <button @click="errorMessage = ''" class="font-bold text-rose-600 hover:text-rose-800">✕</button>
    </div>

    <div v-if="successMessage" class="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between shadow-sm">
      <div class="flex items-center space-x-2">
        <CheckCircle2 class="w-4 h-4 text-emerald-600 flex-shrink-0" />
        <span>{{ successMessage }}</span>
      </div>
      <button @click="successMessage = ''" class="font-bold text-emerald-600 hover:text-emerald-800">✕</button>
    </div>

    <!-- Stats Summary Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
      <div class="p-3 bg-white border border-slate-200 rounded-2xl shadow-sm">
        <div class="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Tổng nhân viên</div>
        <div class="text-xl font-black text-slate-900 mt-1">{{ users.length }}</div>
      </div>
      <div class="p-3 bg-white border border-purple-100 rounded-2xl shadow-sm bg-purple-50/20">
        <div class="text-[11px] font-medium text-purple-700 uppercase tracking-wider">Quản lý</div>
        <div class="text-xl font-black text-purple-800 mt-1">{{ countRole('QUAN_LY') }}</div>
      </div>
      <div class="p-3 bg-white border border-sky-100 rounded-2xl shadow-sm bg-sky-50/20">
        <div class="text-[11px] font-medium text-sky-700 uppercase tracking-wider">Lễ tân</div>
        <div class="text-xl font-black text-sky-800 mt-1">{{ countRole('LE_TAN') }}</div>
      </div>
      <div class="p-3 bg-white border border-emerald-100 rounded-2xl shadow-sm bg-emerald-50/20">
        <div class="text-[11px] font-medium text-emerald-700 uppercase tracking-wider">Buồng phòng</div>
        <div class="text-xl font-black text-emerald-800 mt-1">{{ countRole('BUONG_PHONG') }}</div>
      </div>
      <div class="p-3 bg-white border border-rose-100 rounded-2xl shadow-sm bg-rose-50/20 col-span-2 sm:col-span-1">
        <div class="text-[11px] font-medium text-rose-700 uppercase tracking-wider">Bị khóa</div>
        <div class="text-xl font-black text-rose-800 mt-1">{{ countLocked }}</div>
      </div>
    </div>

    <!-- Filters and Action Toolbar -->
    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2.5 flex-1">
        <!-- Search Input -->
        <div class="relative min-w-[220px] flex-1 max-w-xs">
          <Search class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            v-model="filters.q"
            @input="debouncedFetch"
            type="text"
            placeholder="Tìm tên đăng nhập hoặc họ tên..."
            class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
          />
        </div>

        <!-- Role Filter -->
        <select
          v-model="filters.vaiTro"
          @change="fetchUsers"
          class="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        >
          <option value="">Tất cả vai trò</option>
          <option value="QUAN_LY">Quản lý (QUAN_LY)</option>
          <option value="LE_TAN">Lễ tân (LE_TAN)</option>
          <option value="BUONG_PHONG">Buồng phòng (BUONG_PHONG)</option>
        </select>

        <!-- Status Filter -->
        <select
          v-model="filters.trangThai"
          @change="fetchUsers"
          class="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        >
          <option value="">Tất cả trạng thái</option>
          <option value="HOAT_DONG">Đang hoạt động</option>
          <option value="KHOA">Đã khóa</option>
        </select>

        <!-- Reset Button -->
        <button
          v-if="filters.q || filters.vaiTro || filters.trangThai"
          @click="resetFilters"
          class="px-2.5 py-2 text-xs text-slate-500 hover:text-slate-800 transition"
        >
          Xóa lọc
        </button>
      </div>

      <!-- Action Button -->
      <div class="flex items-center space-x-2">
        <button
          @click="fetchUsers"
          :disabled="loading"
          class="p-2 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-xl text-xs font-semibold transition"
          title="Tải lại danh sách"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
        </button>
        <button
          @click="openCreateModal"
          class="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-sm transition flex items-center space-x-1.5"
        >
          <UserPlus class="w-4 h-4" />
          <span>Thêm tài khoản mới</span>
        </button>
      </div>
    </div>

    <!-- Users Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50/80 text-slate-600 uppercase font-semibold border-b border-slate-200">
            <tr>
              <th class="py-3 px-4">Tên đăng nhập</th>
              <th class="py-3 px-4">Họ và tên</th>
              <th class="py-3 px-4 text-center">Vai trò</th>
              <th class="py-3 px-4 text-center">Trạng thái</th>
              <th class="py-3 px-4 text-center">Lần sai</th>
              <th class="py-3 px-4 text-center">Đổi MK</th>
              <th class="py-3 px-4">Ngày tạo</th>
              <th class="py-3 px-4 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-700">
            <tr v-if="loading" class="text-center py-8">
              <td colspan="8" class="py-8 text-slate-400">
                <div class="inline-flex items-center space-x-2">
                  <RefreshCw class="w-4 h-4 animate-spin text-sky-600" />
                  <span>Đang tải danh sách tài khoản...</span>
                </div>
              </td>
            </tr>
            <tr v-else-if="users.length === 0" class="text-center py-8">
              <td colspan="8" class="py-8 text-slate-400">
                Không tìm thấy tài khoản nhân viên nào phù hợp bộ lọc
              </td>
            </tr>
            <tr
              v-else
              v-for="u in users"
              :key="u.id"
              class="hover:bg-slate-50/60 transition group"
              :class="{ 'bg-rose-50/20': u.trangThai === 'KHOA' }"
            >
              <!-- Username -->
              <td class="py-3 px-4 font-mono font-bold text-slate-900">
                <div class="flex items-center space-x-1.5">
                  <span>{{ u.tenDangNhap }}</span>
                  <span
                    v-if="u.id === currentUserId"
                    class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-sky-100 text-sky-800"
                    title="Tài khoản đang đăng nhập hiện tại"
                  >
                    Bạn
                  </span>
                </div>
              </td>

              <!-- Full Name -->
              <td class="py-3 px-4 font-medium text-slate-800">
                {{ u.hoTen }}
              </td>

              <!-- Role Badge -->
              <td class="py-3 px-4 text-center">
                <span
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold"
                  :class="{
                    'bg-purple-100 text-purple-800 border border-purple-200': u.vaiTro === 'QUAN_LY',
                    'bg-sky-100 text-sky-800 border border-sky-200': u.vaiTro === 'LE_TAN',
                    'bg-emerald-100 text-emerald-800 border border-emerald-200': u.vaiTro === 'BUONG_PHONG'
                  }"
                >
                  {{ formatRole(u.vaiTro) }}
                </span>
              </td>

              <!-- Status Badge -->
              <td class="py-3 px-4 text-center">
                <span
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold"
                  :class="u.trangThai === 'HOAT_DONG' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800 font-bold'"
                >
                  {{ u.trangThai === 'HOAT_DONG' ? 'Hoạt động' : 'Đã khóa' }}
                </span>
              </td>

              <!-- Failed attempts -->
              <td class="py-3 px-4 text-center font-mono">
                <span
                  class="px-2 py-0.5 rounded-md text-[11px]"
                  :class="u.soLanSai > 0 ? 'bg-amber-100 text-amber-900 font-bold' : 'text-slate-400'"
                >
                  {{ u.soLanSai }}
                </span>
              </td>

              <!-- Mandatory password change badge -->
              <td class="py-3 px-4 text-center">
                <span
                  v-if="u.phaiDoiMatKhau"
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200"
                  title="Nhân viên chưa đổi mật khẩu tạm thời"
                >
                  Bắt buộc
                </span>
                <span v-else class="text-slate-400 text-[11px]">Đã đổi</span>
              </td>

              <!-- Created At -->
              <td class="py-3 px-4 text-slate-500 whitespace-nowrap text-[11px]">
                {{ formatDate(u.ngayTao) }}
              </td>

              <!-- Actions -->
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <div class="inline-flex items-center space-x-1.5">
                  <!-- Edit button -->
                  <button
                    @click="openEditModal(u)"
                    class="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
                    title="Chỉnh sửa họ tên và vai trò"
                  >
                    Sửa
                  </button>

                  <!-- Reset Password button -->
                  <button
                    @click="openResetModal(u)"
                    class="px-2.5 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 rounded-lg text-xs font-semibold transition flex items-center space-x-1"
                    title="Đặt lại mật khẩu tạm thời"
                  >
                    <Key class="w-3.5 h-3.5" />
                    <span>Đặt lại MK</span>
                  </button>

                  <!-- Lock / Unlock Toggle button -->
                  <button
                    v-if="u.trangThai === 'HOAT_DONG'"
                    @click="openLockModal(u, true)"
                    :disabled="u.id === currentUserId"
                    class="px-2.5 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold transition disabled:opacity-40 disabled:cursor-not-allowed"
                    :title="u.id === currentUserId ? 'Không thể tự khóa tài khoản của chính mình' : 'Khóa tài khoản nhân viên'"
                  >
                    Khóa
                  </button>
                  <button
                    v-else
                    @click="openLockModal(u, false)"
                    class="px-2.5 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-semibold transition"
                    title="Mở khóa tài khoản nhân viên"
                  >
                    Mở khóa
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal 1: Create Employee Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-md w-full overflow-hidden">
        <div class="p-6 border-b border-slate-100 flex items-center justify-between">
          <div class="flex items-center space-x-2.5">
            <div class="w-8 h-8 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center">
              <UserPlus class="w-4 h-4" />
            </div>
            <h3 class="text-base font-bold text-slate-900">Thêm tài khoản nhân viên mới</h3>
          </div>
          <button @click="closeCreateModal" class="text-slate-400 hover:text-slate-600 font-bold">✕</button>
        </div>

        <form @submit.prevent="submitCreateUser" class="p-6 space-y-4">
          <div v-if="createError" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
            <AlertCircle class="w-4 h-4 flex-shrink-0" />
            <span>{{ createError }}</span>
          </div>

          <!-- Username -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Tên đăng nhập <span class="text-rose-500">*</span>
            </label>
            <input
              v-model="createForm.tenDangNhap"
              type="text"
              required
              placeholder="VD: letan_mai, buongphong_01"
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
            />
            <p class="text-[11px] text-slate-400 mt-1">Chữ thường (a-z), chữ số (0-9) và dấu gạch dưới (_), độ dài 3-30 ký tự.</p>
          </div>

          <!-- Full Name -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Họ và tên <span class="text-rose-500">*</span>
            </label>
            <input
              v-model="createForm.hoTen"
              type="text"
              required
              placeholder="VD: Nguyễn Thị Mai"
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
            />
          </div>

          <!-- Role -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Vai trò công việc <span class="text-rose-500">*</span>
            </label>
            <select
              v-model="createForm.vaiTro"
              required
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
            >
              <option value="LE_TAN">Lễ tân (LE_TAN)</option>
              <option value="BUONG_PHONG">Buồng phòng (BUONG_PHONG)</option>
              <option value="QUAN_LY">Quản lý (QUAN_LY)</option>
            </select>
          </div>

          <!-- Optional initial password -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Mật khẩu khởi tạo (tùy chọn)
            </label>
            <input
              v-model="createForm.matKhau"
              type="text"
              placeholder="Để trống để hệ thống tự sinh ngẫu nhiên"
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
            />
            <p class="text-[11px] text-slate-400 mt-1">Nếu để trống, hệ thống sẽ tự sinh mật khẩu tạm thời 12 ký tự bảo mật cao.</p>
          </div>

          <!-- Footer Buttons -->
          <div class="pt-3 flex items-center justify-end space-x-2 border-t border-slate-100">
            <button
              type="button"
              @click="closeCreateModal"
              class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 transition"
            >
              Hủy
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-sm transition disabled:opacity-50 flex items-center space-x-1.5"
            >
              <RefreshCw v-if="submitting" class="w-3.5 h-3.5 animate-spin" />
              <span>Tạo tài khoản</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal 2: Temporary Password Display Modal (Shown only once) -->
    <div
      v-if="showTempPasswordModal"
      class="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div class="p-6 bg-amber-50/70 border-b border-amber-100 flex items-center space-x-3">
          <div class="w-10 h-10 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center shadow-sm">
            <Key class="w-5 h-5 text-amber-700" />
          </div>
          <div>
            <h3 class="text-base font-bold text-amber-900">{{ tempPasswordTitle }}</h3>
            <p class="text-xs text-amber-700">Mật khẩu tạm thời cho nhân viên</p>
          </div>
        </div>

        <div class="p-6 space-y-4">
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
            <div class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Tài khoản</div>
            <div class="font-mono text-sm font-bold text-slate-900">{{ tempPasswordUsername }}</div>

            <div class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider pt-2">Mật khẩu tạm</div>
            <div class="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-xl">
              <span class="font-mono text-base font-black text-sky-700 tracking-wider select-all">{{ tempPasswordValue }}</span>
              <button
                @click="copyPasswordToClipboard"
                class="px-3 py-1.5 bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200 rounded-lg text-xs font-semibold transition flex items-center space-x-1"
              >
                <Check v-if="copied" class="w-3.5 h-3.5 text-emerald-600" />
                <Copy v-else class="w-3.5 h-3.5" />
                <span>{{ copied ? 'Đã sao chép' : 'Sao chép' }}</span>
              </button>
            </div>
          </div>

          <div class="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-start space-x-2">
            <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div class="leading-relaxed">
              <span class="font-bold">Lưu ý quan trọng:</span> Mật khẩu này chỉ được hiển thị <span class="font-bold underline">một lần duy nhất</span> tại đây. Vui lòng sao chép và gửi trực tiếp cho nhân viên. Khi đăng nhập lần đầu, hệ thống sẽ bắt buộc đổi mật khẩu mới.
            </div>
          </div>

          <div class="pt-2 flex justify-end">
            <button
              @click="closeTempPasswordModal"
              class="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-sm transition"
            >
              Tôi đã sao chép mật khẩu / Đóng hộp thoại
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal 3: Edit Employee Modal -->
    <div
      v-if="showEditModal"
      class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-md w-full overflow-hidden">
        <div class="p-6 border-b border-slate-100 flex items-center justify-between">
          <div class="flex items-center space-x-2.5">
            <div class="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
              <Edit class="w-4 h-4" />
            </div>
            <h3 class="text-base font-bold text-slate-900">Sửa thông tin tài khoản</h3>
          </div>
          <button @click="closeEditModal" class="text-slate-400 hover:text-slate-600 font-bold">✕</button>
        </div>

        <form @submit.prevent="submitEditUser" class="p-6 space-y-4">
          <div v-if="editError" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
            <AlertCircle class="w-4 h-4 flex-shrink-0" />
            <span>{{ editError }}</span>
          </div>

          <!-- Readonly Username -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Tên đăng nhập</label>
            <input
              :value="editForm.tenDangNhap"
              disabled
              class="w-full px-3.5 py-2.5 bg-slate-100 border border-slate-200 rounded-xl text-xs font-mono text-slate-500 cursor-not-allowed outline-none"
            />
          </div>

          <!-- Full Name -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Họ và tên <span class="text-rose-500">*</span>
            </label>
            <input
              v-model="editForm.hoTen"
              type="text"
              required
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
            />
          </div>

          <!-- Role -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Vai trò công việc <span class="text-rose-500">*</span>
            </label>
            <select
              v-model="editForm.vaiTro"
              :disabled="editForm.id === currentUserId"
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition disabled:bg-slate-100 disabled:text-slate-500 disabled:cursor-not-allowed"
            >
              <option value="LE_TAN">Lễ tân (LE_TAN)</option>
              <option value="BUONG_PHONG">Buồng phòng (BUONG_PHONG)</option>
              <option value="QUAN_LY">Quản lý (QUAN_LY)</option>
            </select>
            <p v-if="editForm.id === currentUserId" class="text-[11px] text-amber-600 mt-1">
              Quy tắc hệ thống: Bạn không thể tự thay đổi vai trò của chính mình.
            </p>
          </div>

          <!-- Footer Buttons -->
          <div class="pt-3 flex items-center justify-end space-x-2 border-t border-slate-100">
            <button
              type="button"
              @click="closeEditModal"
              class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 transition"
            >
              Hủy
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-sm transition disabled:opacity-50 flex items-center space-x-1.5"
            >
              <RefreshCw v-if="submitting" class="w-3.5 h-3.5 animate-spin" />
              <span>Lưu thay đổi</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal 4: Lock / Unlock Confirmation Modal -->
    <div
      v-if="showLockModal"
      class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-sm w-full overflow-hidden p-6 space-y-4">
        <div class="flex items-center space-x-3">
          <div
            class="w-10 h-10 rounded-2xl flex items-center justify-center shadow-sm"
            :class="lockActionIsLock ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'"
          >
            <Lock v-if="lockActionIsLock" class="w-5 h-5" />
            <Unlock v-else class="w-5 h-5" />
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-900">
              {{ lockActionIsLock ? 'Xác nhận khóa tài khoản' : 'Xác nhận mở khóa' }}
            </h3>
            <p class="text-xs text-slate-500 font-mono">{{ lockTargetUser?.tenDangNhap }}</p>
          </div>
        </div>

        <p class="text-xs text-slate-600 leading-relaxed">
          <span v-if="lockActionIsLock">
            Bạn có chắc chắn muốn khóa tài khoản của <b>{{ lockTargetUser?.hoTen }}</b>? Thao tác này có hiệu lực ngay lập tức, vô hiệu hóa phiên đăng nhập hiện hành.
          </span>
          <span v-else>
            Bạn có chắc chắn muốn mở khóa cho tài khoản <b>{{ lockTargetUser?.hoTen }}</b>? Bộ đếm lần đăng nhập sai sẽ được đặt lại về 0.
          </span>
        </p>

        <div v-if="lockError" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          <span>{{ lockError }}</span>
        </div>

        <div class="pt-2 flex items-center justify-end space-x-2">
          <button
            @click="showLockModal = false"
            class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 transition"
          >
            Hủy
          </button>
          <button
            @click="submitLockToggle"
            :disabled="submitting"
            class="px-4 py-2 rounded-xl text-xs font-semibold shadow-sm transition disabled:opacity-50"
            :class="lockActionIsLock ? 'bg-rose-600 hover:bg-rose-700 text-white' : 'bg-emerald-600 hover:bg-emerald-700 text-white'"
          >
            {{ lockActionIsLock ? 'Xác nhận khóa' : 'Mở khóa ngay' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal 5: Reset Password Confirmation Modal -->
    <div
      v-if="showResetModal"
      class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-sm w-full overflow-hidden p-6 space-y-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center shadow-sm">
            <Key class="w-5 h-5 text-amber-700" />
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-900">Đặt lại mật khẩu</h3>
            <p class="text-xs text-slate-500 font-mono">{{ resetTargetUser?.tenDangNhap }}</p>
          </div>
        </div>

        <p class="text-xs text-slate-600 leading-relaxed">
          Hệ thống sẽ cấp một mật khẩu tạm ngẫu nhiên mới cho <b>{{ resetTargetUser?.hoTen }}</b>. Mật khẩu hiện tại sẽ bị hủy và nhân viên được yêu cầu đổi mật khẩu ở lần đăng nhập tới.
        </p>

        <div v-if="resetError" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          <span>{{ resetError }}</span>
        </div>

        <div class="pt-2 flex items-center justify-end space-x-2">
          <button
            @click="showResetModal = false"
            class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 transition"
          >
            Hủy
          </button>
          <button
            @click="submitResetPassword"
            :disabled="submitting"
            class="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shadow-sm transition disabled:opacity-50 flex items-center space-x-1"
          >
            <RefreshCw v-if="submitting" class="w-3.5 h-3.5 animate-spin" />
            <span>Sinh mật khẩu mới</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import {
  UserPlus,
  Key,
  Lock,
  Unlock,
  Edit,
  Copy,
  Check,
  Search,
  RefreshCw,
  AlertCircle,
  CheckCircle2
} from 'lucide-vue-next';
import apiClient from '../../api/client';
import { useAuthStore } from '../../stores/auth';

const authStore = useAuthStore();
const currentUserId = computed(() => authStore.user?.id || authStore.user?.user_id);

// State
const users = ref([]);
const loading = ref(false);
const submitting = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

// Filters
const filters = reactive({
  q: '',
  vaiTro: '',
  trangThai: ''
});

// Create Modal State
const showCreateModal = ref(false);
const createError = ref('');
const createForm = reactive({
  tenDangNhap: '',
  hoTen: '',
  vaiTro: 'LE_TAN',
  matKhau: ''
});

// Temp Password Modal State
const showTempPasswordModal = ref(false);
const tempPasswordTitle = ref('');
const tempPasswordUsername = ref('');
const tempPasswordValue = ref('');
const copied = ref(false);

// Edit Modal State
const showEditModal = ref(false);
const editError = ref('');
const editForm = reactive({
  id: null,
  tenDangNhap: '',
  hoTen: '',
  vaiTro: 'LE_TAN'
});

// Lock Modal State
const showLockModal = ref(false);
const lockTargetUser = ref(null);
const lockActionIsLock = ref(true);
const lockError = ref('');

// Reset Password Modal State
const showResetModal = ref(false);
const resetTargetUser = ref(null);
const resetError = ref('');

// Formatters
const formatRole = (role) => {
  switch (role) {
    case 'QUAN_LY':
      return 'Quản lý';
    case 'LE_TAN':
      return 'Lễ tân';
    case 'BUONG_PHONG':
      return 'Buồng phòng';
    default:
      return role;
  }
};

const formatDate = (isoStr) => {
  if (!isoStr) return '-';
  try {
    const d = new Date(isoStr);
    return d.toLocaleString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  } catch {
    return isoStr;
  }
};

const countRole = (role) => {
  return users.value.filter((u) => u.vaiTro === role).length;
};

const countLocked = computed(() => {
  return users.value.filter((u) => u.trangThai === 'KHOA').length;
});

// Fetch Users API
const fetchUsers = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const params = {};
    if (filters.vaiTro) params.vaiTro = filters.vaiTro;
    if (filters.trangThai) params.trangThai = filters.trangThai;
    if (filters.q && filters.q.trim()) params.q = filters.q.trim();

    const res = await apiClient.get('/users', { params });
    users.value = res.data || [];
  } catch (err) {
    errorMessage.value = err.message || 'Không thể tải danh sách tài khoản nhân viên';
  } finally {
    loading.value = false;
  }
};

let debounceTimer = null;
const debouncedFetch = () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetchUsers();
  }, 300);
};

const resetFilters = () => {
  filters.q = '';
  filters.vaiTro = '';
  filters.trangThai = '';
  fetchUsers();
};

// Create User Handlers
const openCreateModal = () => {
  createForm.tenDangNhap = '';
  createForm.hoTen = '';
  createForm.vaiTro = 'LE_TAN';
  createForm.matKhau = '';
  createError.value = '';
  showCreateModal.value = true;
};

const closeCreateModal = () => {
  showCreateModal.value = false;
  createError.value = '';
};

const submitCreateUser = async () => {
  submitting.value = true;
  createError.value = '';
  try {
    const payload = {
      tenDangNhap: createForm.tenDangNhap.trim().toLowerCase(),
      hoTen: createForm.hoTen.trim(),
      vaiTro: createForm.vaiTro,
      matKhau: createForm.matKhau.trim() || undefined
    };

    const res = await apiClient.post('/users', payload);
    closeCreateModal();
    successMessage.value = `Tạo tài khoản "${payload.tenDangNhap}" thành công!`;
    fetchUsers();

    // Show temporary password modal
    tempPasswordTitle.value = 'Tạo tài khoản thành công';
    tempPasswordUsername.value = payload.tenDangNhap;
    tempPasswordValue.value = res.matKhauTam;
    copied.value = false;
    showTempPasswordModal.value = true;
  } catch (err) {
    createError.value = err.message || 'Không thể tạo tài khoản nhân viên';
  } finally {
    submitting.value = false;
  }
};

// Copy Password
const copyPasswordToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(tempPasswordValue.value);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2500);
  } catch {
    // Fallback if clipboard API denied
    copied.value = true;
  }
};

const closeTempPasswordModal = () => {
  showTempPasswordModal.value = false;
};

// Edit User Handlers
const openEditModal = (u) => {
  editForm.id = u.id;
  editForm.tenDangNhap = u.tenDangNhap;
  editForm.hoTen = u.hoTen;
  editForm.vaiTro = u.vaiTro;
  editError.value = '';
  showEditModal.value = true;
};

const closeEditModal = () => {
  showEditModal.value = false;
  editError.value = '';
};

const submitEditUser = async () => {
  submitting.value = true;
  editError.value = '';
  try {
    await apiClient.put(`/users/${editForm.id}`, {
      hoTen: editForm.hoTen.trim(),
      vaiTro: editForm.vaiTro
    });
    closeEditModal();
    successMessage.value = `Cập nhật thông tin tài khoản "${editForm.tenDangNhap}" thành công!`;
    fetchUsers();
  } catch (err) {
    editError.value = err.message || 'Không thể cập nhật tài khoản';
  } finally {
    submitting.value = false;
  }
};

// Lock Handlers
const openLockModal = (u, isLock) => {
  lockTargetUser.value = u;
  lockActionIsLock.value = isLock;
  lockError.value = '';
  showLockModal.value = true;
};

const submitLockToggle = async () => {
  if (!lockTargetUser.value) return;
  submitting.value = true;
  lockError.value = '';
  try {
    await apiClient.post(`/users/${lockTargetUser.value.id}/lock`, {
      khoa: lockActionIsLock.value
    });
    showLockModal.value = false;
    const actionText = lockActionIsLock.value ? 'Khóa' : 'Mở khóa';
    successMessage.value = `${actionText} tài khoản "${lockTargetUser.value.tenDangNhap}" thành công!`;
    fetchUsers();
  } catch (err) {
    lockError.value = err.message || 'Thao tác khóa/mở khóa thất bại';
  } finally {
    submitting.value = false;
  }
};

// Reset Password Handlers
const openResetModal = (u) => {
  resetTargetUser.value = u;
  resetError.value = '';
  showResetModal.value = true;
};

const submitResetPassword = async () => {
  if (!resetTargetUser.value) return;
  submitting.value = true;
  resetError.value = '';
  try {
    const res = await apiClient.post(`/users/${resetTargetUser.value.id}/reset-password`);
    const username = resetTargetUser.value.tenDangNhap;
    showResetModal.value = false;
    successMessage.value = `Đặt lại mật khẩu cho "${username}" thành công!`;
    fetchUsers();

    // Show temporary password modal
    tempPasswordTitle.value = 'Đặt lại mật khẩu thành công';
    tempPasswordUsername.value = username;
    tempPasswordValue.value = res.matKhauTam;
    copied.value = false;
    showTempPasswordModal.value = true;
  } catch (err) {
    resetError.value = err.message || 'Đặt lại mật khẩu thất bại';
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  fetchUsers();
});
</script>
