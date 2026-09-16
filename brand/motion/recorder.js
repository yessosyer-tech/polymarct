/* POLYMARCT / in-page recorder
   Captures a film to a real video file straight from the canvas, with the
   synthesised score on the audio track. No screen recorder, no capture card,
   no drift: the frames come from the same canvas the film draws to.

   REC.attach({ canvas, duration, name, audioNode, onDone })
     ?record=1   start recording on load and save when the film ends
     ?fps=60     frame rate, default 60
     ?mbps=16    video bitrate, default 16

   Where the local dev server is running the file is POSTed to /_save and lands
   in tools/out. Anywhere else it falls back to a normal browser download. */

const REC = (() => {
  function pickMime(){
    const want = [
      "video/webm;codecs=vp9,opus",
      "video/webm;codecs=vp8,opus",
      "video/webm"
    ];
    for (const m of want) if (window.MediaRecorder && MediaRecorder.isTypeSupported(m)) return m;
    return "";
  }

  function badge(text, tone){
    let el = document.getElementById("recbadge");
    if (!el){
      el = document.createElement("div");
      el.id = "recbadge";
      el.style.cssText = "position:fixed;left:16px;top:16px;z-index:300;font-family:'JetBrains Mono',ui-monospace,monospace;" +
        "font-size:12px;letter-spacing:3px;padding:9px 13px;border:1px solid currentColor;background:rgba(8,9,10,.85)";
      document.body.appendChild(el);
    }
    el.style.color = tone === "rec" ? "#FF4D2E" : tone === "ok" ? "#CCFF00" : "#8A8F94";
    el.textContent = text;
    return el;
  }

  async function save(blob, name){
    const mb = (blob.size/1e6).toFixed(1);
    try {
      const r = await fetch("/_save/" + name, { method:"POST", body: blob, headers:{ "Content-Type":"application/octet-stream" } });
      if (r.ok){
        const j = await r.json();
        badge("SAVED " + j.file + " // " + mb + " MB", "ok");
        window.__recDone = { file: j.file, bytes: j.bytes };
        return;
      }
    } catch (e) { /* not the dev server, fall through to a download */ }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    badge("DOWNLOADED " + name + " // " + mb + " MB", "ok");
    window.__recDone = { file: name, bytes: blob.size };
  }

  function attach(opts){
    const q = new URLSearchParams(location.search);
    const fps = +(q.get("fps") || 60);
    const mbps = +(q.get("mbps") || 16);
    const auto = q.get("record") === "1";

    const state = { recording:false, chunks:[], mr:null };

    function start(){
      if (state.recording) return;
      const mime = pickMime();
      if (!mime){ badge("NO MEDIARECORDER", "dim"); return; }

      const stream = opts.canvas.captureStream(fps);
      /* the score rides along on its own track when the film has one */
      if (opts.audioNode && opts.audioContext){
        const dest = opts.audioContext.createMediaStreamDestination();
        opts.audioNode.connect(dest);
        dest.stream.getAudioTracks().forEach(t => stream.addTrack(t));
      }

      state.chunks = [];
      state.mr = new MediaRecorder(stream, {
        mimeType: mime,
        videoBitsPerSecond: mbps * 1e6,
        audioBitsPerSecond: 192000
      });
      state.mr.ondataavailable = e => { if (e.data && e.data.size) state.chunks.push(e.data); };
      state.mr.onstop = async () => {
        state.recording = false;
        const blob = new Blob(state.chunks, { type: "video/webm" });
        badge("WRITING " + (blob.size/1e6).toFixed(1) + " MB", "dim");
        await save(blob, opts.name + ".webm");
        if (opts.onDone) opts.onDone();
      };
      state.mr.start(250);
      state.recording = true;
      window.__recDone = null;
      badge("REC", "rec");
    }

    function stop(){ if (state.recording && state.mr) state.mr.stop(); }

    addEventListener("keydown", e => {
      if (e.key === "c" || e.key === "C"){ state.recording ? stop() : start(); }
    });

    window.REC_START = start;
    window.REC_STOP = stop;
    window.__recAuto = auto;
    return { start, stop, auto };
  }

  return { attach, badge };
})();
