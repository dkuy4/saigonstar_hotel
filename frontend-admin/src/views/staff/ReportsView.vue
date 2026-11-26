<template>
  <div class="reports-page space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-darkbeige-800">
      <div>
        <h1 class="font-display text-2xl font-bold text-white tracking-tight">Báo cáo quản trị & Thống kê KPI</h1>
        <p class="text-xs text-stone-400 mt-1">
          Dữ liệu thời gian thực từ cơ sở dữ liệu Oracle thông qua gói thủ tục PKG_BAO_CAO (FR-40 đến FR-44).
        </p>
      </div>

      <div class="flex items-center gap-3">
        <button
          type="button"
          @click="exportExcel"
          :disabled="exporting || loading"
          class="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white font-medium rounded-lg text-sm shadow-sm transition"
        >
          <svg v-if="exporting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>{{ exporting ? 'Đang xuất Excel...' : 'Xuất Excel (.xlsx)' }}</span>
        </button>
      </div>
    </div>

    <!-- Bộ lọc chung: Khoảng thời gian & Phím chọn nhanh -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2">
            <label class="text-xs font-semibold uppercase text-slate-500 tracking-wider">Từ ngày</label>
            <input
              type="date"
              v-model="filters.from_date"
              class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div class="flex items-center gap-2">
            <label class="text-xs font-semibold uppercase text-slate-500 tracking-wider">Đến ngày</label>
            <input
              type="date"
              v-model="filters.to_date"
              class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div v-if="activeTab === 'revenue'" class="flex items-center gap-2 ml-2">
            <label class="text-xs font-semibold uppercase text-slate-500 tracking-wider">Đơn vị</label>
            <select
              v-model="filters.unit"
              class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              <option value="NGAY">Theo Ngày</option>
              <option value="THANG">Theo Tháng</option>
            </select>
          </div>

          <button
            type="button"
            @click="loadCurrentTab"
            class="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition shadow-sm"
          >
            Áp dụng
          </button>
        </div>

        <!-- Phím chọn nhanh khoảng thời gian -->
        <div class="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg text-xs font-medium text-slate-600">
          <button
            type="button"
            @click="setPreset('this_month')"
            :class="presetActive === 'this_month' ? 'bg-white text-blue-600 shadow-sm font-semibold' : 'hover:text-slate-900'"
            class="px-2.5 py-1 rounded-md transition"
          >
            Tháng này
          </button>
          <button
            type="button"
            @click="setPreset('last_month')"
            :class="presetActive === 'last_month' ? 'bg-white text-blue-600 shadow-sm font-semibold' : 'hover:text-slate-900'"
            class="px-2.5 py-1 rounded-md transition"
          >
            Tháng trước
          </button>
          <button
            type="button"
            @click="setPreset('this_year')"
            :class="presetActive === 'this_year' ? 'bg-white text-blue-600 shadow-sm font-semibold' : 'hover:text-slate-900'"
            class="px-2.5 py-1 rounded-md transition"
          >
            Năm nay
          </button>
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="border-b border-slate-200 bg-white rounded-t-xl px-4 pt-2">
      <nav class="flex space-x-6">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          @click="switchTab(tab.id)"
          :class="[
            activeTab === tab.id
              ? 'border-blue-600 text-blue-600 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 font-medium',
            'whitespace-nowrap py-3 px-1 border-b-2 text-sm flex items-center gap-2 transition'
          ]"
        >
          <component :is="tab.icon" class="w-4 h-4" />
          <span>{{ tab.label }}</span>
        </button>
      </nav>
    </div>

    <!-- Nội dung chính theo từng Tab -->
    <div class="space-y-6">
      <!-- Loading indicator -->
      <div v-if="loading" class="bg-white p-12 rounded-xl border border-slate-200 text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mb-3"></div>
        <p class="text-sm text-slate-500">Đang truy vấn số liệu từ Oracle Database...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
        <div class="font-semibold mb-1">Không thể tải dữ liệu báo cáo</div>
        <div>{{ error }}</div>
        <button @click="loadCurrentTab" class="mt-2 text-xs font-semibold underline hover:text-red-800">Thử lại</button>
      </div>

      <!-- TAB 1: DOANH THU THỰC THU (FR-40) -->
      <div v-else-if="activeTab === 'revenue'" class="space-y-6">
        <!-- Business Rule Callout (AC-17) -->
        <div class="bg-blue-50 border-l-4 border-blue-600 p-4 rounded-r-xl text-xs text-blue-900 leading-relaxed">
          <span class="font-bold">Định nghĩa nghiệp vụ (FR-40):</span> Doanh thu thực thu = Tổng tiền khách thực tế thanh toán (phiếu thu) trừ đi tổng tiền đã hoàn trả (phiếu chi hoàn cọc/hủy). Doanh thu ghi nhận theo kỳ phát sinh giao dịch tài chính, không phụ thuộc vào thời điểm hoàn thành lưu trú.
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div class="text-xs font-semibold uppercase text-slate-400">Tổng tiền thu</div>
            <div class="text-2xl font-bold text-slate-800 mt-2">{{ formatCurrency(revenueData?.tongThu || 0) }}</div>
            <div class="text-xs text-slate-500 mt-1">Từ các phiếu thanh toán hoàn tất</div>
          </div>

          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div class="text-xs font-semibold uppercase text-slate-400">Tổng tiền hoàn trả</div>
            <div class="text-2xl font-bold text-rose-600 mt-2">{{ formatCurrency(revenueData?.tongHoan || 0) }}</div>
            <div class="text-xs text-slate-500 mt-1">Từ các phiếu hoàn cọc hoặc hủy đơn</div>
          </div>

          <div class="bg-white p-5 rounded-xl border border-blue-200 bg-blue-50/30 shadow-sm">
            <div class="text-xs font-semibold uppercase text-blue-600">Thực thu thuần</div>
            <div class="text-2xl font-bold text-blue-700 mt-2">{{ formatCurrency(revenueData?.tongThucThu || 0) }}</div>
            <div class="text-xs text-blue-600/80 mt-1">Chênh lệch thu trừ hoàn trả</div>
          </div>
        </div>

        <!-- Biểu đồ cột SVG -->
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 class="text-sm font-bold text-slate-800 mb-4">Biểu đồ doanh thu thực thu theo kỳ</h3>
          <div v-if="revenueData?.data?.length" class="h-64 flex items-end gap-3 pt-6 pb-2 border-b border-slate-200">
            <div
              v-for="item in revenueData.data"
              :key="item.ky"
              class="flex-1 flex flex-col items-center h-full justify-end group relative"
            >
              <!-- Tooltip hover -->
              <div class="opacity-0 group-hover:opacity-100 transition absolute -top-10 bg-slate-800 text-white text-xs px-2 py-1 rounded shadow pointer-events-none whitespace-nowrap z-10">
                Kỳ: {{ item.ky }} - Thực thu: {{ formatCurrency(item.thucThu) }}
              </div>
              <div
                class="w-full max-w-[48px] bg-gradient-to-t from-blue-600 to-blue-400 rounded-t-md transition-all duration-300 group-hover:from-blue-700 group-hover:to-blue-500"
                :style="{ height: getBarHeight(item.thucThu, maxRevenue) }"
              ></div>
              <div class="text-[11px] text-slate-500 mt-2 truncate w-full text-center">{{ item.ky }}</div>
            </div>
          </div>
          <div v-else class="text-center py-10 text-slate-400 text-sm">Không có dữ liệu trong khoảng thời gian đã chọn</div>
        </div>

        <!-- Bảng chi tiết -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="px-6 py-4 border-b border-slate-200 font-bold text-slate-800 text-sm">Bảng chi tiết doanh thu</div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th class="py-3 px-6">Kỳ (Ngày/Tháng)</th>
                  <th class="py-3 px-6 text-right">Tổng thu (VNĐ)</th>
                  <th class="py-3 px-6 text-right">Hoàn trả (VNĐ)</th>
                  <th class="py-3 px-6 text-right">Thực thu (VNĐ)</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200">
                <tr v-for="item in revenueData?.data" :key="item.ky" class="hover:bg-slate-50 transition">
                  <td class="py-3.5 px-6 font-medium text-slate-800">{{ item.ky }}</td>
                  <td class="py-3.5 px-6 text-right text-slate-600">{{ formatNumber(item.thu) }}</td>
                  <td class="py-3.5 px-6 text-right text-rose-600">{{ formatNumber(item.hoan) }}</td>
                  <td class="py-3.5 px-6 text-right font-bold text-blue-600">{{ formatNumber(item.thucThu) }}</td>
                </tr>
                <tr v-if="!revenueData?.data?.length">
                  <td colspan="4" class="py-8 text-center text-slate-400">Không có dữ liệu phát sinh</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- TAB 2: CÔNG SUẤT PHÒNG (FR-41) -->
      <div v-else-if="activeTab === 'occupancy'" class="space-y-6">
        <!-- Business Rule Callout -->
        <div class="bg-indigo-50 border-l-4 border-indigo-600 p-4 rounded-r-xl text-xs text-indigo-900 leading-relaxed">
          <span class="font-bold">Định nghĩa nghiệp vụ (FR-41):</span> Công suất phòng tính theo tổng giờ-phòng bán / tổng giờ-phòng khả dụng. Tổng giờ-phòng khả dụng đã khấu trừ toàn bộ khoảng thời gian phòng ở trạng thái bảo trì hoặc khóa sửa chữa (BAO_TRI).
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div class="text-xs font-semibold uppercase text-slate-400">Giờ phòng khả dụng</div>
            <div class="text-2xl font-bold text-slate-800 mt-2">{{ formatNumber(occupancyData?.tongGioKhaDung || 0) }} giờ</div>
            <div class="text-xs text-slate-500 mt-1">Đã loại trừ thời gian bảo trì</div>
          </div>

          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div class="text-xs font-semibold uppercase text-slate-400">Giờ phòng đã bán</div>
            <div class="text-2xl font-bold text-slate-800 mt-2">{{ formatNumber(occupancyData?.tongGioBan || 0) }} giờ</div>
            <div class="text-xs text-slate-500 mt-1">Thời gian khách thực tế lưu trú</div>
          </div>

          <div class="bg-white p-5 rounded-xl border border-indigo-200 bg-indigo-50/30 shadow-sm">
            <div class="text-xs font-semibold uppercase text-indigo-600">Công suất toàn khách sạn</div>
            <div class="text-2xl font-bold text-indigo-700 mt-2">{{ occupancyData?.congSuatTrungBinh || 0 }}%</div>
            <div class="text-xs text-indigo-600/80 mt-1">Tỷ lệ sử dụng công suất bình quân</div>
          </div>
        </div>

        <!-- Bảng chi tiết từng hạng phòng -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="px-6 py-4 border-b border-slate-200 font-bold text-slate-800 text-sm">Công suất theo từng hạng phòng</div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th class="py-3 px-6">Mã hạng phòng</th>
                  <th class="py-3 px-6 text-center">Số lượng phòng</th>
                  <th class="py-3 px-6 text-right">Giờ khả dụng</th>
                  <th class="py-3 px-6 text-right">Giờ bán</th>
                  <th class="py-3 px-6 text-right">Công suất (%)</th>
                  <th class="py-3 px-6 w-48">Mức độ lấp đầy</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200">
                <tr v-for="item in occupancyData?.data" :key="item.maHang" class="hover:bg-slate-50 transition">
                  <td class="py-3.5 px-6 font-semibold text-slate-800">{{ item.maHang }}</td>
                  <td class="py-3.5 px-6 text-center text-slate-600">{{ item.soPhong }}</td>
                  <td class="py-3.5 px-6 text-right text-slate-600">{{ formatNumber(item.gioPhongKhaDung) }}</td>
                  <td class="py-3.5 px-6 text-right text-slate-600">{{ formatNumber(item.gioPhongBan) }}</td>
                  <td class="py-3.5 px-6 text-right font-bold" :class="item.congSuatPhanTram >= 50 ? 'text-emerald-600' : 'text-amber-600'">
                    {{ item.congSuatPhanTram }}%
                  </td>
                  <td class="py-3.5 px-6">
                    <div class="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                      <div
                        class="h-2.5 rounded-full transition-all duration-500"
                        :class="item.congSuatPhanTram >= 70 ? 'bg-emerald-500' : item.congSuatPhanTram >= 40 ? 'bg-blue-500' : 'bg-amber-500'"
                        :style="{ width: `${Math.min(item.congSuatPhanTram, 100)}%` }"
                      ></div>
                    </div>
                  </td>
                </tr>
                <tr v-if="!occupancyData?.data?.length">
                  <td colspan="6" class="py-8 text-center text-slate-400">Không có dữ liệu hạng phòng</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- TAB 3: TỶ LỆ HỦY & NO-SHOW (FR-42) -->
      <div v-else-if="activeTab === 'cancellations'" class="space-y-6">
        <!-- Business Rule Callout -->
        <div class="bg-amber-50 border-l-4 border-amber-600 p-4 rounded-r-xl text-xs text-amber-900 leading-relaxed">
          <span class="font-bold">Định nghĩa nghiệp vụ (FR-42):</span> Phân loại chi tiết nguyên nhân không thành công của đơn đặt: Hủy chủ động (khách yêu cầu trước giờ), Không đến nhận phòng (No-Show quá giờ check-in mà không liên hệ), và Hết hạn giữ chỗ (đơn tạm quá hạn thanh toán tiền cọc).
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div class="text-xs font-semibold uppercase text-slate-400">Tổng số đơn phát sinh</div>
            <div class="text-2xl font-bold text-slate-800 mt-2">{{ formatNumber(cancellationData?.tongDon || 0) }}</div>
            <div class="text-xs text-slate-500 mt-1">Tất cả trạng thái đặt phòng</div>
          </div>

          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div class="text-xs font-semibold uppercase text-slate-400">Hủy chủ động</div>
            <div class="text-2xl font-bold text-rose-600 mt-2">
              {{ formatNumber(cancellationData?.huy || 0) }}
              <span class="text-xs font-medium text-slate-500">({{ cancellationData?.tyLeHuy || 0 }}%)</span>
            </div>
            <div class="text-xs text-slate-500 mt-1">Đơn chuyển sang DA_HUY</div>
          </div>

          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div class="text-xs font-semibold uppercase text-slate-400">Không đến (No-Show)</div>
            <div class="text-2xl font-bold text-amber-600 mt-2">
              {{ formatNumber(cancellationData?.noShow || 0) }}
              <span class="text-xs font-medium text-slate-500">({{ cancellationData?.tyLeNoShow || 0 }}%)</span>
            </div>
            <div class="text-xs text-slate-500 mt-1">Đơn chuyển sang NO_SHOW</div>
          </div>

          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div class="text-xs font-semibold uppercase text-slate-400">Hết hạn thanh toán cọc</div>
            <div class="text-2xl font-bold text-slate-600 mt-2">
              {{ formatNumber(cancellationData?.hetHanGiuCho || 0) }}
              <span class="text-xs font-medium text-slate-500">({{ cancellationData?.tyLeHetHan || 0 }}%)</span>
            </div>
            <div class="text-xs text-slate-500 mt-1">Đơn hết thời gian giữ chỗ</div>
          </div>
        </div>

        <!-- Bảng trực quan tỷ lệ -->
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 class="text-sm font-bold text-slate-800 mb-4">Cơ cấu hủy phòng và thất thoát đơn</h3>
          <div class="space-y-4">
            <div>
              <div class="flex justify-between text-xs font-medium mb-1.5">
                <span class="text-slate-600">Khách chủ động hủy đơn: {{ cancellationData?.huy || 0 }} đơn</span>
                <span class="text-rose-600 font-bold">{{ cancellationData?.tyLeHuy || 0 }}%</span>
              </div>
              <div class="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                <div class="bg-rose-500 h-3 rounded-full" :style="{ width: `${cancellationData?.tyLeHuy || 0}%` }"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-xs font-medium mb-1.5">
                <span class="text-slate-600">Khách không đến nhận phòng (No-Show): {{ cancellationData?.noShow || 0 }} đơn</span>
                <span class="text-amber-600 font-bold">{{ cancellationData?.tyLeNoShow || 0 }}%</span>
              </div>
              <div class="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                <div class="bg-amber-500 h-3 rounded-full" :style="{ width: `${cancellationData?.tyLeNoShow || 0}%` }"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-xs font-medium mb-1.5">
                <span class="text-slate-600">Hết hạn thanh toán giữ chỗ: {{ cancellationData?.hetHanGiuCho || 0 }} đơn</span>
                <span class="text-slate-600 font-bold">{{ cancellationData?.tyLeHetHan || 0 }}%</span>
              </div>
              <div class="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                <div class="bg-slate-400 h-3 rounded-full" :style="{ width: `${cancellationData?.tyLeHetHan || 0}%` }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 4: ADR & REVPAR (FR-44) -->
      <div v-else-if="activeTab === 'kpi'" class="space-y-6">
        <!-- Business Rule Callout -->
        <div class="bg-purple-50 border-l-4 border-purple-600 p-4 rounded-r-xl text-xs text-purple-900 leading-relaxed">
          <span class="font-bold">Định nghĩa chỉ số KPI cốt lõi (FR-44):</span>
          <br />- <strong>ADR (Average Daily Rate):</strong> Giá bán phòng bình quân mỗi đêm đã bán = Doanh thu tiền phòng / Tổng số đêm phòng đã bán.
          <br />- <strong>RevPAR (Revenue Per Available Room):</strong> Doanh thu trên mỗi phòng khả dụng = Doanh thu tiền phòng / Tổng số đêm phòng khả dụng.
          <br />- Quy ước quy đổi tiêu chuẩn của hệ thống: 1 đêm phòng tương đương 24 giờ-phòng.
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div class="text-xs font-semibold uppercase text-slate-400">Doanh thu phòng toàn khách sạn</div>
            <div class="text-2xl font-bold text-slate-800 mt-2">{{ formatCurrency(kpiData?.tongDoanhThuPhong || 0) }}</div>
            <div class="text-xs text-slate-500 mt-1">Thuần tiền phòng không gồm dịch vụ</div>
          </div>

          <div class="bg-white p-5 rounded-xl border border-purple-200 bg-purple-50/20 shadow-sm">
            <div class="text-xs font-semibold uppercase text-purple-600">ADR Toàn khách sạn</div>
            <div class="text-2xl font-bold text-purple-700 mt-2">{{ formatCurrency(kpiData?.adrChung || 0) }}</div>
            <div class="text-xs text-purple-600/80 mt-1">Giá bình quân mỗi đêm phòng bán ra</div>
          </div>

          <div class="bg-white p-5 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-sm">
            <div class="text-xs font-semibold uppercase text-emerald-600">RevPAR Toàn khách sạn</div>
            <div class="text-2xl font-bold text-emerald-700 mt-2">{{ formatCurrency(kpiData?.revparChung || 0) }}</div>
            <div class="text-xs text-emerald-600/80 mt-1">Hiệu quả khai thác trên từng phòng</div>
          </div>
        </div>

        <!-- Bảng chi tiết từng hạng phòng -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="px-6 py-4 border-b border-slate-200 font-bold text-slate-800 text-sm">Chi tiết chỉ số ADR & RevPAR theo từng hạng phòng</div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th class="py-3 px-6">Mã hạng phòng</th>
                  <th class="py-3 px-6 text-right">Doanh thu phòng (VNĐ)</th>
                  <th class="py-3 px-6 text-right">Phòng-đêm bán</th>
                  <th class="py-3 px-6 text-right">Phòng-đêm khả dụng</th>
                  <th class="py-3 px-6 text-right">ADR (VNĐ/đêm)</th>
                  <th class="py-3 px-6 text-right">RevPAR (VNĐ/đêm)</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200">
                <tr v-for="item in kpiData?.data" :key="item.maHang" class="hover:bg-slate-50 transition">
                  <td class="py-3.5 px-6 font-semibold text-slate-800">{{ item.maHang }}</td>
                  <td class="py-3.5 px-6 text-right font-medium text-slate-700">{{ formatNumber(item.doanhThuPhong) }}</td>
                  <td class="py-3.5 px-6 text-right text-slate-600">{{ item.phongDemBan }}</td>
                  <td class="py-3.5 px-6 text-right text-slate-600">{{ item.phongDemKhaDung }}</td>
                  <td class="py-3.5 px-6 text-right font-bold text-purple-600">{{ formatNumber(item.adr) }}</td>
                  <td class="py-3.5 px-6 text-right font-bold text-emerald-600">{{ formatNumber(item.revpar) }}</td>
                </tr>
                <tr v-if="!kpiData?.data?.length">
                  <td colspan="6" class="py-8 text-center text-slate-400">Không có dữ liệu cho khoảng thời gian này</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, h } from 'vue'
