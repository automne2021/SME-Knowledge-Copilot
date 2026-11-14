/**
 * README demo, Node 24 + installed Edge; no project dependency changes.
 * Setup: npm.cmd install --prefix .cache/tools/gif --no-audit --no-fund --save-exact gifenc@1.0.3
 * Start: start-web.cmd -NoBrowser
 * Set DEMO_ADMIN_PASSWORD in the process environment (never pass it as an argument).
 * Check without Gemini: node scripts/record_demo_gif.mjs --check
 * Record ONE question: node scripts/record_demo_gif.mjs --record
 * Finish a failed UI capture from its completed server result (GET only):
 *   node scripts/record_demo_gif.mjs --resume <capture-dir>
 * Re-encode saved frames, no browser/model: node scripts/record_demo_gif.mjs --encode <capture-dir>
 * Quota/overload locks this task ledger; never automatically retry or reset it.
 * The task permits two UI questions total. Each uses normal app countTokens and
 * up to two generateContent calls (the app's existing bounded output repair).
 * Only the first second of the real pending state is retained. Other captured
 * phases use their normal timing. README must disclose the shortened wait.
 */
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as sleep } from "node:timers/promises";
import { inflateSync } from "node:zlib";
import { createRequire } from "node:module";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const cache = join(root, ".cache", "demo-gif");
const ledgerPath = join(cache, "ledger.json");
const output = join(root, "docs", "images", "demo.gif");
const origin = "http://127.0.0.1:5173";
const question =
  "Đơn nghỉ phép thông thường cần gửi trước bao lâu và ai phê duyệt?";
const mode = process.argv[2];
const require = createRequire(import.meta.url);
const { GIFEncoder, quantize, nearestColorIndex } = require(
  join(root, ".cache/tools/gif/node_modules/gifenc"),
);
if (Number(process.versions.node.split(".")[0]) < 24)
  throw Error("Node 24 required");
if (!["--check", "--record", "--resume", "--encode"].includes(mode))
  throw Error(
    "Use --check, --record, --resume <capture-dir> or --encode <capture-dir>",
  );
mkdirSync(cache, { recursive: true });

// Decode only the non-interlaced 8-bit RGB/RGBA PNGs emitted by Chromium.
// Node zlib supplies decompression; no second image dependency is needed.
function decodePNG(png) {
  if (png.subarray(0, 8).toString("hex") !== "89504e470d0a1a0a")
    throw Error("Invalid PNG");
  let width, height, channels;
  const parts = [];
  for (let p = 8; p < png.length;) {
    const length = png.readUInt32BE(p),
      type = png.toString("ascii", p + 4, p + 8);
    const data = png.subarray(p + 8, p + 8 + length);
    if (type === "IHDR") {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      channels = data[9] === 2 ? 3 : data[9] === 6 ? 4 : 0;
      if (data[8] !== 8 || !channels || data[12] !== 0)
        throw Error("Unsupported PNG");
    } else if (type === "IDAT") parts.push(data);
    p += length + 12;
  }
  const stride = width * channels,
    raw = inflateSync(Buffer.concat(parts));
  if (raw.length !== height * (stride + 1)) throw Error("Invalid PNG length");
  const pixels = Buffer.alloc(stride * height);
  const paeth = (a, b, c) => {
    const p = a + b - c,
      x = Math.abs(p - a),
      y = Math.abs(p - b),
      z = Math.abs(p - c);
    return x <= y && x <= z ? a : y <= z ? b : c;
  };
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    if (filter > 4) throw Error("Invalid PNG filter");
    for (let x = 0; x < stride; x++) {
      const i = y * stride + x,
        a = x >= channels ? pixels[i - channels] : 0;
      const b = y ? pixels[i - stride] : 0,
        c = y && x >= channels ? pixels[i - stride - channels] : 0;
      const prediction = [0, a, b, Math.floor((a + b) / 2), paeth(a, b, c)][
        filter
      ];
      pixels[i] = (raw[y * (stride + 1) + x + 1] + prediction) & 255;
    }
  }
  const rgba = new Uint8Array(width * height * 4);
  for (let i = 0, j = 0; i < pixels.length; i += channels, j += 4) {
    rgba[j] = pixels[i];
    rgba[j + 1] = pixels[i + 1];
    rgba[j + 2] = pixels[i + 2];
    rgba[j + 3] = 255;
  }
  return { width, height, rgba };
}

