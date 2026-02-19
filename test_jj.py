import os
import glob
from comfy_api_simplified import ComfyApiWrapper, ComfyWorkflowWrapper

# ── CONFIG ──────────────────────────────────────────────
COMFY_URL = "http://0.0.0.0:7860/"
WORKFLOW_PATH = "workflow_jj_grey_api.json"
INPUT_FOLDER = "jj_d"   # folder containing subfolders
OUTPUT_FOLDER = "jj_d_white_o"             # single output folder
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
# ────────────────────────────────────────────────────────

api = ComfyApiWrapper(COMFY_URL)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Collect all subfolders
subfolders = sorted([
    d for d in os.listdir(INPUT_FOLDER)
    if os.path.isdir(os.path.join(INPUT_FOLDER, d))
])

print(f"Found {len(subfolders)} subfolders to process.\n")

for i, subfolder_name in enumerate(subfolders, 1):
    subfolder_path = os.path.join(INPUT_FOLDER, subfolder_name)

    # Find the first image in the subfolder
    image_path = None
    for f in sorted(os.listdir(subfolder_path)):
        if f.lower().endswith(IMAGE_EXTS):
            image_path = os.path.join(subfolder_path, f)
            break

    if image_path is None:
        print(f"[{i}/{len(subfolders)}] SKIP '{subfolder_name}' — no image found")
        continue

    print(f"[{i}/{len(subfolders)}] Processing '{subfolder_name}' → {os.path.basename(image_path)}")

    # 1) Upload image to ComfyUI server
    uploaded_name = f"{subfolder_name}_{os.path.basename(image_path)}"
    api.upload_image(image_path, uploaded_name)

    # 2) Load workflow fresh each time (so changes don't accumulate)
    wf = ComfyWorkflowWrapper(WORKFLOW_PATH)

    # 3) Point the Load Image node to the uploaded file
    wf.set_node_param("Load Image", "image", uploaded_name)

    # 4) Queue and wait for results
    try:
        results = api.queue_and_wait_images(wf, "Save Image")

        for filename, image_data in results.items():
            # Save with subfolder name as prefix for easy identification
            out_name = f"{subfolder_name}_{filename}"
            out_path = os.path.join(OUTPUT_FOLDER, out_name)
            with open(out_path, "wb") as f:
                f.write(image_data)
            print(f"    ✓ Saved: {out_name}")

    except Exception as e:
        print(f"    ✗ ERROR: {e}")

print(f"\nDone! All outputs saved to: {OUTPUT_FOLDER}")