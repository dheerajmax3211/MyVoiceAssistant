import os
import io
import asyncio
import logging
from flask import Flask, request, send_file, render_template_string

import edge_tts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("TTS-Server")

app = Flask(__name__)

VOICES = {
    "Jenny (US - Female)":       "en-US-JennyNeural",
    "Guy (US - Male)":           "en-US-GuyNeural",
    "Aria (US - Female)":        "en-US-AriaNeural",
    "Davis (US - Male)":         "en-US-DavisNeural",
    "Jane (US - Female)":        "en-US-JaneNeural",
    "Jason (US - Male)":         "en-US-JasonNeural",
    "Sara (US - Female)":        "en-US-SaraNeural",
    "Tony (US - Male)":          "en-US-TonyNeural",
    "Amber (US - Female)":       "en-US-AmberNeural",
    "Brandon (US - Male)":       "en-US-BrandonNeural",
    "Cora (US - Female)":        "en-US-CoraNeural",
    "Christopher (US - Male)":   "en-US-ChristopherNeural",
    "Sonia (UK - Female)":       "en-GB-SoniaNeural",
    "Ryan (UK - Male)":          "en-GB-RyanNeural",
    "Libby (UK - Female)":       "en-GB-LibbyNeural",
    "Thomas (UK - Male)":        "en-GB-ThomasNeural",
    "Neerja (India - Female)":   "en-IN-NeerjaNeural",
    "Prabhat (India - Male)":    "en-IN-PrabhatNeural",
}

VOICE = "en-US-JennyNeural"
RATE = "+0%"
PITCH = "+0Hz"

_last_audio = None
_last_text = ""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dheeraj's Voice Assistant (TTS)</title>
<link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500&family=Pacifico&family=Yellowtail&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
::selection { background: rgba(0, 240, 255, 0.25); color: #fff; }

:root {
  --cyan:    #00f0ff;
  --magenta: #ff00ff;
  --lime:    #39ff14;
  --pink:    #ff1493;
  --purple:  #b300ff;
  --orange:  #ff6600;
  --yellow:  #ffe600;
}

body {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: #030303;
  font-family: 'Space Grotesk', 'Segoe UI', system-ui, sans-serif;
  padding: 20px; overflow-x: hidden;
  color: #e0e0e0;
}

/* ===== neon bg canvas ===== */
#neonCanvas { position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: 0.7; }

/* ===== scanline overlay ===== */
.scanlines {
  position: fixed; inset: 0; z-index: 1; pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.03) 2px,
    rgba(0,0,0,0.03) 4px
  );
}

.wrapper { position: relative; z-index: 10; width: 100%; max-width: 680px; }

