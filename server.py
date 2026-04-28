import os
import io
import asyncio
import logging
from flask import Flask, request, send_file, render_template_string

import edge_tts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("TTS-Server")

app = Flask(__name__)

VOICE = "en-US-JennyNeural"
RATE = "+15%"
PITCH = "+2Hz"

_last_audio = None
_last_text = ""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dheeraj's Voice Assistant (TTS)</title>
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

::selection { background: rgba(139, 92, 246, 0.3); color: #fff; }

body {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; padding: 20px;
  overflow-x: hidden;
}

.bg-blobs {
  position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden;
}
.bg-blob {
  position: absolute; border-radius: 50%; filter: blur(128px);
  animation: blobPulse 6s ease-in-out infinite;
}
.bg-blob-1 {
  width: 24rem; height: 24rem; top: 0; left: 25%;
  background: rgba(139, 92, 246, 0.1);
}
.bg-blob-2 {
  width: 24rem; height: 24rem; bottom: 0; right: 25%;
  background: rgba(99, 102, 241, 0.1); animation-delay: 2s;
}
.bg-blob-3 {
  width: 16rem; height: 16rem; top: 25%; right: 33%;
  background: rgba(217, 70, 239, 0.08); animation-delay: 3.5s;
}

@keyframes blobPulse {
  0%, 100% { opacity: 0.6; transform: scale(1) translate(0, 0); }
  33%  { opacity: 1; transform: scale(1.15) translate(20px, -15px); }
  66%  { opacity: 0.5; transform: scale(0.9) translate(-10px, 10px); }
}

.wrapper { position: relative; z-index: 10; width: 100%; max-width: 640px; }

.card {
  background: rgba(255,255,255,0.04); backdrop-filter: blur(28px);
  border: 1px solid rgba(255,255,255,0.06); border-radius: 24px;
  padding: 44px 40px; width: 100%;
  box-shadow: 0 24px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
  animation: cardIn 0.6s ease-out;
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0)    scale(1); }
}

.header { text-align: center; margin-bottom: 28px; }
.header h1 {
  font-size: 26px; font-weight: 600; letter-spacing: -0.3px;
  background: linear-gradient(to right, rgba(255,255,255,0.9), rgba(255,255,255,0.4));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: 4px;
}
.header .divider {
  height: 1px; background: linear-gradient(to right, transparent, rgba(255,255,255,0.15), transparent);
  margin: 10px auto 0; width: 0; animation: dividerGrow 0.6s 0.3s ease-out forwards;
}
@keyframes dividerGrow { to { width: 60%; } }
.header p { color: rgba(255,255,255,0.35); font-size: 13px; margin-top: 8px; }

