/* POLYMARCT / offline film renderer
   Realtime screen capture drops frames the moment anything else on the machine
   wants the GPU. This renders instead: seek to an exact time, read the canvas,
   POST the frame, repeat. The score is rendered separately through an
   OfflineAudioContext, so it is sample exact and the silences stay silent.
   ffmpeg muxes the two into the final file.

   Needs window.FILM = { canvas, duration, name, seek(t), renderAudio() }
   and the dev server from tools/serve.py to write into tools/out.

     await RENDER.run({ fps: 60, quality: .95 })          full film
     await RENDER.run({ fps: 30, from: 0, to: 5 })        a slice, for checking */

const RENDER = (() => {

  /* the badge lives in recorder.js, which not every film loads */
  function badge(text, tone){
    try { if (typeof REC !== "undefined" && REC.badge) REC.badge(text, tone); } catch (e) {}
  }


  /* a long render is thousands of requests; a single blip must not lose the run */
  async function post(name, blob, tries){
    tries = tries || 5;
    for (let a=0; a<tries; a++){
      try {
        const r = await fetch("/_save/" + name, { method:"POST", body: blob,
          headers:{ "Content-Type":"application/octet-stream" } });
        if (r.ok) return r.json();
      } catch (e) { /* retry */ }
      await new Promise(r => setTimeout(r, 200 * (a+1)));
    }
    throw new Error("save failed after " + tries + " tries: " + name);
  }

  function blobOf(canvas, quality){
    return new Promise(res => canvas.toBlob(res, "image/jpeg", quality));
  }

  /* 16 bit PCM WAV, the one format ffmpeg never argues about */
  function wav(buffer){
    const ch = buffer.numberOfChannels, len = buffer.length, rate = buffer.sampleRate;
    const data = new DataView(new ArrayBuffer(44 + len*ch*2));
    const str = (o,s) => { for (let i=0;i<s.length;i++) data.setUint8(o+i, s.charCodeAt(i)); };
    str(0,"RIFF"); data.setUint32(4, 36 + len*ch*2, true); str(8,"WAVE");
    str(12,"fmt "); data.setUint32(16,16,true); data.setUint16(20,1,true);
    data.setUint16(22,ch,true); data.setUint32(24,rate,true);
    data.setUint32(28, rate*ch*2, true); data.setUint16(32, ch*2, true); data.setUint16(34,16,true);
    str(36,"data"); data.setUint32(40, len*ch*2, true);
    const chans = [];
    for (let c=0;c<ch;c++) chans.push(buffer.getChannelData(c));
    let o = 44;
    for (let i=0;i<len;i++)
      for (let c=0;c<ch;c++){
        const v = Math.max(-1, Math.min(1, chans[c][i]));
        data.setInt16(o, v < 0 ? v*0x8000 : v*0x7FFF, true); o += 2;
      }
    return new Blob([data], { type:"audio/wav" });
  }

  async function run(opts){
    const F = window.FILM;
    if (!F) throw new Error("no window.FILM on this page");
    const fps = opts.fps || 60;
    const quality = opts.quality === undefined ? .95 : opts.quality;
    const from = opts.from || 0;
    const to = opts.to === undefined ? F.duration : opts.to;
    const total = Math.round((to - from) * fps);
    const base = opts.startIndex || 0;   /* resume a partial render */

    window.__render = { state:"frames", done:0, total, name:F.name, fps };
    badge("RENDER 0 / " + total, "rec");

    for (let i=0;i<total;i++){
      F.seek(from + i/fps);
      const b = await blobOf(F.canvas, quality);
      await post(F.name + "_" + String(base + i).padStart(5,"0") + ".jpg", b);
      window.__render.done = i+1;
      if (i % 30 === 0) badge("RENDER " + (i+1) + " / " + total, "rec");
      /* yield so the tab stays responsive and memory can settle */
      if (i % 10 === 0) await new Promise(r => setTimeout(r, 0));
    }

    if (F.renderAudio){
      window.__render.state = "audio";
      badge("RENDERING SCORE", "rec");
      const buf = await F.renderAudio();
      await post(F.name + ".wav", wav(buf));
    }

    window.__render.state = "done";
    badge("RENDERED " + total + " FRAMES", "ok");
    return window.__render;
  }

  return { run, wav };
})();
