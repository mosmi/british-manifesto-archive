/* app.js — Frontend Application Logic for Manifesto QA Reader */

(function () {
  'use strict';

  // QA Check Codes Dictionary
  const QA_CODES_DICTIONARY = {
    "C1": { category: "COVERAGE", title: "Word Count Coverage", desc: "Word-count coverage vs pdftotext baseline." },
    
    "E1": { category: "ENCODING", title: "Unicode Replacement", desc: "Unicode replacement characters (U+FFFD → '?')." },
    "E2": { category: "ENCODING", title: "Raw CID Token", desc: "Raw CID tokens still present in text e.g. (cid:N)." },
    "E3": { category: "ENCODING", title: "Control Characters", desc: "Non-printing control characters detected." },

    "H1": { category: "HEADINGS", title: "Quoted Heading", desc: "Heading starts with an opening/closing quotation mark." },
    "H2": { category: "HEADINGS", title: "Lowercase Heading", desc: "Heading starts with a lowercase letter." },
    "H3": { category: "HEADINGS", title: "Sentence Continuation Heading", desc: "Heading appears to be a sentence continuation." },
    "H4": { category: "HEADINGS", title: "Punctuation Start Heading", desc: "Heading starts with punctuation (, . : ; ! ? -)." },
    "H5": { category: "HEADINGS", title: "Adjacent Heading Split", desc: "Adjacent same-level headings that could be merged." },
    "H6": { category: "HEADINGS", title: "Excessive Heading Length", desc: "Heading word count > 30 (likely body text promoted to heading)." },

    "B1": { category: "BULLETS", title: "Raw Bullet Glyph", desc: "Raw bullet glyph (•, ●, ◆) still present in paragraph text." },
    "B2": { category: "BULLETS", title: "Mid-Sentence Bullet", desc: "Bullet glyph embedded inside prose text instead of at paragraph start." },
    "B3": { category: "BULLETS", title: "Orphaned Single-Word Bullet", desc: "Orphaned single-word list item (common sidebar continuation artefact)." },
    "B4": { category: "BULLETS", title: "Dangling Preposition Bullet", desc: "Bullet item ends with a preposition/article ('to', 'in') — probable truncation at column or page boundary." },

    "P1": { category: "PARAGRAPHS", title: "Bare Page Number", desc: "Paragraph is a bare page number (1–3 digits)." },
    "P2": { category: "PARAGRAPHS", title: "All-Caps Slogan Run", desc: "All-caps run of ≥ 5 words (possible un-spaced slogan from cover/sidebar)." },
    "P3": { category: "PARAGRAPHS", title: "Duplicate Paragraph", desc: "Repeated paragraph (exact duplicate appearing more than once)." },
    "P4": { category: "PARAGRAPHS", title: "Very Short Paragraph", desc: "Very short paragraph (< 4 words) that is not a heading or list item." },

    "S1": { category: "SPACING", title: "Missing Space After Period", desc: "Missing space after sentence-ending period ('word.Word')." },
    "S2": { category: "SPACING", title: "Missing Space After Comma", desc: "Missing space after comma ('word,word')." },
    "S3": { category: "SPACING", title: "Merged ALL-CAPS Words", desc: "Run-together ALL-CAPS words ('ANDVOLUNTARY')." },
    "S4": { category: "SPACING", title: "Repeated Consecutive Word", desc: "Repeated consecutive identical word ('of of', 'the the')." },

    "I2": { category: "LAYOUT", title: "Attribution Signature Garble", desc: "Two-column foreword signatures merged into a single line ('Leader of the Leader of the')." },

    "V1": { category: "VERTICAL", title: "Vertical Header Fragment", desc: "Repeated single-letter or two-letter fragments — likely vertical header text." },
    "V2": { category: "VERTICAL", title: "Spaced Initials Paragraph", desc: "Paragraph composed only of spaced initials (e.g. 'P y W b A m')." },
    "V3": { category: "VERTICAL", title: "Single-Character Paragraph", desc: "Improbable single-character paragraph." },

    "R1": { category: "READING ORDER", title: "Column-Join Word Repeat", desc: "Repeated adjacent words at likely column joins within a paragraph." },
    "R2": { category: "READING ORDER", title: "Embedded Bullet Glyph", desc: "Bullet glyph embedded inside a prose paragraph (reading-order symptom)." },
    "R3": { category: "READING ORDER", title: "High Short-Fragment Ratio", desc: "Unusually high ratio of short orphan fragments — suggests spread-column interleaving." }
  };

  // State
  let manifestos = [];
  let currentSlug = '';
  let manifestoData = null;
  let pageData = null;
  let currentPageIndex = 0;
  let currentZoom = 1.0;
  let hasUnsavedChanges = false;

  // DOM Elements
  const manifestoSelect = document.getElementById('manifesto-select');
  const btnPrevPage = document.getElementById('btn-prev-page');
  const btnNextPage = document.getElementById('btn-next-page');
  const btnPrevFlagged = document.getElementById('btn-prev-flagged');
  const btnNextFlagged = document.getElementById('btn-next-flagged');
  const inputPageNum = document.getElementById('input-page-num');
  const textTotalPages = document.getElementById('text-total-pages');
  const badgeFlaggedCount = document.getElementById('badge-flagged-count');
  const btnSave = document.getElementById('btn-save');
  const btnAcceptFlag = document.getElementById('btn-accept-flag');
  const btnGlossary = document.getElementById('btn-glossary');

  const pageImage = document.getElementById('page-image');
  const textZoomLevel = document.getElementById('text-zoom-level');
  const btnZoomIn = document.getElementById('btn-zoom-in');
  const btnZoomOut = document.getElementById('btn-zoom-out');
  const btnZoomReset = document.getElementById('btn-zoom-reset');

  const tabEdit = document.getElementById('tab-edit');
  const tabPreview = document.getElementById('tab-preview');
  const tabDiff = document.getElementById('tab-diff');
  const viewEditor = document.getElementById('view-editor');
  const viewPreview = document.getElementById('view-preview');
  const viewDiff = document.getElementById('view-diff');

  const markdownEditor = document.getElementById('markdown-editor');
  const markdownRendered = document.getElementById('markdown-rendered');
  const diffBaselineText = document.getElementById('diff-baseline-text');
  const diffSelectedText = document.getElementById('diff-selected-text');
  const pageStatusPill = document.getElementById('page-status-pill');

  const qaPageNum = document.getElementById('qa-page-num');
  const metricCandWords = document.getElementById('metric-cand-words');
  const metricBaseWords = document.getElementById('metric-base-words');
  const metricRatio = document.getElementById('metric-ratio');
  const qaIssuesList = document.getElementById('qa-issues-list');

  // Modal Elements
  const modalGlossary = document.getElementById('modal-glossary');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const inputGlossarySearch = document.getElementById('input-glossary-search');
  const glossaryContent = document.getElementById('glossary-content');

  // Initialize
  async function init() {
    setupEventListeners();
    renderGlossary();
    await fetchManifestos();
  }

  // Event Listeners
  function setupEventListeners() {
    manifestoSelect.addEventListener('change', async (e) => {
      if (e.target.value) {
        if (hasUnsavedChanges) {
          await saveCurrentPage(false);
        }
        await loadManifesto(e.target.value);
      }
    });

    btnPrevPage.addEventListener('click', () => changePage(currentPageIndex - 1));
    btnNextPage.addEventListener('click', () => changePage(currentPageIndex + 1));
    btnPrevFlagged.addEventListener('click', () => jumpFlagged(-1));
    btnNextFlagged.addEventListener('click', () => jumpFlagged(1));

    inputPageNum.addEventListener('change', (e) => {
      const val = parseInt(e.target.value, 10) - 1;
      if (!isNaN(val)) changePage(val);
    });

    btnSave.addEventListener('click', () => saveCurrentPage(true));
    btnAcceptFlag.addEventListener('click', acceptCurrentFlag);

    // Zoom
    btnZoomIn.addEventListener('click', () => setZoom(currentZoom + 0.25));
    btnZoomOut.addEventListener('click', () => setZoom(currentZoom - 0.25));
    btnZoomReset.addEventListener('click', () => setZoom(1.0));

    // Tabs
    tabEdit.addEventListener('click', () => switchTab('edit'));
    tabPreview.addEventListener('click', () => switchTab('preview'));
    tabDiff.addEventListener('click', () => switchTab('diff'));

    // Modal Glossary
    btnGlossary.addEventListener('click', () => openGlossary());
    btnCloseModal.addEventListener('click', () => closeGlossary());
    modalGlossary.addEventListener('click', (e) => {
      if (e.target === modalGlossary) closeGlossary();
    });
    inputGlossarySearch.addEventListener('input', (e) => renderGlossary(e.target.value));

    // Live Preview update & Unsaved changes tracking on edit
    markdownEditor.addEventListener('input', () => {
      markUnsaved(true);
      updateRenderedPreview();
    });

    // Warn before closing browser tab if unsaved
    window.addEventListener('beforeunload', (e) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    });

    // Keyboard Shortcuts
    document.addEventListener('keydown', handleGlobalKeydown);
  }

  function markUnsaved(isUnsaved) {
    hasUnsavedChanges = isUnsaved;
    if (isUnsaved) {
      btnSave.classList.add('btn-unsaved');
      btnSave.textContent = '💾 Save Edit *';
    } else {
      btnSave.classList.remove('btn-unsaved');
      btnSave.textContent = '💾 Save Edit';
    }
  }

  function openGlossary(filterText = '') {
    modalGlossary.classList.remove('hidden');
    inputGlossarySearch.value = filterText;
    renderGlossary(filterText);
    inputGlossarySearch.focus();
  }

  function closeGlossary() {
    modalGlossary.classList.add('hidden');
  }

  function renderGlossary(searchQuery = '') {
    const query = searchQuery.trim().toLowerCase();
    const categories = {};

    Object.keys(QA_CODES_DICTIONARY).forEach(code => {
      const info = QA_CODES_DICTIONARY[code];
      const match = !query || 
        code.toLowerCase().includes(query) || 
        info.title.toLowerCase().includes(query) || 
        info.desc.toLowerCase().includes(query) ||
        info.category.toLowerCase().includes(query);

      if (match) {
        categories[info.category] = categories[info.category] || [];
        categories[info.category].push({ code, ...info });
      }
    });

    if (Object.keys(categories).length === 0) {
      glossaryContent.innerHTML = '<div class="no-issues">No matching QA warning/error codes found.</div>';
      return;
    }

    let html = '';
    Object.keys(categories).forEach(cat => {
      html += `<div class="glossary-section">`;
      html += `<div class="glossary-category-title">${cat}</div>`;
      categories[cat].forEach(item => {
        html += `
          <div class="glossary-card">
            <span class="glossary-code">${item.code}</span>
            <div class="glossary-info">
              <span class="glossary-info-title">${item.title}</span>
              <span class="glossary-info-desc">${item.desc}</span>
            </div>
          </div>
        `;
      });
      html += `</div>`;
    });

    glossaryContent.innerHTML = html;
  }

  function switchTab(tabName) {
    [tabEdit, tabPreview, tabDiff].forEach(t => t.classList.remove('active'));
    [viewEditor, viewPreview, viewDiff].forEach(v => v.classList.remove('active'));

    if (tabName === 'edit') {
      tabEdit.classList.add('active');
      viewEditor.classList.add('active');
    } else if (tabName === 'preview') {
      tabPreview.classList.add('active');
      viewPreview.classList.add('active');
      updateRenderedPreview();
    } else if (tabName === 'diff') {
      tabDiff.classList.add('active');
      viewDiff.classList.add('active');
    }
  }

  function setZoom(level) {
    currentZoom = Math.max(0.5, Math.min(3.0, level));
    pageImage.style.transform = `scale(${currentZoom})`;
    textZoomLevel.textContent = `${Math.round(currentZoom * 100)}%`;
  }

  // Fetch Manifestos List
  async function fetchManifestos() {
    try {
      const res = await fetch('/api/manifestos');
      const data = await res.json();
      manifestos = data.manifestos || [];

      manifestoSelect.innerHTML = manifestos.map(m => {
        const flagBadge = m.flagged_count > 0 ? ` ⚠️ (${m.flagged_count} flagged)` : ' ✓';
        return `<option value="${m.slug}">${m.display_name} — ${m.total_pages} pp${flagBadge}</option>`;
      }).join('');

      if (manifestos.length > 0) {
        const flaggedOne = manifestos.find(m => m.flagged_count > 0);
        const target = flaggedOne ? flaggedOne.slug : manifestos[0].slug;
        manifestoSelect.value = target;
        await loadManifesto(target);
      }
    } catch (err) {
      console.error('Failed to fetch manifestos:', err);
    }
  }

  // Load Selected Manifesto
  async function loadManifesto(slug, preservePageIndex = null) {
    currentSlug = slug;
    try {
      const res = await fetch(`/api/manifesto/${slug}`);
      manifestoData = await res.json();

      textTotalPages.textContent = manifestoData.total_pages;
      inputPageNum.max = manifestoData.total_pages;

      const flaggedCount = (manifestoData.flagged_pages || []).length;
      badgeFlaggedCount.textContent = flaggedCount;

      let startPage = 0;
      if (preservePageIndex !== null && preservePageIndex >= 0 && preservePageIndex < manifestoData.total_pages) {
        startPage = preservePageIndex;
      } else if (flaggedCount > 0) {
        startPage = manifestoData.flagged_pages[0].page_index;
      }
      await loadPage(startPage);
    } catch (err) {
      console.error('Failed to load manifesto:', err);
    }
  }

  // Change Page (Auto-saves unsaved edits before navigating)
  async function changePage(pageIndex) {
    if (!manifestoData) return;
    const max = manifestoData.total_pages - 1;
    const target = Math.max(0, Math.min(max, pageIndex));
    if (target === currentPageIndex) return;

    if (hasUnsavedChanges) {
      await saveCurrentPage(false);
    }
    await loadPage(target);
  }

  // Jump to Next / Prev Flagged Page (Auto-saves unsaved edits)
  async function jumpFlagged(direction) {
    if (!manifestoData) return;
    const flaggedPages = (manifestoData.flagged_pages || []).map(p => p.page_index);
    if (flaggedPages.length === 0) return;

    let target = currentPageIndex;
    if (direction > 0) {
      const next = flaggedPages.find(idx => idx > currentPageIndex);
      target = next !== undefined ? next : flaggedPages[0];
    } else {
      const prev = [...flaggedPages].reverse().find(idx => idx < currentPageIndex);
      target = prev !== undefined ? prev : flaggedPages[flaggedPages.length - 1];
    }

    if (hasUnsavedChanges) {
      await saveCurrentPage(false);
    }
    await loadPage(target);
  }

  // Load Page Data
  async function loadPage(pageIndex) {
    currentPageIndex = pageIndex;
    inputPageNum.value = pageIndex + 1;
    qaPageNum.textContent = pageIndex + 1;

    try {
      const res = await fetch(`/api/manifesto/${currentSlug}/page/${pageIndex}`);
      pageData = await res.json();

      if (pageData.image_url) {
        pageImage.src = pageData.image_url;
      } else {
        pageImage.src = '';
      }

      markdownEditor.value = pageData.selected_text || '';
      markUnsaved(false);
      updateRenderedPreview();

      diffBaselineText.textContent = pageData.baseline_text || '(No pdftotext baseline available)';
      diffSelectedText.textContent = pageData.selected_text || '';

      pageStatusPill.textContent = pageData.status || 'unknown';
      pageStatusPill.className = `status-pill ${pageData.status || ''}`;

      updateQADrawer();

    } catch (err) {
      console.error('Failed to load page:', err);
    }
  }

  // Update Rendered Preview
  function updateRenderedPreview() {
    if (window.marked) {
      markdownRendered.innerHTML = marked.parse(markdownEditor.value || '');
    } else {
      markdownRendered.textContent = markdownEditor.value || '';
    }
  }

  // Helper to format issue string into HTML with clickable code badges
  function formatIssueHtml(issueStr) {
    // Look for codes like B2, R2, H2, E1, P2, etc.
    const codeRegex = /\b([A-Z][0-9])\b/g;
    let formatted = issueStr;
    const codesFound = [];
    let match;

    while ((match = codeRegex.exec(issueStr)) !== null) {
      codesFound.push(match[1]);
    }

    if (codesFound.length > 0) {
      codesFound.forEach(code => {
        const dict = QA_CODES_DICTIONARY[code];
        const titleAttr = dict ? `${code}: ${dict.title} — ${dict.desc}` : code;
        const badgeHtml = `<span class="qa-code-badge" data-code="${code}" title="${titleAttr}">${code}</span>`;
        formatted = formatted.replace(new RegExp(`\\b${code}\\b`, 'g'), badgeHtml);
      });
    }

    return `⚠️ ${formatted}`;
  }

  // Update QA Drawer
  function updateQADrawer() {
    if (!pageData) return;

    const candWords = pageData.selected_text ? pageData.selected_text.trim().split(/\s+/).length : 0;
    const baseWords = pageData.baseline_text ? pageData.baseline_text.trim().split(/\s+/).length : 0;
    const ratio = baseWords > 0 ? (candWords / baseWords).toFixed(2) : '1.00';

    metricCandWords.textContent = candWords;
    metricBaseWords.textContent = baseWords;
    metricRatio.textContent = ratio;

    const issues = pageData.issues || [];
    if (issues.length === 0) {
      qaIssuesList.innerHTML = '<div class="no-issues">✓ No gate flags or structural issues recorded for this page.</div>';
    } else {
      qaIssuesList.innerHTML = issues.map(iss => `<div class="qa-issue-item">${formatIssueHtml(iss)}</div>`).join('');
      
      // Bind click events on code badges
      qaIssuesList.querySelectorAll('.qa-code-badge').forEach(badge => {
        badge.addEventListener('click', (e) => {
          const code = e.target.getAttribute('data-code');
          if (code) {
            openGlossary(code);
          }
        });
      });
    }
  }

  // Save Page
  async function saveCurrentPage(refreshManifesto = true) {
    if (!currentSlug || pageData === null) return;

    btnSave.disabled = true;
    btnSave.textContent = '⏳ Saving...';

    try {
      const res = await fetch(`/api/manifesto/${currentSlug}/page/${currentPageIndex}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: markdownEditor.value, mark_reviewed: true })
      });
      const result = await res.json();
      if (result.success) {
        markUnsaved(false);
        btnSave.textContent = '✓ Saved!';
        setTimeout(() => {
          btnSave.disabled = false;
          btnSave.textContent = '💾 Save Edit';
        }, 1200);
        if (refreshManifesto) {
          await loadManifesto(currentSlug, currentPageIndex);
        }
      }
    } catch (err) {
      console.error('Failed to save page:', err);
      btnSave.disabled = false;
      btnSave.textContent = '💾 Save Edit';
    }
  }

  // Accept Flag
  async function acceptCurrentFlag() {
    if (!currentSlug || pageData === null) return;

    try {
      const res = await fetch(`/api/manifesto/${currentSlug}/page/${currentPageIndex}/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await res.json();
      if (result.success) {
        await loadManifesto(currentSlug);
        jumpFlagged(1);
      }
    } catch (err) {
      console.error('Failed to accept flag:', err);
    }
  }

  // Global Keydown Handler
  function handleGlobalKeydown(e) {
    if (e.key === 'Escape' && !modalGlossary.classList.contains('hidden')) {
      closeGlossary();
      return;
    }

    const isEditingText = document.activeElement === markdownEditor || 
                          document.activeElement === inputPageNum || 
                          document.activeElement === inputGlossarySearch;

    if (e.key === 'ArrowLeft' && !isEditingText) {
      e.preventDefault();
      changePage(currentPageIndex - 1);
    } else if (e.key === 'ArrowRight' && !isEditingText) {
      e.preventDefault();
      changePage(currentPageIndex + 1);
    } else if ((e.metaKey || e.ctrlKey) && e.key === 's') {
      e.preventDefault();
      saveCurrentPage();
    } else if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      acceptCurrentFlag();
    }
  }

  // Start app
  document.addEventListener('DOMContentLoaded', init);

})();
