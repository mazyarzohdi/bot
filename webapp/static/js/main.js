// ── Sidebar toggle ────────────────────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('overlay');
  sidebar.classList.toggle('open');
  overlay.classList.toggle('open');
}

// ── Auto-dismiss alerts ────────────────────────────────────────────────────────
document.querySelectorAll('.alert').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity .4s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  }, 4000);
});

// ── Active nav highlight (fallback) ───────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(link => {
  if (link.href && link.href === window.location.href) {
    link.classList.add('active');
  }
});
