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

def download_catvton_models():
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id="zhengchong/CatVTON")
    snapshot_download(repo_id="booksforcharlie/stable-diffusion-inpainting")

# GPU image for CatVTON
gpu_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "libgl1-mesa-glx", "libglib2.0-0")
    .pip_install(
        "fastapi[standard]",
        "torch==2.4.0",
        "torchvision==0.19.0",
        "accelerate>=0.31.0",
        "transformers==4.46.3",
        "pillow==10.3.0",
        "numpy==1.26.4",
        "opencv_python==4.10.0.84",
        "scipy==1.13.1",
        "scikit-image==0.24.0",
        "peft>=0.17.0",
        "fvcore",
        "iopath",
        "omegaconf",
        "cloudpickle",
        "pycocotools",
        "av",
        "matplotlib",
        "setuptools>=51.0.0",
        "huggingface_hub>=0.34.0",
        "diffusers==0.30.0"
    )
    .run_function(download_catvton_models)
    .add_local_dir("backend/CatVTON", remote_path="/root/CatVTON")
)


# ---------------------------------------------------------------------------
# Phase 1: Hello World — verify Modal deployment works
# ---------------------------------------------------------------------------

@app.function(image=cpu_image)
def hello():
    """Simple test function to confirm Modal deployment is working."""
    return "✅ NextGen Virtual Try-On backend is live on Modal!"


# ---------------------------------------------------------------------------
# Stage 3: Virtual Try-On Generation (CatVTON, GPU)
# ---------------------------------------------------------------------------

@app.cls(
    image=gpu_image,
    gpu="A10G",
    timeout=600,
    scaledown_window=240,
)
class CatVTONService:
    @modal.enter()
    def load_model(self):
        import sys
        sys.path.append("/root/CatVTON")
        import torch
        import os
        from huggingface_hub import snapshot_download
        from model.pipeline import CatVTONPipeline
        from diffusers.image_processor import VaeImageProcessor
        from model.cloth_masker import AutoMasker

        repo_path = snapshot_download(repo_id="zhengchong/CatVTON")
        
        self.pipeline = CatVTONPipeline(
            base_ckpt="booksforcharlie/stable-diffusion-inpainting",
            attn_ckpt=repo_path,
            attn_ckpt_version="mix",
            weight_dtype=torch.bfloat16,
            use_tf32=True,
            device='cuda',
            skip_safety_check=True,
        )
        
        self.mask_processor = VaeImageProcessor(
            vae_scale_factor=8, do_normalize=False, do_binarize=True, do_convert_grayscale=True
        )
        self.automasker = AutoMasker(
            densepose_ckpt=os.path.join(repo_path, "DensePose"),
            schp_ckpt=os.path.join(repo_path, "SCHP"),
            device='cuda',
        )

    @modal.method()
    def generate(self, person_bytes: bytes, cloth_bytes: bytes, cloth_type: str = "upper") -> bytes:
        import io
        import torch
        from PIL import Image
        import sys
        sys.path.append("/root/CatVTON")
        from utils import resize_and_crop, resize_and_padding

        person_image = Image.open(io.BytesIO(person_bytes)).convert("RGB")
        
        # Use pure white (255, 255, 255) as CatVTON expects strict e-commerce backgrounds
        bg_color = (255, 255, 255)
        cloth_img_raw = Image.open(io.BytesIO(cloth_bytes))
        if cloth_img_raw.mode in ('RGBA', 'LA') or (cloth_img_raw.mode == 'P' and 'transparency' in cloth_img_raw.info):
            cloth_image = Image.new("RGB", cloth_img_raw.size, bg_color)
            if cloth_img_raw.mode == 'RGBA':
                cloth_image.paste(cloth_img_raw, mask=cloth_img_raw.split()[3])
            else:
                cloth_image.paste(cloth_img_raw.convert("RGBA"), mask=cloth_img_raw.convert("RGBA").split()[3])
        else:
            cloth_image = cloth_img_raw.convert("RGB")
        
        width, height = 768, 1024
        person_image = resize_and_crop(person_image, (width, height))
        cloth_image = resize_and_padding(cloth_image, (width, height))

        # Generate Mask automatically
        mask_result = self.automasker(person_image, cloth_type)
        mask = mask_result['mask']
        mask = self.mask_processor.blur(mask, blur_factor=5)
        
        # Inference — all CatVTON defaults for maximum quality
        # guidance_scale=2.5: CatVTON default
        # eta=1.0: CatVTON was trained with stochastic DDIM (eta=1.0), NOT deterministic (eta=0.0)
        #          Using 0.0 constrains the denoiser too much and causes color drift
        result_image = self.pipeline(
            image=person_image,
            condition_image=cloth_image,
            mask=mask,
            num_inference_steps=75,
            guidance_scale=2.5,
            generator=None,
        )[0]
        
        # Repaint the result: paste the generated garment back onto the original resized person image
        # using the mask. This keeps the person's face, hair, hands, and background 100% original
        # and crisp, while only updating the clothing.
        from utils import repaint_result
        final_image = repaint_result(result_image, person_image, mask)
        
        out_buffer = io.BytesIO()
        final_image.save(out_buffer, format="PNG")
        return out_buffer.getvalue()


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
# Stage 4: Background Job Function
# ---------------------------------------------------------------------------

