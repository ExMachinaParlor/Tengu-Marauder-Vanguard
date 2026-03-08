/* TMV Operator Console — vanilla JS, no dependencies */
'use strict';

// ── Drive control ────────────────────────────────────────────────────────────
// Keyboard: W/↑ forward  S/↓ backward  A/← left  D/→ right  Space stop
// Keys are ignored when focus is inside a text input or select element.

const _KEY_MAP = {
  w: 'forward',  ArrowUp:    'forward',
  s: 'backward', ArrowDown:  'backward',
  a: 'left',     ArrowLeft:  'left',
  d: 'right',    ArrowRight: 'right',
};

let _activeKey = null;

document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
  if (e.repeat) return;

  if (e.key === ' ') {
    e.preventDefault();
    stopMotors();
    return;
  }

  const direction = _KEY_MAP[e.key];
  if (direction && direction !== _activeKey) {
    _activeKey = direction;
    move(direction);
    _highlightDpad(direction, true);
  }
});

document.addEventListener('keyup', e => {
  const direction = _KEY_MAP[e.key];
  if (direction && direction === _activeKey) {
    _activeKey = null;
    stopMotors();
    _highlightDpad(direction, false);
  }
});

function _highlightDpad(direction, active) {
  // Find the button whose onclick contains this direction and toggle active style
  document.querySelectorAll('button[onclick^="move"]').forEach(btn => {
    if (btn.getAttribute('onclick').includes(`'${direction}'`)) {
      btn.style.borderColor = active ? 'var(--accent)' : '';
      btn.style.color = active ? 'var(--accent)' : '';
    }
  });
}

function move(direction) {
  fetch('/api/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ direction }),
  })
    .then(r => r.json())
    .then(data => setDriveStatus(data.ok ? `► ${direction.toUpperCase()}` : `[!] ${data.error}`))
    .catch(e => setDriveStatus(`[!] ${e.message}`));
}

function stopMotors() {
  fetch('/api/stop', { method: 'POST' })
    .then(r => r.json())
    .then(() => setDriveStatus('■ STOPPED'))
    .catch(e => setDriveStatus(`[!] ${e.message}`));
}

function setDriveStatus(msg) {
  const el = document.getElementById('drive-status');
  if (el) el.textContent = msg;
}

// ── Camera status ─────────────────────────────────────────────────────────────

function checkCamera() {
  fetch('/api/camera/status')
    .then(r => r.json())
    .then(data => {
      const img     = document.getElementById('cam-img');
      const offline = document.getElementById('cam-offline');
      const tag     = document.getElementById('cam-tag');
      if (!img || !offline) return;

      if (data.available) {
        if (!img.src || img.src === window.location.href) img.src = '/video_feed';
        img.style.display = '';
        offline.style.display = 'none';
        if (tag) tag.style.display = 'none';
      } else {
        img.src = '';
        img.style.display = 'none';
        offline.style.display = 'flex';
        if (tag) tag.style.display = '';
      }
    })
    .catch(() => {});
}

// ── System status polling ────────────────────────────────────────────────────