.voice-pill {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(139,92,246,0.1); border-radius: 20px;
  padding: 8px 18px; font-size: 13px; color: rgba(255,255,255,0.55);
  margin-bottom: 24px;
}
.voice-pill span { color: #c4b5fd; font-weight: 500; }

.textarea-wrap {
  position: relative; background: rgba(0,0,0,0.25);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 16px;
  transition: border-color 0.3s;
}
.textarea-wrap:focus-within { border-color: rgba(139,92,246,0.4); }

textarea {
  display: block; width: 100%; min-height: 160px; background: transparent;
  border: none; outline: none; resize: vertical; padding: 20px 22px;
  color: rgba(255,255,255,0.85); font-size: 15px; line-height: 1.7;
  font-family: inherit;
}
textarea::placeholder { color: rgba(255,255,255,0.18); }

.status-bar { display: flex; align-items: center; gap: 10px; margin-top: 8px; min-height: 28px; }

.typing-indicator { display: none; align-items: center; gap: 6px; }
.typing-indicator span { font-size: 12px; color: rgba(255,255,255,0.45); }
.typing-dots { display: flex; gap: 3px; }
.typing-dots i {
  width: 5px; height: 5px; border-radius: 50%; background: rgba(255,255,255,0.6);
  animation: dotBounce 1.2s ease-in-out infinite;
}
.typing-dots i:nth-child(1) { animation-delay: 0s; }
.typing-dots i:nth-child(2) { animation-delay: 0.15s; }
.typing-dots i:nth-child(3) { animation-delay: 0.3s; }

@keyframes dotBounce {
  0%, 100% { opacity: 0.3; transform: scale(0.85); }
  50%  { opacity: 0.9; transform: scale(1.15); }
}

.status-text { font-size: 12px; color: rgba(255,255,255,0.35); }

.controls { display: flex; gap: 10px; margin-top: 16px; }
.btn {
  padding: 12px 16px; border: none; border-radius: 12px;
  font-size: 14px; font-weight: 600; cursor: pointer;
  font-family: inherit; transition: all 0.2s ease;
}
.btn:active { transform: scale(0.97); }

.btn-play {
  flex: 2; background: linear-gradient(135deg, #7c3aed, #8b5cf6); color: #fff;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-play:hover:not(:disabled) { filter: brightness(1.15); transform: translateY(-1px); }
.btn-play:disabled { opacity: 0.4; cursor: not-allowed; transform: none; filter: none; }
.btn-play.speaking { background: linear-gradient(135deg, #ef4444, #f97316); }

.btn-stop { background: rgba(255,255,255,0.06); color: #fff; }
.btn-stop:hover { background: rgba(255,255,255,0.12); }

.btn-clear { background: transparent; color: rgba(255,255,255,0.4); border: 1px solid rgba(255,255,255,0.08); }
.btn-clear:hover { color: #fff; border-color: rgba(255,255,255,0.2); }

.btn-download {
  display: none; background: linear-gradient(135deg, #10b981, #059669); color: #fff;
}
.btn-download:hover { filter: brightness(1.15); transform: translateY(-1px); }

.spinner {
  display: none; width: 22px; height: 22px;
  border: 2.5px solid rgba(255,255,255,0.12);
  border-top: 2.5px solid #a78bfa; border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.fade-in { animation: fadeIn 0.35s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

/* mouse glow */
.glow { position: fixed; pointer-events: none; z-index: 0; opacity: 0;
  width: 40rem; height: 40rem; border-radius: 50%;
  background: radial-gradient(circle, rgba(139,92,246,0.04), transparent 70%);
  filter: blur(80px); transition: opacity 0.4s;
}
.glow.active { opacity: 1; }
</style>
</head>
<body>

<div class="bg-blobs">
  <div class="bg-blob bg-blob-1"></div>
  <div class="bg-blob bg-blob-2"></div>
  <div class="bg-blob bg-blob-3"></div>
</div>

<div class="glow" id="glow"></div>

<div class="wrapper">
  <div class="card">
    <div class="header">
      <h1>You type, I speak</h1>
      <div class="divider"></div>
      <p>Text to Speech &bull; Microsoft Neural Voice</p>
    </div>

    <div class="voice-pill">
      Voice: <span>Jenny (Neural)</span> &bull; Engine: <span>Edge TTS</span>
    </div>

    <div class="textarea-wrap">
      <textarea id="textInput" placeholder="Paste or type text here..."></textarea>
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
      <button class="btn btn-play" id="playBtn">▶ Play</button>
      <button class="btn btn-stop" id="stopBtn">■ Stop</button>
      <button class="btn btn-clear" id="clearBtn">Clear</button>
      <button class="btn btn-download" id="downloadBtn">⬇ MP3</button>
    </div>
  </div>
</div>

<script>
const textInput = document.getElementById('textInput');
const playBtn   = document.getElementById('playBtn');
const stopBtn   = document.getElementById('stopBtn');
const clearBtn  = document.getElementById('clearBtn');
const downloadBtn = document.getElementById('downloadBtn');
const status    = document.getElementById('status');
const spinner   = document.getElementById('spinner');
const typing    = document.getElementById('typingIndicator');
const glow      = document.getElementById('glow');

let audio = null;
let audioBlob = null;

document.addEventListener('mousemove', function(e) {
  glow.style.left = (e.clientX - 640) + 'px';
  glow.style.top  = (e.clientY - 640) + 'px';
});
textInput.addEventListener('focus', function() { glow.classList.add('active'); });
textInput.addEventListener('blur',  function() { glow.classList.remove('active'); });

async function speak() {
  var text = textInput.value.trim();
  if (!text) { status.textContent = 'Please enter some text first'; return; }

  stopAudio();
  playBtn.disabled = true;
  playBtn.textContent = '◌ Generating...';
  spinner.style.display = 'block';
  typing.style.display = 'flex';
  status.textContent = '';

  try {
    var resp = await fetch('/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
    if (!resp.ok) throw new Error('Server error');

    audioBlob = await resp.blob();
    var url = URL.createObjectURL(audioBlob);
    audio = new Audio(url);

    playBtn.textContent = '● Speaking...';
    playBtn.classList.add('speaking');
    spinner.style.display = 'none';
    typing.style.display = 'none';
    playBtn.disabled = false;
    downloadBtn.style.display = 'inline-block';

    audio.play();
    audio.onended = function() {
      playBtn.textContent = '▶ Play';
      playBtn.classList.remove('speaking');
      status.textContent = 'Finished';
      URL.revokeObjectURL(url);
      audio = null;
    };
    audio.onerror = function() {
      playBtn.textContent = '▶ Play';
      playBtn.classList.remove('speaking');
      status.textContent = 'Playback error';
      audio = null;
    };
  } catch (err) {
    playBtn.disabled = false;
    playBtn.textContent = '▶ Play';
    spinner.style.display = 'none';
    typing.style.display = 'none';
    status.textContent = 'Failed to generate speech';
    console.error(err);
  }
}

function stopAudio() {
  if (audio) { audio.pause(); audio.currentTime = 0; audio = null; }
  playBtn.textContent = '▶ Play';
  playBtn.classList.remove('speaking');
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
  stopAudio(); status.textContent = '';
  downloadBtn.style.display = 'none'; audioBlob = null;
});
clearBtn.addEventListener('click', function() {
  textInput.value = ''; status.textContent = '';
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


def _generate_tts(text):
    async def _run():
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
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

    logger.info(f"Generating speech: '{text[:80]}...' ({len(text)} chars)")

    try:
        mp3_data = _generate_tts(text)
        logger.info(f"Generated {mp3_data.getbuffer().nbytes} bytes of audio")

        _last_audio = io.BytesIO(mp3_data.getvalue())
        _last_text = text

        return send_file(mp3_data, mimetype="audio/mpeg")

    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        return {"error": str(e)}, 500


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
