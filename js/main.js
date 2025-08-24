// Main Application Module
class App {
    constructor() {
        this.currentPage = 'dashboard';
        this.init();
    }

    init() {
        this.setupNavigation();
        this.showPage('dashboard');
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                this.showPage(page);
            });
        });
    }

    showPage(pageName) {
        // Hide all pages
        const pages = document.querySelectorAll('.page');
        pages.forEach(page => {
            page.style.display = 'none';
        });

        // Show selected page
        const targetPage = document.getElementById(`${pageName}Page`);
        if (targetPage) {
            targetPage.style.display = 'block';
            this.currentPage = pageName;
        }

        // Update navigation
        this.updateNavigation(pageName);

        // Load page-specific data
        this.loadPageData(pageName);
    }

    updateNavigation(activePage) {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === activePage) {
                link.classList.add('active');
            }
        });
    }

    loadPageData(pageName) {
        switch (pageName) {
            case 'dashboard':
                if (window.dashboard) {
                    window.dashboard.loadData();
                }
                break;
            case 'ecr':
                if (window.ecr) {
                    window.ecr.loadECRs();
                }
                break;
            case 'ecn':
                if (window.ecn) {
                    window.ecn.loadECNs();
                }
                break;
            case 'items':
                if (window.items) {
                    window.items.loadItems();
                }
                break;
            case 'reports':
                if (window.reports) {
                    window.reports.loadReports();
                }
                break;
        }
    }

    // Utility method to check authentication
    requireAuth() {
        if (!window.auth.isAuthenticated()) {
            window.auth.showError('Please login to access this feature');
            window.auth.showLoginModal();
            return false;
        }
        return true;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
}); 