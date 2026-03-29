const container = document.getElementById("uploads");
const searchInput = document.getElementById("search");
const buttons = document.querySelectorAll("#categories button");

let currentFilter = "all";
let currentSubject = "";
let searchQuery = "";

function sortUploads(data) {
  return [...data].sort((a, b) => {
    if (a.subject < b.subject) return -1;
    if (a.subject > b.subject) return 1;
    return a.title.localeCompare(b.title);
  });
}

function render() {
  let filtered = uploads.filter(u => {
    let match = true;

    if (currentFilter === "mine") {
      match = u.user_id === currentUserId;
    } else if (currentFilter === "subject") {
      match = u.subject === currentSubject;
    }

    const matchSearch =
      u.title.toLowerCase().includes(searchQuery);

    return match && matchSearch;
  });

  filtered = sortUploads(filtered);
  container.innerHTML = filtered.map(u => {
  const isOwner = u.user_id === currentUserId;
  const ext = u.filename.split(".").pop().toUpperCase();
  return `
  <div class="upload-card">
    <strong>[${ext}] ${u.title}</strong><br>
    <small>${u.subject}</small><br>
    <span>${u.uploader}</span><br>

    <a href="/uploads/${u.filename}" target="_blank">View</a>
    <a href="/download/${u.filename}">
      <button>Download</button>
    </a>

    ${
      isOwner ? `
      <button onclick="openEdit(${u.id}, '${u.title}', '${u.subject}')">Edit</button>

      <button onclick="deleteFile(${u.id})">Delete</button>
      ` : ""
    }
  </div>
  `;
}).join("");
}

searchInput.addEventListener("input", e => {
  searchQuery = e.target.value.toLowerCase();
  render();
});

buttons.forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelector(".active")?.classList.remove("active");
    btn.classList.add("active");

    const type = btn.dataset.filter;

    if (type === "all") {
      currentFilter = "all";
    } else if (type === "mine") {
      currentFilter = "mine";
    } else if (type === "subject") {
      currentFilter = "subject";
      currentSubject = btn.dataset.subject;
    }

    render();
  });
});

function deleteFile(id) {
  if (!confirm("Are you sure you want to delete this file? This action cannot be undone.")) return;

  fetch(`/delete_my_upload/${id}`, {
    method: "POST"
  }).then(() => {
    location.reload();
  });
}
render();

function openEdit(id, title, subject) {
  const modal = document.getElementById("editModal");
  const form = document.getElementById("editForm");

  document.getElementById("editTitle").value = title;
  document.getElementById("editSubject").value = subject;

  form.action = `/edit_upload/${id}`;

  modal.style.display = "block";
}

function closeEdit() {
  document.getElementById("editModal").style.display = "none";
}