.card {
  position: relative; background: rgba(10,10,15,0.85);
  backdrop-filter: blur(24px); border-radius: 20px; padding: 40px 36px;
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow:
    0 0 40px rgba(0,240,255,0.06),
    0 0 80px rgba(255,0,255,0.04),
    0 24px 80px rgba(0,0,0,0.6);
  animation: cardIn 0.6s ease-out;
  overflow: hidden;
}
.card::before {
  content: ''; position: absolute; top: -1px; left: 20%; right: 20%; height: 1px;
  background: linear-gradient(90deg, transparent, var(--cyan), var(--magenta), transparent);
  animation: borderGlow 3s ease-in-out infinite;
}
@keyframes borderGlow {
  0%, 100% { opacity: 0.4; }
  50%  { opacity: 1; }
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(24px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

.header { text-align: center; margin-bottom: 24px; }
.header h1 {
  font-family: 'Dancing Script', 'Yellowtail', 'Pacifico', cursive;
  font-size: 48px; font-weight: 700; line-height: 1.2; margin-bottom: 16px;
  color: #ff1493;
  filter: drop-shadow(0 0 14px rgba(255,20,147,0.25)) drop-shadow(0 2px 4px rgba(0,0,0,0.6));
  text-shadow: 0 0 10px rgba(255,20,147,0.3);
  letter-spacing: 1px;
}
.header .divider {
  height: 1px; margin: 10px auto 0; width: 0;
  background: linear-gradient(90deg, transparent, var(--cyan), var(--magenta), transparent);
  animation: dividerGrow 0.7s 0.3s ease-out forwards;
}
@keyframes dividerGrow { to { width: 65%; } }
.header p { color: rgba(255,255,255,0.3); font-size: 13px; margin-top: 8px; letter-spacing: 0.5px; }

.settings-row {
  display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap;
}
.settings-row > * { flex: 1; min-width: 160px; }

.select-group { position: relative; }
.select-label {
  display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px;
  color: rgba(255,255,255,0.3); margin-bottom: 6px; font-weight: 600;
}
.neon-select {
  width: 100%; appearance: none; -webkit-appearance: none;
  padding: 10px 36px 10px 14px;
  background: rgba(0,0,0,0.5);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 10px;
  color: #d0d0d0; font-size: 13px; font-family: inherit;
  cursor: pointer; outline: none; transition: all 0.25s;
}
.neon-select:hover, .neon-select:focus {
  border-color: var(--cyan);
  box-shadow: 0 0 12px rgba(0,240,255,0.15);
}
.select-group::after {
  content: '\25BC'; position: absolute; right: 14px; bottom: 12px;
  font-size: 10px; color: rgba(255,255,255,0.35); pointer-events: none;
}

.rate-display {
  font-size: 12px; color: var(--cyan); font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  min-width: 50px; text-align: right;
}
input[type="range"] {
  -webkit-appearance: none; appearance: none; width: 100%; height: 6px;
  background: rgba(255,255,255,0.06); border-radius: 3px; outline: none; cursor: pointer;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%;
  background: var(--cyan);
  box-shadow: 0 0 12px rgba(0,240,255,0.5);
  cursor: pointer; border: 2px solid #000;
}
input[type="range"]::-moz-range-thumb {
  width: 18px; height: 18px; border-radius: 50%;
  background: var(--cyan); box-shadow: 0 0 12px rgba(0,240,255,0.5);
  cursor: pointer; border: 2px solid #000;
}

.textarea-wrap {
  position: relative; background: rgba(0,0,0,0.4);
  border: 1px solid rgba(255,255,255,0.06); border-radius: 14px;
  transition: all 0.3s;
}
.textarea-wrap:focus-within {
  border-color: var(--magenta);
  box-shadow: 0 0 20px rgba(255,0,255,0.15), inset 0 0 20px rgba(255,0,255,0.03);
}
.textarea-wrap.char-glow {
  border-color: var(--cyan);
  box-shadow: 0 0 20px rgba(0,240,255,0.15), inset 0 0 20px rgba(0,240,255,0.03);
}

textarea {
  display: block; width: 100%; min-height: 150px; background: transparent;
  border: none; outline: none; resize: vertical; padding: 18px 20px;
  color: rgba(255,255,255,0.85); font-size: 15px; line-height: 1.7;
  font-family: inherit;
}
textarea::placeholder { color: rgba(255,255,255,0.14); }

.char-count {
  position: absolute; bottom: 8px; right: 16px;
  font-size: 11px; color: rgba(255,255,255,0.2);
  font-family: 'JetBrains Mono', monospace;
}

.status-bar { display: flex; align-items: center; gap: 10px; margin-top: 10px; min-height: 30px; }
.typing-indicator { display: none; align-items: center; gap: 8px; }
.typing-indicator span { font-size: 12px; color: rgba(255,255,255,0.4); }
.typing-dots { display: flex; gap: 4px; }
.typing-dots i {
  width: 6px; height: 6px; border-radius: 50%;
  animation: dotBounce 1.2s ease-in-out infinite;
}
.typing-dots i:nth-child(1) { background: var(--cyan);   animation-delay: 0s; }
.typing-dots i:nth-child(2) { background: var(--magenta); animation-delay: 0.15s; }
.typing-dots i:nth-child(3) { background: var(--lime);    animation-delay: 0.3s; }

@keyframes dotBounce {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50%  { opacity: 1; transform: scale(1.2); }
}

.spinner {
  display: none; width: 20px; height: 20px;
  border: 2px solid rgba(255,255,255,0.08);
  border-top: 2px solid var(--cyan); border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.status-text { font-size: 12px; color: rgba(255,255,255,0.3); }

.controls { display: flex; gap: 10px; margin-top: 14px; }
.btn {
  padding: 12px 16px; border: none; border-radius: 10px;
  font-size: 14px; font-weight: 600; cursor: pointer;
  font-family: inherit; transition: all 0.2s ease; position: relative;
}
.btn:active { transform: scale(0.97); }

.btn-play {
  flex: 2; background: transparent; color: #fff;
  border: 1px solid var(--cyan);
  box-shadow: 0 0 16px rgba(0,240,255,0.3);
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-play:hover:not(:disabled) {
  background: rgba(0,240,255,0.1);
  box-shadow: 0 0 24px rgba(0,240,255,0.5);
  transform: translateY(-1px);
}
.btn-play:disabled { opacity: 0.3; cursor: not-allowed; transform: none; box-shadow: none; }
.btn-play.speaking {
  border-color: var(--magenta);
  box-shadow: 0 0 20px rgba(255,0,255,0.4);
}

.btn-stop { background: rgba(255,255,255,0.04); color: #fff; border: 1px solid rgba(255,255,255,0.08); }
.btn-stop:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.2); }

.btn-clear { background: transparent; color: rgba(255,255,255,0.3); border: 1px solid rgba(255,255,255,0.06); }
.btn-clear:hover { color: #fff; border-color: rgba(255,255,255,0.2); }

.btn-download {
  display: none; background: transparent; color: #fff;
  border: 1px solid var(--lime);
  box-shadow: 0 0 12px rgba(57,255,20,0.25);
}
.btn-download:hover { background: rgba(57,255,20,0.1); box-shadow: 0 0 20px rgba(57,255,20,0.45); transform: translateY(-1px); }

.pulse-ring { animation: pulseRing 2s ease-out infinite; }
@keyframes pulseRing {
  0%   { box-shadow: 0 0 8px rgba(0,240,255,0.2); }
  50%  { box-shadow: 0 0 24px rgba(0,240,255,0.5); }
  100% { box-shadow: 0 0 8px rgba(0,240,255,0.2); }
}
</style>
</head>
<body>

<canvas id="neonCanvas"></canvas>
<div class="scanlines"></div>

<div class="wrapper">
  <div class="card">
    <div class="header">
      <h1>You Type, I Speak</h1>
      <div class="divider"></div>
      <p>paste text &bull; pick a voice &bull; hit play</p>
    </div>

    <div class="settings-row">
      <div class="select-group">
        <label class="select-label">Voice</label>
        <select class="neon-select" id="voiceSelect">
          <option value="Jenny (US - Female)">Jenny (US - Female)</option>
          <option value="Guy (US - Male)">Guy (US - Male)</option>
          <option value="Aria (US - Female)">Aria (US - Female)</option>
          <option value="Davis (US - Male)">Davis (US - Male)</option>
          <option value="Jane (US - Female)">Jane (US - Female)</option>
          <option value="Jason (US - Male)">Jason (US - Male)</option>
          <option value="Sara (US - Female)">Sara (US - Female)</option>
          <option value="Tony (US - Male)">Tony (US - Male)</option>
          <option value="Amber (US - Female)">Amber (US - Female)</option>
          <option value="Brandon (US - Male)">Brandon (US - Male)</option>
          <option value="Cora (US - Female)">Cora (US - Female)</option>
          <option value="Christopher (US - Male)">Christopher (US - Male)</option>
          <option value="Sonia (UK - Female)">Sonia (UK - Female)</option>
          <option value="Ryan (UK - Male)">Ryan (UK - Male)</option>
          <option value="Libby (UK - Female)">Libby (UK - Female)</option>
          <option value="Thomas (UK - Male)">Thomas (UK - Male)</option>
          <option value="Neerja (India - Female)">Neerja (India - Female)</option>
          <option value="Prabhat (India - Male)">Prabhat (India - Male)</option>
        </select>
      </div>

      <div>
        <label class="select-label">Speed &mdash; <span class="rate-display" id="rateDisplay">Normal</span></label>
        <input type="range" id="rateSlider" min="-50" max="50" value="0" step="5">
      </div>
    </div>

    <div class="textarea-wrap" id="textareaWrap">
      <textarea id="textInput" placeholder="Paste or type text here..."></textarea>
      <div class="char-count" id="charCount">0 chars</div>
    </div>

    <div class="status-bar">
      <div class="typing-indicator" id="typingIndicator">
        <div class="typing-dots"><i></i><i></i><i></i></div>
        <span>Generating speech...</span>
      </div>
      <div class="spinner" id="spinner"></div>
      <div class="status-text" id="status"></div>
    </div>

    <div class="controls">
      <button class="btn btn-play pulse-ring" id="playBtn">&#9654; Play</button>
      <button class="btn btn-stop" id="stopBtn">&#9632; Stop</button>
      <button class="btn btn-clear" id="clearBtn">Clear</button>
      <button class="btn btn-download" id="downloadBtn">&#10515; MP3</button>
    </div>
  </div>
</div>

<script>
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
var canvas      = document.getElementById('neonCanvas');
var ctx         = canvas.getContext('2d');

var audio = null;
var audioBlob = null;

/* --- NEON CANVAS BACKGROUND --- */
function resizeCanvas() {
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

var lines = [];
for (var i = 0; i < 40; i++) {
  lines.push({
    x: Math.random() * 2000,
    y: Math.random() * 2000,
    vx: (Math.random() - 0.5) * 0.6,
    vy: (Math.random() - 0.5) * 0.6,
    len: 60 + Math.random() * 140,
    hue: Math.random() < 0.33 ? 190 : Math.random() < 0.5 ? 300 : 120,
    alpha: 0.04 + Math.random() * 0.08,
    angle: Math.random() * Math.PI * 2,
    spin: (Math.random() - 0.5) * 0.004
  });
}

var particles = [];
for (var p = 0; p < 50; p++) {
  particles.push({
    x: Math.random() * 2000,
    y: Math.random() * 2000,
    vx: (Math.random() - 0.5) * 0.3,
    vy: (Math.random() - 0.5) * 0.3,
    r: 1 + Math.random() * 2.5,
    hue: Math.random() < 0.25 ? 190 : Math.random() < 0.5 ? 300 : Math.random() < 0.75 ? 120 : 30,
    alpha: 0.15 + Math.random() * 0.35
  });
}

function drawNeon() {
  var w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  /* neon lines */
  for (var i = 0; i < lines.length; i++) {
    var l = lines[i];
    l.x += l.vx; l.y += l.vy; l.angle += l.spin;
    if (l.x < -200) l.x = w + 200; if (l.x > w + 200) l.x = -200;
    if (l.y < -200) l.y = h + 200; if (l.y > h + 200) l.y = -200;

    var dx = Math.cos(l.angle) * l.len;
    var dy = Math.sin(l.angle) * l.len;
    ctx.beginPath();
    ctx.moveTo(l.x, l.y);
    ctx.lineTo(l.x + dx, l.y + dy);
    ctx.strokeStyle = 'hsla(' + l.hue + ', 100%, 65%, ' + l.alpha + ')';
    ctx.lineWidth = 0.6;
    ctx.stroke();

    /* glow */
    ctx.beginPath();
    ctx.moveTo(l.x, l.y);
    ctx.lineTo(l.x + dx, l.y + dy);
    ctx.strokeStyle = 'hsla(' + l.hue + ', 100%, 65%, ' + (l.alpha * 0.3) + ')';
    ctx.lineWidth = 3;
    ctx.stroke();
  }

  /* particles */
  for (var j = 0; j < particles.length; j++) {
    var pt = particles[j];
    pt.x += pt.vx; pt.y += pt.vy;
    if (pt.x < -50) pt.x = w + 50; if (pt.x > w + 50) pt.x = -50;
    if (pt.y < -50) pt.y = h + 50; if (pt.y > h + 50) pt.y = -50;

    ctx.beginPath();
    ctx.arc(pt.x, pt.y, pt.r, 0, Math.PI * 2);
    ctx.fillStyle = 'hsla(' + pt.hue + ', 100%, 70%, ' + pt.alpha + ')';
    ctx.fill();

    ctx.beginPath();
    ctx.arc(pt.x, pt.y, pt.r * 3, 0, Math.PI * 2);
    ctx.fillStyle = 'hsla(' + pt.hue + ', 100%, 70%, ' + (pt.alpha * 0.12) + ')';
    ctx.fill();
  }
  requestAnimationFrame(drawNeon);
}
drawNeon();

/* --- SETTINGS --- */
var rateLabels = {
  '-50': 'Very Slow', '-25': 'Slow', '0': 'Normal',
  '25': 'Fast', '50': 'Very Fast'
};
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
  if (len > 50) { wrap.classList.add('char-glow'); }
  else { wrap.classList.remove('char-glow'); }
});

/* --- TTS --- */
async function speak() {
  var text = textInput.value.trim();
  if (!text) { statusEl.textContent = 'Please enter some text first'; return; }

  stopAudio();
  playBtn.disabled = true;
  playBtn.classList.remove('pulse-ring');
  playBtn.innerHTML = '&#9678; Generating...';
  spinner.style.display = 'block';
  typing.style.display = 'flex';
  statusEl.textContent = '';

  var voiceName = voiceSelect.value;
  var rateNum = parseInt(rateSlider.value);
  var rateVal = (rateNum >= 0 ? '+' : '') + rateNum + '%';

  try {
    var resp = await fetch('/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text, voice: voiceName, rate: rateVal })
    });
    if (!resp.ok) throw new Error('Server error');

    audioBlob = await resp.blob();
    var url = URL.createObjectURL(audioBlob);
    audio = new Audio(url);

    playBtn.innerHTML = '&#9679; Speaking...';
    playBtn.classList.add('speaking');
    spinner.style.display = 'none';
    typing.style.display = 'none';
    playBtn.disabled = false;
    downloadBtn.style.display = 'inline-block';

    audio.play();
    audio.onended = function() {
      playBtn.innerHTML = '&#9654; Play';
      playBtn.classList.remove('speaking');
      playBtn.classList.add('pulse-ring');
      statusEl.textContent = 'Finished';
      URL.revokeObjectURL(url);
      audio = null;
    };
    audio.onerror = function() {
      playBtn.innerHTML = '&#9654; Play';
      playBtn.classList.remove('speaking');
      playBtn.classList.add('pulse-ring');
      statusEl.textContent = 'Playback error';
      audio = null;
    };
  } catch (err) {
    playBtn.disabled = false;
    playBtn.innerHTML = '&#9654; Play';
    playBtn.classList.add('pulse-ring');
    spinner.style.display = 'none';
    typing.style.display = 'none';
    statusEl.textContent = 'Failed to generate speech';
    console.error(err);
  }
}

function stopAudio() {
  if (audio) { audio.pause(); audio.currentTime = 0; audio = null; }
  playBtn.innerHTML = '&#9654; Play';
  playBtn.classList.remove('speaking');
  playBtn.classList.add('pulse-ring');
}

function downloadMp3() {
  if (!audioBlob) return;
  var url = URL.createObjectURL(audioBlob);
  var a = document.createElement('a');
  var filename = (textInput.value.trim().slice(0, 40).replace(/\s+/g, '_') || 'speech') + '.mp3';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(function() { URL.revokeObjectURL(url); }, 100);
}

playBtn.addEventListener('click', speak);
downloadBtn.addEventListener('click', downloadMp3);
stopBtn.addEventListener('click', function() {
  stopAudio(); statusEl.textContent = '';
  downloadBtn.style.display = 'none'; audioBlob = null;
});
clearBtn.addEventListener('click', function() {
  textInput.value = ''; statusEl.textContent = ''; charCount.textContent = '0 chars';
  wrap.classList.remove('char-glow');
  downloadBtn.style.display = 'none'; audioBlob = null; textInput.focus();
});

document.addEventListener('keydown', function(e) {
  if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); speak(); }
});
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


