"""
Quantize Qwen 3.5 model for mobile deployment.

Supports downloading from HuggingFace and quantizing to various formats:
- Q4_K_M (recommended for 4GB devices) 
- Q5_K_M (higher quality, less compression)
- Q6_K (best quality, larger size)
- Q3_K_M (maximum compression)
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import Optional

try:
    import llama_cpp
    HAVE_LLAMA_CPP = True
except ImportError:
    HAVE_LLAMA_CPP = False

try:
    from huggingface_hub import hf_hub_download
    HAVE_HF_HUB = True
except ImportError:
    HAVE_HF_HUB = False


# ============================================================================
#  Configuration
# ============================================================================

QWEN_REPO_ID = "Qwen/Qwen2.5-7B-Instruct-GGUF"  # Qwen 2.5 7B (no 3.5 yet, using 2.5)
QWEN_FILE = "qwen2.5-7b-instruct-q8_0.gguf"

# Quantization formats (bitrate, compression ratio, quality)
QUANTIZATION_FORMATS = {
    "q3_k_m": {"bits": 3, "compression": 10, "quality": "low", "desc": "Max compression (3-bit)"},
    "q4_k_m": {"bits": 4, "compression": 8, "quality": "good", "desc": "Balanced (4-bit) - RECOMMENDED"},
    "q5_k_m": {"bits": 5, "compression": 6, "quality": "high", "desc": "High quality (5-bit)"},
    "q6_k": {"bits": 6, "compression": 5, "quality": "very_high", "desc": "Very high quality (6-bit)"},
    "q8_0": {"bits": 8, "compression": 2, "quality": "max", "desc": "Near-original (8-bit int)"},
}


# ============================================================================
#  Helpers
# ============================================================================

def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def download_model(repo_id: str, filename: str, local_dir: str = ".") -> str:
    """Download GGUF model from HuggingFace Hub."""
    if not HAVE_HF_HUB:
        print("❌ huggingface_hub not installed. Install with: pip install huggingface-hub")
        sys.exit(1)
    
    print(f"\n📥 Downloading {filename} from {repo_id}...")
    print("   This may take 10-30 minutes depending on model size and connection speed")
    
    try:
        path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
        )
        return path
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)


def quantize_model(
    input_path: str,
    output_path: str,
    qtype: str = "q4_k_m",
) -> bool:
    """
    Quantize a GGUF model to a specified format.
    
    Args:
        input_path: Path to input GGUF model (should be high-precision like q8_0)
        output_path: Path to save quantized model
        qtype: Quantization type (q3_k_m, q4_k_m, q5_k_m, q6_k, q8_0)
    
    Returns:
        True if successful, False otherwise
    """
    if not HAVE_LLAMA_CPP:
        print("❌ llama-cpp-python not installed. Install with: pip install llama-cpp-python")
        sys.exit(1)
    
    if not os.path.exists(input_path):
        print(f"❌ Input model not found: {input_path}")
        return False
    
    qtype_lower = qtype.lower()
    if qtype_lower not in QUANTIZATION_FORMATS:
        print(f"❌ Unknown quantization type: {qtype}")
        print(f"   Valid types: {', '.join(QUANTIZATION_FORMATS.keys())}")
        return False
    
    fmt_info = QUANTIZATION_FORMATS[qtype_lower]
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"🔄 QUANTIZATION: {Path(input_path).name}")
    print(f"{'='*70}")
    print(f"Input:           {input_path}")
    input_size = os.path.getsize(input_path)
    print(f"Input Size:      {format_size(input_size)}")
    print(f"Output:          {output_path}")
    print(f"Format:          {qtype.upper()} - {fmt_info['desc']}")
    print(f"Quality:         {fmt_info['quality']} (≈ {fmt_info['bits']}-bit)")
    print(f"Expected Ratio:  ~1/{fmt_info['compression']}x compression")
    print(f"Expected Size:   ~{format_size(input_size // fmt_info['compression'])}")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    
    try:
        # Get quantization type enum from llama_cpp
        qtype_map = {
            "q3_k_m": 26,  # GGML_TYPE_Q3_K
            "q4_k_m": 25,  # GGML_TYPE_Q4_K
            "q5_k_m": 28,  # GGML_TYPE_Q5_K
            "q6_k": 27,    # GGML_TYPE_Q6_K
            "q8_0": 7,     # GGML_TYPE_Q8_0
        }
        
        qtype_id = qtype_map.get(qtype_lower, 25)  # Default to Q4_K_M
        
        # Call quantization
        print("⏳ Quantizing... (this may take 5-15 minutes)")
        llama_cpp.llama_model_quantize(
            input_path.encode("utf-8"),
            output_path.encode("utf-8"),
            llama_cpp.llama_model_quantize_params(qtype=qtype_id)
        )
        
        elapsed = time.time() - start_time
        
        # Verify output
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            ratio = input_size / output_size
            
            print(f"\n{'='*70}")
            print(f"✅ QUANTIZATION COMPLETE!")
            print(f"{'='*70}")
            print(f"Output Size:     {format_size(output_size)}")
            print(f"Compression:     {ratio:.1f}x (input/output)")
            print(f"Time:            {elapsed:.1f} seconds")
            print(f"Speed:           {format_size(input_size/elapsed)}/sec")
            print(f"Saved:           {format_size(input_size - output_size)}")
            print(f"{'='*70}\n")
            
            return True
        else:
            print(f"❌ Quantization failed: output file not created")
            return False
            
    except Exception as e:
        print(f"❌ Quantization error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Quantize Qwen 3.5 (or other GGUF) models for mobile deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download and quantize Qwen with Q4_K_M format
  python quantize_qwen35.py --download --format q4_k_m
  
  # Quantize existing model
  python quantize_qwen35.py --input qwen2.5-7b-instruct-q8_0.gguf --format q4_k_m
  
  # Download only
  python quantize_qwen35.py --download --no-quantize
  
  # Show available formats
  python quantize_qwen35.py --formats
        """
    )
    
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input GGUF model (high-precision like q8_0)",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save quantized model (default: auto-generate)",
    )
    
    parser.add_argument(
        "--format",
        type=str,
        default="q4_k_m",
        help="Quantization format (default: q4_k_m)",
    )
    
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download Qwen model from HuggingFace Hub",
    )
    
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="Download only, don't quantize",
    )
    
    parser.add_argument(
        "--formats",
        action="store_true",
        help="Show available quantization formats",
    )
    
    parser.add_argument(
        "--repo",
        type=str,
        default=QWEN_REPO_ID,
        help=f"HuggingFace repo ID (default: {QWEN_REPO_ID})",
    )
    
    parser.add_argument(
        "--file",
        type=str,
        default=QWEN_FILE,
        help=f"Model filename in repo (default: {QWEN_FILE})",
    )
    
    args = parser.parse_args()
    
    # Show formats
    if args.formats:
        print("\n📊 Available Quantization Formats:")
        print("=" * 70)
        for fmt, info in QUANTIZATION_FORMATS.items():
            print(f"  {fmt:10s}  {info['desc']:40s}  Quality: {info['quality']}")
        print("=" * 70 + "\n")
        return
    
    # Download if requested
    if args.download:
        print("📦 Preparing to download Qwen model...")
        model_path = download_model(args.repo, args.file, local_dir=".")
        print(f"✅ Model downloaded to: {model_path}\n")
        args.input = model_path
    
    # Quantize
    if not args.no_quantize:
        if not args.input:
            print("❌ No input model specified. Use --input or --download")
            sys.exit(1)
        
        # Generate output path if not specified
        if not args.output:
            input_name = Path(args.input).stem
            args.output = f"{input_name}-{args.format.upper()}.gguf"
        
        success = quantize_model(args.input, args.output, args.format)
        if success:
            print(f"📦 Quantized model ready: {args.output}")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
