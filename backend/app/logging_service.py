import os
import json
from datetime import datetime

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
os.makedirs(LOG_DIR, exist_ok=True)


def save_log(image_bytes: bytes, parsed: dict, orig_filename: str = None) -> dict:
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    base = orig_filename or f'image_{ts}.jpg'
    img_name = f'{ts}_{base}'
    img_path = os.path.join(LOG_DIR, img_name)
    # write image
    with open(img_path, 'wb') as f:
        f.write(image_bytes)
    # write metadata
    meta = {
        'timestamp': ts,
        'image': img_name,
        'parsed': parsed
    }
    meta_name = f'{ts}_{(orig_filename or "image")}.json'
    meta_path = os.path.join(LOG_DIR, meta_name)
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return {'image': img_name, 'meta': meta_name}


def list_logs():
    items = []
    for fn in sorted(os.listdir(LOG_DIR), reverse=True):
        items.append(fn)
    return items


def read_log(name: str):
    path = os.path.join(LOG_DIR, name)
    if not os.path.exists(path):
        return None
    if name.lower().endswith('.json'):
        with open(path, 'r', encoding='utf-8') as f:
            import json
            return json.load(f)
    else:
        return path
