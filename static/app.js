/* ═══════════════════════════════════════════════
   Dheeraj's Voice Assistant — Main JS
   ═══════════════════════════════════════════════ */

// ── DOM References ──────────────────────────────
var textInput   = document.getElementById('textInput');
var playBtn     = document.getElementById('playBtn');
var stopBtn     = document.getElementById('stopBtn');
var clearBtn    = document.getElementById('clearBtn');
var downloadBtn = document.getElementById('downloadBtn');
var statusEl    = document.getElementById('status');
var spinner     = document.getElementById('spinner');
var typing      = document.getElementById('typingIndicator');
var voiceSelect = document.getElementById('voiceSelect');
var rateSlider  = document.getElementById('rateSlider');
var rateDisplay = document.getElementById('rateDisplay');
var charCount   = document.getElementById('charCount');
var wrap        = document.getElementById('textareaWrap');
var bgCanvas    = document.getElementById('neonCanvas');
var bgCtx       = bgCanvas.getContext('2d');
var waveCanvas  = document.getElementById('waveCanvas');
var waveCtx     = waveCanvas.getContext('2d');
var vizWrap     = document.getElementById('visualizerWrap');

// Document panel
var docViewer    = document.getElementById('docViewer');
var docStatus    = document.getElementById('docStatus');
var addImageBtn  = document.getElementById('addImageBtn');
var openDocBtn   = document.getElementById('openDocBtn');
var newDocBtn    = document.getElementById('newDocBtn');
var saveDocBtn   = document.getElementById('saveDocBtn');
var imageInput   = document.getElementById('imageInput');
var docFileInput = document.getElementById('docFileInput');
var ocrLoading   = document.getElementById('ocrLoading');
var ocrLoadingText = document.getElementById('ocrLoadingText');

// Source toggle
var srcTextBtn = document.getElementById('srcTextBtn');
var srcDocBtn  = document.getElementById('srcDocBtn');

// Audio controls
var pauseBtn    = document.getElementById('pauseBtn');
var skipBackBtn = document.getElementById('skipBackBtn');
var skipFwdBtn  = document.getElementById('skipFwdBtn');
var progressTrack = document.getElementById('progressTrack');
var progressFill  = document.getElementById('progressFill');
var timeDisplay   = document.getElementById('timeDisplay');

// Modal
var modalOverlay = document.getElementById('modalOverlay');
var modalSaveBtn = document.getElementById('modalSaveBtn');
var modalDiscardBtn = document.getElementById('modalDiscardBtn');
var modalCancelBtn  = document.getElementById('modalCancelBtn');

// ── State ───────────────────────────────────────
var audio = null;
var audioBlob = null;
var audioCtx = null;
var analyser = null;
var vizAnimId = null;
var ttsSource = 'text'; // 'text' or 'doc'
var docElements = [];
var docDirty = false;
var isPaused = false;
var progressInterval = null;

// Chunked playback state
var chunks = [];
var currentChunkIdx = 0;
var chunkAudioBlobs = [];
var isChunkedMode = false;
var totalChunkedDuration = 0;
var chunkStartTimes = [];

// ═══════════════════════════════════════════════
// NEON CANVAS BACKGROUND
// ═══════════════════════════════════════════════
function resizeCanvas() { bgCanvas.width = window.innerWidth; bgCanvas.height = window.innerHeight; }
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

