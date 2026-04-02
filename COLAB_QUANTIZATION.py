"""
Google Colab - Qwen Model Quantization Script

This script quantizes Qwen 3.5/2.5 models on Google Colab and allows you to download
the quantized models.

SETUP IN COLAB:
1. Create a new notebook: https://colab.research.google.com
2. Copy-paste each cell code below into separate cells in Colab
3. Run each cell sequentially (Shift+Enter)
4. Download the quantized model at the end

Note: Colab free tier has enough GPU/CPU and 12GB storage for quantization
"""

# ============================================================================
#  CELL 1: Install Dependencies
# ============================================================================

"""
!pip install -q llama-cpp-python --prefer-binary
!pip install -q huggingface-hub tqdm requests
!apt-get install -y -qq cmake ninja-build git

print("✅ Dependencies installed")
"""

# ============================================================================
#  CELL 2: Check Colab Specs
# ============================================================================

"""
import psutil
import os

print("\n" + "="*70)
print("COLAB ENVIRONMENT INFO")
print("="*70)

# Check GPU
import subprocess
gpu_check = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                          capture_output=True, text=True, stderr=subprocess.DEVNULL)
if gpu_check.returncode == 0:
    print(f"GPU: {gpu_check.stdout.strip()}")
else:
    print("GPU: None (CPU only)")

# Check RAM
total_ram = psutil.virtual_memory().total / (1024**3)
print(f"RAM: {total_ram:.1f} GB")

# Check Storage
total_disk = psutil.disk_usage('/').total / (1024**3)
free_disk = psutil.disk_usage('/').free / (1024**3)
print(f"Storage: {total_disk:.1f} GB total, {free_disk:.1f} GB available")

print("="*70 + "\n")
"""

# ============================================================================
#  CELL 3: Download Qwen Model from HuggingFace
# ============================================================================

"""
from huggingface_hub import hf_hub_download
import os
from pathlib import Path

print("\n" + "="*70)
print("DOWNLOADING QWEN MODEL")
print("="*70 + "\n")

# Configuration
REPO_ID = "Qwen/Qwen2.5-7B-Instruct-GGUF"  # Qwen 2.5 7B (smaller than full version)
MODEL_FILE = "qwen2.5-7b-instruct-q8_0.gguf"  # Base high-precision model

print(f"Repository: {REPO_ID}")
print(f"Model File: {MODEL_FILE}")
print(f"Download Size: ~7.3 GB")
print()

model_path = hf_hub_download(
    repo_id=REPO_ID,
    filename=MODEL_FILE,
    local_dir="./models",
    local_dir_use_symlinks=False,
    progress=True,
)

print(f"\n✅ Model downloaded to: {model_path}")
print(f"   Size: {os.path.getsize(model_path) / (1024**3):.2f} GB")
"""

# ============================================================================
#  CELL 4: Quantize Model to Q4_K_M
# ============================================================================

"""
import llama_cpp
import time
import os
from pathlib import Path

print("\n" + "="*70)
print("QUANTIZING MODEL")
print("="*70 + "\n")

# Paths
input_model = "./models/qwen2.5-7b-instruct-q8_0.gguf"
output_model = "./models/qwen2.5-7b-instruct-q4_k_m.gguf"

input_size = os.path.getsize(input_model)
print(f"Input Model:  {Path(input_model).name}")
print(f"Input Size:   {input_size / (1024**3):.2f} GB")
print(f"Output Model: {Path(output_model).name}")
print(f"Format:       Q4_K_M (4-bit, balanced)")
print(f"\nStarting quantization...")
print("-" * 70)

start_time = time.time()

# Quantization type Q4_K_M = 25 in llama_cpp
llama_cpp.llama_model_quantize(
    input_model.encode("utf-8"),
    output_model.encode("utf-8"),
    llama_cpp.llama_model_quantize_params(qtype=25)  # Q4_K_M
)

elapsed = time.time() - start_time

if os.path.exists(output_model):
    output_size = os.path.getsize(output_model)
    ratio = input_size / output_size
    
    print(f"\n{'='*70}")
    print(f"✅ QUANTIZATION COMPLETE!")
    print(f"{'='*70}")
    print(f"Output Size:  {output_size / (1024**3):.2f} GB")
    print(f"Compression: {ratio:.1f}x")
    print(f"Space Saved: {(input_size - output_size) / (1024**3):.2f} GB")
    print(f"Time:        {elapsed / 60:.1f} minutes")
    print(f"Speed:       {input_size / elapsed / (1024**3):.2f} GB/sec")
    print(f"{'='*70}\n")
else:
    print("❌ Quantization failed!")
"""

# ============================================================================
#  CELL 5 (OPTIONAL): Quantize to Other Formats
# ============================================================================

"""
# OPTIONAL: Quantize to multiple formats for comparison

import llama_cpp
import time
import os

formats = {
    "q3_k_m": 26,  # Low compression
    "q5_k_m": 28,  # High quality
    "q6_k": 27,    # Very high quality
}

input_model = "./models/qwen2.5-7b-instruct-q8_0.gguf"

print("\n" + "="*70)
print("QUANTIZING TO MULTIPLE FORMATS")
print("="*70 + "\n")

for fmt_name, fmt_id in formats.items():
    output_model = f"./models/qwen2.5-7b-instruct-{fmt_name}.gguf"
    
    print(f"Starting {fmt_name.upper()}...")
    start = time.time()
    
    llama_cpp.llama_model_quantize(
        input_model.encode("utf-8"),
        output_model.encode("utf-8"),
        llama_cpp.llama_model_quantize_params(qtype=fmt_id)
    )
    
    if os.path.exists(output_model):
        size_gb = os.path.getsize(output_model) / (1024**3)
        elapsed = time.time() - start
        print(f"  ✅ Size: {size_gb:.2f} GB  Time: {elapsed/60:.1f}m\n")
    else:
        print(f"  ❌ Failed\n")
"""

