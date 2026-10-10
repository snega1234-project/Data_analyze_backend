document.addEventListener('DOMContentLoaded', () => {
    // Clear the backend uploads folder on refresh/load
    fetch('/api/cleanup', { method: 'POST' }).catch(err => console.error('Cleanup failed:', err));

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

    // DB Query Elements
    const tabFile = document.getElementById('tab-file');
    const tabDb = document.getElementById('tab-db');
    const uploadSection = document.getElementById('upload-section');
    const dbConnectSection = document.getElementById('db-connect-section');
    const dbQuerySection = document.getElementById('db-query-section');
    const dbForm = document.getElementById('db-form');
    const dbLoader = document.getElementById('db-loader');
    const dbResult = document.getElementById('db-result');
    const downloadCsvBtn = document.getElementById('download-csv-btn');
    const downloadExcelBtn = document.getElementById('download-excel-btn');
    const dbCancelBtn = document.getElementById('db-cancel-btn');

    let currentFileName = '';
    let currentDbResultData = null; // Store CSV data temporarily
    let currentDbExcelData = null; // Store Excel base64 temporarily

    // Tab switching logic
    tabFile.addEventListener('click', () => {
        tabFile.classList.replace('action-btn', 'primary-btn');
        tabDb.classList.replace('primary-btn', 'action-btn');
        uploadSection.style.display = 'block';
        if (!configureSection.classList.contains('disabled')) {
            configureSection.style.display = 'block';
        }
        dbConnectSection.style.display = 'none';
        dbQuerySection.style.display = 'none';
        visualizationSection.style.display = currentFileName ? 'block' : 'none';
    });

    tabDb.addEventListener('click', () => {
        tabDb.classList.replace('action-btn', 'primary-btn');
        tabFile.classList.replace('primary-btn', 'action-btn');
        uploadSection.style.display = 'none';
        configureSection.style.display = 'none';
        visualizationSection.style.display = 'none';
        dbConnectSection.style.display = 'block';
        dbQuerySection.style.display = 'block';
    });

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

    // Test Connection Logic
    const testConnectionBtn = document.getElementById('test-connection-btn');
    if (testConnectionBtn) {
        testConnectionBtn.addEventListener('click', async () => {
            const dbType = document.getElementById('db-type').value;
            const connectionString = document.getElementById('db-connection').value;
            
            if (!dbType || !connectionString) {
                showToast('Please select database type and enter connection string', 'error');
                return;
            }
            
            const originalText = testConnectionBtn.textContent;
            testConnectionBtn.textContent = '...';
            testConnectionBtn.disabled = true;
            
            try {
                const response = await fetch('/api/test_connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ db_type: dbType, connection_string: connectionString })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    showToast('Connection successful!', 'success');
                    testConnectionBtn.style.background = '#10b981';
                    testConnectionBtn.style.color = 'white';
                    testConnectionBtn.textContent = 'Success';
                } else {
                    showToast('Connection failed: ' + data.message, 'error');
                    testConnectionBtn.textContent = 'Failed';
                    testConnectionBtn.style.background = '#ef4444';
                }
            } catch (err) {
                showToast('Connection test error', 'error');
                testConnectionBtn.textContent = 'Failed';
                testConnectionBtn.style.background = '#ef4444';
            } finally {
                setTimeout(() => {
                    testConnectionBtn.textContent = originalText;
                    testConnectionBtn.disabled = false;
                    testConnectionBtn.style.background = '';
                    testConnectionBtn.style.color = '';
                }, 3000);
            }
        });
    }

    // DB Form Logic
    dbForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const dbType = document.getElementById('db-type').value;
        const connectionString = document.getElementById('db-connection').value;
        const apiKey = document.getElementById('ai-api-key').value;
        const query = document.getElementById('ai-query').value;
        
        const formData = new FormData();
        formData.append('db_type', dbType);
        formData.append('connection_string', connectionString);
        formData.append('api_key', apiKey);
        formData.append('query', query);

        const submitBtn = dbForm.querySelector('button[type="submit"]');
        submitBtn.style.display = 'none';
        dbLoader.style.display = 'block';
        dbResult.style.display = 'none';

        try {
            const response = await fetch('/api/db_query', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || await response.text());
            }

            const data = await response.json();
            // Data expected: { csv_data: "...", excel_base64: "..." }
            currentDbResultData = data.csv_data;
            currentDbExcelData = data.excel_base64;
            
            dbForm.style.display = 'none';
            dbResult.style.display = 'block';
            showToast('Query executed successfully!', 'success');
        } catch (error) {
            showToast('Error executing query: ' + error.message, 'error');
            submitBtn.style.display = 'block';
        } finally {
            dbLoader.style.display = 'none';
        }
    });

    downloadCsvBtn.addEventListener('click', () => {
        if (!currentDbResultData) return;
        const blob = new Blob([currentDbResultData], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'query_results.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    });

    if (downloadExcelBtn) {
        downloadExcelBtn.addEventListener('click', () => {
            if (!currentDbExcelData) return;
            // Decode base64 to binary
            const binaryString = window.atob(currentDbExcelData);
            const binaryLen = binaryString.length;
            const bytes = new Uint8Array(binaryLen);
            for (let i = 0; i < binaryLen; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            const blob = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'query_results.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        });
    }

    dbCancelBtn.addEventListener('click', () => {
        currentDbResultData = null;
        currentDbExcelData = null;
        dbResult.style.display = 'none';
        dbForm.style.display = 'block';
        dbForm.reset();
        dbForm.querySelector('button[type="submit"]').style.display = 'block';
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
