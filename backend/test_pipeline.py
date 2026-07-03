"""
Test script for the Virtual Try-On Modal pipeline.
===================================================
Run individual stages to verify they work before wiring them together.

Usage:
    # Test hello world
    modal run backend/modal_app.py

    # Test background removal with a sample image
    python backend/test_pipeline.py --stage rembg --image path/to/garment.jpg

    # Test pose analysis with a sample image
    python backend/test_pipeline.py --stage pose --image path/to/person.jpg

    # Test full pipeline (once Phase 2 is complete)
    python backend/test_pipeline.py --stage full --person path/to/person.jpg --garment path/to/garment.jpg
"""

import argparse
import sys
import os


def test_rembg(image_path: str):
    """Test Stage 1: background removal via Modal remote call."""
    import modal

    # Get a reference to the deployed function
    remove_bg = modal.Function.from_name("virtual-tryon", "remove_background")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print(f"📤 Sending image ({len(image_bytes)} bytes) to remove_background...")
    result_bytes = remove_bg.remote(image_bytes)

    output_path = os.path.splitext(image_path)[0] + "_no_bg.png"
    with open(output_path, "wb") as f:
        f.write(result_bytes)

    print(f"✅ Background removed! Output saved to: {output_path}")
    print(f"   Output size: {len(result_bytes)} bytes")


def test_pose(image_path: str):
    """Test Stage 2: pose analysis via Modal remote call."""
    import modal
    import json
    import base64

    analyze = modal.Function.from_name("virtual-tryon", "analyze_pose")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print(f"📤 Sending image ({len(image_bytes)} bytes) to analyze_pose...")
    result = analyze.remote(image_bytes)

    if not result.get("person_detected"):
        print(f"❌ No person detected: {result.get('error', 'Unknown error')}")
        return

    print(f"✅ Person detected!")
    print(f"   Image dimensions: {result['image_width']}x{result['image_height']}")
    print(f"   Keypoints found: {len(result['keypoints'])}")

    # Save pose visualization
    if result.get("pose_image_b64"):
        pose_path = os.path.splitext(image_path)[0] + "_pose.png"
        with open(pose_path, "wb") as f:
            f.write(base64.b64decode(result["pose_image_b64"]))
        print(f"   Pose visualization saved to: {pose_path}")

    # Save agnostic mask
    if result.get("agnostic_mask_b64"):
        mask_path = os.path.splitext(image_path)[0] + "_mask.png"
        with open(mask_path, "wb") as f:
            f.write(base64.b64decode(result["agnostic_mask_b64"]))
        print(f"   Agnostic mask saved to: {mask_path}")


def test_hello():
    """Test the hello world function to verify Modal deployment."""
    import modal

    hello = modal.Function.from_name("virtual-tryon", "hello")
    result = hello.remote()
    print(f"🎉 {result}")


def main():
    parser = argparse.ArgumentParser(description="Test Virtual Try-On pipeline stages")
    parser.add_argument(
        "--stage",
        choices=["hello", "rembg", "pose", "full"],
        required=True,
        help="Which pipeline stage to test",
    )
    parser.add_argument("--image", help="Path to input image (for rembg or pose)")
    parser.add_argument("--person", help="Path to person image (for full test)")
    parser.add_argument("--garment", help="Path to garment image (for full test)")

    args = parser.parse_args()

    if args.stage == "hello":
        test_hello()
    elif args.stage == "rembg":
        if not args.image:
            print("❌ --image is required for rembg test")
            sys.exit(1)
        test_rembg(args.image)
    elif args.stage == "pose":
        if not args.image:
            print("❌ --image is required for pose test")
            sys.exit(1)
        test_pose(args.image)
    elif args.stage == "full":
        if not args.person or not args.garment:
            print("❌ --person and --garment are required for full test")
            sys.exit(1)
        print("⏳ Full pipeline test will be available after Phase 2.")


if __name__ == "__main__":
    main()
