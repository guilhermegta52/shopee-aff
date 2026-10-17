#!/usr/bin/env python3
"""Optional, explicitly approved AI presenter scene for Promo Radar.

No generation or billing occurs unless both PRESENTER_MODE=ai and
ENABLE_PAID_AI_GENERATION=true are set. Keeps original photo-only pipeline
as default. Reference image is the real product's Shopee HTTPS URL.
"""
import json, os, pathlib, time, urllib.request, urllib.parse

MODEL = "kling-video/v3.0/std/image-to-video"
API = "https://api.higgsfield.ai"
ALLOWED_HOSTS = {"api.higgsfield.ai"}

def _request(path, key, payload=None):
    url = API + path
    headers = {"Authorization": "Key " + key, "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.load(resp)

def _safe_video_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Generated video requires an HTTPS URL")
    return url

def generate(prod, dest):
    if os.getenv("PRESENTER_MODE") != "ai":
        return None
    if os.getenv("ENABLE_PAID_AI_GENERATION") != "true":
        raise RuntimeError("AI presenter would incur credits; set ENABLE_PAID_AI_GENERATION=true only after approval")
    key = os.getenv("HF_KEY") or os.getenv("HF_CREDENTIALS")
    if not key:
        raise RuntimeError("HF_KEY required for optional presenter generation")
    image = str(prod.get("image") or "")
    parsed = urllib.parse.urlparse(image)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(("susercontent.com", "shopee.com.br")):
        raise RuntimeError("Real Shopee HTTPS product image required as AI presenter reference")
    title = str(prod.get("title", ""))[:140]
    prompt = (
        "Vertical professional UGC product advertisement in a realistic clean Brazilian studio. "
        "An adult human presenter naturally holds and presents the EXACT product shown in the reference photograph "
        "to camera, gentle hand and head movement, studio lighting, waist-up composition. "
        "Maintain true proportions, shape and branding of the pictured product. "
        "Do not invent components, functions, certifications or performance claims. "
        "No text, graphics, prices, subtitles or other product. Product: " + title
    )
    data = _request("/" + MODEL, key, {
        "image_url": image, "prompt": prompt, "duration": 5,
        "sound": "off", "multi_shots": False, "cfg_scale": 0.5
    })
    rid = data.get("request_id")
    if not rid:
        raise RuntimeError("AI provider did not return request_id: " + str(data.get("status", "unknown")))
    record = {"request_id": str(rid), "model": MODEL, "duration": 5,
              "sound": "off", "status": str(data.get("status", "submitted"))}
    record_path = pathlib.Path(dest).with_name("presenter-request.json")
    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print("AI_REQUEST_ACCEPTED", rid, flush=True)
    deadline = time.monotonic() + 480
    while time.monotonic() < deadline:
        reply = _request("/requests/" + urllib.parse.quote(str(rid), safe="") + "/status", key)
        status = str(reply.get("status", "")).lower()
        record["status"] = status
        record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        if status == "completed":
            video = reply.get("video") or (reply.get("result") or {}).get("video")
            link = video.get("url") if isinstance(video, dict) else video
            if not link:
                raise RuntimeError("AI generation completed but no video URL returned")
            _safe_video_url(link)
            req = urllib.request.Request(link, headers={"User-Agent": "PromoRadar/1.0"})
            with urllib.request.urlopen(req, timeout=100) as r:
                data = r.read(80 * 1024 * 1024 + 1)
            if len(data) < 10000 or len(data) > 80 * 1024 * 1024:
                raise RuntimeError("AI presenter video missing or too large")
            pathlib.Path(dest).write_bytes(data)
            return pathlib.Path(dest)
        if status in ("failed", "canceled", "nsfw"):
            raise RuntimeError("AI presenter request ended with status " + status)
        time.sleep(8)
    raise RuntimeError("AI presenter generation timeout; check provider dashboard before retrying to avoid duplicate charges")