var lines = [];
for (var i = 0; i < 40; i++) {
  lines.push({
    x: Math.random() * 2000, y: Math.random() * 2000,
    vx: (Math.random() - 0.5) * 0.6, vy: (Math.random() - 0.5) * 0.6,
    len: 60 + Math.random() * 140,
    hue: Math.random() < 0.33 ? 190 : Math.random() < 0.5 ? 300 : 120,
    alpha: 0.04 + Math.random() * 0.08,
    angle: Math.random() * Math.PI * 2, spin: (Math.random() - 0.5) * 0.004
  });
}
var particles = [];
for (var p = 0; p < 50; p++) {
  particles.push({
    x: Math.random() * 2000, y: Math.random() * 2000,
    vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3,
    r: 1 + Math.random() * 2.5,
    hue: Math.random() < 0.25 ? 190 : Math.random() < 0.5 ? 300 : Math.random() < 0.75 ? 120 : 30,
    alpha: 0.15 + Math.random() * 0.35
  });
}
function drawNeon() {
  var w = bgCanvas.width, h = bgCanvas.height;
  bgCtx.clearRect(0, 0, w, h);
  for (var i = 0; i < lines.length; i++) {
    var l = lines[i];
    l.x += l.vx; l.y += l.vy; l.angle += l.spin;
    if (l.x < -200) l.x = w + 200; if (l.x > w + 200) l.x = -200;
    if (l.y < -200) l.y = h + 200; if (l.y > h + 200) l.y = -200;
    var dx = Math.cos(l.angle) * l.len, dy = Math.sin(l.angle) * l.len;
    bgCtx.beginPath(); bgCtx.moveTo(l.x, l.y); bgCtx.lineTo(l.x + dx, l.y + dy);
    bgCtx.strokeStyle = 'hsla(' + l.hue + ', 100%, 65%, ' + l.alpha + ')';
    bgCtx.lineWidth = 0.6; bgCtx.stroke();
    bgCtx.beginPath(); bgCtx.moveTo(l.x, l.y); bgCtx.lineTo(l.x + dx, l.y + dy);
    bgCtx.strokeStyle = 'hsla(' + l.hue + ', 100%, 65%, ' + (l.alpha * 0.3) + ')';
    bgCtx.lineWidth = 3; bgCtx.stroke();
  }
  for (var j = 0; j < particles.length; j++) {
    var pt = particles[j];
    pt.x += pt.vx; pt.y += pt.vy;
    if (pt.x < -50) pt.x = w + 50; if (pt.x > w + 50) pt.x = -50;
    if (pt.y < -50) pt.y = h + 50; if (pt.y > h + 50) pt.y = -50;
    bgCtx.beginPath(); bgCtx.arc(pt.x, pt.y, pt.r, 0, Math.PI * 2);
    bgCtx.fillStyle = 'hsla(' + pt.hue + ', 100%, 70%, ' + pt.alpha + ')';
    bgCtx.fill();
    bgCtx.beginPath(); bgCtx.arc(pt.x, pt.y, pt.r * 3, 0, Math.PI * 2);
    bgCtx.fillStyle = 'hsla(' + pt.hue + ', 100%, 70%, ' + (pt.alpha * 0.12) + ')';
    bgCtx.fill();
  }
  requestAnimationFrame(drawNeon);
}
drawNeon();

// ═══════════════════════════════════════════════
// WAVEFORM VISUALIZER
// ═══════════════════════════════════════════════
function resizeWaveCanvas() {
  var rect = vizWrap.getBoundingClientRect();
  var dpr = window.devicePixelRatio || 1;
  waveCanvas.width = rect.width * dpr; waveCanvas.height = rect.height * dpr;
  waveCtx.scale(dpr, dpr);
  waveCanvas.style.width = rect.width + 'px'; waveCanvas.style.height = rect.height + 'px';
}
function initVisualizer() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === 'suspended') audioCtx.resume();
  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 256; analyser.smoothingTimeConstant = 0.85;
  var source = audioCtx.createMediaElementSource(audio);
  source.connect(analyser); analyser.connect(audioCtx.destination);
  vizWrap.classList.add('active'); resizeWaveCanvas();
  var bufLen = analyser.frequencyBinCount, dataArr = new Uint8Array(bufLen);
  function draw() {
    vizAnimId = requestAnimationFrame(draw);
    analyser.getByteTimeDomainData(dataArr);
    var w = waveCanvas.width / (window.devicePixelRatio || 1);
    var h = waveCanvas.height / (window.devicePixelRatio || 1);
    waveCtx.clearRect(0, 0, w, h);
    waveCtx.lineWidth = 2; waveCtx.beginPath();
    var sw = w / bufLen, x = 0;
    for (var i = 0; i < bufLen; i++) {
      var v = dataArr[i] / 128.0, y = (v * h) / 2;
      if (i === 0) waveCtx.moveTo(x, y); else waveCtx.lineTo(x, y);
      x += sw;
    }
    waveCtx.lineTo(w, h / 2);
    var grad = waveCtx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, '#ff1493'); grad.addColorStop(0.5, '#ff00ff'); grad.addColorStop(1, '#00f0ff');
    waveCtx.strokeStyle = grad; waveCtx.shadowColor = '#ff1493'; waveCtx.shadowBlur = 8; waveCtx.stroke();
    waveCtx.strokeStyle = '#ff1493'; waveCtx.shadowBlur = 18; waveCtx.lineWidth = 0.8; waveCtx.stroke();
    waveCtx.shadowBlur = 0;
  }
  draw();
}
function stopVisualizer() {
  if (vizAnimId) { cancelAnimationFrame(vizAnimId); vizAnimId = null; }
  vizWrap.classList.remove('active');
  if (analyser) { try { analyser.disconnect(); } catch(e){} analyser = null; }
}
window.addEventListener('resize', function() { if (vizWrap.classList.contains('active')) resizeWaveCanvas(); });

