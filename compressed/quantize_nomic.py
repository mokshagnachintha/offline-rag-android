"""
Quantize Nomic Embed Text model for mobile deployment.

Nomic embeddings are small (~80 MB) and fast, but can be further 
quantized to reduce size for highly constrained devices.
"""

import os
import sys
import time
import argparse
from pathlib import Path

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


NOMIC_REPO_ID = "nomic-ai/nomic-embed-text-v1.5-GGUF"
NOMIC_FILE = "nomic-embed-text-v1.5.Q8_0.gguf"  # High precision base


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
    
    print(f"\n📥 Downloading {filename}...")
    print(f"   From: {repo_id}")
    
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


def quantize_nomic(
    input_path: str,
    output_path: str,
    qtype: str = "q4_k_m",
) -> bool:
    """
    Quantize Nomic embedding model.
    
    Args:
        input_path: Path to input GGUF (Q8_0)
        output_path: Path to save quantized model
        qtype: Quantization type (q4_k_m, q5_k_m, q6_k)
    
    Returns:
        True if successful, False otherwise
    """
    if not HAVE_LLAMA_CPP:
        print("❌ llama-cpp-python not installed")
        print("   Install with: pip install llama-cpp-python")
        sys.exit(1)
    
    if not os.path.exists(input_path):
        print(f"❌ Input model not found: {input_path}")
        return False
    
    qtype_lower = qtype.lower()
    valid_types = ["q3_k_m", "q4_k_m", "q5_k_m", "q6_k", "q8_0"]
    
    if qtype_lower not in valid_types:
        print(f"❌ Unknown type: {qtype}")
        print(f"   Valid: {', '.join(valid_types)}")
        return False
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"🔄 NOMIC EMBEDDING QUANTIZATION")
    print(f"{'='*70}")
    print(f"Input:           {input_path}")
    input_size = os.path.getsize(input_path)
    print(f"Input Size:      {format_size(input_size)}")
    print(f"Output:          {output_path}")
    print(f"Format:          {qtype.upper()}")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    
    try:
        qtype_map = {
            "q3_k_m": 26,
            "q4_k_m": 25,
            "q5_k_m": 28,
            "q6_k": 27,
            "q8_0": 7,
        }
        
        qtype_id = qtype_map.get(qtype_lower, 25)
        
        print("⏳ Quantizing Nomic embeddings...")
        llama_cpp.llama_model_quantize(
            input_path.encode("utf-8"),
            output_path.encode("utf-8"),
            llama_cpp.llama_model_quantize_params(qtype=qtype_id)
        )
        
        elapsed = time.time() - start_time
        
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            ratio = input_size / output_size if output_size > 0 else 0
            
            print(f"\n{'='*70}")
            print(f"✅ QUANTIZATION COMPLETE!")
            print(f"{'='*70}")
            print(f"Output Size:     {format_size(output_size)}")
            print(f"Compression:     {ratio:.1f}x")
            print(f"Time:            {elapsed:.1f} seconds")
            print(f"{'='*70}\n")
            
            return True
        else:
            print(f"❌ Output file not created")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Quantize Nomic Embed Text model for mobile deployment",
        epilog="""
Examples:
  python compressed/quantize_nomic.py --download --format q4_k_m
  python compressed/quantize_nomic.py --input nomic-embed-text-v1.5.Q8_0.gguf
        """
    )
    
    parser.add_argument("--input", type=str, default=None,
                        help="Path to input GGUF model")
    parser.add_argument("--output", type=str, default=None,
                        help="Path to save quantized model")
    parser.add_argument("--format", type=str, default="q4_k_m",
                        help="Quantization format (q4_k_m, q5_k_m, q6_k)")
    parser.add_argument("--download", action="store_true",
                        help="Download from HuggingFace Hub")
    parser.add_argument("--no-quantize", action="store_true",
                        help="Download only, don't quantize")
    
    args = parser.parse_args()
    
    if args.download:
        model_path = download_model(NOMIC_REPO_ID, NOMIC_FILE)
        print(f"✅ Downloaded to: {model_path}\n")
        args.input = model_path
    
    if not args.no_quantize:
        if not args.input:
            print("❌ No input model. Use --input or --download")
            sys.exit(1)
        
        if not args.output:
            input_name = Path(args.input).stem
            args.output = f"{input_name}-{args.format.upper()}.gguf"
        
        success = quantize_nomic(args.input, args.output, args.format)
        if success:
            print(f"📦 Done: {args.output}")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
