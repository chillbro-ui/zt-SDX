window.Upload = {
  render() {
    return `
      <div class="upload-page fade-in">
        <header style="margin-bottom: 30px;">
          <h1 style="color: var(--text-primary); font-size: 2rem; font-weight: 600;">Secure File Upload</h1>
          <p style="color: var(--text-secondary); font-size: 1.05rem; margin-top: 5px;">Transmit documents to the Enterprise Vault. All files are automatically subjected to AI Risk Scoring and Data Loss Prevention (DLP) scans.</p>
        </header>

        <div class="card" style="padding: 60px 40px; text-align: center; border: 2px dashed var(--border-strong); border-radius: 12px; background: rgba(0,0,0,0.15); transition: all 0.2s ease;" id="drop-zone">
          <div style="font-size: 3.5rem; margin-bottom: 20px;">📤</div>
          <h3 style="margin-bottom: 10px; color: var(--text-primary); font-size: 1.5rem;">Drag & Drop Files Here</h3>
          <p style="color: var(--text-secondary); margin-bottom: 20px; font-size: 1rem;">Or click to browse your local filesystem</p>

          <div style="margin-bottom: 25px; display: flex; align-items: center; justify-content: center; gap: 12px;">
            <label style="color: var(--text-secondary); font-size: 0.95rem;">Classification:</label>
            <select id="sensitivity-select" class="input" style="padding: 8px 14px; width: auto; background: var(--bg-base); border: 1px solid var(--border-strong); color: var(--text-primary); border-radius: 6px;">
              <option value="PUBLIC">PUBLIC</option>
              <option value="INTERNAL" selected>INTERNAL</option>
              <option value="CONFIDENTIAL">CONFIDENTIAL</option>
              <option value="SECRET">SECRET</option>
            </select>
          </div>
          
          <input type="file" id="file-input" style="display: none;" onchange="window.Upload.handleFileSelect(event)">
          <button class="btn btn-primary" onclick="document.getElementById('file-input').click()" style="padding: 14px 32px; font-size: 1.1rem; font-weight: 600;">
            Select File to Encrypt
          </button>
        </div>

        <div id="upload-status" style="margin-top: 30px; display: none;">
            <!-- Status will be injected here -->
        </div>
      </div>
    `;
  },

  afterRender() {
      const dropZone = document.getElementById('drop-zone');
      if (!dropZone) return;

      // Drag and drop event listeners
      dropZone.addEventListener('dragover', (e) => {
          e.preventDefault();
          dropZone.style.background = 'rgba(0, 240, 255, 0.05)';
          dropZone.style.borderColor = 'var(--ztsdx-cyan)';
      });

      dropZone.addEventListener('dragleave', (e) => {
          e.preventDefault();
          dropZone.style.background = 'rgba(0,0,0,0.15)';
          dropZone.style.borderColor = 'var(--border-strong)';
      });

      dropZone.addEventListener('drop', (e) => {
          e.preventDefault();
          dropZone.style.background = 'rgba(0,0,0,0.15)';
          dropZone.style.borderColor = 'var(--border-strong)';
          
          if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
              this.uploadFile(e.dataTransfer.files[0]);
          }
      });
  },

  handleFileSelect(event) {
      const file = event.target.files[0];
      if (!file) return;
      this.uploadFile(file);
  },

  async uploadFile(file) {
      const statusDiv = document.getElementById('upload-status');
      const dropZone  = document.getElementById('drop-zone');
      const sensitivity = document.getElementById('sensitivity-select')?.value || 'INTERNAL';

      dropZone.style.opacity = '0.4';
      dropZone.style.pointerEvents = 'none';

      statusDiv.style.display = 'block';
      statusDiv.innerHTML = `
        <div class="card" style="padding: 24px; display: flex; align-items: center; gap: 20px; border-left: 4px solid var(--ztsdx-cyan);">
            <div style="font-size: 2.5rem; animation: pulse 1.5s infinite;">⏳</div>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: var(--text-primary); font-size: 1.1rem;">Uploading ${file.name}...</div>
                <div style="font-size: 0.95rem; color: var(--text-secondary); margin-top: 6px;">Encrypting payload (${sensitivity}) and transmitting to ZT-SDX Gateway...</div>
            </div>
        </div>
      `;

      try {
          const response = await window.api.uploadFile(file, sensitivity);
          const fileData = response.file || response;

          statusDiv.innerHTML = `
            <div class="card" style="padding: 30px; border-left: 4px solid #52c41a; background: rgba(82, 196, 26, 0.05);">
                <h3 style="color: #52c41a; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; font-size: 1.4rem;">
                    ✅ Transfer Successful
                </h3>
                <p style="color: var(--text-primary); font-size: 1.05rem; margin-bottom: 20px;">${response.message || 'File uploaded and queued for DLP scan.'}</p>

                <div style="padding: 16px; background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--text-secondary);">
                    <div style="margin-bottom: 8px;"><strong>File ID:</strong> ${fileData.id || '—'}</div>
                    <div style="margin-bottom: 8px;"><strong>Classification:</strong> ${sensitivity}</div>
                    <div><strong>SHA256:</strong> ${fileData.sha256 || '—'}</div>
                </div>

                <div style="margin-top: 25px; display: flex; gap: 15px;">
                    <button class="btn btn-primary" onclick="window.location.hash='#files'">View in Vault</button>
                    <button class="btn btn-secondary" onclick="window.Upload.reset()">Upload Another</button>
                </div>
            </div>
          `;
      } catch (error) {
          statusDiv.innerHTML = `
            <div class="card" style="padding: 30px; border-left: 4px solid #ff4d4f; background: rgba(255, 77, 79, 0.05);">
                <h3 style="color: #ff4d4f; margin-bottom: 10px; font-size: 1.4rem;">❌ Upload Blocked</h3>
                <p style="color: var(--text-primary); font-size: 1.05rem;">${error.message || 'The transfer was interrupted or rejected by policy.'}</p>
                <div style="margin-top: 20px;">
                    <button class="btn btn-secondary" onclick="window.Upload.reset()">Try Again</button>
                </div>
            </div>
          `;
      } finally {
          dropZone.style.opacity = '1';
          dropZone.style.pointerEvents = 'auto';
          document.getElementById('file-input').value = '';
      }
  },

  reset() {
      document.getElementById('upload-status').style.display = 'none';
  }
};
