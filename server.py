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

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dheeraj's Voice Assistant (TTS)</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; padding: 20px;
}
.card {
  background: rgba(255,255,255,0.06); backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1); border-radius: 24px;
  padding: 48px 40px; width: 100%; max-width: 620px;
  box-shadow: 0 24px 80px rgba(0,0,0,0.4);
}
h1 { font-size: 26px; font-weight: 600; color: #fff; margin-bottom: 6px; text-align: center; letter-spacing: -0.3px; }
.subtitle { color: rgba(255,255,255,0.5); font-size: 13px; text-align: center; margin-bottom: 36px; }
textarea {
  width: 100%; height: 220px; background: rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.12); border-radius: 14px;
  padding: 18px 20px; color: #e0e0e0; font-size: 15px; line-height: 1.6;
  resize: vertical; font-family: inherit; outline: none;
  transition: border-color 0.25s; min-height: 120px;
}
textarea::placeholder { color: rgba(255,255,255,0.25); }
textarea:focus { border-color: rgba(99,102,241,0.6); }
.controls { display: flex; gap: 12px; margin-top: 20px; }
.btn {
  flex: 1; padding: 14px 20px; border: none; border-radius: 12px;
  font-size: 15px; font-weight: 600; cursor: pointer; letter-spacing: 0.2px;
  transition: all 0.2s ease; font-family: inherit;
}
.btn-play { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; flex: 2; }
.btn-play:hover { filter: brightness(1.15); transform: translateY(-1px); }
.btn-play:active { transform: translateY(0); }
.btn-play:disabled { opacity: 0.45; cursor: not-allowed; transform: none; filter: none; }
.btn-play.speaking { background: linear-gradient(135deg, #ef4444, #f97316); }
.btn-stop { background: rgba(255,255,255,0.08); color: #fff; }
.btn-stop:hover { background: rgba(255,255,255,0.14); }
.btn-clear { background: transparent; color: rgba(255,255,255,0.5); border: 1px solid rgba(255,255,255,0.12); }
.btn-clear:hover { color: #fff; border-color: rgba(255,255,255,0.25); }
.status { margin-top: 16px; font-size: 12px; color: rgba(255,255,255,0.4); text-align: center; min-height: 18px; }
.voice-info {
  margin-bottom: 20px; padding: 10px 14px; background: rgba(99,102,241,0.12);
  border-radius: 10px; color: rgba(255,255,255,0.6); font-size: 13px; text-align: center;
}
.voice-info span { color: #a5b4fc; font-weight: 500; }
.loading-spinner {
  display: none; width: 30px; height: 30px; border: 3px solid rgba(255,255,255,0.15);
  border-top: 3px solid #8b5cf6; border-radius: 50%; animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="card">
  <h1>Dheeraj's Voice Assistant</h1>
  <p class="subtitle">Text to Speech &bull; Microsoft Neural Voice</p>

  <div class="voice-info">
    Voice: <span>Jenny (Neural)</span> &bull; Engine: <span>Edge TTS</span>
  </div>

  <div class="loading-spinner" id="spinner"></div>

  <textarea id="textInput" placeholder="Paste or type text here..."></textarea>

  <div class="controls">
    <button class="btn btn-play" id="playBtn">▶ Play</button>
    <button class="btn btn-stop" id="stopBtn">■ Stop</button>
    <button class="btn btn-clear" id="clearBtn">Clear</button>
  </div>

  <p class="status" id="status"></p>
</div>

<script>
const textInput = document.getElementById('textInput');
const playBtn = document.getElementById('playBtn');
const stopBtn = document.getElementById('stopBtn');
const clearBtn = document.getElementById('clearBtn');
const status = document.getElementById('status');
const spinner = document.getElementById('spinner');

let audio = null;

async function speak() {
  const text = textInput.value.trim();
  if (!text) { status.textContent = 'Please enter some text first'; return; }

  stopAudio();
  playBtn.disabled = true;
  playBtn.textContent = '◌ Generating...';
  spinner.style.display = 'block';
  status.textContent = '';

  try {
    const resp = await fetch('/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    if (!resp.ok) throw new Error('Server error');

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    audio = new Audio(url);

    playBtn.textContent = '● Speaking...';
    playBtn.classList.add('speaking');
    spinner.style.display = 'none';
    playBtn.disabled = false;

    audio.play();

    audio.onended = () => {
      playBtn.textContent = '▶ Play';
      playBtn.classList.remove('speaking');
      status.textContent = 'Finished';
      URL.revokeObjectURL(url);
      audio = null;
    };

    audio.onerror = () => {
      playBtn.textContent = '▶ Play';
      playBtn.classList.remove('speaking');
      status.textContent = 'Playback error';
      audio = null;
    };

  } catch (err) {
    playBtn.disabled = false;
    playBtn.textContent = '▶ Play';
    spinner.style.display = 'none';
    status.textContent = 'Failed to generate speech';
    console.error(err);
  }
}

function stopAudio() {
  if (audio) { audio.pause(); audio.currentTime = 0; audio = null; }
  playBtn.textContent = '▶ Play';
  playBtn.classList.remove('speaking');
}

playBtn.addEventListener('click', speak);
stopBtn.addEventListener('click', () => { stopAudio(); status.textContent = ''; });
clearBtn.addEventListener('click', () => { textInput.value = ''; status.textContent = ''; textInput.focus(); });

document.addEventListener('keydown', (e) => {
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
        return send_file(mp3_data, mimetype="audio/mpeg")

    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        return {"error": str(e)}, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    logger.info(f"Starting TTS server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
