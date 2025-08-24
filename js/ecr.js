// ECR (Engineering Change Request) Module
class ECR {
    constructor() {
        this.baseURL = 'http://127.0.0.1:8000';
        this.ecrs = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const createEcrBtn = document.getElementById('createEcrBtn');
        if (createEcrBtn) {
            createEcrBtn.addEventListener('click', () => this.showCreateECRModal());
        }
    }

    async loadECRs() {
        if (!window.auth.isAuthenticated()) {
            this.showLoginPrompt();
            return;
        }

        try {
            // For now, use mock data since backend ECR endpoints don't exist yet
            this.ecrs = [
                {
                    id: 1,
                    title: 'Update Product Design',
                    description: 'Modify the product design to improve user experience',
                    status: 'Draft',
                    creator: 'john.doe',
                    created_date: '2024-01-15',
                    reason: 'Customer feedback indicates need for better ergonomics',
                    solution: 'Redesign handle grip and adjust button placement'
                },
                {
                    id: 2,
                    title: 'Material Change Request',
                    description: 'Switch to more sustainable material',
                    status: 'Submitted',
                    creator: 'jane.smith',
                    created_date: '2024-01-10',
                    reason: 'Environmental compliance requirements',
                    solution: 'Replace current plastic with biodegradable alternative'
                }
            ];

            this.renderECRs();
        } catch (error) {
            console.error('Error loading ECRs:', error);
            this.showError('Failed to load ECRs');
        }
    }

    renderECRs() {
        const ecrList = document.getElementById('ecrList');
        if (!ecrList) return;

        if (this.ecrs.length === 0) {
            ecrList.innerHTML = `
                <div class="list-item">
                    <div class="list-item-header">
                        <h3>No ECRs Found</h3>
                    </div>
                    <p>No Engineering Change Requests have been created yet.</p>
                    <button class="btn btn-primary" onclick="window.ecr.showCreateECRModal()">
                        <i class="fas fa-plus"></i> Create First ECR
                    </button>
                </div>
            `;
            return;
        }

        ecrList.innerHTML = this.ecrs.map(ecr => `
            <div class="list-item" data-ecr-id="${ecr.id}">
                <div class="list-item-header">
                    <h3 class="list-item-title">${ecr.title}</h3>
                    <span class="list-item-status status-${ecr.status.toLowerCase()}">${ecr.status}</span>
                </div>
                <div class="list-item-content">
                    <p><strong>Description:</strong> ${ecr.description}</p>
                    <p><strong>Reason:</strong> ${ecr.reason}</p>
                    <p><strong>Proposed Solution:</strong> ${ecr.solution}</p>
                    <div class="list-item-meta">
                        <span><i class="fas fa-user"></i> ${ecr.creator}</span>
                        <span><i class="fas fa-calendar"></i> ${ecr.created_date}</span>
                    </div>
                </div>
                <div class="list-item-actions">
                    <button class="btn btn-primary" onclick="window.ecr.viewECR(${ecr.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-secondary" onclick="window.ecr.editECR(${ecr.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                </div>
            </div>
        `).join('');
    }

    showCreateECRModal() {
        if (!window.auth.isAuthenticated()) {
            window.auth.showError('Please login to create an ECR');
            window.auth.showLoginModal();
            return;
        }

        // Create modal HTML
        const modalHTML = `
            <div class="modal" id="createEcrModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Create Engineering Change Request</h2>
                        <span class="close" onclick="window.ecr.hideCreateECRModal()">&times;</span>
                    </div>
                    <form id="createEcrForm">
                        <div class="form-group">
                            <label for="ecrTitle">Title</label>
                            <input type="text" id="ecrTitle" required>
                        </div>
                        <div class="form-group">
                            <label for="ecrDescription">Description</label>
                            <textarea id="ecrDescription" rows="3" required></textarea>
                        </div>
                        <div class="form-group">
                            <label for="ecrReason">Reason for Change</label>
                            <textarea id="ecrReason" rows="3" required></textarea>
                        </div>
                        <div class="form-group">
                            <label for="ecrSolution">Proposed Solution</label>
                            <textarea id="ecrSolution" rows="3" required></textarea>
                        </div>
                        <div class="form-group">
                            <label for="ecrAttachments">Attachments</label>
                            <input type="file" id="ecrAttachments" multiple>
                        </div>
                        <button type="submit" class="btn btn-primary">Create ECR</button>
                    </form>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Show modal
        document.getElementById('createEcrModal').style.display = 'block';

        // Add form submit handler
        document.getElementById('createEcrForm').addEventListener('submit', (e) => this.handleCreateECR(e));
    }

    hideCreateECRModal() {
        const modal = document.getElementById('createEcrModal');
        if (modal) {
            modal.remove();
        }
    }

    async handleCreateECR(e) {
        e.preventDefault();
        
        const formData = {
            title: document.getElementById('ecrTitle').value,
            description: document.getElementById('ecrDescription').value,
            reason: document.getElementById('ecrReason').value,
            solution: document.getElementById('ecrSolution').value
        };

        try {
            // For now, just add to local array since backend doesn't have ECR endpoints
            const newECR = {
                id: this.ecrs.length + 1,
                ...formData,
                status: 'Draft',
                creator: window.auth.getUser().username,
                created_date: new Date().toISOString().split('T')[0]
            };

            this.ecrs.unshift(newECR);
            this.renderECRs();
            this.hideCreateECRModal();
            this.showSuccess('ECR created successfully!');
        } catch (error) {
            console.error('Error creating ECR:', error);
            this.showError('Failed to create ECR');
        }
    }

    viewECR(ecrId) {
        const ecr = this.ecrs.find(e => e.id === ecrId);
        if (!ecr) return;

        // Create view modal
        const modalHTML = `
            <div class="modal" id="viewEcrModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>ECR Details</h2>
                        <span class="close" onclick="window.ecr.hideViewECRModal()">&times;</span>
                    </div>
                    <div style="padding: 2rem;">
                        <h3>${ecr.title}</h3>
                        <p><strong>Status:</strong> <span class="status-${ecr.status.toLowerCase()}">${ecr.status}</span></p>
                        <p><strong>Description:</strong> ${ecr.description}</p>
                        <p><strong>Reason:</strong> ${ecr.reason}</p>
                        <p><strong>Proposed Solution:</strong> ${ecr.solution}</p>
                        <p><strong>Created by:</strong> ${ecr.creator}</p>
                        <p><strong>Created on:</strong> ${ecr.created_date}</p>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.getElementById('viewEcrModal').style.display = 'block';
    }

    hideViewECRModal() {
        const modal = document.getElementById('viewEcrModal');
        if (modal) {
            modal.remove();
        }
    }

    editECR(ecrId) {
        // Implementation for editing ECR
        this.showError('Edit functionality coming soon');
    }

    showLoginPrompt() {
        const ecrPage = document.getElementById('ecrPage');
        ecrPage.innerHTML = `
            <div class="page-header">
                <h1>ECR Management</h1>
                <p>Please login to manage ECRs</p>
            </div>
            <div class="ecr-list">
                <div class="list-item">
                    <div class="list-item-header">
                        <h3>Login Required</h3>
                    </div>
                    <p>You need to be logged in to manage Engineering Change Requests.</p>
                    <button class="btn btn-primary" onclick="window.auth.showLoginModal()">
                        <i class="fas fa-sign-in-alt"></i> Login
                    </button>
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

// Initialize ECR module
window.ecr = new ECR(); 