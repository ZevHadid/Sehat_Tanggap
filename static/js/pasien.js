// Modal functionality
function showAddPatientModal() {
    document.getElementById('addPatientModal').style.display = 'block';
}

function closeAddPatientModal() {
    document.getElementById('addPatientModal').style.display = 'none';
}

function showDetailModal() {
    document.getElementById('detailModal').style.display = 'block';
}

function closeDetailModal() {
    document.getElementById('detailModal').style.display = 'none';
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
}

// Form submission
document.getElementById('addPatientForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Get form data
    const formData = {
        nama: document.getElementById('nama').value,
        nisn: document.getElementById('nisn').value,
        kelas: document.getElementById('kelas').value,
        keluhan: document.getElementById('keluhan').value,
        obat: document.getElementById('obat').value
    };

    // Here you would typically send the data to your backend
    console.log('Form submitted:', formData);
    
    // Clear form and close modal
    this.reset();
    closeAddPatientModal();
});

// Sidebar toggle functionality
const sidebar = document.querySelector('.sidebar');
const mainContent = document.querySelector('.main-content');
const toggleBtn = document.querySelector('.toggle-btn');

toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
});

// Add active class to current menu item
const menuItems = document.querySelectorAll('.sidebar-menu a');
menuItems.forEach(item => {
    item.addEventListener('click', function() {
        if (!this.classList.contains('logout')) {
            menuItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        }
    });
});