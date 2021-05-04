from fastapi import Request, File, APIRouter, Depends, status, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
from .. import ocr
import os
import uuid
import json

router = APIRouter(
    tags=['image_extractor'],
    prefix="/extractor"
)

router.mount("/static", StaticFiles(directory='app/static'), name="static")

templates = Jinja2Templates(directory="app/templates")


def _save_file_to_disk(uploaded_file, path="../temp", save_as="default"):
    extension = os.path.splitext(uploaded_file.filename)[-1]
    temp_file = os.path.join(path, save_as + extension)
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)
    return temp_file


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/api/v1/extract_text")
async def extract_text(image: UploadFile = File(...)):
    temp_file = _save_file_to_disk(image, path="app\temp", save_as="temp")
    text = await ocr.read_image(temp_file)
    return {"filename": image.filename, "text": text}


@router.post("/api/v1/bulk_extract_text")
async def bulk_extract_text(request: Request, bg_task: BackgroundTasks):
    images = await request.form()
    folder_name = "app/temp/" + str(uuid.uuid4())
    folder_name = folder_name.replace("/", "\\")
    os.mkdir(folder_name)

    for image in images.values():
        temp_file = _save_file_to_disk(
            image, path=folder_name, save_as=image.filename)

    bg_task.add_task(ocr.read_images_from_dir, folder_name, write_to_file=True)
    return {"task_id": folder_name, "num_files": len(images)}


@router.get('/api/v1/bulk_output/{task_id:path}', name="path-convertor")
async def bulk_output(task_id):
    text_map = {}
    for file_ in os.listdir(task_id):
        if file_.endswith("txt"):
            text_map[file_] = open(os.path.join(task_id, file_)).read()
    return {"task_id": task_id, "output": text_map}