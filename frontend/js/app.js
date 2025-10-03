// Simple routing system
const routes = ["home", "simulate", "summary", "view"];

function showRoute(id) {
  console.log('=== showRoute called with:', id);
  
  // Hide all routes first
  routes.forEach(r => {
    const element = document.getElementById(r);
    if (element) {
      element.classList.add('hidden');
      console.log('Hiding route:', r);
    } else {
      console.log('Route element not found:', r);
    }
  });
  
  
  // Show the requested route
  const targetElement = document.getElementById(id);
  console.log('Target element for', id, ':', targetElement);
  if (targetElement) {
    targetElement.classList.remove('hidden');
    console.log('Route shown successfully:', id);
  } else {
    console.error('Route not found:', id);
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  console.log('Page loaded');
  showRoute('home'); // Start with home page
});

// Handle all clicks
document.addEventListener('click', function(e) {
  console.log('Click detected:', e.target, 'Classes:', e.target.className);
  
  // Handle nav links
  if (e.target.classList.contains('nav-link')) {
    e.preventDefault();
    console.log('Nav link clicked');
    
    // Update active state
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
    });
    e.target.classList.add('active');
    
    // Get route
    const href = e.target.getAttribute('href');
    if (href && href.startsWith('#')) {
      const route = href.replace('#', '');
      console.log('Navigating to:', route);
      showRoute(route);
    }
  }
  
  
  // Handle any link with href starting with #
  if (e.target.tagName === 'A' && e.target.getAttribute('href') && e.target.getAttribute('href').startsWith('#')) {
    console.log('Link with hash clicked:', e.target.getAttribute('href'));
    e.preventDefault();
    const route = e.target.getAttribute('href').replace('#', '');
    console.log('Going to route:', route);
    showRoute(route);
  }
});



// File upload and processing functions
async function uploadAndParse(endpoint, file) {
  const form = new FormData();
  form.append('file', file);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120000);
  let res;
  try {
    res = await fetch(endpoint, { method: 'POST', body: form, signal: controller.signal });
  } catch (e) {
    clearTimeout(timeout);
    if (e.name === 'AbortError') {
      throw new Error('Request timed out. Please try with a smaller file or check your connection.');
    }
    throw e;
  } finally {
    clearTimeout(timeout);
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

document.getElementById('btnProcess')?.addEventListener('click', async () => {
  const spec = document.getElementById('specFile').files[0];
  const edi = document.getElementById('ediFile').files[0];
  const error = document.getElementById('error');
  const loading = document.getElementById('loading');
  const btn = document.getElementById('btnProcess');
  error.textContent = '';
  loading.classList.add('hidden');
  
  if (!spec || !edi) {
    error.textContent = 'Please select both files.';
    return;
  }
  
  try {
    btn.disabled = true;
    btn.textContent = 'Processing...';
    loading.classList.remove('hidden');
    
    const [specXml, ediXml] = await Promise.all([
      uploadAndParse('/api/parse/spec', spec),
      uploadAndParse('/api/parse/edi', edi)
    ]);
    const compareRes = await fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        edi_xml: ediXml.xml,
        spec_xml: specXml.xml,
        edi_fields: ediXml.fields || [],
        spec_requirements: specXml.requirements || {},
        edi_field_values: ediXml.field_values || {},
        spec_status_map: specXml.status_map || {}
      })
    });
    if (!compareRes.ok) {
      const err = await compareRes.json().catch(() => ({ detail: 'Compare failed' }));
      throw new Error(err.detail || 'Compare failed');
    }
    const result = await compareRes.json();
    window.__lastSpecXml = specXml.xml;
    window.__lastEdiXml = ediXml.xml;
    renderSummary(result);
    showRoute('summary');
  } catch (e) {
    error.textContent = e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Process';
    loading.classList.add('hidden');
  }
});

// Download handlers
document.getElementById('btnDownloadJson')?.addEventListener('click', () => {
  const data = window.__comparison || {};
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'edi_summary.json';
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
});

