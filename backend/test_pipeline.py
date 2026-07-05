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

    # Test full pipeline (HTTP endpoint)
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


def test_full(person_path: str, garment_path: str):
    """Test the full end-to-end pipeline via the HTTP endpoint."""
    import requests
    import base64

    url = "https://m-abdullah-amir--virtual-tryon-tryon-endpoint.modal.run"

    print(f"📤 Sending request to {url}...")
    print("   (First call may take 3-5 mins while GPU warms up — please be patient)")

    with open(person_path, "rb") as p_file, open(garment_path, "rb") as g_file:
        files = {
            "person_image": (os.path.basename(person_path), p_file, "image/png"),
            "garment_image": (os.path.basename(garment_path), g_file, "image/jpeg"),
        }
        data = {
            "mode": "single",
            "category": "upper",
            "tuck_in": "false",
        }

        response = requests.post(url, files=files, data=data, timeout=1200)

    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        return

    result = response.json()

    # Check for success (backend now returns {"success": True, "result_image": "..."})
    if not result.get("success"):
        print(f"❌ Pipeline failed: {result}")
        return

    print("✅ Full pipeline succeeded!")

    # Decode and save the result image
    result_b64 = result.get("result_image")
    if not result_b64:
        print(f"❌ No result_image in response: {result}")
        return

    output_path = "full_pipeline_result.png"
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(result_b64))

    print(f"   Result image saved to: {output_path}")
    print(f"   Image size: {os.path.getsize(output_path):,} bytes")


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
        test_full(args.person, args.garment)


if __name__ == "__main__":
    main()
