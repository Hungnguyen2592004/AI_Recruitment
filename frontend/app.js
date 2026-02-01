// Auto-detect API URL based on environment
// Helper function to escape HTML
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// API URL - sử dụng relative path vì backend và frontend cùng origin
const API = "";

document.addEventListener("DOMContentLoaded", () => {

  /* ================= UPLOAD PAGE ================= */
  const uploadForm = document.getElementById("uploadForm");

  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault(); // chặn submit mặc định

      const file = document.getElementById("cvFile").files[0];
      const jdText = document.getElementById("jdText").value.trim();

      if (!file || !jdText) {
        alert("Thiếu CV hoặc mô tả công việc");
        return;
      }

      const formData = new FormData();
      formData.append("file", file);
      formData.append("jd_text", jdText);

      // Hiển thị loading và disable button
      const submitBtn = document.querySelector('button[type="submit"]');
      const originalBtnText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Đang phân tích, vui lòng chờ...';
      
      // Hiển thị thông báo chờ
      const waitMsg = document.createElement('div');
      waitMsg.className = 'alert alert-info mt-3';
      waitMsg.innerHTML = '<i class="fas fa-clock me-2"></i>Đang phân tích CV bằng AI, vui lòng chờ một chút...';
      submitBtn.parentElement.appendChild(waitMsg);

      try {
        const res = await fetch(`${API}/cv/analyze`, {
          method: "POST",
          body: formData
        });

        // Xóa thông báo chờ
        waitMsg.remove();
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;

        if (!res.ok) {
          // Đọc error message từ response
          let errorMsg = "Lỗi không xác định";
          try {
            const errorData = await res.json();
            errorMsg = errorData.detail || errorData.error || errorMsg;
          } catch (e) {
            errorMsg = `HTTP ${res.status}: ${res.statusText}`;
          }
          throw new Error(errorMsg);
        }

        // backend OK → sang list
        window.location.href = "list.html";

      } catch (err) {
        // Xóa thông báo chờ nếu có lỗi
        if (waitMsg.parentElement) waitMsg.remove();
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
        
        console.error("Upload error:", err);
        alert("Lỗi khi phân tích CV: " + (err.message || "Không kết nối được backend"));
      }
    });
  }

  /* ================= LIST PAGE ================= */
  if (document.getElementById("cvTable")) {
    loadCVs();
  }
});

