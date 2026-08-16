#!/usr/bin/env bash

set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

while [[ -z "${OPENAI_API_KEY:-}" ]]; do
  read -r -s -p "请粘贴 OpenAI API Key（输入内容不会显示），然后按回车：" OPENAI_API_KEY
  printf '\n'
  OPENAI_API_KEY="${OPENAI_API_KEY#"${OPENAI_API_KEY%%[![:space:]]*}"}"
  OPENAI_API_KEY="${OPENAI_API_KEY%"${OPENAI_API_KEY##*[![:space:]]}"}"
  if [[ -z "$OPENAI_API_KEY" ]]; then
    printf '没有检测到输入，请重新粘贴。\n' >&2
    unset OPENAI_API_KEY
  fi
done

OPENAI_API_KEY="${OPENAI_API_KEY#"${OPENAI_API_KEY%%[![:space:]]*}"}"
OPENAI_API_KEY="${OPENAI_API_KEY%"${OPENAI_API_KEY##*[![:space:]]}"}"
export OPENAI_API_KEY
printf '正在安全验证 API Key……\n'
if ! .venv/bin/python - <<'PY'
from openai import OpenAI

try:
    OpenAI().models.list()
except Exception as exc:
    print(f"验证失败：{type(exc).__name__}")
    raise SystemExit(1)
PY
then
  printf '\nAPI Key 验证失败，网站未启动。请删除这把 Key 并重新运行本程序。\n' >&2
  unset OPENAI_API_KEY
  exit 2
fi
printf 'API Key 验证成功，正在启动网站。\n'

exec .venv/bin/streamlit run app.py \
  --server.port 8501 \
  --server.address 127.0.0.1 \
  --server.headless true \
  --browser.gatherUsageStats false
