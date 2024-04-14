import os
import requests
from typing import Optional
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("../../ai_api/webapi/train", StaticFiles(directory="train"), name="train")

templates = Jinja2Templates(directory="templates")

# Создаем папку для хранения загруженных изображений, если она еще не существует
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Страница загрузки
@app.get('/')
async def main(request: Request, response_class=HTMLResponse, data=None):
    return templates.TemplateResponse(
        request=request, name="load.html", context={"data": data}
    )

# Поздгрузка данных от API
# @app.post('/upload/')
# async def upload(request: Request, data):
#     return await main(request, data=data)
# test_response = {
#   "results": [
#     [
#       11221,
#       "Казначейский знак. Россия. 20 рублей. 1917 г.",
#       "Прямоугольной формы.Аверс: в центре герб  России Временного правительства в виде орла без короны, скипетра и державы, с опущенными  вниз крыльями, вверху: «казначейский знак 20 руб.», слева и справа номинал цифрами и прописью: «20 рублей», внизу: «Обязателен к обращению наравне с кредитными билетами».Реверс:  номинал в центре: «20 рублей» и по четырем сторонам: «20», ниже в три строки: «Подделка преследуется законом»Водяной знак: в виде коврика.",
#       "Нумизматика",
#       0
#     ],
#     [
#       11221,
#       "Казначейский знак.",
#       "Казначейский знак. Номинал 20 рублей.",
#       "Нумизматика",
#       0.06597113609313965
#     ],
#     [
#       11221,
#       "Казначейские знаки России достоинством в 20, 40 рублей и Государственный кредитный билет достоинством в 250 рублей.",
#       "nan",
#       "Нумизматика",
#       0.08115226030349731
#     ]
#   ]
# }

# Отправка изобрадения для поиска похожих и получение списка с инфой о изображениях
@app.post("/search/")
async def upload_file(request: Request, file: UploadFile = File(...)):

    api_url = "http://api:8001/search"
    file_image = {'file': file}
    req = requests.post(api_url, files=file_image)

    if req.status_code == 200:
        data = req.json()
        for item in data["results"]:
            img_path = get_image_path(item[0])
            item[0] = img_path
        return await main(request, data=data["results"])
    else:
        return f"Error in sending image {req.status_code}: {req.text}"

    # data = test_response
    # for item in data["results"]:
    #     img_path = get_image_path(item[0])
    #     item[0] = img_path
    # return await main(request, data=data["results"])


    # # Получаем путь для сохранения файла
    # file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    # # Сохраняем файл / отправляем на обработку и получаем массив данных
    # with open(file_location, "wb") as buffer:
    #     buffer.write(await file.read())

    # # Изобрадение поступает из API с моделями в формате 
    # data = [
    #     ['img_1.jpeg', 'name', 'description', 0.0], 
    #     ['img_1.jpeg', 'name', 'description', 0.7],
    #     ['img_1.jpeg', 'name', 'description', 0.9],
    #     ['img_1.jpeg', 'name', 'description', 0.9],
    #     ['img_1.jpeg', 'name', 'description', 0.9],
    #     ['img_1.jpeg', 'name', 'description', 0.9],
    #     ['img_1.jpeg', 'name', 'description', 0.9]
    # ]
    # # Передаем массив данных в функцию main
    # return await main(request, data=data)

# Функция по вытаскиванию картинки по ключу
# async def get_image(key: int):
#     directory_path = os.path.abspath(f"train/{str(key)}")
#     for root, dirs, files in os.walk(directory_path):
#         for file in files:
#             image_path = os.path.join(root, file)
#             return FileResponse(image_path)
#     return {"message": f"No image found with key '{key}"}

@app.post("/get-image-path/")
def get_image_path(key: str):
    # Путь к директории
    directory_path = os.path.abspath(f"../../ai_api/webapi/train/{str(key)}")
    
    # Проверяем, существует ли директория
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        # Ищем все файлы в директории
        files = os.listdir(directory_path)
        
        # Если есть фотографии, возвращаем путь к первой фотографии
        if files:
            first_photo = os.path.join(str(key), files[0])
            return first_photo
        else:
            return None  # Если нет фотографий, возвращаем None
    else:
        return None  # Если директория не существует, возвращаем None
    
@app.get("/reset/")
async def reset_data(request: Request):

    # Возвращаем пользователя на главную страницу
    return RedirectResponse(url="/")