function updateStatus() {
  fetch('/api/status')
    .then(r => r.json())
    .then(s => {
      setText('s-cpu',    `${s.cpu_percent}%`);
      setText('s-ram',    `${s.ram_used_mb}/${s.ram_total_mb} MB`);
      setText('s-disk',   `${s.disk_used_gb}/${s.disk_total_gb} GB`);
      setText('s-uptime', s.uptime);
      setText('s-gps',    s.gps || '—');
      setStatusValue('s-motors',   s.motors);
      setStatusValue('s-marauder', s.marauder);

      const bar = document.getElementById('status-bar');
      if (bar) {
        bar.textContent =
          `CPU ${s.cpu_percent}%  |  RAM ${s.ram_used_mb}/${s.ram_total_mb} MB  |  UP ${s.uptime}  |  GPS ${s.gps}`;
      }
    })
    .catch(() => {});
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function setStatusValue(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = value.toUpperCase();
  const online = value === 'online' || value === 'connected';
  el.className = 'value ' + (online ? 'val-online' : 'val-offline');
}

// ── Marauder console ─────────────────────────────────────────────────────────

function loadMarauderPorts() {
  fetch('/api/marauder/ports')
    .then(r => r.json())
    .then(data => {
      if (!data.ok) return;
      const sel = document.getElementById('marauder-port');
      if (!sel) return;
      sel.innerHTML = data.ports.length
        ? ''
        : '<option value="">no device</option>';
      data.ports.forEach(port => {
        const opt = document.createElement('option');
        opt.value = port;
        opt.textContent = port;
        if (port === data.active) opt.selected = true;
        sel.appendChild(opt);
      });
      const ps = document.getElementById('port-status');
      if (ps) ps.textContent = data.active && data.ports.includes(data.active)
        ? 'connected'
        : data.ports.length ? 'select port' : 'no device';
    })
    .catch(() => {});
}

function switchMarauderPort() {
  const sel = document.getElementById('marauder-port');
  const port = sel ? sel.value : '';
  if (!port) return;
  const ps = document.getElementById('port-status');
  if (ps) ps.textContent = 'connecting...';
  fetch('/api/marauder/port', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ port }),
  })
    .then(r => r.json())
    .then(data => {
      if (ps) ps.textContent = data.ok ? 'connected' : `failed: ${data.error || ''}`;
    })
    .catch(e => { if (ps) ps.textContent = `error: ${e.message}`; });
}

function sendMarauder() {
  const select = document.getElementById('marauder-cmd');
  const cmd = select ? select.value : '';
  if (!cmd) return;

  fetch('/api/marauder', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command: cmd }),
  })
    .then(r => r.json())
    .then(data => {
      const el = document.getElementById('cmd-result');
      if (el) el.textContent = data.ok ? `► Sent: ${data.command}` : `[!] ${data.error}`;
    })
    .catch(e => {
      const el = document.getElementById('cmd-result');
      if (el) el.textContent = `[!] ${e.message}`;
    });
}

function updateMarauderLogs() {
  fetch('/api/marauder/logs')
    .then(r => r.json())
    .then(data => {
      if (!data.ok || !data.logs.length) return;
      const el = document.getElementById('marauder-log');
      if (!el) return;
      el.textContent = data.logs.join('\n');
      el.scrollTop = el.scrollHeight;
    })
    .catch(() => {});
}

// ── Recon — wireless interfaces ──────────────────────────────────────────────

function loadInterfaces() {
  fetch('/api/wireless/interfaces')
    .then(r => r.json())
    .then(data => {
      if (!data.ok) return;
      const tbody = document.getElementById('iface-body');
      if (!tbody) return;
      if (!data.interfaces.length) {
        tbody.innerHTML = '<tr><td colspan="5" style="color:var(--dim)">no interfaces</td></tr>';
        return;
      }
      tbody.innerHTML = data.interfaces.map(i =>
        `<tr>
          <td>${i.interface || '—'}</td>
          <td>${i.type || '—'}</td>
          <td>${i.ssid || '—'}</td>
          <td>${i.channel || '—'}</td>
          <td>${i.addr || '—'}</td>
        </tr>`
      ).join('');
    })
    .catch(() => {});
}

// ── Recon — async scan engine ─────────────────────────────────────────────────

const _scanPollers = {};

