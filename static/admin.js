const isAdminPage = document.getElementById("usersList") !== null;

function sortUploads(data) {
  return [...data].sort((a, b) => {
    if ((a.subject || "") < (b.subject || "")) return -1;
    if ((a.subject || "") > (b.subject || "")) return 1;
    return a.title.localeCompare(b.title);
  });
}
if (isAdminPage) {
  const userSearch = document.getElementById("userSearch");

  userSearch.addEventListener("input", e => {
    const query = e.target.value.toLowerCase();

    document.querySelectorAll(".user-item").forEach(li => {
      const name = li.dataset.username;
      li.style.display = name.includes(query) ? "" : "none";
    });
  });
}

if (isAdminPage) {
  const uploadContainer = document.getElementById("uploadsList");
  const uploadSearch = document.getElementById("uploadSearch");
  const filterButtons = document.querySelectorAll("#uploadFilters button");

  let currentFilter = "all";
  let currentSubject = "";
  let searchQuery = "";

function renderUploads() {
  let filtered = uploads.filter(u => {
    let match = true;

    if (currentFilter === "subject") {
      match = (u.subject || "Other") === currentSubject;
    }

    const searchMatch =
      u.title.toLowerCase().includes(searchQuery) ||
      (u.subject || "").toLowerCase().includes(searchQuery) ||
      u.uploader.toLowerCase().includes(searchQuery);

    return match && searchMatch;
  });

  filtered = sortUploads(filtered);

  uploadContainer.innerHTML = filtered.map(u => {
    const ext = u.filename.split(".").pop().toUpperCase();

    return `
      <li class="upload-card">
        <strong>[${ext}] ${u.title}</strong><br>
        <small>${u.subject || "Other"}</small><br>
        <span>${u.uploader}</span><br>

        <a href="/uploads/${u.filename}" target="_blank">View</a>
        <a href="/download/${u.filename}">
          <button>Download</button>
        </a>

        <button onclick="deleteUpload(${u.id})">Delete</button>
      </li>
    `;
  }).join("");
}

  uploadSearch.addEventListener("input", e => {
    searchQuery = e.target.value.toLowerCase();
    renderUploads();
  });

  filterButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelector(".active")?.classList.remove("active");
      btn.classList.add("active");

      if (btn.dataset.filter === "all") {
        currentFilter = "all";
      } else {
        currentFilter = "subject";
        currentSubject = btn.dataset.subject;
      }

      renderUploads();
    });
  });

  renderUploads();
}
function deleteUpload(id) {
  if (!confirm("Delete this upload?")) return;

  fetch(`/delete_upload/${id}`, {
    method: "POST"
  })
  .then(res => res.json())
  .then(data => {
    if (!data.success) throw new Error("Delete failed");
    location.reload();
  })
  .catch(err => {
    console.error(err);
    alert("Failed to delete upload");
  });
}