// ═══════════════════════════════════════════════
// SETTINGS
// ═══════════════════════════════════════════════
var rateLabels = { '-50': 'Very Slow', '-25': 'Slow', '0': 'Normal', '25': 'Fast', '50': 'Very Fast' };
function updateRateDisplay() {
  var v = parseInt(rateSlider.value);
  rateDisplay.textContent = rateLabels[String(v)] || (v > 0 ? '+' + v + '%' : v + '%');
  if (v === 0) rateDisplay.style.color = 'var(--cyan)';
  else if (v > 0) rateDisplay.style.color = 'var(--lime)';
  else rateDisplay.style.color = 'var(--orange)';
}
rateSlider.addEventListener('input', updateRateDisplay);
updateRateDisplay();

textInput.addEventListener('input', function() {
  var len = textInput.value.length;
  charCount.textContent = len + ' char' + (len !== 1 ? 's' : '');
  if (len > 50) wrap.classList.add('char-glow'); else wrap.classList.remove('char-glow');
});

// ═══════════════════════════════════════════════
// TTS ENGINE
// ═══════════════════════════════════════════════
function formatTime(sec) {
  if (isNaN(sec) || !isFinite(sec)) return '0:00';
  var m = Math.floor(sec / 60), s = Math.floor(sec % 60);
  return m + ':' + (s < 10 ? '0' : '') + s;
}

function startProgressTracking() {
  clearInterval(progressInterval);
  progressInterval = setInterval(function() {
    if (audio && audio.duration) {
      var pct = (audio.currentTime / audio.duration) * 100;
      progressFill.style.width = pct + '%';
      timeDisplay.textContent = formatTime(audio.currentTime) + ' / ' + formatTime(audio.duration);
    }
  }, 200);
}

function stopProgressTracking() {
  clearInterval(progressInterval);
  progressFill.style.width = '0%';
  timeDisplay.textContent = '0:00 / 0:00';
}

function getTextForTTS() {
  if (ttsSource === 'doc') {
    return docElements.map(function(el) { return el.text; }).join('\n\n');
  }
  return textInput.value.trim();
}

async function speak() {
  var text = getTextForTTS();
  if (!text) {
    statusEl.textContent = ttsSource === 'doc' ? 'Document is empty' : 'Please enter some text first';
    return;
  }
  stopAudio();
  playBtn.disabled = true;
  playBtn.classList.remove('pulse-ring');
  playBtn.innerHTML = '&#9678; Generating...';
  spinner.style.display = 'block';
  typing.style.display = 'flex';
  statusEl.textContent = '';
  isPaused = false;
  pauseBtn.textContent = '⏸ Pause';
  pauseBtn.classList.remove('active-control');

  var voiceName = voiceSelect.value;
  var rateNum = parseInt(rateSlider.value);
  var rateVal = (rateNum >= 0 ? '+' : '') + rateNum + '%';

  // Chunk long text (>3000 chars)
  if (text.length > 3000) {
    chunks = chunkText(text, 3000);
    currentChunkIdx = 0;
    isChunkedMode = true;
    chunkAudioBlobs = [];
    await playChunk(voiceName, rateVal);
  } else {
    isChunkedMode = false;
    chunks = [];
    try {
      var resp = await fetch('/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, voice: voiceName, rate: rateVal })
      });
      if (!resp.ok) throw new Error('Server error');
      audioBlob = await resp.blob();
      startPlayback(audioBlob);
    } catch (err) {
      resetPlayBtn();
      statusEl.textContent = 'Failed to generate speech';
      console.error(err);
    }
  }
}