import apiClient from '../../api/client'

// Icons định nghĩa dạng Functional Component
const ChartBarIcon = (props) => h('svg', { ...props, fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
  h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', strokeWidth: '2', d: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' })
])
const ClockIcon = (props) => h('svg', { ...props, fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
  h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', strokeWidth: '2', d: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' })
])
const XCircleIcon = (props) => h('svg', { ...props, fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
  h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', strokeWidth: '2', d: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z' })
])
const TrendingUpIcon = (props) => h('svg', { ...props, fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
  h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', strokeWidth: '2', d: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6' })
])

const tabs = [
  { id: 'revenue', label: 'Doanh thu thực thu', icon: ChartBarIcon },
  { id: 'occupancy', label: 'Công suất phòng', icon: ClockIcon },
  { id: 'cancellations', label: 'Tỷ lệ hủy & No-show', icon: XCircleIcon },
  { id: 'kpi', label: 'ADR & RevPAR', icon: TrendingUpIcon }
]

const activeTab = ref('revenue')
const presetActive = ref('this_month')
const loading = ref(false)
const exporting = ref(false)
const error = ref('')

const filters = reactive({
  from_date: '',
  to_date: '',
  unit: 'NGAY'
})

// Data stores for tabs
const revenueData = ref(null)
const occupancyData = ref(null)
const cancellationData = ref(null)
const kpiData = ref(null)