document.getElementById('btnDownloadCSV')?.addEventListener('click', () => {
  const result = window.__comparison || {};
  const fields = Array.isArray(result.detailed_fields) ? result.detailed_fields : [];
  const header = ['Field Code', 'Field Name', 'Status', 'Cardinality', 'Type', 'Length', 'In EDI', 'Usage'];
  const rows = fields.map(f => [
    safeCsv(f.field_name),
    safeCsv(f.name),
    safeCsv(f.status),
    safeCsv(f.cardinality),
    safeCsv(f.type),
    safeCsv(f.length),
    safeCsv(f.present_in_edi ? 'Present' : 'Missing'),
    safeCsv(f.usage)
  ].join(','));
  const csv = [header.join(','), ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'edi_fields.csv';
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
});

function safeCsv(v) {
  const s = (v == null ? '' : String(v));
  const needsQuotes = /[",\n]/.test(s);
  const escaped = s.replaceAll('"', '""');
  return needsQuotes ? `"${escaped}"` : escaped;
}

function renderSummary(result) {
  const summary = document.getElementById('summaryContent');
  window.__comparison = result;
  
  const validationStatus = result.is_810 ? 
    '<div class="pill" style="background:#22c55e;color:white;">✓ Valid EDI 810</div>' :
    '<div class="pill" style="background:#ef4444;color:white;">✗ Invalid EDI 810</div>';

  const executive = result.executive_summary ? 
    `<div class="exec-summary"><pre>${result.executive_summary}</pre></div>` : '';

  const keyFieldsHtml = createKeyFieldsPanel(result.key_fields || {});
  const ediPresentTable = createEdiPresentStatus(result.edi_present_status || []);
  
  if (result.segment_summary && result.segment_summary.length > 0) {
    const totalSegments = result.segment_summary.length;
    const segmentCountDisplay = `<p style="margin:10px 0;color:var(--text-light);">Showing ${totalSegments} of ${totalSegments} segments</p>`;
    summary.innerHTML = `${validationStatus}${executive}${keyFieldsHtml}${ediPresentTable}${segmentCountDisplay}<h3 id="summaryTitle">Segment Summary</h3>${createSegmentTable(result.segment_summary)}`;
  } else {
    summary.innerHTML = `${validationStatus}${executive}${keyFieldsHtml}${ediPresentTable}<h3 id="summaryTitle">Field Details (Legacy)</h3>${createDetailedTable(result.detailed_fields)}`;
  }
  
  activateFilters();
  document.getElementById('specXML').textContent = (window.__lastSpecXml || '').trim();
  document.getElementById('ediXML').textContent = (window.__lastEdiXml || '').trim();
}

function createEdiPresentStatus(items) {
  if (!items || items.length === 0) { return '' }
  const rows = items.map(i => `<tr>
    <td style="width:140px;"><code>${i.field}</code></td>
    <td>${i.status_letter}</td>
    <td>${i.status_label}</td>
  </tr>`).join('');
  return `<div class="card"><h3>EDI-present Fields (Spec Status)</h3>
    <table class="table small"><thead><tr><th>Field</th><th>Letter</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>
  </div>`;
}

function createKeyFieldsPanel(key) {
  try {
    const segmentsOrder = [
      'GS', 'ST', 'BIG', 'REF', 'N1', 'N2', 'N3', 'N4', 'PER', 'ITD', 'DTM', 'FOB', 'CUR', 'IT1', 'PID'
    ];
    const labelMap = {
      GS: 'GS - Functional Group Header',
      ST: 'ST - Transaction Set Header',
      BIG: 'BIG - Invoice Information',
      REF: 'REF - Reference Identification',
      N1: 'N1 - Name',
      N2: 'N2 - Additional Name Information',
      N3: 'N3 - Address Information',
      N4: 'N4 - Geographic Location',
      PER: 'PER - Administrative Contact',
      ITD: 'ITD - Terms of Sale',
      DTM: 'DTM - Date/Time Reference',
      FOB: 'FOB - Freight On Board',
      CUR: 'CUR - Currency',
      IT1: 'IT1 - Line Item',
      PID: 'PID - Product/Item Description'
    };

    const hasAny = key && Object.keys(key).length > 0;
    if (!hasAny) { return '' }

    const sections = segmentsOrder
      .filter(seg => key[seg] && Object.keys(key[seg]).length > 0)
      .map(seg => {
        const rows = Object.entries(key[seg])
          .map(([k, v]) => `<tr><td style="width:140px;"><code>${k}</code></td><td>${escapeHtml(v)}</td></tr>`)
          .join('');
        return `<div class="card"><h3>${labelMap[seg] || seg}</h3><table class="table small"><tbody>${rows}</tbody></table></div>`;
      }).join('');

    return `<div class="key-fields">
      <h3>Key Fields</h3>
      <div class="card-grid">${sections}</div>
    </div>`;
  } catch (e) {
    console.warn('Failed to render key fields', e);
    return '';
  }
}

function escapeHtml(str) {
  return String(str)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

function createSegmentTable(segments) {
  if (!segments || segments.length === 0) { return '<p class="pill">No segments found</p>' }
  
  const rows = segments.map(segment => {
    let rowClass = '';
    if (segment.x12_requirement === 'mandatory') {
      rowClass = segment.present_in_edi === 'Yes' ? 'segment-mandatory-present' : 'segment-mandatory-missing';
    } else {
      rowClass = segment.present_in_edi === 'Yes' ? 'segment-optional-present' : 'segment-optional-missing';
    }
    
    const statusBadge = segment.status.includes('Present') 
      ? `<span style="color:#22c55e;font-weight:bold;">${segment.status}</span>`
      : `<span style="color:#ef4444;font-weight:bold;">${segment.status}</span>`;
    
    return `<tr class="${rowClass}">
      <td><strong>${segment.segment_tag}</strong></td>
      <td>${segment.x12_requirement}</td>
      <td>${segment.company_usage}</td>
      <td>${segment.min_usage}</td>
      <td>${segment.max_usage}</td>
      <td>${segment.present_in_edi}</td>
      <td>${statusBadge}</td>
    </tr>`;
  }).join('');
  
  return `<table class="table segment-table">
    <thead>
      <tr>
        <th>SEGMENT TAG</th>
        <th>X12 REQUIREMENT</th>
        <th>COMPANY USAGE</th>
        <th>MIN USAGE</th>
        <th>MAX USAGE</th>
        <th>PRESENT IN EDI</th>
        <th>STATUS</th>
      </tr>
    </thead>
    <tbody>
      ${rows}
    </tbody>
  </table>`;
}

function createDetailedTable(fields) {
  if (!fields || fields.length === 0) { return '<p class="pill">No fields found</p>' }
  
  const fieldsToShow = fields;
  
  const rows = fieldsToShow.map(field => {
    const statusBadge = `<span class="status-badge ${field.status.toLowerCase()}">${field.status}</span>`;
    
    const lengthErrorIndicator = field.length_error ? 
      `<br><span style="color:#dc2626;font-size:11px;">⚠ ${field.length_error}</span>` : '';
    
    const truncatedUsage = field.usage.length > 100 ? 
      field.usage.substring(0, 100) + '...' : field.usage;
    
    const presenceBadge = `<span class="presence-badge ${field.present_in_edi ? 'present' : 'missing'}">${field.present_in_edi ? 'Present' : 'Missing'}</span>`;
    return `<tr class="${field.color}">
      <td><strong>${field.field_name}</strong>${lengthErrorIndicator}</td>
      <td>${field.name}</td>
      <td>${statusBadge}</td>
      <td>${field.cardinality}</td>
      <td>${field.type}</td>
      <td>${field.length}</td>
      <td>${presenceBadge}</td>
      <td class="usage-text">${truncatedUsage}</td>
    </tr>`;
  }).join('');
  
  return `<table class="table">
    <thead>
      <tr>
        <th>Field Code</th>
        <th>Field Name</th>
        <th>Status</th>
        <th>Cardinality</th>
        <th>Type</th>
        <th>Length</th>
        <th>In EDI</th>
        <th>Usage</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function tableFrom(items, label) {
  if (!items || items.length === 0) { return '<p class="pill">None</p>' }
  const rows = items.map(i => `<tr><td>${i}</td><td>${label}</td></tr>`).join('');
  return `<table class="table"><thead><tr><th>Field</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>`
}

function activateFilters() {
  const result = window.__comparison || {};
  const allFields = result.detailed_fields || [];
  
  const buttons = [...document.querySelectorAll('.filter-btn')];
  const search = document.getElementById('searchField');
  const out = document.getElementById('summaryContent');
  const title = document.getElementById('summaryTitle');
  
  function filterFields(type, searchQuery) {
    let filtered = [...allFields];
    
    if (type !== 'all') {
      switch (type) {
        case 'mandatory':
          filtered = filtered.filter(f => f.status === 'Mandatory');
          break;
        case 'optional':
          filtered = filtered.filter(f => f.status === 'Optional');
          break;
        case 'present':
          filtered = filtered.filter(f => f.present_in_edi === true);
          break;
        case 'missing':
          filtered = filtered.filter(f => f.present_in_edi === false);
          break;
      }
    }
    
    if (searchQuery && searchQuery.length > 0) {
      const q = searchQuery.toUpperCase();
      filtered = filtered.filter(f => 
        f.field_name.includes(q) ||
        f.name.toUpperCase().includes(q)
      );
    }
    
    return filtered;
  }
  
  function render(type) {
    buttons.forEach(b => b.classList.toggle('active', b.dataset.type === type));
    const q = (search.value || '').trim();
    const filteredFields = filterFields(type, q);
    
    const titleMap = {
      'all': 'All Fields',
      'mandatory': 'Mandatory Fields',
      'optional': 'Optional Fields',
      'present': 'Fields Present in EDI',
      'missing': 'Fields Missing from EDI'
    };
    title.textContent = titleMap[type] || 'Fields';
    
    const validationStatus = result.is_810 ? 
      '<div class="pill" style="background:#22c55e;color:white;">✓ Valid EDI 810</div>' :
      '<div class="pill" style="background:#ef4444;color:white;">✗ Invalid EDI 810</div>';
    
    out.innerHTML = validationStatus + createDetailedTable(filteredFields);
  }
  
  buttons.forEach(b => b.onclick = () => render(b.dataset.type));
  
  let searchTimeout;
  search.oninput = () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      const active = (buttons.find(b => b.classList.contains('active'))?.dataset.type) || 'all';
      render(active);
    }, 300);
  };
  
  render('all');
}