document.addEventListener('DOMContentLoaded', () => {
    const themeList = document.getElementById('theme-list');
    const runBtn = document.getElementById('run-pipeline-btn');
    const saveBtn = document.getElementById('save-draft-btn');
    const approveBtn = document.getElementById('approve-draft-btn');
    
    const draftTitle = document.getElementById('draft-title');
    const draftStatus = document.getElementById('draft-status');
    const editorContainer = document.getElementById('editor-container');
    const emptyState = document.getElementById('empty-state');
    const mdEditor = document.getElementById('markdown-editor');
    const mdPreview = document.getElementById('markdown-preview');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    let currentDraftId = null;
    let currentDraftData = null;

    // File Uploader Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('csv-file-input');
    const selectedFileInfo = document.getElementById('selected-file-info');
    const fileNameDisplay = document.getElementById('file-name-display');
    const clearFileBtn = document.getElementById('clear-file-btn');
    
    let selectedFile = null;

    // File Uploader Events
    if (dropZone && fileInput) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                handleFileSelect(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFileSelect(e.target.files[0]);
            }
        });

        clearFileBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            selectedFile = null;
            fileInput.value = '';
            selectedFileInfo.classList.add('hidden');
        });

        function handleFileSelect(file) {
            if (file.name.endsWith('.csv')) {
                selectedFile = file;
                fileNameDisplay.textContent = file.name;
                selectedFileInfo.classList.remove('hidden');
            } else {
                alert('Please select a valid CSV file.');
            }
        }
    }

    // Fetch and render drafts
    async function fetchDrafts() {
        try {
            const response = await fetch('/api/drafts');
            const drafts = await response.json();
            renderThemeList(drafts);
        } catch (error) {
            console.error('Error fetching drafts:', error);
        }
    }

    function renderThemeList(drafts) {
        themeList.innerHTML = '';
        if (drafts.length === 0) {
            themeList.innerHTML = '<p style="color: #9496a8; padding: 1rem; text-align: center;">No themes found. Click "Run Pipeline" to start.</p>';
            return;
        }

        drafts.forEach(draft => {
            const li = document.createElement('li');
            li.className = `theme-item ${currentDraftId === draft.id ? 'active' : ''}`;
            
            const isApproved = draft.status === 'approved';
            li.innerHTML = `
                <div class="theme-name">${draft.theme}</div>
                <div class="theme-meta">
                    <span class="badge ${isApproved ? 'approved' : 'pending'}">${draft.status}</span>
                </div>
            `;
            
            li.addEventListener('click', () => loadDraft(draft.id));
            themeList.appendChild(li);
        });
    }

    // Load a specific draft
    async function loadDraft(id) {
        try {
            const response = await fetch(`/api/drafts/${id}`);
            const draft = await response.json();
            
            currentDraftId = draft.id;
            currentDraftData = draft;
            
            draftTitle.textContent = draft.theme;
            
            const isApproved = draft.status === 'approved';
            draftStatus.textContent = draft.status.toUpperCase();
            draftStatus.className = `status-badge ${isApproved ? 'approved' : 'pending'}`;
            
            mdEditor.value = draft.markdown;
            updatePreview();
            
            emptyState.classList.add('hidden');
            editorContainer.classList.remove('hidden');
            
            saveBtn.disabled = false;
            approveBtn.disabled = isApproved;
            
            fetchDrafts(); // Refresh list to update active state
        } catch (error) {
            console.error('Error loading draft:', error);
        }
    }

    // Update Markdown Preview
    function updatePreview() {
        if (window.marked) {
            mdPreview.innerHTML = marked.parse(mdEditor.value);
        }
    }

    mdEditor.addEventListener('input', updatePreview);

    // Save Draft
    saveBtn.addEventListener('click', async () => {
        if (!currentDraftId) return;
        
        saveBtn.textContent = 'Saving...';
        saveBtn.disabled = true;
        
        try {
            await fetch(`/api/drafts/${currentDraftId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ markdown: mdEditor.value })
            });
            saveBtn.textContent = 'Saved!';
            setTimeout(() => { saveBtn.textContent = 'Save Edits'; saveBtn.disabled = false; }, 2000);
        } catch (error) {
            console.error('Error saving draft:', error);
            saveBtn.textContent = 'Error';
            saveBtn.disabled = false;
        }
    });

    // Approve Draft
    approveBtn.addEventListener('click', async () => {
        if (!currentDraftId) return;
        
        approveBtn.textContent = 'Approving...';
        approveBtn.disabled = true;
        
        try {
            await fetch(`/api/drafts/${currentDraftId}/approve`, {
                method: 'POST'
            });
            await loadDraft(currentDraftId); // Reload to get updated status
        } catch (error) {
            console.error('Error approving draft:', error);
            approveBtn.textContent = 'Error';
            approveBtn.disabled = false;
        }
    });

    // Run Pipeline
    runBtn.addEventListener('click', async () => {
        loadingOverlay.classList.remove('hidden');
        
        try {
            let fetchOptions = { method: 'POST' };
            if (selectedFile) {
                const formData = new FormData();
                formData.append('file', selectedFile);
                fetchOptions.body = formData;
            }

            const response = await fetch('/api/run', fetchOptions);
            if (response.ok) {
                await fetchDrafts();
                currentDraftId = null;
                editorContainer.classList.add('hidden');
                emptyState.classList.remove('hidden');
                draftTitle.textContent = 'Select a Theme';
                draftStatus.textContent = '';
            } else if (response.status === 400) {
                const errorData = await response.json();
                alert(`Data Error: ${errorData.detail}`);
            } else {
                alert('Pipeline failed to run. Check backend console logs.');
            }
        } catch (error) {
            console.error('Error running pipeline:', error);
            alert('Error running pipeline. Make sure the backend server is running and API keys are set.');
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    });

    // Tab Switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Update buttons
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            // Update content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(e.target.dataset.target).classList.add('active');
        });
    });

    // Initial load
    fetchDrafts();
});