function chunkText(text, maxLen) {
  var result = [];
  var paras = text.split(/\n\n+/);
  var current = '';
  for (var i = 0; i < paras.length; i++) {
    if ((current + '\n\n' + paras[i]).length > maxLen && current) {
      result.push(current.trim());
      current = paras[i];
    } else {
      current += (current ? '\n\n' : '') + paras[i];
    }
  }
  if (current.trim()) result.push(current.trim());
  // If any chunk is still > maxLen, split by sentences
  var final = [];
  for (var j = 0; j < result.length; j++) {
    if (result[j].length > maxLen) {
      var sentences = result[j].match(/[^.!?]+[.!?]+/g) || [result[j]];
      var sub = '';
      for (var k = 0; k < sentences.length; k++) {
        if ((sub + sentences[k]).length > maxLen && sub) {
          final.push(sub.trim());
          sub = sentences[k];
        } else {
          sub += sentences[k];
        }
      }
      if (sub.trim()) final.push(sub.trim());
    } else {
      final.push(result[j]);
    }
  }
  return final;
}

async function playChunk(voiceName, rateVal) {
  if (currentChunkIdx >= chunks.length) {
    resetPlayBtn();
    statusEl.textContent = 'Finished reading document';
    stopVisualizer();
    stopProgressTracking();
    return;
  }
  statusEl.textContent = 'Chunk ' + (currentChunkIdx + 1) + '/' + chunks.length;
  try {
    var resp = await fetch('/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: chunks[currentChunkIdx], voice: voiceName, rate: rateVal })
    });
    if (!resp.ok) throw new Error('Server error');
    var blob = await resp.blob();
    chunkAudioBlobs[currentChunkIdx] = blob;
    startPlayback(blob, function() {
      currentChunkIdx++;
      playChunk(voiceName, rateVal);
    });
  } catch (err) {
    resetPlayBtn();
    statusEl.textContent = 'Failed at chunk ' + (currentChunkIdx + 1);
    console.error(err);
  }
}

function startPlayback(blob, onEndCallback) {
  var url = URL.createObjectURL(blob);
  audio = new Audio(url);
  playBtn.innerHTML = '&#9679; Speaking...';
  playBtn.classList.add('speaking');
  spinner.style.display = 'none';
  typing.style.display = 'none';
  playBtn.disabled = false;
  downloadBtn.style.display = 'inline-flex';

  audio.play();
  initVisualizer();
  startProgressTracking();

  audio.onended = function() {
    stopVisualizer();
    stopProgressTracking();
    URL.revokeObjectURL(url);
    if (onEndCallback) {
      onEndCallback();
    } else {
      resetPlayBtn();
      statusEl.textContent = 'Finished';
      audio = null;
    }
  };
  audio.onerror = function() {
    resetPlayBtn();
    statusEl.textContent = 'Playback error';
    stopVisualizer();
    stopProgressTracking();
    audio = null;
  };
}

function resetPlayBtn() {
  playBtn.disabled = false;
  playBtn.innerHTML = '&#9654; Play';
  playBtn.classList.remove('speaking');
  playBtn.classList.add('pulse-ring');
  spinner.style.display = 'none';
  typing.style.display = 'none';
  isPaused = false;
  pauseBtn.textContent = '⏸ Pause';
  pauseBtn.classList.remove('active-control');
}

function stopAudio() {
  if (audio) { audio.pause(); audio.currentTime = 0; audio = null; }
  stopVisualizer();
  stopProgressTracking();
  resetPlayBtn();
  isChunkedMode = false;
  chunks = [];
  currentChunkIdx = 0;
}

