import base64
import io
import json
import random
import requests
from flask import Flask, request, jsonify
from PIL import Image
import numpy as np

app = Flask(__name__)

LD_API = "http://127.0.0.1:8081"

SCHEDULER_MAP = {
    "DPM++ 2M": "dpm",
    "DPM++ 2M Karras": "dpm_karras",
    "DPM++ 2M SDE": "dpm_sde",
    "DPM++ 2M SDE Karras": "dpm_sde_karras",
    "Euler a": "euler_a",
    "Euler A": "euler_a",
    "Euler a Karras": "euler_a_karras",
    "Euler": "euler",
    "Euler Karras": "euler_karras",
    "LCM": "lcm",
    "DPM++ 2M SDE Heun": "dpm_sde",
    "DPM++ 2M SDE Heun Karras": "dpm_sde_karras",
}


def translate_request(req_json):
    body = {}
    body["prompt"] = req_json.get("prompt", "")
    body["negative_prompt"] = req_json.get("negative_prompt", "")
    body["steps"] = req_json.get("steps", 20)
    body["cfg"] = req_json.get("cfg_scale", 7.5)

    # Fix: If seed is -1, generate a random unsigned 32-bit integer
    seed = req_json.get("seed", -1)
    if seed == -1:
        body["seed"] = random.randint(0, 4294967295)
    else:
        body["seed"] = seed

    w = req_json.get("width", 512)
    h = req_json.get("height", 512)
    if w == h:
        body["size"] = w
    else:
        body["width"] = w
        body["height"] = h

    sampler = req_json.get("sampler_name", "")
    body["scheduler"] = SCHEDULER_MAP.get(sampler, "dpm")

    if "init_images" in req_json and req_json["init_images"]:
        body["image"] = req_json["init_images"][0]
        body["denoise_strength"] = req_json.get("denoising_strength", 0.6)

    return body


def raw_rgb_to_png_base64(raw_b64, width, height, channels=3):
    raw_bytes = base64.b64decode(raw_b64)
    img_array = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(height, width, channels)
    img = Image.fromarray(img_array, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def parse_sse_stream(response):
    final_image = None
    final_seed = -1
    final_width = 512
    final_height = 512

    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        data = json.loads(line[6:])
        event_type = data.get("type")

        if event_type == "complete":
            final_image = data["image"]
            final_seed = data.get("seed", -1)
            final_width = data.get("width", 512)
            final_height = data.get("height", 512)
        elif event_type == "error":
            return None, data.get("message", "Unknown error")

    if not final_image:
        return None, "No image in response"

    png_b64 = raw_rgb_to_png_base64(final_image, final_width, final_height)
    return {
        "images": [png_b64],
        "info": json.dumps({
            "seed": final_seed,
            "width": final_width,
            "height": final_height
        })
    }, None


@app.route("/sdapi/v1/txt2img", methods=["POST"])
def txt2img():
    ld_body = translate_request(request.json)
    resp = requests.post(
        f"{LD_API}/generate", json=ld_body, stream=True, timeout=120
    )
    result, error = parse_sse_stream(resp)
    if error:
        return jsonify({"error": error}), 500
    result["parameters"] = request.json
    return jsonify(result)


@app.route("/sdapi/v1/img2img", methods=["POST"])
def img2img():
    return txt2img()


@app.route("/sdapi/v1/samplers", methods=["GET"])
def samplers():
    return jsonify([
        {"name": s, "aliases": [s], "options": {}}
        for s in SCHEDULER_MAP.keys()
    ])


@app.route("/sdapi/v1/schedulers", methods=["GET"])
def schedulers():
    return jsonify([
        {"name": s, "label": s}
        for s in ["dpm", "dpm_karras", "dpm_sde", "dpm_sde_karras",
                   "euler_a", "euler_a_karras", "euler", "euler_karras", "lcm"]
    ])


@app.route("/sdapi/v1/sd-models", methods=["GET"])
def sd_models():
    return jsonify([{
        "title": "Local Dream Model",
        "model_name": "Local Dream Model",
        "filename": "localdream",
        "hash": "ld",
        "sha256": "ld",
        "config": None
    }])


@app.route("/sdapi/v1/options", methods=["GET"])
def options():
    return jsonify({
        "samples_format": "png",
        "sd_model_checkpoint": "localdream"
    })


@app.route("/sdapi/v1/loras", methods=["GET"])
def loras():
    return jsonify([])


@app.route("/sdapi/v1/upscalers", methods=["GET"])
def upscalers():
    return jsonify([{"name": "None", "model_name": None, "scale": 1}])


@app.route("/sdapi/v1/latent-upscale-modes", methods=["GET"])
def latent_upscale():
    return jsonify([])


@app.route("/", methods=["GET"])
def root():
    return "LD Bridge running"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7866)
