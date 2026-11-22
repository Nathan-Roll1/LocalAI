set -euo pipefail
qa="$RUNNER_TEMP/llama-stock"
mkdir -p "$qa"/{models,backends,configuration}
cd "$qa"
curl -fsSL --retry 3 https://github.com/mudler/LocalAI/releases/download/v5.0.1/local-ai-v5.0.1-linux-amd64 -o local-ai
echo 'cd1e3eb72d9d0b63d5163804d507a5af0605a8d0518af24ea4eca8ae26866a5b  local-ai' | sha256sum --check
chmod +x local-ai
export LOCALAI_BACKENDS_PATH="$qa/backends" LOCALAI_MODELS_PATH="$qa/models" LOCALAI_CONFIG_DIR="$qa/configuration" LOCALAI_BACKEND_GALLERIES='[]'
image='quay.io/go-skynet/local-ai-backends@sha256:9f9f2ad2aa8f3c517065bb5668c7f83577d52f3638f39daead60e8093a3cbc31'
./local-ai backends install "$image" llama-cpp llama-cpp >backend-install.log 2>&1 || { tail -c 3000 backend-install.log; exit 1; }
find backends -name 'llama-cpp-cpu-all' -exec sha256sum {} \;
curl -fsSL https://raw.githubusercontent.com/ggml-org/whisper.cpp/b0a11594aec50892a02cd8d129eee2dfe93a8bb8/samples/jfk.wav -o jfk.wav
curl -fsSL https://raw.githubusercontent.com/docling-project/docling/0f3564c772e006c73417f61658a2d41c8352224d/tests/data/audio/sources/sample_10s.mp3 -o sample_10s.mp3
gallery="https://raw.githubusercontent.com/$GITHUB_REPOSITORY/$GITHUB_SHA/fourier-llama-qa/gallery.yaml"
export LOCALAI_GALLERIES=$(jq -cn --arg u "$gallery" '[{name:"oruk",url:$u}]')
./local-ai run --address=127.0.0.1:8080 --disable-backend-install >localai.log 2>&1 & server=$!
trap 'tail -c 5500 localai.log; kill "$server" 2>/dev/null || true' EXIT
for i in $(seq 1 75); do curl -fs http://127.0.0.1:8080/v1/models >/dev/null && break; kill -0 "$server"; sleep 1; done
python "$GITHUB_WORKSPACE/fourier-llama-qa/verify.py"