def _generate_tts(text, voice=None, rate=None):
    async def _run():
        v = voice or VOICE
        r = rate or RATE
        communicate = edge_tts.Communicate(text, v, rate=r, pitch=PITCH)
        mp3_data = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_data.write(chunk["data"])
        mp3_data.seek(0)
        return mp3_data
    return asyncio.run(_run())


@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json()
    if not data or "text" not in data:
        return {"error": "No text provided"}, 400

    text = data["text"].strip()
    if not text:
        return {"error": "Empty text"}, 400

    voice = data.get("voice")
    rate = data.get("rate")

    voice_short = VOICES.get(voice, voice or VOICE)

    logger.info(f"Generating speech: '{text[:80]}...' ({len(text)} chars) voice={voice_short} rate={rate}")

    try:
        mp3_data = _generate_tts(text, voice=voice_short, rate=rate)
        logger.info(f"Generated {mp3_data.getbuffer().nbytes} bytes of audio")

        _last_audio = io.BytesIO(mp3_data.getvalue())
        _last_text = text

        return send_file(mp3_data, mimetype="audio/mpeg")

    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        return {"error": str(e)}, 500


@app.route("/voices")
def list_voices():
    return {"voices": list(VOICES.keys())}


@app.route("/download")
def download():
    if _last_audio is None:
        return {"error": "No audio generated yet"}, 404

    _last_audio.seek(0)
    download_name = (_last_text[:40].strip().replace(" ", "_") or "speech") + ".mp3"
    return send_file(
        _last_audio,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=download_name,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5070))
    logger.info(f"Starting TTS server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