@app.function(image=cpu_image, timeout=1800)
def tryon_job(person_bytes: bytes, garment_bytes: bytes, bottom_bytes: bytes | None, mode: str, tuck_in: bool) -> dict:
    try:
        # 1. Pose estimation (to ensure valid person)
        pose_result = analyze_pose.remote(person_bytes)
        if not pose_result.get("person_detected", False):
            return {"success": False, "error": "Could not detect a person in the image. Please try a clearer full-body photo."}
        
        if mode == "single":
            # Pass raw garment directly. Running remove_background can accidentally 
            # erase parts of white garments or thin fabrics.
            final_bytes = CatVTONService().generate.remote(person_bytes, garment_bytes, cloth_type="upper")
        else:
            # Process top then bottom
            mid_bytes = CatVTONService().generate.remote(person_bytes, garment_bytes, cloth_type="upper")
            final_bytes = CatVTONService().generate.remote(mid_bytes, bottom_bytes, cloth_type="lower")
            
        return {
            "success": True,
            "result_image": base64.b64encode(final_bytes).decode("utf-8")
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Web Endpoints — Full pipeline orchestration with Polling
# ---------------------------------------------------------------------------

import fastapi
from fastapi.responses import JSONResponse

@app.function(image=cpu_image)
@modal.fastapi_endpoint(method="POST")
async def tryon(request: fastapi.Request):
    try:
        form = await request.form()
        mode = form.get("mode", "single")
        person_file = form.get("person_image")
        
        if not person_file:
            return JSONResponse({"error": "person_image is required."}, status_code=400)
        person_bytes = await person_file.read()

        tuck_in = form.get("tuck_in", "false") == "true"

        if mode == "single":
            garment_file = form.get("garment_image")
            if not garment_file:
                return JSONResponse({"error": "garment_image is required."}, status_code=400)
            garment_bytes = await garment_file.read()
            bottom_bytes = None
        else:
            top_file = form.get("top_image")
            bottom_file = form.get("bottom_image")
            if not top_file or not bottom_file:
                return JSONResponse({"error": "top_image and bottom_image required."}, status_code=400)
            garment_bytes = await top_file.read()
            bottom_bytes = await bottom_file.read()

        # Spawn the job in the background and return the job ID
        call = tryon_job.spawn(person_bytes, garment_bytes, bottom_bytes, mode, tuck_in)
        
        return JSONResponse({"status": "processing", "job_id": call.object_id})
    except Exception as e:
        return JSONResponse({"error": f"Failed to start job: {str(e)}"}, status_code=500)


@app.function(image=cpu_image)
@modal.fastapi_endpoint(method="GET")
def status(job_id: str):
    from modal.functions import FunctionCall
    try:
        call = FunctionCall.from_id(job_id)
        try:
            result = call.get(timeout=0) # Non-blocking check
            if result.get("success"):
                return JSONResponse({"status": "completed", "result_image": result["result_image"]})
            else:
                return JSONResponse({"status": "error", "error": result.get("error", "Unknown error")})
        except TimeoutError:
            return JSONResponse({"status": "processing"})
        except Exception as e:
            return JSONResponse({"status": "error", "error": str(e)})
    except Exception as e:
        return JSONResponse({"status": "error", "error": f"Invalid job ID or expired: {str(e)}"})


# ---------------------------------------------------------------------------
# Local entrypoint for testing individual functions
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main():
    """Quick test: call hello() to verify Modal deployment."""
    result = hello.remote()
    print(result)