function encode(directory) {
  directory = resolve(directory);
  if (!directory.startsWith(cache + "\\") && !directory.startsWith(cache + "/"))
    throw Error("Capture must be inside .cache/demo-gif");
  const manifest = JSON.parse(
    readFileSync(join(directory, "capture.json"), "utf8"),
  );
  if (!manifest.complete)
    throw Error("Capture is incomplete; do not publish it");
  const gif = GIFEncoder();
  let lastHash, palette, indexed, width, height, rgba, previousRGBA;
  for (const frame of manifest.frames) {
    if (!/^\d{4}\.png$/.test(frame.file)) throw Error("Invalid frame filename");
    const png = readFileSync(join(directory, frame.file));
    const hash = createHash("sha256").update(png).digest("hex");
    if (hash !== lastHash) {
      const decoded = decodePNG(png);
      ({ width, height, rgba } = decoded);
      if (width !== 960 || height !== 600)
        throw Error("Expected 960x600 frame");
      palette = quantize(rgba, 254);
      // Exact RGB cache avoids merging the app's nearby white/blue background
      // colors into one rgb565 lookup bucket during palette mapping.
      const colors = new Map();
      indexed = new Uint8Array(width * height);
      for (let i = 0, p = 0; i < rgba.length; i += 4, p++) {
        const key = (rgba[i] << 16) | (rgba[i + 1] << 8) | rgba[i + 2];
        if (!colors.has(key))
          colors.set(
            key,
            nearestColorIndex(palette, [rgba[i], rgba[i + 1], rgba[i + 2]]),
          );
        indexed[p] = colors.get(key);
      }
      lastHash = hash;
    }
    // Keep all 10 fps frames while encoding unchanged pixels transparently.
    // Disposal 1 retains the previous canvas; no timing or content is dropped.
    const transparentIndex = palette.length;
    const delta = indexed.slice();
    if (previousRGBA) {
      for (let i = 0, p = 0; i < rgba.length; i += 4, p++) {
        if (
          rgba[i] === previousRGBA[i] &&
          rgba[i + 1] === previousRGBA[i + 1] &&
          rgba[i + 2] === previousRGBA[i + 2]
        )
          delta[p] = transparentIndex;
      }
    }
    gif.writeFrame(delta, width, height, {
      palette: [...palette, [0, 0, 0]],
      delay: 100,
      repeat: 0,
      transparent: Boolean(previousRGBA),
      transparentIndex,
      dispose: 1,
    });
    previousRGBA = rgba;
  }
  gif.finish();
  const bytes = gif.bytes();
  if (bytes.length >= 5_000_000) throw Error("GIF exceeds 5 MB");
  writeFileSync(output, bytes);
  const result = {
    frames: manifest.frames.length,
    seconds: manifest.frames.length / 10,
    width,
    height,
    bytes: bytes.length,
    sha256: createHash("sha256").update(bytes).digest("hex"),
  };
  writeFileSync(
    join(directory, "encoded.json"),
    JSON.stringify(result, null, 2) + "\n",
  );
  console.log(JSON.stringify(result));
}

class CDP {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    this.listeners = new Map();
    ws.addEventListener("message", ({ data }) => {
      const message = JSON.parse(data);
      if (message.id) {
        const item = this.pending.get(message.id);
        if (!item) return;
        this.pending.delete(message.id);
        clearTimeout(item.timer);
        if (message.error)
          item.reject(Error("CDP command failed: " + message.error.message));
        else item.resolve(message.result);
      } else this.listeners.get(message.method)?.(message.params);
    });
    ws.addEventListener("close", () => {
      for (const item of this.pending.values()) {
        clearTimeout(item.timer);
        item.reject(Error("CDP closed"));
      }
      this.pending.clear();
    });
  }
  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.id;
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(Error("CDP timeout: " + method));
      }, 20000);
      this.pending.set(id, { resolve, reject, timer });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async evaluate(expression) {
    const result = await this.send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (result.exceptionDetails) throw Error("Page evaluation failed"); // Never echo credential expressions.
    return result.result.value;
  }
}

