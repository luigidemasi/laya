# Copyright 2026 Luigi De Masi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM docker.io/library/python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TORCH_DISABLE_NATIVE_JIT=1 \
    TOKENIZERS_PARALLELISM=false \
    HF_HOME=/home/laya/.cache/huggingface \
    LAYA_DEVICE=cpu \
    LAYA_MODELS=typed-decisions \
    LAYA_REVISION=reviewed \
    LAYA_PRELOAD=1 \
    LAYA_THREADS=4 \
    LAYA_API_PATH=/v1/systemone

# Install the CPU wheel explicitly; do not download CUDA libraries for CPU inference.
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && pip check

RUN useradd --uid 10001 --create-home laya \
    && mkdir -p /home/laya/.cache/huggingface \
    && chown -R laya:laya /home/laya/.cache
WORKDIR /app
COPY app.py test_app.py LICENSE.txt NOTICE.txt ./
RUN python -m unittest -v
LABEL org.opencontainers.image.title="Laya decision API with configurable request path" \
      org.opencontainers.image.version="0.3.22-2" \
      org.opencontainers.image.source="https://github.com/luigidemasi/laya" \
      org.opencontainers.image.licenses="Apache-2.0"
USER laya
EXPOSE 8100
HEALTHCHECK --interval=10s --timeout=5s --start-period=10m \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8100/health', timeout=4)"
CMD ["uvicorn", "app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8100"]
