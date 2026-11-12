/**
 * VAPS Technosoft - Language Translator Frontend Application
 * Interacts with FastAPI backend for text and document translations.
 */

// Determine API base URL dynamically
const API_BASE = (function () {
  if (window.location.protocol === 'file:' || (window.location.port !== '8000' && !window.location.host.includes('vercel.app'))) {
    return 'http://127.0.0.1:8000';
  }
  return '';
})();

// Native language names and scripts
const NATIVE_LANGUAGE_MAP = {
  kn: { native: 'ಕನ್ನಡ', family: 'Dravidian' },
  hi: { native: 'हिन्दी', family: 'Indo-Aryan' },
  ta: { native: 'தமிழ்', family: 'Dravidian' },
  te: { native: 'తెలుగు', family: 'Dravidian' },
  ml: { native: 'മലയാളം', family: 'Dravidian' },
  mr: { native: 'मराठी', family: 'Indo-Aryan' },
  bn: { native: 'বাংলা', family: 'Indo-Aryan' },
  gu: { native: 'ગુજરાતી', family: 'Indo-Aryan' },
  pa: { native: 'ਪੰਜਾਬੀ', family: 'Indo-Aryan' },
  or: { native: 'ଓଡ଼ିଆ', family: 'Indo-Aryan' },
  ur: { native: 'اردو', family: 'Indo-Aryan' }
};

// Application State
const state = {
  languages: [],
  selectedTargetLang: 'kn',
  selectedFile: null,
  isTranslating: false,
  fontSize: 17,
  docOriginalText: '',
  docTranslatedText: ''
};

