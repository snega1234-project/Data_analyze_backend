document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const fileNameDisplay = document.getElementById('file-name');
    const uploadBtn = document.getElementById('upload-btn');
    const configureSection = document.getElementById('configure-section');
    const xFieldSelect = document.getElementById('x-field');
    const yFieldSelect = document.getElementById('y-field');
    const chartForm = document.getElementById('chart-form');
    const visualizationSection = document.getElementById('visualization-section');
    const chartImage = document.getElementById('chart-image');
    const uploadLoader = document.getElementById('upload-loader');
    const chartLoader = document.getElementById('chart-loader');

    let currentFileName = '';

    // Drag and drop handlers
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
            fileInput.files = e.dataTransfer.files;
            handleFileSelect();
        }
    });

    fileInput.addEventListener('change', handleFileSelect);

    function handleFileSelect() {
        if (fileInput.files.length > 0) {
            fileNameDisplay.textContent = fileInput.files[0].name;
            uploadBtn.disabled = false;
            // Make button blue
            uploadBtn.classList.remove('action-btn');
            uploadBtn.classList.add('primary-btn');
            
            // Hide the visualization section and disable configure section when a new file is browsed
            visualizationSection.style.display = 'none';
            configureSection.classList.add('disabled');
            
            // Hide previous dataset info
            const datasetInfo = document.getElementById('dataset-info');
            if (datasetInfo) datasetInfo.style.display = 'none';
        }
    }

    uploadBtn.addEventListener('click', async () => {
        if (!fileInput.files.length) return;

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        uploadBtn.style.display = 'none';
        uploadLoader.style.display = 'block';

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || await response.text());
            }

            const data = await response.json();
            currentFileName = data.filename;
            
            // Populate selects
            xFieldSelect.innerHTML = '';
            yFieldSelect.innerHTML = '<option value="">-- None --</option>';
            
            data.columns.forEach(col => {
                xFieldSelect.innerHTML += `<option value="${col}">${col}</option>`;
                yFieldSelect.innerHTML += `<option value="${col}">${col}</option>`;
            });

            configureSection.classList.remove('disabled');
            
            // Provide visual feedback for success
            const originalText = uploadBtn.textContent;
            uploadBtn.textContent = 'Upload Successful!';
            uploadBtn.style.background = '#10b981'; // Green
            
            const datasetInfo = document.getElementById('dataset-info');
            if (datasetInfo && data.row_count !== undefined) {
                datasetInfo.textContent = `Dataset loaded: ${data.row_count.toLocaleString()} rows × ${data.column_count.toLocaleString()} columns`;
                datasetInfo.style.display = 'block';
            }
            
            setTimeout(() => {
                uploadBtn.textContent = originalText;
                uploadBtn.style.background = '';
            }, 3000);

        } catch (error) {
            showToast('Error uploading file: ' + error.message, 'error');
        } finally {
            uploadBtn.style.display = 'block';
            uploadLoader.style.display = 'none';
        }
    });

    chartForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!currentFileName) return;

        const chartType = document.getElementById('chart-type').value;
        const xField = document.getElementById('x-field').value;
        const yField = document.getElementById('y-field').value;

        const formData = new FormData();
        formData.append('filename', currentFileName);
        formData.append('chart_type', chartType);
        formData.append('x_field', xField);
        formData.append('y_field', yField);

        const submitBtn = chartForm.querySelector('button[type="submit"]');
        submitBtn.style.display = 'none';
        chartLoader.style.display = 'block';

        try {
            const response = await fetch('/api/visualize', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || await response.text());
            }

            const data = await response.json();
            chartImage.src = data.image;
            visualizationSection.style.display = 'block';
            
            // Scroll to visualization
            setTimeout(() => {
                visualizationSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        } catch (error) {
            showToast('Error generating chart: ' + error.message, 'error');
        } finally {
            submitBtn.style.display = 'block';
            chartLoader.style.display = 'none';
        }
    });

    // Custom Toast Logic
    function showToast(message, type = 'error') {
        const container = document.getElementById('toast-container');
        if (!container) return; // Fallback just in case
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const content = document.createElement('div');
        content.className = 'toast-content';
        content.textContent = message;
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = () => removeToast(toast);
        
        toast.appendChild(content);
        toast.appendChild(closeBtn);
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                removeToast(toast);
            }
        }, 5000);
    }
    
    function removeToast(toast) {
        toast.classList.add('hiding');
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }
});