// Formatters
const formatCurrency = (val) => {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0)
}

const formatNumber = (val) => {
  return new Intl.NumberFormat('vi-VN').format(val || 0)
}

const maxRevenue = computed(() => {
  if (!revenueData.value?.data?.length) return 1
  const vals = revenueData.value.data.map(i => i.thucThu)
  return Math.max(...vals, 1)
})

const getBarHeight = (value, max) => {
  if (value <= 0) return '4px'
  const pct = Math.max(8, Math.round((value / max) * 100))
  return `${pct}%`
}

// Preset Handlers
const setPreset = (type) => {
  presetActive.value = type
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()

  if (type === 'this_month') {
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    filters.from_date = formatDate(firstDay)
    filters.to_date = formatDate(lastDay)
  } else if (type === 'last_month') {
    const firstDay = new Date(year, month - 1, 1)
    const lastDay = new Date(year, month, 0)
    filters.from_date = formatDate(firstDay)
    filters.to_date = formatDate(lastDay)
  } else if (type === 'this_year') {
    const firstDay = new Date(year, 0, 1)
    const lastDay = new Date(year, 11, 31)
    filters.from_date = formatDate(firstDay)
    filters.to_date = formatDate(lastDay)
  }

  loadCurrentTab()
}

const formatDate = (d) => {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

// Tab Switching
const switchTab = (tabId) => {
  activeTab.value = tabId
  loadCurrentTab()
}

// API Loader
const loadCurrentTab = async () => {
  loading.value = true
  error.value = ''

  try {
    const params = {
      from: filters.from_date,
      to: filters.to_date,
      from_date: filters.from_date,
      to_date: filters.to_date
    }

    if (activeTab.value === 'revenue') {
      params.unit = filters.unit
      const res = await apiClient.get('/reports/revenue', { params })
      revenueData.value = res
    } else if (activeTab.value === 'occupancy') {
      const res = await apiClient.get('/reports/occupancy', { params })
      occupancyData.value = res
    } else if (activeTab.value === 'cancellations') {
      const res = await apiClient.get('/reports/cancellations', { params })
      cancellationData.value = res
    } else if (activeTab.value === 'kpi') {
      const res = await apiClient.get('/reports/kpi', { params })
      kpiData.value = res
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Lỗi kết nối máy chủ'
  } finally {
    loading.value = false
  }
}

// Excel Export
const exportExcel = async () => {
  exporting.value = true
  try {
    const endpointMap = {
      revenue: '/reports/revenue',
      occupancy: '/reports/occupancy',
      cancellations: '/reports/cancellations',
      kpi: '/reports/kpi'
    }

    const params = {
      from: filters.from_date,
      to: filters.to_date,
      from_date: filters.from_date,
      to_date: filters.to_date,
      format: 'xlsx'
    }
    if (activeTab.value === 'revenue') {
      params.unit = filters.unit
    }

    const res = await apiClient.get(endpointMap[activeTab.value], {
      params,
      responseType: 'blob'
    })

    // Create download link
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `BaoCao_${activeTab.value}_${filters.from_date}_${filters.to_date}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  } catch (err) {
    alert('Lỗi xuất tệp Excel: ' + (err.response?.data?.detail || err.message))
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  setPreset('this_month')
})
</script>

<style scoped>
.reports-page {
  animation: fadeIn 0.2s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
