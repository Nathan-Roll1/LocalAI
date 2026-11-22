import json
import re
import time
from pathlib import Path

import requests

base = "http://127.0.0.1:8080"
name = "oruk-fourier-2b-q8"
files = [
    ("jfk.wav", "audio/wav", "And so my fellow Americans ask not what your country can do for you ask what you can do for your country"),
    ("sample_10s.mp3", "audio/mpeg", "Shakespeare on scenery by Oscar Wilde This is a LibriVox recording All LibriVox recordings are in the public domain"),
]
response = requests.post(base + "/models/apply", json={"id": "oruk@" + name}, timeout=30)
print("NAMED_GALLERY_APPLY", response.status_code, response.text, flush=True)
response.raise_for_status()
job = response.json()["uuid"]
for _ in range(180):
    status = requests.get(base + "/models/jobs/" + job, timeout=10).json()
    if status.get("error"):
        raise RuntimeError(status)
    if status.get("processed"):
        break
    time.sleep(2)
else:
    raise RuntimeError(status)
matched = [m for m in requests.get(base + "/v1/models").json()["data"] if m["id"] == name]
assert len(matched) == 1, matched
print("GALLERY_INSTALLED", matched, flush=True)
weights = {p.name: p.stat().st_size for p in Path("models").rglob("*.gguf")}
assert sum(weights.values()) == 2190133984, weights
results = []
for filename, media, ref in files:
    with open(filename, "rb") as audio:
        reply = requests.post(base + "/v1/audio/transcriptions", files={"file": (filename, audio, media)}, data={"model": name, "language": "en", "response_format": "json", "temperature":"0"}, timeout=270)
    print("RAW_MULTIPART", filename, reply.status_code, reply.text[:800], flush=True)
    text = reply.json().get("text", "") if reply.ok else ""
    tag = "<asr_text>" in text or re.search(r"^\s*language\s+[a-z]+\b", text, re.I) is not None
    words = lambda t: re.findall("[a-z]+", t.lower())
    results.append(dict(file=filename,status=reply.status_code,raw_response=reply.text[:1500],reference=ref,word_match=words(text)==words(ref),contains_metadata=bool(tag),normalized_words=len(words(text))))
receipt = {"localai":"v5.0.1", "llama_cpp_release_image":"quay.io/go-skynet/local-ai-backends@sha256:9f9f2ad2aa8f3c517065bb5668c7f83577d52f3638f39daead60e8093a3cbc31", "canonical_revision":"d09bf574fa9e0150e27fa33c236e6deb1089f781", "gallery":"oruk@"+name,"model_files":weights,"transcriptions":results}
Path("result.json").write_text(json.dumps(receipt,indent=2)+"\n")
print("CLEAN_TRANSCRIPTS", [r["word_match"] and not r["contains_metadata"] for r in results],flush=True)
assert all(r["word_match"] and not r["contains_metadata"] for r in results)
