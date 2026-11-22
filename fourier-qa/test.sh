set -euo pipefail
mkdir -p /tmp/fourier-stock/{models,engine}
cd /tmp/fourier-stock
curl --fail --location --retry 3 -sS https://github.com/mudler/LocalAI/releases/download/v5.0.1/local-ai-v5.0.1-linux-amd64 -o local-ai
echo 'cd1e3eb72d9d0b63d5163804d507a5af0605a8d0518af24ea4eca8ae26866a5b  local-ai' | sha256sum --check
chmod +x local-ai
image='quay.io/go-skynet/local-ai-backends@sha256:0ae184f09dfa0c76c509e39800121bef4d046c44a3e5c3b393b3483e9ef6d57e'
docker pull -q "$image"
container=$(docker create "$image" /run.sh)
docker export "$container" | tar -x -C engine
docker rm "$container" >/dev/null
engine=$(dirname "$(find "$PWD/engine" -name run.sh -print -quit)")
test -f "$engine/model_specs/qwen3_asr.json"
printf 'Stock Qwen3-ASR metadata %s\n' "$(sha256sum "$engine/model_specs/qwen3_asr.json")"
curl -fsSL https://raw.githubusercontent.com/ggml-org/whisper.cpp/b0a11594aec50892a02cd8d129eee2dfe93a8bb8/samples/jfk.wav -o jfk.wav
curl -fsSL https://raw.githubusercontent.com/docling-project/docling/0f3564c772e006c73417f61658a2d41c8352224d/tests/data/audio/sources/sample_10s.mp3 -o sample_10s.mp3
(cd "$engine" && AUDIOCPP_DEFAULT_BACKEND=cpu ./run.sh --addr 127.0.0.1:50051) >backend.log 2>&1 & worker=$!
gallery_url="https://raw.githubusercontent.com/$GITHUB_REPOSITORY/$GITHUB_SHA/fourier-qa/gallery.yaml"
export LOCALAI_GALLERIES="[{\"name\":\"oruk\",\"url\":\"$gallery_url\"}]" LOCALAI_BACKEND_GALLERIES='[]' LOCALAI_MODELS_PATH="$PWD/models"
./local-ai run --address=127.0.0.1:8080 --models-path="$PWD/models" --external-grpc-backends=audio-cpp:127.0.0.1:50051 >localai.log 2>&1 & server=$!
trap 'tail -c 8000 backend.log; tail -c 8000 localai.log; kill "$worker" "$server" 2>/dev/null || true' EXIT
for i in $(seq 1 60); do curl -fs http://127.0.0.1:8080/v1/models >/dev/null && break; kill -0 "$server" "$worker"; sleep 1; done
python "$GITHUB_WORKSPACE/fourier-qa/test.py"
