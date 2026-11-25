<template>
  <div class="space-y-6 pb-12">
    <!-- Header & Action Toolbar -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight">Nhật ký kiểm toán hệ thống</h1>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800">
            F19 Admin - Bất biến (AC-14)
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Lưu vết toàn bộ thao tác thêm, sửa, đổi trạng thái, xóa trên cơ sở dữ liệu (FR-45, FR-47, US-23, AC-14)
        </p>
      </div>

      <!-- Quick Admin Navigation Links -->
      <div class="flex flex-wrap items-center gap-2">
        <router-link
          to="/nv/quan-ly/phong"
          class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition"
        >
          Phòng (16.1)
        </router-link>
        <router-link
          to="/nv/quan-ly/hang-phong"
          class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition"
        >
          Hạng phòng (16.2)
        </router-link>
        <router-link
          to="/nv/quan-ly/bang-gia"
          class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition"
        >
          Bảng giá (16.3)
        </router-link>
        <router-link
          to="/nv/quan-ly/tai-khoan"
          class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition"
        >
          Tài khoản (F17)
        </router-link>
        <router-link
          to="/nv/bao-cao"
          class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition"
        >
          Báo cáo (F18)
        </router-link>
      </div>
    </div>

    <!-- Mode Tabs: Dòng nhật ký vs Tua lại trạng thái (State-At) -->
    <div class="border-b border-slate-200 bg-white rounded-t-xl px-4 pt-2">
      <nav class="flex space-x-6">
        <button
          type="button"
          @click="activeMode = 'logs'"
          :class="[
            activeMode === 'logs'
              ? 'border-indigo-600 text-indigo-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 font-medium',
            'whitespace-nowrap py-3 px-1 border-b-2 text-sm flex items-center gap-2 transition'
          ]"
        >
          <History class="w-4 h-4" />
          <span>Danh sách nhật ký thao tác</span>
          <span class="ml-1.5 px-2 py-0.5 text-xs font-semibold bg-indigo-50 text-indigo-600 rounded-full">
            {{ totalLogs }}
          </span>
        </button>

        <button
          type="button"
          @click="activeMode = 'state_at'"
          :class="[
            activeMode === 'state_at'
              ? 'border-indigo-600 text-indigo-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 font-medium',
            'whitespace-nowrap py-3 px-1 border-b-2 text-sm flex items-center gap-2 transition'
          ]"
        >
          <Clock class="w-4 h-4" />
          <span>Tua lại trạng thái tại thời điểm (BR-46)</span>
        </button>
      </nav>
    </div>

    <!-- TAB 1: DANH SÁCH NHẬT KÝ THAO TÁC -->
    <div v-if="activeMode === 'logs'" class="space-y-4">
      <!-- Bộ lọc nâng cao -->
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <!-- Bảng -->
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Bảng dữ liệu</label>
            <select
              v-model="filters.bang"
              class="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="">Tất cả các bảng</option>
              <option v-for="t in availableTables" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>

          <!-- Khóa dòng -->
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Khóa dòng (ID)</label>
            <input
              type="text"
              v-model="filters.khoaDong"
              placeholder="VD: 1054, 101..."
              class="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <!-- Hành động -->
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Hành động</label>
            <select
              v-model="filters.hanhDong"
              class="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="">Tất cả hành động</option>
              <option v-for="a in availableActions" :key="a" :value="a">{{ a }}</option>
            </select>
          </div>

          <!-- Vai trò -->
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Vai trò</label>
            <select
              v-model="filters.vaiTro"
              class="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="">Tất cả vai trò</option>
              <option value="QUAN_LY">Quản lý (QUAN_LY)</option>
              <option value="LE_TAN">Lễ tân (LE_TAN)</option>
              <option value="BUONG_PHONG">Buồng phòng (BUONG_PHONG)</option>
              <option value="KHACH">Khách hàng (KHACH)</option>
              <option value="HE_THONG">Hệ thống (HE_THONG)</option>
            </select>
          </div>

          <!-- Kênh -->
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Kênh thao tác</label>
            <select
              v-model="filters.kenh"
              class="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="">Tất cả các kênh</option>
              <option value="WEB">Web khách (WEB)</option>
              <option value="QUAY">Tại quầy lễ tân (QUAY)</option>
              <option value="HE_THONG">Hệ thống ngầm (HE_THONG)</option>
            </select>
          </div>

          <!-- Người dùng / Search -->
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">Người thực hiện</label>
            <input
              type="text"
              v-model="filters.nguoiDung"
              placeholder="Username hoặc tên..."
              class="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
          <div class="flex flex-wrap items-center gap-3">
            <div class="flex items-center gap-2">
              <label class="text-xs text-slate-500 font-medium">Từ ngày:</label>
              <input
                type="date"
                v-model="filters.tuNgay"
                class="text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            <div class="flex items-center gap-2">
              <label class="text-xs text-slate-500 font-medium">Đến ngày:</label>
              <input
                type="date"
                v-model="filters.denNgay"
                class="text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            <button
              type="button"
              @click="applyFilters"
              class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition shadow-sm flex items-center gap-1.5"
            >
              <Search class="w-3.5 h-3.5" />
              <span>Áp dụng lọc</span>
            </button>

            <button
              type="button"
              @click="resetFilters"
              class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-xs font-medium transition"
            >
              Đặt lại
            </button>
          </div>

          <div class="flex items-center gap-2">
            <label class="text-xs text-slate-500">Hiển thị:</label>
            <select
              v-model="pagination.pageSize"
              @change="applyFilters"
              class="text-xs px-2 py-1 border border-slate-300 rounded bg-white outline-none"
            >
              <option :value="10">10 dòng</option>
              <option :value="20">20 dòng</option>
              <option :value="50">50 dòng</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Loading Indicator -->
      <div v-if="loading" class="bg-white p-12 rounded-xl border border-slate-200 text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent mb-3"></div>
        <p class="text-sm text-slate-500">Đang tải nhật ký kiểm toán...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
        <div class="font-semibold mb-1">Lỗi tải dữ liệu</div>
        <div>{{ error }}</div>
        <button @click="fetchLogs" class="mt-2 text-xs font-semibold underline hover:text-red-800">Thử lại</button>
      </div>

      <!-- Data Table -->
      <div v-else class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th class="py-3 px-4">Mã NK</th>
                <th class="py-3 px-4">Bảng</th>
                <th class="py-3 px-4">Khóa dòng</th>
                <th class="py-3 px-4">Hành động</th>
                <th class="py-3 px-4">Người thực hiện</th>
                <th class="py-3 px-4">Vai trò / Kênh</th>
                <th class="py-3 px-4">Thời điểm</th>
                <th class="py-3 px-4">Lý do</th>
                <th class="py-3 px-4 text-center">Chi tiết</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr
                v-for="item in auditLogs"
                :key="item.nhatKyId"
                class="hover:bg-indigo-50/30 transition cursor-pointer"
                @click="openDiffModal(item)"
              >
                <!-- Mã NK -->
                <td class="py-3 px-4 font-mono font-medium text-slate-500">
                  #{{ item.nhatKyId }}
                </td>

                <!-- Bảng -->
                <td class="py-3 px-4">
                  <span class="inline-flex px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                    {{ item.bang }}
                  </span>
                </td>

                <!-- Khóa dòng -->
                <td class="py-3 px-4 font-mono font-semibold text-slate-900">
                  {{ item.khoaDong }}
                </td>

                <!-- Hành động -->
                <td class="py-3 px-4">
                  <span
                    class="inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                    :class="getActionBadgeClass(item.hanhDong)"
                  >
                    {{ item.hanhDong }}
                  </span>
                </td>

                <!-- Người thực hiện -->
                <td class="py-3 px-4">
                  <div class="font-medium text-slate-900">
                    {{ item.tenDangNhap || (item.nguoiThucHienId ? `ID: ${item.nguoiThucHienId}` : 'Hệ thống') }}
                  </div>
                  <div v-if="item.diaChiIp" class="text-[10px] text-slate-400 font-mono">
                    {{ item.diaChiIp }}
                  </div>
                </td>

                <!-- Vai trò / Kênh -->
                <td class="py-3 px-4">
                  <div class="text-[11px] font-medium text-slate-700">
                    {{ item.vaiTro }}
                  </div>
                  <span class="inline-flex text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-500">
                    {{ item.kenh }}
                  </span>
                </td>

                <!-- Thời điểm -->
                <td class="py-3 px-4 text-slate-600 font-mono text-[11px]">
                  {{ formatDateTime(item.thoiDiem) }}
                </td>

                <!-- Lý do -->
                <td class="py-3 px-4 text-slate-500 max-w-[180px] truncate" :title="item.lyDo || ''">
                  {{ item.lyDo || '-' }}
                </td>

                <!-- Action Button -->
                <td class="py-3 px-4 text-center" @click.stop="openDiffModal(item)">
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-md font-semibold text-[11px] transition"
                  >
                    <Eye class="w-3.5 h-3.5" />
                    <span>Xem Diff</span>
                  </button>
                </td>
              </tr>

              <tr v-if="auditLogs.length === 0">
                <td colspan="9" class="py-12 text-center text-slate-400 text-sm">
                  Không tìm thấy bản ghi nhật ký kiểm toán nào khớp với bộ lọc
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="px-4 py-3 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
          <div>
            Hiển thị <span class="font-bold">{{ startRow }}</span> đến <span class="font-bold">{{ endRow }}</span> trên tổng số <span class="font-bold">{{ totalLogs }}</span> bản ghi
          </div>

          <div class="flex items-center space-x-2">
            <button
              type="button"
              @click="changePage(pagination.page - 1)"
              :disabled="pagination.page <= 1"
              class="px-2.5 py-1 border border-slate-300 rounded bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed font-medium transition"
            >
              Trang trước
            </button>
            <span class="px-2 font-semibold text-slate-800">Trang {{ pagination.page }} / {{ pagination.totalPages }}</span>
            <button
              type="button"
              @click="changePage(pagination.page + 1)"
              :disabled="pagination.page >= pagination.totalPages"
              class="px-2.5 py-1 border border-slate-300 rounded bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed font-medium transition"
            >
              Trang sau
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: TUA LẠI TRẠNG THÁI TẠI THỜI ĐIỂM (STATE-AT) -->
    <div v-else-if="activeMode === 'state_at'" class="space-y-6">
      <div class="bg-indigo-50 border-l-4 border-indigo-600 p-4 rounded-r-xl text-xs text-indigo-900 leading-relaxed">
        <span class="font-bold">Định nghĩa nghiệp vụ (BR-46, AC-14):</span> Tính năng tái hiện trạng thái tại thời điểm (State-At / Time Travel) cho phép quản lý xem chính xác toàn bộ dữ liệu của một đơn đặt phòng, phòng hoặc bảng giá tại bất kỳ thời điểm nào trong quá khứ dựa trên nhật ký bất biến.
      </div>

      <!-- Form tra cứu -->
      <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm max-w-3xl space-y-4">
        <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Clock class="w-4 h-4 text-indigo-600" />
          <span>Thông số tái hiện trạng thái</span>
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Đối tượng (Bảng)</label>
            <select
              v-model="stateAtQuery.bang"
              class="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="DAT_PHONG">DAT_PHONG (Đơn đặt phòng)</option>
              <option value="PHONG">PHONG (Phòng khách sạn)</option>
              <option value="BANG_GIA">BANG_GIA (Bảng giá)</option>
              <option value="NGUOI_DUNG">NGUOI_DUNG (Tài khoản)</option>
              <option value="GIAO_DICH_THANH_TOAN">GIAO_DICH_THANH_TOAN (Giao dịch)</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Khóa dòng (ID đối tượng)</label>
            <input
              type="text"
              v-model="stateAtQuery.khoaDong"
              placeholder="VD: 1054, 1, 222..."
              class="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Mốc thời điểm T</label>
            <input
              type="datetime-local"
              v-model="stateAtQuery.thoiDiem"
              class="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
        </div>

        <div class="flex items-center gap-3 pt-2">
          <button
            type="button"
            @click="queryStateAt"
            :disabled="stateAtLoading || !stateAtQuery.khoaDong"
            class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-lg text-xs font-semibold transition shadow-sm flex items-center gap-2"
          >
            <RefreshCw v-if="stateAtLoading" class="w-3.5 h-3.5 animate-spin" />
            <Search v-else class="w-3.5 h-3.5" />
            <span>Tua lại trạng thái</span>
          </button>
        </div>
      </div>

      <!-- Kết quả State-At -->
      <div v-if="stateAtResult" class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <span
              class="inline-flex px-2.5 py-1 rounded-full text-xs font-bold"
              :class="stateAtResult.found ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
            >
              {{ stateAtResult.found ? 'Đã tái hiện thành công' : 'Không có dữ liệu' }}
            </span>
            <span class="text-xs text-slate-600">
              Đối tượng: <strong class="text-slate-900">{{ stateAtResult.bang }} #{{ stateAtResult.khoaDong }}</strong>
            </span>
          </div>

          <div v-if="stateAtResult.found" class="text-xs text-slate-500">
            Ghi nhận gần nhất: <strong class="text-slate-700 font-mono">{{ formatDateTime(stateAtResult.auditTime) }}</strong>
            - Thao tác: <span class="font-bold text-indigo-600">{{ stateAtResult.action }}</span>
            bởi <span class="font-bold text-slate-700">{{ stateAtResult.performedBy || stateAtResult.role }}</span>
          </div>
        </div>

        <div class="p-6">
          <div class="text-xs text-slate-500 mb-4">{{ stateAtResult.message }}</div>

          <div v-if="stateAtResult.state" class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              v-for="(val, key) in stateAtResult.state"
              :key="key"
              class="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs"
            >
              <span class="font-semibold text-slate-600 font-mono">{{ key }}</span>
              <span class="font-bold text-slate-900 font-mono text-right truncate max-w-[220px]" :title="String(val)">
                {{ val === null ? 'null' : val }}
              </span>
            </div>
          </div>

          <div v-else-if="stateAtResult.found" class="p-6 text-center text-slate-400 text-sm">
            Bản ghi này ở trạng thái đã bị xóa tại mốc thời gian đã chọn
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL SO SÁNH THAY ĐỔI (DIFF MODAL) -->
    <div
      v-if="showDiffModal && selectedItem"
      class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden animate-fadeIn">
        <!-- Modal Header -->
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold text-slate-900">Chi tiết thay đổi nhật ký #{{ selectedItem.nhatKyId }}</h2>
              <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-200 text-slate-700">
                {{ selectedItem.bang }}
              </span>
              <span
                class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase"
                :class="getActionBadgeClass(selectedItem.hanhDong)"
              >
                {{ selectedItem.hanhDong }}
              </span>
            </div>
            <p class="text-xs text-slate-500 mt-1">
              Khóa dòng: <strong class="font-mono text-slate-700">{{ selectedItem.khoaDong }}</strong>
              - Thời điểm: <span class="font-mono text-slate-700">{{ formatDateTime(selectedItem.thoiDiem) }}</span>
              - Người thực hiện: <span class="font-bold text-indigo-600">{{ selectedItem.tenDangNhap || selectedItem.vaiTro }}</span>
            </p>
          </div>

          <button
            type="button"
            @click="closeDiffModal"
            class="text-slate-400 hover:text-slate-600 p-1 rounded-lg transition"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Modal Body: Diff Columns -->
        <div class="p-6 overflow-y-auto space-y-4 flex-1">
          <div v-if="selectedItem.lyDo" class="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900">
            <strong>Lý do thao tác:</strong> {{ selectedItem.lyDo }}
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Cột trái: Giá trị cũ -->
            <div class="border border-slate-200 rounded-xl p-4 bg-slate-50/50">
              <div class="text-xs font-bold uppercase tracking-wider text-rose-600 mb-3 flex items-center justify-between">
                <span>Giá trị trước thay đổi (Old State)</span>
                <span v-if="!selectedItem.giaTriCu" class="text-slate-400 font-normal">Không có (Thao tác tạo mới)</span>
              </div>

              <div v-if="selectedItem.giaTriCu" class="space-y-2">
                <div
                  v-for="(val, key) in selectedItem.giaTriCu"
                  :key="key"
                  class="p-2 rounded text-xs transition"
                  :class="isKeyChanged(key) ? 'bg-amber-100/70 border border-amber-300' : 'bg-white border border-slate-200'"
                >
                  <div class="flex items-center justify-between">
                    <span class="font-mono font-semibold text-slate-600">{{ key }}</span>
                    <span v-if="isKeyChanged(key)" class="text-[9px] uppercase font-bold text-amber-700 bg-amber-200 px-1.5 py-0.2 rounded">
                      Đã sửa
                    </span>
                  </div>
                  <div class="font-mono text-slate-800 mt-1 break-all">
                    {{ val === null ? 'null' : val }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Cột phải: Giá trị mới -->
            <div class="border border-slate-200 rounded-xl p-4 bg-slate-50/50">
              <div class="text-xs font-bold uppercase tracking-wider text-emerald-600 mb-3 flex items-center justify-between">
                <span>Giá trị sau thay đổi (New State)</span>
                <span v-if="!selectedItem.giaTriMoi" class="text-slate-400 font-normal">Không có (Thao tác xóa)</span>
              </div>

              <div v-if="selectedItem.giaTriMoi" class="space-y-2">
                <div
                  v-for="(val, key) in selectedItem.giaTriMoi"
                  :key="key"
                  class="p-2 rounded text-xs transition"
                  :class="isKeyChanged(key) ? 'bg-emerald-100/70 border border-emerald-300' : 'bg-white border border-slate-200'"
                >
                  <div class="flex items-center justify-between">
                    <span class="font-mono font-semibold text-slate-600">{{ key }}</span>
                    <span v-if="isKeyChanged(key)" class="text-[9px] uppercase font-bold text-emerald-700 bg-emerald-200 px-1.5 py-0.2 rounded">
                      Giá trị mới
                    </span>
                  </div>
                  <div class="font-mono text-slate-800 mt-1 break-all">
                    {{ val === null ? 'null' : val }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            type="button"
            @click="closeDiffModal"
            class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-semibold transition"
          >
            Đóng cửa sổ
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import {
  History,
  Clock,
  Search,
  RefreshCw,
  Eye,
  X
} from 'lucide-vue-next'
import apiClient from '../../api/client'

const activeMode = ref('logs')
const loading = ref(false)
const error = ref('')

const auditLogs = ref([])
const availableTables = ref([])
const availableActions = ref([])
const totalLogs = ref(0)

const pagination = reactive({
  page: 1,
  pageSize: 20,
  totalPages: 1
})

const filters = reactive({
  bang: '',
  khoaDong: '',
  hanhDong: '',
  vaiTro: '',
  kenh: '',
  nguoiDung: '',
  tuNgay: '',
  denNgay: ''
})

const startRow = computed(() => {
  if (totalLogs.value === 0) return 0
  return (pagination.page - 1) * pagination.pageSize + 1
})

const endRow = computed(() => {
  return Math.min(pagination.page * pagination.pageSize, totalLogs.value)
})

// Diff Modal State
const showDiffModal = ref(false)
const selectedItem = ref(null)

const openDiffModal = (item) => {
  selectedItem.value = item
  showDiffModal.value = true
}

const closeDiffModal = () => {
  showDiffModal.value = false
  selectedItem.value = null
}

const isKeyChanged = (key) => {
  if (!selectedItem.value?.giaTriCu || !selectedItem.value?.giaTriMoi) return false
  const oldVal = selectedItem.value.giaTriCu[key]
  const newVal = selectedItem.value.giaTriMoi[key]
  return JSON.stringify(oldVal) !== JSON.stringify(newVal)
}

// State-At Query State
const stateAtQuery = reactive({
  bang: 'DAT_PHONG',
  khoaDong: '',
  thoiDiem: ''
})
const stateAtLoading = ref(false)
const stateAtResult = ref(null)

const queryStateAt = async () => {
  if (!stateAtQuery.khoaDong) return
  stateAtLoading.value = true
  try {
    const params = {
      bang: stateAtQuery.bang,
      khoaDong: stateAtQuery.khoaDong,
      thoiDiem: stateAtQuery.thoiDiem || undefined
    }
    const res = await apiClient.get('/audit-logs/state-at', { params })
    stateAtResult.value = res.data || res
  } catch (err) {
    alert('Lỗi tra cứu trạng thái: ' + (err.response?.data?.detail || err.message))
  } finally {
    stateAtLoading.value = false
  }
}

// Helpers
const formatDateTime = (val) => {
  if (!val) return '-'
  try {
    const d = new Date(val)
    return new Intl.DateTimeFormat('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(d)
  } catch {
    return val
  }
}

const getActionBadgeClass = (action) => {
  switch (action) {
    case 'TAO':
    case 'THEM':
      return 'bg-emerald-100 text-emerald-800'
    case 'SUA':
      return 'bg-blue-100 text-blue-800'
    case 'DOI_TRANG_THAI':
      return 'bg-purple-100 text-purple-800'
    case 'XOA':
      return 'bg-rose-100 text-rose-800'
    default:
      return 'bg-slate-100 text-slate-700'
  }
}

// Fetch Logs
const fetchLogs = async () => {
  loading.value = true
  error.value = ''

  try {
    const params = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      bang: filters.bang || undefined,
      khoaDong: filters.khoaDong || undefined,
      hanhDong: filters.hanhDong || undefined,
      vaiTro: filters.vaiTro || undefined,
      kenh: filters.kenh || undefined,
      nguoiDung: filters.nguoiDung || undefined,
      tuNgay: filters.tuNgay || undefined,
      denNgay: filters.denNgay || undefined
    }

    const res = await apiClient.get('/audit-logs', { params })
    const data = res.data || res

    auditLogs.value = data.items || []
    totalLogs.value = data.total || 0
    pagination.page = data.page || 1
    pagination.pageSize = data.pageSize || 20
    pagination.totalPages = data.totalPages || 1

    if (data.tables?.length) availableTables.value = data.tables
    if (data.actions?.length) availableActions.value = data.actions
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Lỗi kết nối máy chủ'
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  pagination.page = 1
  fetchLogs()
}

const resetFilters = () => {
  filters.bang = ''
  filters.khoaDong = ''
  filters.hanhDong = ''
  filters.vaiTro = ''
  filters.kenh = ''
  filters.nguoiDung = ''
  filters.tuNgay = ''
  filters.denNgay = ''
  applyFilters()
}

const changePage = (newPage) => {
  if (newPage >= 1 && newPage <= pagination.totalPages) {
    pagination.page = newPage
    fetchLogs()
  }
}

onMounted(() => {
  // Default datetime for state-at
  const now = new Date()
  const yyyy = now.getFullYear()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')
  const hh = String(now.getHours()).padStart(2, '0')
  const min = String(now.getMinutes()).padStart(2, '0')
  stateAtQuery.thoiDiem = `${yyyy}-${mm}-${dd}T${hh}:${min}`

  fetchLogs()
})
</script>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.97); }
  to { opacity: 1; transform: scale(1); }
}
.animate-fadeIn {
  animation: fadeIn 0.15s ease-out;
}
</style>