// Global Tab Switching function (failsafe)
function switchTab(tabName) {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');

  tabBtns.forEach(btn => {
    if (btn.getAttribute('data-tab') === tabName) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  tabPanels.forEach(panel => {
    if (panel.id === `tab-${tabName}`) {
      panel.classList.add('active');
    } else {
      panel.classList.remove('active');
    }
  });
}
window.switchTab = switchTab;

/* ==========================================================================
   Initialization (Runs immediately or when DOM is ready)
   ========================================================================== */
function init() {
  checkApiHealth();
  fetchSupportedLanguages();
  bindTextTranslatorEvents();
  bindDocTranslatorEvents();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

/* ==========================================================================
   API Health & Supported Languages
   ========================================================================== */
async function checkApiHealth() {
  const statusDot = document.getElementById('status-dot');
  const statusText = document.getElementById('status-text');
  if (!statusDot || !statusText) return;

  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      const data = await res.json();
      if (data.status === 'healthy') {
        statusDot.className = 'status-dot healthy';
        statusText.textContent = 'API Connected';
        return;
      }
    }
    throw new Error('Unhealthy status');
  } catch (err) {
    statusDot.className = 'status-dot offline';
    statusText.textContent = 'Backend Offline';
  }
}

async function fetchSupportedLanguages() {
  try {
    const res = await fetch(`${API_BASE}/languages`);
    if (!res.ok) throw new Error('Failed to fetch languages');
    const data = await res.json();
    state.languages = data.languages || [];
  } catch (err) {
    state.languages = [
      { code: 'kn', name: 'Kannada' },
      { code: 'hi', name: 'Hindi' },
      { code: 'ta', name: 'Tamil' },
      { code: 'te', name: 'Telugu' },
      { code: 'ml', name: 'Malayalam' },
      { code: 'mr', name: 'Marathi' },
      { code: 'bn', name: 'Bengali' },
      { code: 'gu', name: 'Gujarati' },
      { code: 'pa', name: 'Punjabi' },
      { code: 'or', name: 'Odia' },
      { code: 'ur', name: 'Urdu' }
    ];
  }
  renderLanguageSelects();
  renderLanguagesGrid();
}

function renderLanguageSelects() {
  const targetSelect = document.getElementById('target-lang-select');
  const docTargetSelect = document.getElementById('doc-target-lang-select');
  if (!targetSelect || !docTargetSelect) return;

  const optionsHtml = state.languages.map(lang => {
    const native = NATIVE_LANGUAGE_MAP[lang.code]?.native || '';
    return `<option value="${lang.code}">${lang.name} ${native ? `(${native})` : ''}</option>`;
  }).join('');

  targetSelect.innerHTML = optionsHtml;
  docTargetSelect.innerHTML = optionsHtml;

  targetSelect.value = state.selectedTargetLang;
  docTargetSelect.value = state.selectedTargetLang;
}

function setTargetLanguage(code) {
  state.selectedTargetLang = code;
  const targetSelect = document.getElementById('target-lang-select');
  const docTargetSelect = document.getElementById('doc-target-lang-select');
  if (targetSelect) targetSelect.value = code;
  if (docTargetSelect) docTargetSelect.value = code;
}
window.setTargetLanguage = setTargetLanguage;

function renderLanguagesGrid() {
  const languagesGrid = document.getElementById('languages-grid');
  if (!languagesGrid) return;

  languagesGrid.innerHTML = state.languages.map(lang => {
    const meta = NATIVE_LANGUAGE_MAP[lang.code] || { native: lang.name, family: 'Indian' };
    return `
      <div class="language-card" onclick="selectLanguageAndSwitch('${lang.code}')">
        <div>
          <div class="lang-card-header">
            <span class="lang-native-name">${meta.native}</span>
            <span class="lang-code-badge">${lang.code}</span>
          </div>
          <div class="lang-english-name">${lang.name}</div>
          <div class="lang-family">Family: ${meta.family}</div>
        </div>
        <div class="lang-card-footer">
          <span>Click to Translate</span>
          <span>→</span>
        </div>
      </div>
    `;
  }).join('');
}

window.selectLanguageAndSwitch = function(code) {
  setTargetLanguage(code);
  switchTab('text');
  showToast(`Selected ${state.languages.find(l => l.code === code)?.name || code}`, 'info');
};

/* ==========================================================================
   Text Translator Operations
   ========================================================================== */
function bindTextTranslatorEvents() {
  const sourceText = document.getElementById('source-text');
  const targetSelect = document.getElementById('target-lang-select');
  const translateBtn = document.getElementById('translate-btn');
  const clearBtn = document.getElementById('clear-btn');
  const pasteBtn = document.getElementById('paste-btn');
  const copyBtn = document.getElementById('copy-btn');
  const speakBtn = document.getElementById('speak-btn');
  const downloadTxtBtn = document.getElementById('download-txt-btn');
  const fontIncBtn = document.getElementById('font-inc-btn');
  const fontDecBtn = document.getElementById('font-dec-btn');
  const targetOutput = document.getElementById('target-output');

  if (sourceText) {
    sourceText.addEventListener('input', updateCounts);
    sourceText.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        translateText();
      }
    });
  }

  if (targetSelect) {
    targetSelect.addEventListener('change', (e) => {
      setTargetLanguage(e.target.value);
      if (sourceText && sourceText.value.trim().length > 0) {
        translateText();
      }
    });
  }

  if (translateBtn) translateBtn.addEventListener('click', translateText);

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (sourceText) sourceText.value = '';
      if (targetOutput) {
        targetOutput.innerHTML = '<span class="target-placeholder">Translation will appear here in native Indian script...</span>';
      }
      updateCounts();
      if (sourceText) sourceText.focus();
    });
  }

  if (pasteBtn) {
    pasteBtn.addEventListener('click', async () => {
      try {
        const text = await navigator.clipboard.readText();
        if (text && sourceText) {
          sourceText.value = text;
          updateCounts();
          showToast('Text pasted from clipboard', 'info');
          translateText();
        }
      } catch (err) {
        showToast('Clipboard access denied. Please paste manually.', 'error');
      }
    });
  }

  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      const text = targetOutput ? targetOutput.innerText.trim() : '';
      if (!text || text.includes('Translation will appear here')) {
        showToast('No translated text to copy', 'error');
        return;
      }
      navigator.clipboard.writeText(text).then(() => {
        showToast('Translation copied to clipboard!', 'success');
      }).catch(() => {
        showToast('Failed to copy to clipboard', 'error');
      });
    });
  }

  if (speakBtn) {
    speakBtn.addEventListener('click', () => {
      const text = targetOutput ? targetOutput.innerText.trim() : '';
      if (!text || text.includes('Translation will appear here')) {
        showToast('No translated text to speak', 'error');
        return;
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = state.selectedTargetLang === 'hi' ? 'hi-IN' : 'en-IN';
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
        showToast('Playing speech pronunciation...', 'info');
      } else {
        showToast('Speech synthesis not supported in this browser', 'error');
      }
    });
  }

  if (downloadTxtBtn) {
    downloadTxtBtn.addEventListener('click', () => {
      const text = targetOutput ? targetOutput.innerText.trim() : '';
      if (!text || text.includes('Translation will appear here')) {
        showToast('No translated text to download', 'error');
        return;
      }
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `translation_${state.selectedTargetLang}.txt`;
      a.click();
      URL.revokeObjectURL(url);
      showToast('Downloaded translation as .txt', 'success');
    });
  }

  if (fontIncBtn && targetOutput) {
    fontIncBtn.addEventListener('click', () => {
      if (state.fontSize < 28) {
        state.fontSize += 2;
        targetOutput.style.fontSize = `${state.fontSize}px`;
      }
    });
  }

  if (fontDecBtn && targetOutput) {
    fontDecBtn.addEventListener('click', () => {
      if (state.fontSize > 13) {
        state.fontSize -= 2;
        targetOutput.style.fontSize = `${state.fontSize}px`;
      }
    });
  }
}