/* ================= LOAD CVS ================= */
async function loadCVs(url = "/cv/list") {
  const loading = document.getElementById("loadingState");
  const table = document.getElementById("tableContainer");
  const tbody = document.getElementById("cvTable");

  loading.style.display = "block";
  table.classList.add("d-none");

  try {
    const res = await fetch(API + url);
    if (!res.ok) throw new Error("Fetch failed");

    const data = await res.json();
    tbody.innerHTML = "";

    // Store CV data globally for detail view
    window.cvDataStore = {};
    
    if (!data || data.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-muted">
            <i class="fas fa-inbox me-2"></i>Chưa có CV nào. Hãy upload CV để bắt đầu!
          </td>
        </tr>
      `;
      loading.style.display = "none";
      table.classList.remove("d-none");
      return;
    }

    // Store CV data globally for detail view
    window.cvDataStore = window.cvDataStore || {};
    
    data.forEach(cv => {
      // Xử lý dữ liệu an toàn
      const name = (cv.name && cv.name !== "(Không xác định)" && cv.name.length < 50) 
        ? cv.name 
        : "(Không xác định)";
      
      const position = cv.position || cv.candidate_position || "(Không rõ)";
      const skills = Array.isArray(cv.skills) ? cv.skills : [];
      const years = cv.years_experience || cv.years || 0;
      const score = parseFloat(cv.score) || 0;
      const cvId = cv.id || 0;

      // Store CV data
      window.cvDataStore[cvId] = cv;

      // Format skills display
      const skillsDisplay = skills.length > 0 
        ? skills.slice(0, 3).join(", ") + (skills.length > 3 ? "..." : "")
        : "Chưa có";

      // Score badge color
      let scoreClass = 'bg-secondary';
      if (score >= 70) scoreClass = 'bg-success';
      else if (score >= 50) scoreClass = 'bg-warning';
      else if (score > 0) scoreClass = 'bg-danger';

      tbody.innerHTML += `
        <tr>
          <td><strong>${escapeHtml(name)}</strong></td>
          <td>${escapeHtml(cv.email || "")}</td>
          <td>${escapeHtml(cv.phone || "")}</td>
          <td>${escapeHtml(position)}</td>
          <td><small>${escapeHtml(skillsDisplay)}</small></td>
          <td>${years} năm</td>
          <td><span class="badge ${scoreClass}">${score.toFixed(1)}</span></td>
          <td>
            <button class="btn btn-sm btn-outline-primary" onclick="showCVDetail(${cvId})" title="Xem chi tiết">
              <i class="fas fa-eye"></i>
            </button>
          </td>
        </tr>
      `;
    });

  } catch (err) {
    console.error("Load CVs error:", err);
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center text-danger">
          <i class="fas fa-exclamation-triangle me-2"></i>Lỗi khi tải danh sách CV. Vui lòng thử lại.
        </td>
      </tr>
    `;
  }

  loading.style.display = "none";
  table.classList.remove("d-none");
}

/* ================= FILTER ================= */
function filterCV() {
  const position = document.getElementById("position").value.trim();
  const skill = document.getElementById("skill").value.trim();
  const minYears = document.getElementById("minYears").value.trim();

  let url = "/cv/filter-advanced?";

  if (position) url += `position=${encodeURIComponent(position)}&`;
  if (skill) url += `skill=${encodeURIComponent(skill)}&`;
  if (minYears) url += `min_years=${parseInt(minYears)}&`;

  url = url.replace(/&$/, "");
  loadCVs(url);
}

/* ================= NATURAL LANGUAGE SEARCH ================= */
function naturalSearch() {
  const query = document.getElementById("naturalSearch").value.trim();
  if (!query) {
    alert("Vui lòng nhập từ khóa tìm kiếm");
    return;
  }
  
  const url = `/cv/search?query=${encodeURIComponent(query)}`;
  loadCVs(url);
}

// Allow Enter key to trigger search
document.addEventListener("DOMContentLoaded", () => {
  const naturalSearchInput = document.getElementById("naturalSearch");
  if (naturalSearchInput) {
    naturalSearchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        naturalSearch();
      }
    });
  }
});