function togglePause() {
  if (!audio) return;
  if (isPaused) {
    audio.play();
    isPaused = false;
    pauseBtn.textContent = '⏸ Pause';
    pauseBtn.classList.remove('active-control');
    playBtn.innerHTML = '&#9679; Speaking...';
    playBtn.classList.add('speaking');
  } else {
    audio.pause();
    isPaused = true;
    pauseBtn.textContent = '▶ Resume';
    pauseBtn.classList.add('active-control');
    playBtn.innerHTML = '⏸ Paused';
    playBtn.classList.remove('speaking');
  }
}

function skipForward() {
  if (audio && audio.duration) {
    audio.currentTime = Math.min(audio.currentTime + 10, audio.duration - 0.1);
  }
}
function skipBackward() {
  if (audio) {
    audio.currentTime = Math.max(audio.currentTime - 10, 0);
  }
}

function downloadMp3() {
  if (!audioBlob) return;
  var url = URL.createObjectURL(audioBlob);
  var a = document.createElement('a');
  var filename = (getTextForTTS().slice(0, 40).replace(/\s+/g, '_') || 'speech') + '.mp3';
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(function() { URL.revokeObjectURL(url); }, 100);
}

// Progress bar click-to-seek
progressTrack.addEventListener('click', function(e) {
  if (!audio || !audio.duration) return;
  var rect = progressTrack.getBoundingClientRect();
  var pct = (e.clientX - rect.left) / rect.width;
  audio.currentTime = pct * audio.duration;
});

// ═══════════════════════════════════════════════
// SOURCE TOGGLE
// ═══════════════════════════════════════════════
srcTextBtn.addEventListener('click', function() {
  ttsSource = 'text';
  srcTextBtn.classList.add('active');
  srcDocBtn.classList.remove('active');
});
srcDocBtn.addEventListener('click', function() {
  ttsSource = 'doc';
  srcDocBtn.classList.add('active');
  srcTextBtn.classList.remove('active');
});

// ═══════════════════════════════════════════════
// DOCUMENT MANAGEMENT
// ═══════════════════════════════════════════════
function renderDoc() {
  if (docElements.length === 0) {
    docViewer.innerHTML = '<div class="doc-empty"><div class="icon">📄</div><p>No document open<br>Add images or open a .docx file</p></div>';
    docStatus.textContent = 'No document';
    return;
  }
  var html = '';
  for (var i = 0; i < docElements.length; i++) {
    var el = docElements[i];
    if (el.type === 'heading') {
      var cls = 'doc-heading doc-h' + (el.level || 1);
      html += '<div class="' + cls + '">' + escapeHtml(el.text) + '</div>';
    } else {
      html += '<div class="doc-paragraph">' + escapeHtml(el.text) + '</div>';
    }
  }
  docViewer.innerHTML = html;
  docStatus.textContent = docElements.length + ' element' + (docElements.length !== 1 ? 's' : '');
  docDirty = true;
}

function escapeHtml(str) {
  var div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ── Add Image(s) ────────────────────────────
addImageBtn.addEventListener('click', function() { imageInput.click(); });
imageInput.addEventListener('change', async function() {
  var files = imageInput.files;
  if (!files || files.length === 0) return;
  if (files.length > 10) {
    alert('Maximum 10 images allowed at once.');
    imageInput.value = '';
    return;
  }
  // Validate sizes
  for (var i = 0; i < files.length; i++) {
    if (files[i].size > 10 * 1024 * 1024) {
      alert('Image "' + files[i].name + '" exceeds 10 MB limit.');
      imageInput.value = '';
      return;
    }
  }

  ocrLoading.classList.add('show');
  ocrLoadingText.textContent = 'Processing ' + files.length + ' image' + (files.length > 1 ? 's' : '') + '...';

  var formData = new FormData();
  for (var j = 0; j < files.length; j++) {
    formData.append('images', files[j]);
  }

  try {
    var resp = await fetch('/ocr', { method: 'POST', body: formData });
    var data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'OCR failed');

    if (data.elements && data.elements.length > 0) {
      // Append to server
      await fetch('/doc/append', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ elements: data.elements })
      });
      docElements = docElements.concat(data.elements);
      renderDoc();
      docViewer.scrollTop = docViewer.scrollHeight;
      statusEl.textContent = 'Extracted ' + data.elements.length + ' elements';
    } else {
      statusEl.textContent = 'No text found in image(s)';
    }
  } catch (err) {
    alert('OCR Error: ' + err.message);
    console.error(err);
  } finally {
    ocrLoading.classList.remove('show');
    imageInput.value = '';
  }
});

