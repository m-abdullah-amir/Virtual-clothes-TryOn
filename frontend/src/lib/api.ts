const MODAL_TRYON_URL = "https://m-abdullah-amir--virtual-tryon-tryon.modal.run";
const MODAL_STATUS_URL = "https://m-abdullah-amir--virtual-tryon-status.modal.run";

export interface TryOnResult {
  success: boolean;
  result_image?: string; // base64-encoded
  error?: string;
}

export async function runTryOn(
  personImage: File,
  garmentImage: File | null,
  bottomImage: File | null = null,
  mode: "single" | "complete_outfit" = "single",
  tuckIn: boolean = false
): Promise<TryOnResult> {
  const formData = new FormData();
  formData.append("person_image", personImage);
  formData.append("mode", mode);
  formData.append("tuck_in", tuckIn.toString());

  if (mode === "single" && garmentImage) {
    formData.append("garment_image", garmentImage);
  } else if (mode === "complete_outfit" && garmentImage && bottomImage) {
    formData.append("top_image", garmentImage);
    formData.append("bottom_image", bottomImage);
  }

  // 1. Submit the job
  const initRes = await fetch(MODAL_TRYON_URL, {
    method: "POST",
    body: formData,
  });

  if (!initRes.ok) {
    const errorText = await initRes.text();
    throw new Error(`Failed to start job: ${initRes.status} - ${errorText}`);
  }

  const initData = await initRes.json();
  if (initData.error) {
    return { success: false, error: initData.error };
  }

  const jobId = initData.job_id;
  if (!jobId) {
    return { success: false, error: "Did not receive a job_id from server" };
  }

  // 2. Poll for completion every 5 seconds
  while (true) {
    await new Promise((resolve) => setTimeout(resolve, 5000));

    const statusRes = await fetch(`${MODAL_STATUS_URL}?job_id=${encodeURIComponent(jobId)}`, {
      method: "GET",
    });

    if (!statusRes.ok) {
      const errorText = await statusRes.text();
      throw new Error(`Failed to check status: ${statusRes.status} - ${errorText}`);
    }

    const statusData = await statusRes.json();

    if (statusData.status === "completed") {
      return {
        success: true,
        result_image: statusData.result_image,
      };
    } else if (statusData.status === "error") {
      return {
        success: false,
        error: statusData.error || "Generation failed",
      };
    }
    // If status is "processing", loop continues
  }
}
