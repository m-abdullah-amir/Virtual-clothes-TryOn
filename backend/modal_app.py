"""
NextGen Smart Virtual Try-On — Modal Serverless Backend
========================================================
This file defines the full AI pipeline as Modal serverless functions:
  - Stage 1: Garment background removal (rembg, CPU)
  - Stage 2: Pose/body analysis (MediaPipe, CPU)
  - Stage 3: Try-on generation (CatVTON, GPU) — added in Phase 2
  - Web endpoint: orchestrates the full pipeline

Modal CLI is already authenticated. Deploy with:
    modal deploy backend/modal_app.py
"""

import modal
import io
import base64
import json
from typing import Optional

# ---------------------------------------------------------------------------
# Modal App & Container Images
# ---------------------------------------------------------------------------

app = modal.App("virtual-tryon")

# CPU image for lightweight tasks (rembg + MediaPipe)
cpu_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1-mesa-glx", "libglib2.0-0")
    .pip_install(
        "fastapi[standard]",
        "rembg[gpu]==2.0.57",
        "onnxruntime==1.19.2",
        "mediapipe==0.10.18",
        "opencv-python-headless==4.10.0.84",
        "Pillow==10.4.0",
        "numpy==1.26.4",
    )
    .run_commands(
        "python -c \"import urllib.request, os; os.makedirs(os.path.expanduser('~/.u2net'), exist_ok=True); urllib.request.urlretrieve('https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx', os.path.expanduser('~/.u2net/u2net.onnx'))\""
    )
)

# GPU image for CatVTON — will be defined in Phase 2
# gpu_image = (...)


# ---------------------------------------------------------------------------
# Phase 1: Hello World — verify Modal deployment works
# ---------------------------------------------------------------------------

@app.function(image=cpu_image)
def hello():
    """Simple test function to confirm Modal deployment is working."""
    return "✅ NextGen Virtual Try-On backend is live on Modal!"


# ---------------------------------------------------------------------------
# Stage 1: Garment Background Removal (rembg, CPU)
# ---------------------------------------------------------------------------

@app.function(
    image=cpu_image,
    timeout=300,
    memory=2048,
)
def remove_background(image_bytes: bytes) -> bytes:
    """
    Remove the background from a garment image.

    Args:
        image_bytes: Raw bytes of the garment image (JPG/PNG/WebP).

    Returns:
        PNG bytes of the garment with transparent background.
    """
    from rembg import remove
    from PIL import Image

    # Load the input image
    input_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    # Remove background — rembg returns an RGBA image with transparent bg
    output_image = remove(input_image)

    # Save as PNG to preserve transparency
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    output_buffer.seek(0)

    return output_buffer.getvalue()


# ---------------------------------------------------------------------------
# Stage 2: Pose / Body Analysis (MediaPipe, CPU)
# ---------------------------------------------------------------------------

@app.function(
    image=cpu_image,
    timeout=120,
    memory=2048,
)
def analyze_pose(image_bytes: bytes) -> dict:
    """
    Analyze a person's pose in their photo using MediaPipe.

    This extracts body landmarks needed for accurate garment placement
    by CatVTON. It also generates:
      - An agnostic mask (body region where the garment will be placed)
      - Pose keypoints for the generation model

    Args:
        image_bytes: Raw bytes of the person's full-body photo.

    Returns:
        A dict with:
          - "keypoints": list of {x, y, z, visibility} landmark dicts
          - "pose_image_b64": base64-encoded pose visualization image
          - "agnostic_mask_b64": base64-encoded agnostic mask image
          - "image_width": original image width
          - "image_height": original image height
          - "person_detected": bool — whether a person was found
    """
    import cv2
    import numpy as np
    import mediapipe as mp
    from PIL import Image

    # Load image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return {
            "person_detected": False,
            "error": "Could not decode image",
        }

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]

    # Run MediaPipe Pose
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.5,
    )
    results = pose.process(img_rgb)

    if not results.pose_landmarks:
        pose.close()
        return {
            "person_detected": False,
            "error": "No person detected in the image. Please upload a clear, full-body photo.",
            "image_width": w,
            "image_height": h,
        }

    # Extract keypoints
    landmarks = results.pose_landmarks.landmark
    keypoints = []
    for lm in landmarks:
        keypoints.append({
            "x": lm.x,
            "y": lm.y,
            "z": lm.z,
            "visibility": lm.visibility,
        })

    # Generate pose visualization image
    mp_drawing = mp.solutions.drawing_utils
    pose_img = np.zeros_like(img_rgb)
    mp_drawing.draw_landmarks(
        pose_img,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=3),
        mp_drawing.DrawingSpec(color=(200, 200, 200), thickness=2),
    )

    # Generate agnostic mask — mask the torso/body region where garments go
    agnostic_mask = _generate_agnostic_mask(landmarks, w, h)

    # Encode outputs as base64
    pose_pil = Image.fromarray(pose_img)
    pose_buffer = io.BytesIO()
    pose_pil.save(pose_buffer, format="PNG")
    pose_b64 = base64.b64encode(pose_buffer.getvalue()).decode("utf-8")

    mask_pil = Image.fromarray(agnostic_mask)
    mask_buffer = io.BytesIO()
    mask_pil.save(mask_buffer, format="PNG")
    mask_b64 = base64.b64encode(mask_buffer.getvalue()).decode("utf-8")

    pose.close()

    return {
        "person_detected": True,
        "keypoints": keypoints,
        "pose_image_b64": pose_b64,
        "agnostic_mask_b64": mask_b64,
        "image_width": w,
        "image_height": h,
    }