# ============================================================================
#  CELL 6: Download Quantized Model from Colab
# ============================================================================

"""
# Method 1: Using google.colab (easiest)
from google.colab import files
import os

print("\n" + "="*70)
print("DOWNLOADING QUANTIZED MODEL")
print("="*70 + "\n")

# The quantized model
model_file = "./models/qwen2.5-7b-instruct-q4_k_m.gguf"

if os.path.exists(model_file):
    file_size = os.path.getsize(model_file) / (1024**3)
    print(f"Downloading: qwen2.5-7b-instruct-q4_k_m.gguf")
    print(f"Size: {file_size:.2f} GB")
    print(f"\nClick 'Save' when prompted in the download dialog.\n")
    
    files.download(model_file)
    print("✅ Download completed!")
else:
    print("❌ Model file not found. Run quantization cell first.")
"""

# ============================================================================
#  CELL 7 (OPTIONAL): List All Generated Models
# ============================================================================

"""
import os

print("\n" + "="*70)
print("AVAILABLE MODELS")
print("="*70 + "\n")

model_dir = "./models"
if os.path.exists(model_dir):
    models = [f for f in os.listdir(model_dir) if f.endswith('.gguf')]
    
    print(f"{'Filename':<50} {'Size':<15}")
    print("-" * 65)
    
    for model in sorted(models):
        path = os.path.join(model_dir, model)
        size_gb = os.path.getsize(path) / (1024**3)
        print(f"{model:<50} {size_gb:>6.2f} GB")
    
    print("="*65)
else:
    print("No models directory found.")
"""

# ============================================================================
#  CELL 8: Copy to Google Drive (OPTIONAL - for persistent storage)
# ============================================================================

"""
# If you want to save to Google Drive for later use

from google.colab import drive
import shutil
import os

print("\nMounting Google Drive...")
drive.mount('/content/drive')

# Copy quantized model to Drive
model_file = "./models/qwen2.5-7b-instruct-q4_k_m.gguf"
drive_path = "/content/drive/MyDrive/qwen_models/qwen2.5-7b-instruct-q4_k_m.gguf"

if os.path.exists(model_file):
    os.makedirs(os.path.dirname(drive_path), exist_ok=True)
    print(f"\nCopying to Google Drive...")
    shutil.copy(model_file, drive_path)
    print(f"✅ Saved to: {drive_path}")
else:
    print("Model file not found.")
"""

# ============================================================================
#  QUICK START INSTRUCTIONS
# ============================================================================

COLAB_INSTRUCTIONS = """
╔════════════════════════════════════════════════════════════════════════════╗
║                   GOOGLE COLAB QUANTIZATION GUIDE                          ║
╚════════════════════════════════════════════════════════════════════════════╝

STEP 1: Open Google Colab
  → Go to https://colab.research.google.com
  → Click "New notebook"

STEP 2: Create Cells
  → For each code block below, create a new cell (Ctrl+M, then B)
  → Paste the code into each cell
  → OR: Create a single cell and run all code sequentially

STEP 3: Run Cells in Order
  1. Install Dependencies
  2. Check Colab Specs
  3. Download Qwen Model (~7.3 GB, ~5 min)
  4. Quantize Model (Q4_K_M, ~10 min)
  5. Download Quantized Model (~2 GB)

STEP 4: Download
  → When prompted, click "Save" in the download dialog
  → Your quantized model downloads to ~/Downloads/

═════════════════════════════════════════════════════════════════════════════

WHAT YOU GET:
  ✅ qwen2.5-7b-instruct-q4_k_m.gguf (~2.0 GB)
  ✅ 3.6x compression from original (7.3 GB → 2.0 GB)
  ✅ Good quality for mobile RAG
  ✅ ~15-20 minutes total processing

═════════════════════════════════════════════════════════════════════════════

OPTIONAL: Multiple Formats
  → Uncomment CELL 5 to generate Q3_K_M, Q5_K_M, Q6_K formats
  → Takes additional 20-30 minutes
  → Download any format from CELL 6

═════════════════════════════════════════════════════════════════════════════

OPTIONAL: Save to Google Drive
  → Uncomment CELL 8 to save quantized models to Google Drive
  → Persistent storage across sessions
  → Good for multiple projects

═════════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING:

Q: "Out of Memory" error?
A: Colab has enough storage. If you get RAM error, try:
   - Restart runtime (Runtime → Restart runtime)
   - Close other tabs/notebooks
   - Use 1.5B model instead (smaller)

Q: Download stuck?
A: Try Method 2 with Google Drive (CELL 8)
   Or use a direct download link from HuggingFace web

Q: "Build failed" on llama-cpp-python?
A: Run CELL 1 again with: !pip install llama-cpp-python --prefer-binary --force-reinstall

═════════════════════════════════════════════════════════════════════════════

AFTER DOWNLOADING:

1. Place in O-RAG project:
   cp qwen2.5-7b-instruct-q4_k_m.gguf ~/Desktop/O-rag/

2. Update your app to use it:
   python main.py

3. Models auto-load from local if available

═════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(COLAB_INSTRUCTIONS)
