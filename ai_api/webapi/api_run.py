from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import FileResponse
from PIL import Image
import io

import clickhouse_connect

import os
from PIL import Image
from lavis.models import load_model_and_preprocess
from transformers import pipeline

lang_pipe = pipeline("translation", model="Helsinki-NLP/opus-mt-en-ru")

CLICKHOUSE_CLOUD_HOSTNAME = 'clickhouse'
CLICKHOUSE_CLOUD_USER = 'default'
CLICKHOUSE_CLOUD_PASSWORD = ''

IMAGES_PATH = 'train/'

client = clickhouse_connect.get_client(
    host=CLICKHOUSE_CLOUD_HOSTNAME, port=8123, username=CLICKHOUSE_CLOUD_USER, password=CLICKHOUSE_CLOUD_PASSWORD)

client.command(
    'CREATE TABLE IF NOT EXISTS mincult_test (key UInt32 PRIMARY KEY, name String NOT NULL, description String, group String NOT NULL, embedding Array(Float32) NOT NULL) ENGINE MergeTree ORDER BY key')

model, vis_processors, txt_processors = load_model_and_preprocess(name="blip_feature_extractor", model_type="base",
                                                                  is_eval=True)

model_capt, vis_processors_capt, txt_processors_capt = load_model_and_preprocess("blip_caption", model_type="base_coco")

app = FastAPI()


@app.post("/search")
async def search(image: UploadFile = File(...)):
    image_bytes = await image.read()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = vis_processors["eval"](img).unsqueeze(0)
    img = {"image": img, "text_input": [""]}
    embedding = model.extract_features(img, mode="image").image_embeds[0, 0, :].detach().numpy().tolist()

    res = client.query(
        "SELECT key, name, description, group, cosineDistance(embedding, {embed:Array(Float32)}) AS distance FROM mincult_test ORDER BY distance ASC LIMIT 10",
        parameters={'embed': embedding})

    return {"results": res.result_rows}


@app.get("/get")
async def get(key: int):
    res = client.query(
        "SELECT key, name, description, group FROM mincult_test WHERE key={k:UInt32}",
        parameters={'k': key})

    return {"result": res.first_item}


@app.post("/get_image/{key}")
async def get_image(key: int):
    directory_path = os.path.abspath(f"train/{str(key)}")

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            image_path = os.path.join(root, file)
            return FileResponse(image_path)
    return {"message": f"No image found with key '{key}"}


def single_description(raw_image):
    image = vis_processors_capt["eval"](raw_image).unsqueeze(0)
    samples = {"image": image}
    captions = model_capt.generate(samples, num_captions=3, use_nucleus_sampling=True)
    return samples[-1]


@app.post("/caption")
async def generate_caption(image: UploadFile = File(...)):
    image_bytes = await image.read()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    return {"result": single_description(img)}