def _generate_agnostic_mask(landmarks, width: int, height: int) -> "np.ndarray":
    """
    Generate an agnostic mask covering the torso region of the person.

    This mask indicates where the garment should be placed. CatVTON uses
    this to know which body region to inpaint with the garment.

    The mask covers the area from shoulders to hips, which is the primary
    region for upper-body garment try-on.
    """
    import cv2
    import numpy as np

    mask = np.zeros((height, width), dtype=np.uint8)

    # Key body landmarks for torso region
    # MediaPipe indices: 11=left_shoulder, 12=right_shoulder,
    # 23=left_hip, 24=right_hip
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    left_hip = landmarks[23]
    right_hip = landmarks[24]

    # Convert normalized coordinates to pixel coordinates
    # Add padding to capture the full torso area
    padding_x = int(width * 0.05)
    padding_y = int(height * 0.02)

    pts = np.array([
        [int(right_shoulder.x * width) - padding_x,
         int(right_shoulder.y * height) - padding_y],
        [int(left_shoulder.x * width) + padding_x,
         int(left_shoulder.y * height) - padding_y],
        [int(left_hip.x * width) + padding_x,
         int(left_hip.y * height) + padding_y],
        [int(right_hip.x * width) - padding_x,
         int(right_hip.y * height) + padding_y],
    ], dtype=np.int32)

    # Fill the torso polygon on the mask
    cv2.fillConvexPoly(mask, pts, 255)

    # Smooth the mask edges slightly
    mask = cv2.GaussianBlur(mask, (15, 15), 0)
    # Re-threshold after blur to keep a clean mask
    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    return mask


# ---------------------------------------------------------------------------
# Web Endpoint — Full pipeline orchestration (expanded in Phase 2)
# ---------------------------------------------------------------------------

@app.function(image=cpu_image, timeout=300)
@modal.fastapi_endpoint(method="POST")
async def tryon_endpoint(request: "fastapi.Request"):
    """
    Main API endpoint for the virtual try-on pipeline.

    Accepts multipart form data:
      - person_image: file (required)
      - mode: "single" | "complete_outfit" (required)
      - garment_image: file (required if mode="single")
      - top_image: file (required if mode="complete_outfit")
      - bottom_image: file (required if mode="complete_outfit")
      - tuck_in: "true" | "false" (optional)

    Returns:
      - JSON with result_image (base64) on success
      - JSON with error message on failure
    """
    from fastapi.responses import JSONResponse

    try:
        form = await request.form()

        # --- Validate required fields ---
        mode = form.get("mode", "single")
        if mode not in ("single", "complete_outfit"):
            return JSONResponse(
                {"error": "Invalid mode. Must be 'single' or 'complete_outfit'."},
                status_code=400,
            )

        person_file = form.get("person_image")
        if not person_file:
            return JSONResponse(
                {"error": "person_image is required."},
                status_code=400,
            )
        person_bytes = await person_file.read()

        tuck_in = form.get("tuck_in", "false") == "true"

        # --- Get garment image(s) based on mode ---
        if mode == "single":
            garment_file = form.get("garment_image")
            if not garment_file:
                return JSONResponse(
                    {"error": "garment_image is required for single mode."},
                    status_code=400,
                )
            garment_bytes = await garment_file.read()
        else:
            top_file = form.get("top_image")
            bottom_file = form.get("bottom_image")
            if not top_file or not bottom_file:
                return JSONResponse(
                    {"error": "top_image and bottom_image are required for complete_outfit mode."},
                    status_code=400,
                )
            top_bytes = await top_file.read()
            bottom_bytes = await bottom_file.read()

        # --- Stage 1: Remove garment background(s) ---
        if mode == "single":
            garment_clean = remove_background.remote(garment_bytes)
        else:
            # Process top and bottom garments in parallel
            garment_top_future = remove_background.spawn(top_bytes)
            garment_bottom_future = remove_background.spawn(bottom_bytes)
            garment_top_clean = garment_top_future.get()
            garment_bottom_clean = garment_bottom_future.get()

        # --- Stage 2: Analyze pose ---
        pose_result = analyze_pose.remote(person_bytes)

        if not pose_result.get("person_detected", False):
            return JSONResponse(
                {"error": pose_result.get("error", "No person detected in the image.")},
                status_code=400,
            )

        # --- Stage 3: CatVTON generation (Phase 2) ---
        # TODO: Wire up generate_tryon function in Phase 2
        # For now, return a placeholder response confirming pipeline stages work
        return JSONResponse({
            "status": "pipeline_stages_ok",
            "message": "Stages 1 & 2 completed successfully. CatVTON generation (Stage 3) will be wired in Phase 2.",
            "mode": mode,
            "tuck_in": tuck_in,
            "person_detected": True,
            "pose_keypoints_count": len(pose_result.get("keypoints", [])),
            "image_dimensions": f"{pose_result['image_width']}x{pose_result['image_height']}",
        })

    except Exception as e:
        return JSONResponse(
            {"error": f"Pipeline failed: {str(e)}"},
            status_code=500,
        )


# ---------------------------------------------------------------------------
# Local entrypoint for testing individual functions
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main():
    """Quick test: call hello() to verify Modal deployment."""
    result = hello.remote()
    print(result)