function updateCounts() {
  const sourceText = document.getElementById('source-text');
  const charCount = document.getElementById('char-count');
  const wordCount = document.getElementById('word-count');
  if (!sourceText) return;

  const text = sourceText.value;
  if (charCount) charCount.textContent = `${text.length.toLocaleString()} / 150,000`;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  if (wordCount) wordCount.textContent = `${words.toLocaleString()} words`;
}

async function translateText() {
  const sourceText = document.getElementById('source-text');
  const translateBtn = document.getElementById('translate-btn');
  const targetOutput = document.getElementById('target-output');
  if (!sourceText || !translateBtn || !targetOutput) return;

  const text = sourceText.value.trim();
  if (!text) {
    showToast('Please enter text to translate', 'error');
    sourceText.focus();
    return;
  }

  if (state.isTranslating) return;

  state.isTranslating = true;
  translateBtn.disabled = true;
  const originalBtnHtml = translateBtn.innerHTML;
  translateBtn.innerHTML = `
    <span class="spinner"></span>
    <span>Translating...</span>
  `;

  targetOutput.innerHTML = `
    <div style="display: flex; align-items: center; gap: 0.75rem; color: var(--text-muted); padding: 1rem 0;">
      <span class="spinner" style="border-top-color: var(--primary);"></span>
      <span>Generating high-precision translation into ${NATIVE_LANGUAGE_MAP[state.selectedTargetLang]?.native || state.selectedTargetLang}...</span>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/translate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: text,
        source_language: 'en',
        target_language: state.selectedTargetLang
      })
    });

    const data = await res.json();

    if (!res.ok) {
      const errorMsg = data.detail || 'Translation request failed.';
      throw new Error(errorMsg);
    }

    targetOutput.textContent = data.translated_text;
    showToast('Translation completed successfully!', 'success');
  } catch (err) {
    console.error('Translation error:', err);
    targetOutput.innerHTML = `
      <div style="color: var(--danger); padding: 0.75rem 0;">
        <strong>Translation Notice:</strong> ${escapeHtml(err.message)}
      </div>
    `;
    showToast(err.message, 'error');
  } finally {
    state.isTranslating = false;
    translateBtn.disabled = false;
    translateBtn.innerHTML = originalBtnHtml;
  }
}
window.translateText = translateText;

// Direct Document Loader into Editor
async function loadDocumentIntoEditor(file) {
  if (!file) return;

  const allowedExts = ['docx', 'pdf', 'txt'];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!allowedExts.includes(ext)) {
    showToast('Please upload a .docx, .pdf, or .txt file', 'error');
    return;
  }

  const sourceText = document.getElementById('source-text');
  const targetOutput = document.getElementById('target-output');

  showToast(`Extracting text from ${file.name}...`, 'info');
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_language', 'en');
  formData.append('target_language', state.selectedTargetLang || 'kn');

  try {
    const res = await fetch(`${API_BASE}/translate/document`, {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Extraction failed');

    if (sourceText) sourceText.value = data.original_text;
    if (targetOutput) targetOutput.textContent = data.translated_text;
    updateCounts();
    showToast(`Loaded and translated ${file.name}!`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}
window.loadDocumentIntoEditor = loadDocumentIntoEditor;

/* ==========================================================================
   Document Translator Operations
   ========================================================================== */
function bindDocTranslatorEvents() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const removeFileBtn = document.getElementById('remove-file-btn');
  const docTranslateViewBtn = document.getElementById('doc-translate-view-btn');
  const docTranslateDownloadBtn = document.getElementById('doc-translate-download-btn');
  const docTabBtns = document.querySelectorAll('.doc-tab-btn');
  const docCopyBtn = document.getElementById('doc-copy-btn');

  if (dropZone) {
    ['dragenter', 'dragover'].forEach(name => {
      dropZone.addEventListener(name, (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(name => {
      dropZone.addEventListener(name, (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
      });
    });

    dropZone.addEventListener('drop', (e) => {
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelected(e.dataTransfer.files[0]);
      }
    });
  }

  if (removeFileBtn) {
    removeFileBtn.addEventListener('click', () => {
      state.selectedFile = null;
      if (fileInput) fileInput.value = '';
      const fileBox = document.getElementById('file-selected-box');
      if (fileBox) fileBox.style.display = 'none';
      if (dropZone) dropZone.style.display = 'block';
      if (docTranslateViewBtn) docTranslateViewBtn.disabled = true;
      if (docTranslateDownloadBtn) docTranslateDownloadBtn.disabled = true;
      showToast('Document removed');
    });
  }

  if (docTranslateViewBtn) docTranslateViewBtn.addEventListener('click', translateDocumentAndView);
  if (docTranslateDownloadBtn) docTranslateDownloadBtn.addEventListener('click', translateDocumentAndDownload);

  docTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      docTabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const viewType = btn.getAttribute('data-view');
      const viewer = document.getElementById('doc-viewer');
      if (viewer) {
        if (viewType === 'translated') {
          viewer.textContent = state.docTranslatedText;
        } else {
          viewer.textContent = state.docOriginalText;
        }
      }
    });
  });

  if (docCopyBtn) {
    docCopyBtn.addEventListener('click', () => {
      if (!state.docTranslatedText) return;
      navigator.clipboard.writeText(state.docTranslatedText).then(() => {
        showToast('Document translation copied!', 'success');
      });
    });
  }
}

function handleFileSelected(file) {
  if (!file) return;

  const allowedExts = ['docx', 'pdf', 'txt'];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!allowedExts.includes(ext)) {
    showToast('Unsupported file type. Please upload .docx, .pdf, or .txt', 'error');
    return;
  }

  state.selectedFile = file;

  const fileName = document.getElementById('file-name');
  const fileSize = document.getElementById('file-size');
  const fileTypeIcon = document.getElementById('file-type-icon');
  const dropZone = document.getElementById('drop-zone');
  const fileBox = document.getElementById('file-selected-box');
  const viewBtn = document.getElementById('doc-translate-view-btn');
  const dlBtn = document.getElementById('doc-translate-download-btn');

  if (fileName) fileName.textContent = file.name;
  if (fileSize) fileSize.textContent = `${(file.size / 1024).toFixed(1)} KB`;
  if (fileTypeIcon) fileTypeIcon.textContent = ext.toUpperCase();

  if (dropZone) dropZone.style.display = 'none';
  if (fileBox) fileBox.style.display = 'flex';
  if (viewBtn) viewBtn.disabled = false;
  if (dlBtn) dlBtn.disabled = false;

  showToast(`Loaded document: ${file.name}`, 'info');
}
window.handleFileSelected = handleFileSelected;

async function translateDocumentAndView() {
  if (!state.selectedFile) {
    showToast('Please select a file first', 'error');
    return;
  }

  const docTargetSelect = document.getElementById('doc-target-lang-select');
  const targetLang = docTargetSelect ? docTargetSelect.value : state.selectedTargetLang;
  const formData = new FormData();
  formData.append('file', state.selectedFile);
  formData.append('source_language', 'en');
  formData.append('target_language', targetLang);

  const viewBtn = document.getElementById('doc-translate-view-btn');
  const origHtml = viewBtn ? viewBtn.innerHTML : '';
  if (viewBtn) {
    viewBtn.disabled = true;
    viewBtn.innerHTML = '<span class="spinner"></span> Extracting & Translating...';
  }

  try {
    const res = await fetch(`${API_BASE}/translate/document`, {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Document translation failed.');

    state.docOriginalText = data.original_text;
    state.docTranslatedText = data.translated_text;

    const resultCard = document.getElementById('doc-result-card');
    const viewer = document.getElementById('doc-viewer');
    if (resultCard) resultCard.style.display = 'flex';
    if (viewer) viewer.textContent = data.translated_text;

    const transTab = document.querySelector('.doc-tab-btn[data-view="translated"]');
    const origTab = document.querySelector('.doc-tab-btn[data-view="original"]');
    if (transTab) transTab.classList.add('active');
    if (origTab) origTab.classList.remove('active');

    showToast(`Translated ${data.original_characters.toLocaleString()} characters successfully!`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (viewBtn) {
      viewBtn.disabled = false;
      viewBtn.innerHTML = origHtml;
    }
  }
}
window.translateDocumentAndView = translateDocumentAndView;

async function translateDocumentAndDownload() {
  if (!state.selectedFile) {
    showToast('Please select a file first', 'error');
    return;
  }

  const docTargetSelect = document.getElementById('doc-target-lang-select');
  const targetLang = docTargetSelect ? docTargetSelect.value : state.selectedTargetLang;
  const formData = new FormData();
  formData.append('file', state.selectedFile);
  formData.append('source_language', 'en');
  formData.append('target_language', targetLang);

  const dlBtn = document.getElementById('doc-translate-download-btn');
  const origHtml = dlBtn ? dlBtn.innerHTML : '';
  if (dlBtn) {
    dlBtn.disabled = true;
    dlBtn.innerHTML = '<span class="spinner"></span> Generating .docx...';
  }

  try {
    const res = await fetch(`${API_BASE}/translate/document/download`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Download generation failed.');
    }

    const blob = await res.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    const baseName = state.selectedFile.name.replace(/\.[^/.]+$/, '');
    a.download = `translated_${baseName}.docx`;
    a.click();
    URL.revokeObjectURL(downloadUrl);

    showToast('Word document (.docx) downloaded successfully!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (dlBtn) {
      dlBtn.disabled = false;
      dlBtn.innerHTML = origHtml;
    }
  }
}
window.translateDocumentAndDownload = translateDocumentAndDownload;

// Toast Notification Utility
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
window.showToast = showToast;

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
