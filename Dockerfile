# syntax=docker/dockerfile:1

# ── Stage 1: build wheels ──────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip wheel --wheel-dir /wheels -r requirements.txt

# robot_hat is not on PyPI — install from source into the wheels directory
RUN git clone --depth=1 https://github.com/ExMachinaParlor/robot-hat.git /tmp/robot-hat && \
    pip wheel --wheel-dir /wheels /tmp/robot-hat && \
    rm -rf /tmp/robot-hat


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    APP_DATA=/app/data

WORKDIR ${APP_HOME}

# Runtime-only system libraries (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    i2c-tools \
    udev \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    tini \
    iw \
    rfkill \
    nmap \
    arp-scan \
    bluez \
    gpsd-clients \
    rtl-433 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user with fixed uid/gid
RUN groupadd --system --gid 10001 app && \
    useradd --system --uid 10001 --gid 10001 \
            --create-home --home-dir /home/app app && \
    mkdir -p ${APP_DATA} && \
    chown -R app:app ${APP_HOME} /home/app

# Install pre-built wheels from builder stage
COPY --from=builder /wheels /wheels
COPY --chown=app:app requirements.txt ./
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Patch robot_hat __init__.py to make optional modules (audio, TTS) non-fatal.
# robot_hat imports pyaudio/TTS at package level; we don't need them for motor control.
RUN <<EOF python3
import pathlib, glob
for init in glob.glob('/usr/local/lib/python*/site-packages/robot_hat/__init__.py'):
    p = pathlib.Path(init)
    lines = p.read_text().splitlines()
    output = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('from .') and ' import ' in stripped:
            syms_part = stripped.split(' import ', 1)[1]
            syms = [s.strip() for s in syms_part.split(',')]
            output.append('try:')
            output.append(f'    {stripped}')
            output.append('except Exception:')
            for sym in syms:
                alias = sym.split(' as ')[-1].strip() if ' as ' in sym else sym.strip()
                output.append(f'    {alias} = None')
        else:
            output.append(line)
    p.write_text('\n'.join(output) + '\n')
    print(f'Patched {init}')
EOF

# Copy application source after dependencies for better layer caching
COPY --chown=app:app . ${APP_HOME}

RUN chown -R app:app ${APP_DATA}

USER 10001:10001

EXPOSE 5000

# Healthcheck against the Flask index route
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/', timeout=3)"

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "Control/operatorcontrol.py"]
