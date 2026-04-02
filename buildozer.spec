[app]
# Application name and package
title          = O-RAG
package.name   = orag
package.domain = com.yourname

source.dir    = .
source.include_exts = py,png,jpg,kv,atlas,db,gguf
# Include the pre-built ARM64 llama-server binary (no extension)
source.include_patterns = llama-server-arm64
source.exclude_dirs = __pycache__,.git,.venv,venv,.mypy_cache,quantization,bin,p4a-recipes,llama_cpp_src,build_log_dl,build_log_dl2,llamacpp_bin,quantize,evaluation,compressed,.github

version = 1.0.0

# Python dependencies
# Pure-Python packages (certifi, requests, etc.) are pip-installed by p4a.
# Only packages that need C compilation are listed as recipes.
requirements =
    python3,
    kivy==2.3.0,
    hostpython3,
    setuptools,
    sqlite3,
    openssl,
    requests,
    certifi,
    idna,
    charset-normalizer,
    urllib3,
    pypdf,
    plyer,
    huggingface-hub,
    tqdm,
    filelock,
    packaging,
    fsspec

# Android bootstrap
p4a.bootstrap = sdl2

# Orientation: portrait only
orientation = portrait

# Android-specific
android.permissions =
    READ_EXTERNAL_STORAGE,
    WRITE_EXTERNAL_STORAGE,
    MANAGE_EXTERNAL_STORAGE,
    READ_MEDIA_IMAGES,
    READ_MEDIA_VIDEO,
    INTERNET,
    FOREGROUND_SERVICE,
    FOREGROUND_SERVICE_SPECIAL_USE,
    POST_NOTIFICATIONS

# Background service — keeps llama-server alive between app sessions
# Format: Name:path:foreground
android.services = LlamaService:service/main.py:foreground

android.api         = 34
android.minapi      = 26
android.ndk         = 25b
android.ndk_api     = 26
android.archs       = arm64-v8a
android.allow_backup = False

# Extra Java options for 4GB device optimization
# -Xmx512m: Reduced heap for 4GB devices (saves ~256MB vs default)
# -XX:+UseG1GC: G1 garbage collector (better for mobile)
# -XX:MaxGCPauseMillis=100: Shorter GC pauses for responsiveness
# -XX:+UnlockExperimentalVMOptions: Enable experimental optimizations
# -XX:G1NewCollectionPercentThreshold=30: Tune young gen collection
android.add_jvm_options = -Xmx512m,-XX:+UseG1GC,-XX:MaxGCPauseMillis=100

# App icon
icon.filename      = %(source.dir)s/assets/app_icon.png
presplash.filename = %(source.dir)s/assets/app_splash.png

[buildozer]
log_level = 2
warn_on_root = 1
