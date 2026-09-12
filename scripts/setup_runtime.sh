#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -d .venv || python3 -m venv .venv
.venv/bin/pip install -r configs/runtime-requirements.txt
if [ ! -d vendor/llama.cpp/.git ]; then
  git clone https://github.com/ggml-org/llama.cpp vendor/llama.cpp
fi
git -C vendor/llama.cpp checkout acecd56032ddc34bada14a2d978f110d9c987095
.venv/bin/cmake -S vendor/llama.cpp -B vendor/llama.cpp/build \
  -DGGML_CUDA=ON -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc \
  -DCMAKE_CUDA_ARCHITECTURES=89 -DLLAMA_BUILD_TESTS=OFF
.venv/bin/cmake --build vendor/llama.cpp/build --target llama-server -j 12