function startScan(type) {
  const statusEl = document.getElementById(`${type}-status`);
  if (statusEl) {
    statusEl.textContent = 'starting...';
    statusEl.className = 'scan-status scanning';
  }

  const body = {};
  if (type === 'network') {
    const sel = document.getElementById('net-iface-select');
    if (sel && sel.value) body.interface = sel.value;
  }
  if (type === 'bluetooth') {
    const sel = document.getElementById('bt-adapter-select');
    if (sel && sel.value) body.adapter = sel.value;
  }

  fetch(`/api/scan/${type}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
    .then(r => r.json())
    .then(data => {
      if (!data.ok) {
        setScanStatus(type, 'error', data.error);
        return;
      }
      if (_scanPollers[type]) clearInterval(_scanPollers[type]);
      _scanPollers[type] = setInterval(() => pollScan(type), 2000);
    })
    .catch(e => setScanStatus(type, 'error', e.message));
}

function pollScan(type) {
  fetch(`/api/scan/${type}`)
    .then(r => r.json())
    .then(data => {
      if (!data.ok) return;
      setScanStatus(type, data.status, data.error);
      if (data.status === 'done' || data.status === 'error') {
        clearInterval(_scanPollers[type]);
        delete _scanPollers[type];
        if (data.status === 'done') renderScanResults(type, data.data);
      }
    })
    .catch(() => {});
}

function setScanStatus(type, status, error) {
  const el = document.getElementById(`${type}-status`);
  if (!el) return;
  const labels = { idle: 'idle', scanning: 'scanning...', done: 'done', error: `error: ${error}` };
  el.textContent = labels[status] || status;
  el.className = `scan-status ${status}`;
}

function renderScanResults(type, data) {
  if (type === 'network') {
    const tbody = document.getElementById('network-body');
    if (!tbody) return;
    if (!data.length) {
      tbody.innerHTML = '<tr><td colspan="3" style="color:var(--dim)">no hosts found</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(h =>
      `<tr><td>${h.ip}</td><td>${h.mac || '—'}</td><td>${h.vendor || '—'}</td></tr>`
    ).join('');
  }

  if (type === 'bluetooth') {
    const tbody = document.getElementById('bluetooth-body');
    if (!tbody) return;
    if (!data.length) {
      tbody.innerHTML = '<tr><td colspan="2" style="color:var(--dim)">no devices found</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(d =>
      `<tr><td>${d.mac}</td><td>${d.name || '—'}</td></tr>`
    ).join('');
  }

  if (type === 'rf') {
    const el = document.getElementById('rf-results');
    if (!el) return;
    el.textContent = data.length
      ? data.map(s => JSON.stringify(s, null, 2)).join('\n---\n')
      : 'no signals decoded';
  }
}

// ── Recon — interface / adapter dropdowns ─────────────────────────────────────

function loadNetworkInterfaceOptions() {
  fetch('/api/interfaces/network')
    .then(r => r.json())
    .then(data => {
      if (!data.ok) return;
      const sel = document.getElementById('net-iface-select');
      if (!sel) return;
      const current = sel.value;
      sel.innerHTML = '<option value="">auto</option>';
      data.interfaces.forEach(iface => {
        const opt = document.createElement('option');
        opt.value = iface;
        opt.textContent = iface;
        if (iface === current) opt.selected = true;
        sel.appendChild(opt);
      });
    })
    .catch(() => {});
}

function loadBtAdapterOptions() {
  fetch('/api/bluetooth/adapters')
    .then(r => r.json())
    .then(data => {
      if (!data.ok) return;
      const sel = document.getElementById('bt-adapter-select');
      if (!sel) return;
      const current = sel.value;
      sel.innerHTML = data.adapters.length
        ? ''
        : '<option value="">none detected</option>';
      data.adapters.forEach(adapter => {
        const opt = document.createElement('option');
        opt.value = adapter;
        opt.textContent = adapter;
        if (adapter === current || (!current && adapter === 'hci0')) opt.selected = true;
        sel.appendChild(opt);
      });
    })
    .catch(() => {});
}

// ── Bootstrap ────────────────────────────────────────────────────────────────

updateStatus();
checkCamera();
loadInterfaces();
loadNetworkInterfaceOptions();
loadBtAdapterOptions();
loadMarauderPorts();
setInterval(updateStatus,              3000);
setInterval(checkCamera,               5000);
setInterval(loadInterfaces,            10000);
setInterval(updateMarauderLogs,        2000);
setInterval(loadNetworkInterfaceOptions, 15000);
setInterval(loadBtAdapterOptions,        15000);
setInterval(loadMarauderPorts,           10000);