/* ================= SHOW CV DETAIL ================= */
function showCVDetail(id) {
  const cvData = window.cvDataStore[id];
  if (!cvData) {
    alert("Không tìm thấy thông tin CV. Vui lòng tải lại trang.");
    return;
  }
  
  const modalElement = document.getElementById("cvDetailModal");
  if (!modalElement) {
    alert("Modal không tồn tại");
    return;
  }
  
  const modal = new bootstrap.Modal(modalElement);
  const content = document.getElementById("cvDetailContent");
  
  const skills = Array.isArray(cvData.skills) ? cvData.skills : [];
  const experiences = Array.isArray(cvData.experiences) ? cvData.experiences : [];
  const projects = Array.isArray(cvData.projects) ? cvData.projects : [];
  const education = Array.isArray(cvData.education) ? cvData.education : [];
  const socialLinks = Array.isArray(cvData.social_links) ? cvData.social_links : [];
  const score = parseFloat(cvData.score) || 0;
  
  let educationHtml = "";
  if (education.length > 0) {
    educationHtml = education.map(edu => {
      const school = escapeHtml(edu.school || edu.institution || "");
      const degree = escapeHtml(edu.degree || edu.qualification || "");
      const major = escapeHtml(edu.major || edu.field || "");
      const year = escapeHtml(edu.year || "");
      return `<div class="mb-3 p-2 border rounded">
        ${school ? `<strong><i class="fas fa-university me-2"></i>${school}</strong><br>` : ""}
        ${degree ? `<span class="text-primary">${degree}</span><br>` : ""}
        ${major ? `<em>${major}</em><br>` : ""}
        ${year ? `<small class="text-muted">Năm: ${year}</small>` : ""}
      </div>`;
    }).join("");
  } else {
    educationHtml = "<p class=\"text-muted\"><i class=\"fas fa-info-circle me-2\"></i>Chưa có thông tin</p>";
  }
  
  // Score badge color
  let scoreClass = 'bg-secondary';
  if (score >= 70) scoreClass = 'bg-success';
  else if (score >= 50) scoreClass = 'bg-warning';
  else if (score > 0) scoreClass = 'bg-danger';
  
  content.innerHTML = `
    <div class="row">
      <div class="col-md-6">
        <h6><i class="fas fa-user me-2 text-primary"></i>Thông tin cá nhân</h6>
        <table class="table table-sm table-borderless">
          <tr><td class="text-muted" style="width: 40%;"><strong>Họ tên:</strong></td><td>${escapeHtml(cvData.name || "N/A")}</td></tr>
          <tr><td class="text-muted"><strong>Email:</strong></td><td>${cvData.email ? `<a href="mailto:${cvData.email}">${escapeHtml(cvData.email)}</a>` : "N/A"}</td></tr>
          <tr><td class="text-muted"><strong>Điện thoại:</strong></td><td>${cvData.phone ? `<a href="tel:${cvData.phone}">${escapeHtml(cvData.phone)}</a>` : "N/A"}</td></tr>
          <tr><td class="text-muted"><strong>Ngày sinh:</strong></td><td>${escapeHtml(cvData.date_of_birth || "N/A")}</td></tr>
          <tr><td class="text-muted"><strong>Địa chỉ:</strong></td><td>${escapeHtml(cvData.address || "N/A")}</td></tr>
        </table>
      </div>
      <div class="col-md-6">
        <h6><i class="fas fa-briefcase me-2 text-primary"></i>Thông tin nghề nghiệp</h6>
        <table class="table table-sm table-borderless">
          <tr><td class="text-muted" style="width: 40%;"><strong>Vị trí:</strong></td><td><span class="badge bg-info">${escapeHtml(cvData.position || cvData.candidate_position || "N/A")}</span></td></tr>
          <tr><td class="text-muted"><strong>Kinh nghiệm:</strong></td><td><strong>${cvData.years_experience || cvData.years || 0} năm</strong></td></tr>
          <tr><td class="text-muted"><strong>Điểm số:</strong></td><td><span class="badge ${scoreClass} fs-6">${score.toFixed(1)}</span></td></tr>
        </table>
      </div>
    </div>
    
    <hr>
    
    <div class="mb-3">
      <h6><i class="fas fa-graduation-cap me-2 text-primary"></i>Học vấn</h6>
      ${educationHtml}
    </div>
    
    <div class="mb-3">
      <h6><i class="fas fa-code me-2 text-primary"></i>Kỹ năng</h6>
      <div>
        ${skills.length > 0 
          ? skills.map(s => `<span class="badge bg-primary me-1 mb-1">${escapeHtml(s)}</span>`).join("") 
          : "<p class=\"text-muted\"><i class=\"fas fa-info-circle me-2\"></i>Chưa có thông tin</p>"}
      </div>
    </div>
    
    <div class="mb-3">
      <h6><i class="fas fa-briefcase me-2 text-primary"></i>Kinh nghiệm làm việc</h6>
      ${experiences.length > 0 
        ? `<ul class="list-unstyled">${experiences.map(exp => `<li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>${escapeHtml(exp)}</li>`).join("")}</ul>` 
        : "<p class=\"text-muted\"><i class=\"fas fa-info-circle me-2\"></i>Chưa có thông tin</p>"}
    </div>
    
    <div class="mb-3">
      <h6><i class="fas fa-project-diagram me-2 text-primary"></i>Dự án</h6>
      ${projects.length > 0 
        ? `<ul class="list-unstyled">${projects.map(proj => `<li class="mb-2"><i class="fas fa-folder-open text-warning me-2"></i>${escapeHtml(proj)}</li>`).join("")}</ul>` 
        : "<p class=\"text-muted\"><i class=\"fas fa-info-circle me-2\"></i>Chưa có thông tin</p>"}
    </div>
    
    <div class="mb-3">
      <h6><i class="fas fa-link me-2 text-primary"></i>Mạng xã hội</h6>
      ${socialLinks.length > 0 
        ? `<div>${socialLinks.map(link => `<a href="${link}" target="_blank" class="btn btn-sm btn-outline-primary me-2 mb-1"><i class="fas fa-external-link-alt me-1"></i>${escapeHtml(link)}</a>`).join("")}</div>` 
        : "<p class=\"text-muted\"><i class=\"fas fa-info-circle me-2\"></i>Chưa có thông tin</p>"}
    </div>
    
    ${cvData.summary ? `
    <div class="mb-3">
      <h6><i class="fas fa-info-circle me-2 text-primary"></i>Giới thiệu bản thân</h6>
      <div class="p-3 bg-light rounded">
        <p class="mb-0">${escapeHtml(cvData.summary)}</p>
      </div>
    </div>
    ` : ""}
  `;
  
  modal.show();
}