async function waitFor(action, description, timeout = 20000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const value = await action();
    if (value) return value;
    await sleep(100);
  }
  throw Error("Timed out: " + description);
}

async function record() {
  if (!process.env.DEMO_ADMIN_PASSWORD)
    throw Error("Set DEMO_ADMIN_PASSWORD in environment");
  const ledger = existsSync(ledgerPath)
    ? JSON.parse(readFileSync(ledgerPath, "utf8"))
    : { task: "00-T4", question, maxQuestions: 2, attempts: [] };
  if (mode === "--record" && (ledger.stopped || ledger.attempts.length >= 2))
    throw Error("Task budget exhausted or stopped; no request sent");
  const resume = mode === "--resume";
  const directory = resume
    ? resolve(process.argv[3] || "")
    : join(cache, new Date().toISOString().replace(/[:.]/g, "-"));
  if (!directory.startsWith(cache + "\\") && !directory.startsWith(cache + "/"))
    throw Error("Capture must be inside .cache/demo-gif");
  let cdp,
    attempt = resume
      ? ledger.attempts.find(
          (a) => a.capture === directory.split(/[\\/]/).at(-1),
        )
      : undefined;
  if (
    resume &&
    (!attempt?.sessionId ||
      attempt.status !== "server-completed-ui-interrupted")
  )
    throw Error("Resume requires a verified completed server result in ledger");
  const manifest = resume
    ? JSON.parse(readFileSync(join(directory, "capture.json"), "utf8"))
    : {
        question,
        complete: false,
        fps: 10,
        viewport: [1280, 800],
        pendingRetainedSeconds: 1,
        frames: [],
      };
  if (
    resume &&
    (manifest.complete || manifest.frames.at(-1)?.phase !== "pending")
  )
    throw Error("Resume only an incomplete capture ending at pending");
  const saveLedger = () =>
    writeFileSync(ledgerPath, JSON.stringify(ledger, null, 2) + "\n");
  const profile = join(directory, "edge-profile-" + Date.now());
  mkdirSync(profile, { recursive: true });
  const edgePath =
    process.env.EDGE_PATH ||
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
  const edge = spawn(
    edgePath,
    [
      "--headless=new",
      "--disable-gpu",
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-extensions",
      "--disable-background-networking",
      "--remote-debugging-address=127.0.0.1",
      "--remote-debugging-port=0",
      "--user-data-dir=" + profile,
      "--window-size=1280,800",
      "about:blank",
    ],
    { windowsHide: true, stdio: "ignore" },
  );
  try {
    let spawnFailure = false;
    edge.on("error", () => {
      spawnFailure = true;
    });
    const port = await waitFor(() => {
      if (spawnFailure) throw Error("Could not launch installed Edge");
      const file = join(profile, "DevToolsActivePort");
      return (
        existsSync(file) && Number(readFileSync(file, "utf8").split("\n")[0])
      );
    }, "Edge CDP port");
    const targets = await (
      await fetch(`http://127.0.0.1:${port}/json/list`)
    ).json();
    const target = targets.find((t) => t.type === "page");
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.addEventListener("open", resolve, { once: true });
      ws.addEventListener(
        "error",
        () => reject(Error("CDP connection failed")),
        { once: true },
      );
    });
    cdp = new CDP(ws);
    await cdp.send("Page.enable");
    await cdp.send("Network.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1280,
      height: 800,
      deviceScaleFactor: 1,
      mobile: false,
    });
    await cdp.send("Page.navigate", { url: origin + "/login" });
    await waitFor(
      () =>
        cdp.evaluate('Boolean(document.querySelector("input[name=username]"))'),
      "login screen",
    );
    // Native input events exercise the existing React login form; never record login.
    for (const [selector, value] of [
      ["input[name=username]", "demo.admin"],
      ["input[name=password]", process.env.DEMO_ADMIN_PASSWORD],
    ]) {
      await cdp.evaluate(
        `document.querySelector(${JSON.stringify(selector)}).focus()`,
      );
      await cdp.send("Input.insertText", { text: value });
    }
    await cdp.evaluate('document.querySelector("form").requestSubmit()');
    await waitFor(
      () => cdp.evaluate('Boolean(document.querySelector("#question"))'),
      "authenticated chat",
    );
    await waitFor(
      () =>
        cdp.evaluate(
          '/[1-9]\\d* tài liệu sẵn sàng/.test(document.querySelector(".chat-heading")?.textContent || "")',
        ),
      "existing ready documents",
    );
    if (resume) {
      await cdp.send("Page.navigate", {
        url: origin + "/chat/" + attempt.sessionId,
      });
      await waitFor(
        () =>
          cdp.evaluate('Boolean(document.querySelector(".answer .citation"))'),
        "completed answer from history",
      );
      manifest.resumedFromCompletedHistory = true;
    } else if (mode === "--record") {
      // Prepare an empty session before recording. This avoids the development
      // StrictMode mount/auto-send race on navigation from a new conversation.
      const sessionId = await cdp.evaluate(
        `(async()=>{const {token}=JSON.parse(sessionStorage.getItem('sme.auth.v1'));const r=await fetch('/api/v1/chat/sessions',{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({title:${JSON.stringify(question)}})});if(!r.ok)throw Error();return (await r.json()).data.id})()`,
      );
      await cdp.send("Page.navigate", { url: origin + "/chat/" + sessionId });
      await waitFor(
        () =>
          cdp.evaluate(
            'Boolean(document.querySelector("#question")) && !document.querySelector(".chat-thread [role=status]")',
          ),
        "empty session ready",
      );
    }
    await cdp.evaluate("document.fonts.ready.then(() => true)");
    await sleep(400);
    const screenshot = async () =>
      Buffer.from(
        (
          await cdp.send("Page.captureScreenshot", {
            format: "png",
            captureBeyondViewport: false,
            clip: { x: 0, y: 0, width: 1280, height: 800, scale: 0.75 },
          })
        ).data,
        "base64",
      );
    if (mode === "--check") {
      writeFileSync(join(directory, "check.png"), await screenshot());
      console.log(
        "Check passed; no Gemini request. Screenshot: " +
          join(directory, "check.png"),
      );
      return;
    }
    let queryResponse;
    cdp.listeners.set("Network.responseReceived", (p) => {
      if (
        p.response.url === origin + "/api/v1/chat/query" &&
        p.type === "Fetch"
      )
        queryResponse = { id: p.requestId, status: p.response.status };
    });
    const snap = async (phase) => {
      const start = Date.now(),
        file = String(manifest.frames.length).padStart(4, "0") + ".png";
      if (
        await cdp.evaluate('Boolean(document.querySelector(".feedback-error"))')
      )
        throw Error("UI error visible; capture rejected, no automatic retry");
      writeFileSync(join(directory, file), await screenshot());
      manifest.frames.push({ file, phase });
      await sleep(Math.max(0, 100 - (Date.now() - start)));
    };
    const hold = async (phase, frames) => {
      for (let i = 0; i < frames; i++) await snap(phase);
    };
    if (!resume) {
      await hold("intro", 7);
      await cdp.evaluate('document.querySelector("#question").focus()');
      const letters = [...question];
      for (let i = 0; i < letters.length; i++) {
        await cdp.send("Input.insertText", { text: letters[i] });
        if (i % 2 === 1 || i === letters.length - 1) await snap("typing");
        else await sleep(40);
      }
      await hold("question", 8);
      attempt = {
        number: ledger.attempts.length + 1,
        reservedAt: new Date().toISOString(),
        status: "reserved",
        capture: directory.split(/[\\/]/).at(-1),
      };
      ledger.attempts.push(attempt);
      saveLedger(); // Persist before any UI submission.
      const sent = Date.now();
      await cdp.evaluate(
        'document.querySelector("#question").form.requestSubmit()',
      );
      attempt.status = "submitted";
      saveLedger();
      await waitFor(
        () => cdp.evaluate('Boolean(document.querySelector(".thinking"))'),
        "real pending state",
      );
      await hold("pending", 10);
      await waitFor(
        async () => {
          if (queryResponse && queryResponse.status >= 400) {
            const body = await cdp.send("Network.getResponseBody", {
              requestId: queryResponse.id,
            });
            const error = JSON.parse(body.body).error;
            attempt.errorCode = error?.code;
            attempt.reason = error?.details?.reason;
            attempt.runId = error?.details?.run_id;
            // Provider failures stop this task; quota/overload are never retried.
            ledger.stopped =
              ["quota", "overloaded"].includes(attempt.reason) ||
              ["model_unavailable", "model_timeout"].includes(
                attempt.errorCode,
              );
            attempt.status = "failed";
            saveLedger();
            throw Error(
              "Chat failed: " +
                attempt.errorCode +
                " / " +
                (attempt.reason || "unknown") +
                "; task stopped",
            );
          }
          return cdp.evaluate(
            'Boolean(document.querySelector(".answer .citation"))',
          );
        },
        "answer with citations",
        165000,
      );
      attempt.answerWaitMs = Date.now() - sent;
      const answer = JSON.parse(
        (
          await cdp.send("Network.getResponseBody", {
            requestId: queryResponse.id,
          })
        ).body,
      ).data;
      attempt.runId = answer.run_id || answer.id;
      attempt.sessionId = answer.session_id;
    }
    const view = await cdp.evaluate(
      '({ai:document.querySelector(".ai-label")?.textContent,claims:document.querySelector(".answer-claims")?.textContent,source:document.querySelector(".source-card-name")?.textContent})',
    );
    if (
      view.ai !== "AI-generated" ||
      !view.source?.includes("quy_dinh_nghi_phep")
    )
      throw Error("Unexpected answer/source; preserve capture for review");
    manifest.answer = view;
    await hold("answer", 35);
    const bounds = await cdp.evaluate(
      '(()=>{const r=document.querySelector(".citation").getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()',
    );
    await cdp.send("Input.dispatchMouseEvent", {
      type: "mouseMoved",
      ...bounds,
    });
    await hold("citation-hover", 7);
    await cdp.send("Input.dispatchMouseEvent", {
      type: "mousePressed",
      button: "left",
      clickCount: 1,
      ...bounds,
    });
    await cdp.send("Input.dispatchMouseEvent", {
      type: "mouseReleased",
      button: "left",
      clickCount: 1,
      ...bounds,
    });
    await cdp.send("Input.dispatchMouseEvent", {
      type: "mouseMoved",
      x: 1270,
      y: 790,
    });
    await waitFor(
      () =>
        cdp.evaluate(
          'Boolean(document.querySelector(".source-excerpt blockquote"))',
        ),
      "highlighted source",
    );
    manifest.source = await cdp.evaluate(
      '({file:document.querySelector(".source-filename")?.textContent,text:document.querySelector(".source-excerpt blockquote")?.textContent,background:getComputedStyle(document.querySelector(".source-excerpt")).backgroundColor})',
    );
    if (
      !manifest.source.file?.includes("quy_dinh_nghi_phep") ||
      !/3 ngày/.test(manifest.source.text) ||
      !/quản lý trực tiếp/i.test(manifest.source.text)
    )
      throw Error("Source does not support the demo answer");
    await hold("source", 50);
    manifest.complete = true;
    attempt.status = "completed";
    saveLedger();
  } finally {
    writeFileSync(
      join(directory, "capture.json"),
      JSON.stringify(manifest, null, 2) + "\n",
    );
    if (cdp) {
      try {
        await cdp.evaluate(
          '(async()=>{const raw=sessionStorage.getItem("sme.auth.v1");if(!raw)return true;const {token}=JSON.parse(raw);const r=await fetch("/api/v1/auth/logout",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!r.ok)throw Error();sessionStorage.clear();return true})()',
        );
      } catch {
        console.error("Logout could not be verified");
      }
      try {
        await cdp.send("Browser.close");
      } catch {
        /* Browser may close before replying. */
      }
    }
    if (edge.exitCode === null) edge.kill();
  }
  encode(directory);
}

try {
  if (mode === "--encode") encode(process.argv[3] || "");
  else await record();
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