// ── Open Document ───────────────────────────
openDocBtn.addEventListener('click', function() {
  if (docDirty && docElements.length > 0) {
    showModal(function() {
      // After save/discard, open file picker
      docFileInput.click();
    });
  } else {
    docFileInput.click();
  }
});
docFileInput.addEventListener('change', async function() {
  var file = docFileInput.files[0];
  if (!file) return;

  ocrLoading.classList.add('show');
  ocrLoadingText.textContent = 'Opening document...';

  var formData = new FormData();
  formData.append('file', file);

  try {
    var resp = await fetch('/doc/open', { method: 'POST', body: formData });
    var data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Failed to open');
    docElements = data.elements || [];
    renderDoc();
    statusEl.textContent = 'Opened: ' + file.name;
    docDirty = false;
  } catch (err) {
    alert('Error opening document: ' + err.message);
  } finally {
    ocrLoading.classList.remove('show');
    docFileInput.value = '';
  }
});

// ── New Document ────────────────────────────
newDocBtn.addEventListener('click', function() {
  if (docDirty && docElements.length > 0) {
    showModal(function() {
      clearDocument();
    });
  } else {
    clearDocument();
  }
});

async function clearDocument() {
  await fetch('/doc/new', { method: 'POST' });
  docElements = [];
  docDirty = false;
  renderDoc();
  statusEl.textContent = 'New document created';
}

// ── Save Document ───────────────────────────
saveDocBtn.addEventListener('click', saveDocument);
async function saveDocument() {
  if (docElements.length === 0) {
    alert('Document is empty, nothing to save.');
    return;
  }
  try {
    var resp = await fetch('/doc/save');
    if (!resp.ok) throw new Error('Save failed');
    var blob = await resp.blob();
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = 'document.docx';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function() { URL.revokeObjectURL(url); }, 100);
    docDirty = false;
    statusEl.textContent = 'Document saved';
  } catch (err) {
    alert('Error saving document: ' + err.message);
  }
}

// ── Modal ───────────────────────────────────
var modalCallback = null;
function showModal(callback) {
  modalCallback = callback;
  modalOverlay.classList.add('show');
}
modalSaveBtn.addEventListener('click', async function() {
  modalOverlay.classList.remove('show');
  await saveDocument();
  if (modalCallback) modalCallback();
  modalCallback = null;
});
modalDiscardBtn.addEventListener('click', function() {
  modalOverlay.classList.remove('show');
  docDirty = false;
  if (modalCallback) modalCallback();
  modalCallback = null;
});
modalCancelBtn.addEventListener('click', function() {
  modalOverlay.classList.remove('show');
  modalCallback = null;
});

// ═══════════════════════════════════════════════
// EVENT LISTENERS
// ═══════════════════════════════════════════════
playBtn.addEventListener('click', speak);
downloadBtn.addEventListener('click', downloadMp3);
pauseBtn.addEventListener('click', togglePause);
skipBackBtn.addEventListener('click', skipBackward);
skipFwdBtn.addEventListener('click', skipForward);

stopBtn.addEventListener('click', function() {
  stopAudio(); statusEl.textContent = '';
  downloadBtn.style.display = 'none'; audioBlob = null;
});

clearBtn.addEventListener('click', function() {
  textInput.value = ''; statusEl.textContent = ''; charCount.textContent = '0 chars';
  stopAudio(); wrap.classList.remove('char-glow');
  downloadBtn.style.display = 'none'; audioBlob = null; textInput.focus();
});

document.addEventListener('keydown', function(e) {
  if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); speak(); }
  if (e.key === ' ' && e.target === document.body) { e.preventDefault(); togglePause(); }
});

// Init doc display
renderDoc();
