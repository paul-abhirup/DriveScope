#!/usr/bin/env bash
# download_models.sh — Download quantized small VLM weights for DriveScope local inference.
#
# Usage:
#   ./scripts/download_models.sh [--model smolvlm-2.2b|smolvlm-500m|smolvlm-256m]
#                                [--quant q4_k_m|q8_0|fp16]
#                                [--output-dir ./weights]
#
# Downloads GGUF weights (and the mmproj vision projector required for image
# tokenization in llama.cpp) from Hugging Face. Idempotent: existing files with
# matching sizes are skipped.
set -euo pipefail

MODEL="smolvlm-256m"
QUANT="q4_k_m"
OUT_DIR="$(pwd)/weights"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model) MODEL="$2"; shift 2 ;;
        --quant) QUANT="$2"; shift 2 ;;
        --output-dir) OUT_DIR="$2"; shift 2 ;;
        -h|--help)
            grep '^#' "$0" | head -20
            exit 0 ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

mkdir -p "$OUT_DIR"

# Model registry: repo + file templates for each model/quant pair.
# SmolVLM2 GGUFs are published under ggml-org on Hugging Face.
case "${MODEL}:${QUANT}" in
    smolvlm-256m:q4_k_m)
        REPO="ggml-org/SmolVLM2-256M-Video-Instruct-GGUF"
        MODEL_FILE="SmolVLM2-256M-Video-Instruct-Q4_K_M.gguf"
        MMPROJ_FILE="mmproj-SmolVLM2-256M-Video-Instruct-Q8_0.gguf"
        ;;
    smolvlm-2.2b:q4_k_m)
        REPO="ggml-org/SmolVLM2-2.2B-Instruct-GGUF"
        MODEL_FILE="SmolVLM2-2.2B-Instruct-Q4_K_M.gguf"
        MMPROJ_FILE="mmproj-SmolVLM2-2.2B-Instruct-Q8_0.gguf"
        ;;
    smolvlm-256m:q8_0)
        REPO="ggml-org/SmolVLM2-256M-Video-Instruct-GGUF"
        MODEL_FILE="SmolVLM2-256M-Video-Instruct-Q8_0.gguf"
        MMPROJ_FILE="mmproj-SmolVLM2-256M-Video-Instruct-Q8_0.gguf"
        ;;
    smolvlm-256m:fp16)
        REPO="ggml-org/SmolVLM2-256M-Video-Instruct-GGUF"
        MODEL_FILE="SmolVLM2-256M-Video-Instruct-f16.gguf"
        MMPROJ_FILE="mmproj-SmolVLM2-256M-Video-Instruct-f16.gguf"
        ;;
    smolvlm-500m:q8_0)
        REPO="ggml-org/SmolVLM2-500M-Video-Instruct-GGUF"
        MODEL_FILE="SmolVLM2-500M-Video-Instruct-Q8_0.gguf"
        MMPROJ_FILE="mmproj-SmolVLM2-500M-Video-Instruct-Q8_0.gguf"
        ;;
    smolvlm-500m:fp16)
        REPO="ggml-org/SmolVLM2-500M-Video-Instruct-GGUF"
        MODEL_FILE="SmolVLM2-500M-Video-Instruct-f16.gguf"
        MMPROJ_FILE="mmproj-SmolVLM2-500M-Video-Instruct-f16.gguf"
        ;;
    *)
        echo "Unsupported model/quant combination: ${MODEL}/${QUANT}" >&2
        echo "Supported: smolvlm-2.2b (q4_k_m), smolvlm-256m (q4_k_m|q8_0|fp16), smolvlm-500m (q8_0|fp16)" >&2
        exit 1 ;;
esac

download() {
    local file="$1"
    local url="https://huggingface.co/${REPO}/resolve/main/${file}"
    local dest="${OUT_DIR}/${file}"
    if [[ -f "$dest" ]]; then
        echo "[skip] ${file} already exists ($(du -h "$dest" | cut -f1))"
        return 0
    fi
    echo "[downloading] ${url}"
    curl -fL --retry 3 --progress-bar -o "${dest}.part" "$url"
    mv "${dest}.part" "$dest"
    echo "[done] ${file} ($(du -h "$dest" | cut -f1))"
}

download "$MODEL_FILE"
download "$MMPROJ_FILE"

cat <<EOF

Download complete.
  Model weights : ${OUT_DIR}/${MODEL_FILE}
  Vision proj.  : ${OUT_DIR}/${MMPROJ_FILE}

To wire the adapter, set:
  export VLM_MODEL_PATH="${OUT_DIR}/${MODEL_FILE}"
  export VLM_MMPROJ_PATH="${OUT_DIR}/${MMPROJ_FILE}"
EOF
