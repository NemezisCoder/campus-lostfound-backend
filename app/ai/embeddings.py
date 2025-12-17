# app/ai/embeddings.py

import io
from functools import lru_cache
from typing import List

import numpy as np
from PIL import Image
import torch
import open_clip


# --- Model loader (cached) ----------------------------------------------------

@lru_cache(maxsize=1)
def _get_clip():
    # NOTE: ViT-B-32 is a good MVP baseline: decent quality, reasonable speed.
    model_name = "ViT-B-32"
    pretrained = "openai"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name, pretrained=pretrained
    )
    model.eval()
    model.to(device)

    return model, preprocess, device


# --- Public API ---------------------------------------------------------------

def embed_image_bytes(data: bytes) -> List[float]:
    """Encode image bytes into a normalized CLIP embedding vector."""
    if not data:
        return []

    model, preprocess, device = _get_clip()

    img = Image.open(io.BytesIO(data)).convert("RGB")
    x = preprocess(img).unsqueeze(0).to(device)

    with torch.no_grad():
        feat = model.encode_image(x)
        feat = feat / feat.norm(dim=-1, keepdim=True)  # normalize for cosine
        vec = feat.squeeze(0).detach().cpu().float().numpy()

    return vec.tolist()


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity for two normalized vectors."""
    if not a or not b:
        return 0.0

    va = np.asarray(a, dtype=np.float32)
    vb = np.asarray(b, dtype=np.float32)

    # If vectors are not normalized for some reason, normalize here safely.
    na = np.linalg.norm(va) + 1e-12
    nb = np.linalg.norm(vb) + 1e-12
    va = va / na
    vb = vb / nb

    return float(np.dot(va, vb))
