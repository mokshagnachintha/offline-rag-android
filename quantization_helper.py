"""
quantization_helper.py — Optional utility for self-quantizing Qwen 3.5 models.

If official GGUF versions are unavailable, use this helper to download and
quantize Qwen model to GGUF format using llama.cpp.

Usage:
    from quantization_helper import quantize_qwen_to_gguf
    quantize_qwen_to_gguf("Qwen/Qwen2.5-3B-Instruct", "Q4_K_M")
    # Output: ~/O-rag/models/qwen3.5-1b-instruct-q4_k_m.gguf (~1.5GB)

Requires:
    - llama.cpp cloned and built locally
    - convert.py from llama.cpp/convert_hf_to_gguf.py
    - ./quantize binary from llama.cpp build

Prerequisites:
    1. Clone llama.cpp: git clone https://github.com/ggml-org/llama.cpp.git
    2. Build: cd llama.cpp && make
    3. Set PATH to include quantize binary
"""

import subprocess
import os
import tempfile
from pathlib import Path
from typing import Optional


def quantize_qwen_to_gguf(
    model_name: str = "Qwen/Qwen2.5-3B-Instruct",
    quant_type: str = "Q4_K_M",
    output_dir: Optional[str] = None,
    llama_cpp_path: Optional[str] = None,
) -> Path:
    """
    Download Qwen model and quantize to GGUF format.

    Args:
        model_name: HuggingFace model ID (e.g., "Qwen/Qwen2.5-3B-Instruct")
        quant_type: Quantization type (Q4_K_M, Q5_K_M, Q8_0, etc.)
        output_dir: Output directory (default: ~/O-rag/models)
        llama_cpp_path: Path to llama.cpp directory with build artifacts

    Returns:
        Path to generated GGUF file

    Raises:
        RuntimeError: If download, conversion, or quantization fails
    """
    if output_dir is None:
        output_dir = os.path.expanduser("~/O-rag/models")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Step 1: Download model
        print(f"[quantize] Step 1/3: Downloading {model_name}...")
        try:
            result = subprocess.run(
                ["huggingface-cli", "download", model_name, "--local-dir", str(tmpdir)],
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )
            if result.returncode != 0:
                raise RuntimeError(f"Download failed: {result.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "huggingface-cli not found. Install with: pip install huggingface-hub"
            )

        # Step 2: Convert to GGUF
        print("[quantize] Step 2/3: Converting to GGUF format...")

        # Find convert script
        convert_py = None
        if llama_cpp_path:
            llama_cpp_path = Path(llama_cpp_path)
            convert_py = llama_cpp_path / "convert_hf_to_gguf.py"
        else:
            # Try to find it in PATH or common locations
            candidates = [
                Path.cwd() / "convert_hf_to_gguf.py",
                Path.home() / "llama.cpp" / "convert_hf_to_gguf.py",
                Path("/opt/llama.cpp/convert_hf_to_gguf.py"),
            ]
            for cand in candidates:
                if cand.exists():
                    convert_py = cand
                    break

        if not convert_py or not convert_py.exists():
            raise RuntimeError(
                "convert_hf_to_gguf.py not found. "
                "Ensure llama.cpp is cloned and provide llama_cpp_path."
            )

        gguf_path = tmpdir / "model.gguf"
        try:
            result = subprocess.run(
                ["python", str(convert_py), "--model-dir", str(tmpdir), "--outtype", "f16"],
                cwd=str(convert_py.parent),
                capture_output=True,
                text=True,
                timeout=3600,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Conversion failed: {result.stderr}")
        except FileNotFoundError:
            raise RuntimeError("Python not found in PATH")

        # Step 3: Quantize
        print(f"[quantize] Step 3/3: Quantizing to {quant_type}...")

        # Find quantize binary
        quantize_exe = None
        if llama_cpp_path:
            llama_cpp_path = Path(llama_cpp_path)
            # Try common build output locations
            candidates = [
                llama_cpp_path / "quantize",
                llama_cpp_path / "build" / "bin" / "quantize",
                llama_cpp_path / "Release" / "quantize.exe",
                llama_cpp_path / "quantize.exe",
            ]
            for cand in candidates:
                if cand.exists():
                    quantize_exe = cand
                    break

        if not quantize_exe:
            # Try PATH
            try:
                result = subprocess.run(["which", "quantize"], capture_output=True, text=True)
                if result.returncode == 0:
                    quantize_exe = Path(result.stdout.strip())
            except Exception:
                pass

        if not quantize_exe or not quantize_exe.exists():
            raise RuntimeError(
                "quantize binary not found. "
                "Build llama.cpp: cd llama.cpp && make quantize"
            )

        output_path = output_dir / f"qwen3.5-1b-instruct-{quant_type.lower()}.gguf"

        try:
            result = subprocess.run(
                [str(quantize_exe), str(gguf_path), str(output_path), quant_type],
                capture_output=True,
                text=True,
                timeout=3600,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Quantization failed: {result.stderr}")
        except FileNotFoundError:
            raise RuntimeError(f"Quantize binary not found at {quantize_exe}")

        # Verify output
        if not output_path.exists():
            raise RuntimeError(f"Output file not created: {output_path}")

        size_gb = output_path.stat().st_size / (1024**3)
        print(f"✅ Quantization complete!")
        print(f"   Output: {output_path}")
        print(f"   Size: {size_gb:.2f} GB")

        return output_path


if __name__ == "__main__":
    import sys

    # CLI interface
    model = "Qwen/Qwen2.5-3B-Instruct"
    quant = "Q4_K_M"

    if len(sys.argv) > 1:
        model = sys.argv[1]
    if len(sys.argv) > 2:
        quant = sys.argv[2]

    print(f"Quantizing {model} to {quant}...")
    result_path = quantize_qwen_to_gguf(model, quant)
    print(f"Saved to: {result_path}")
