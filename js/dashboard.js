// Dashboard Module
class Dashboard {
    constructor() {
        this.baseURL = 'http://127.0.0.1:8000';
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Add any dashboard-specific event listeners here
    }

    async loadData() {
        if (!window.auth.isAuthenticated()) {
            this.showLoginPrompt();
            return;
        }

        try {
            // For now, we'll use mock data since the backend doesn't have ECR/ECN endpoints yet
            this.updateDashboardStats({
                ecrTotal: 12,
                ecrPending: 3,
                ecnTotal: 8,
                ecnInProgress: 2
            });
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    updateDashboardStats(stats) {
        document.getElementById('ecrTotal').textContent = stats.ecrTotal;
        document.getElementById('ecrPending').textContent = stats.ecrPending;
        document.getElementById('ecnTotal').textContent = stats.ecnTotal;
        document.getElementById('ecnInProgress').textContent = stats.ecnInProgress;
    }

    showLoginPrompt() {
        const dashboardContent = document.getElementById('dashboardPage');
        dashboardContent.innerHTML = `
            <div class="page-header">
                <h1>Dashboard</h1>
                <p>Please login to view your dashboard</p>
            </div>
            <div class="dashboard-grid">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-sign-in-alt"></i>
                        <h3>Login Required</h3>
                    </div>
                    <div class="card-content">
                        <p>You need to be logged in to view the dashboard.</p>
                        <button class="btn btn-primary" onclick="window.auth.showLoginModal()">
                            <i class="fas fa-sign-in-alt"></i> Login
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    showError(message) {
        if (window.auth) {
            window.auth.showError(message);
        }
    }

    showSuccess(message) {
        if (window.auth) {
            window.auth.showSuccess(message);
        }
    }
}

// Initialize dashboard
window.dashboard = new Dashboard(); 