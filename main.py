from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import cv2
import numpy as np

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/results", StaticFiles(directory="results"), name="results")

# Template rendering
templates = Jinja2Templates(directory="templates")

# Folder paths
UPLOAD_FOLDER = 'uploads/'
RESULT_FOLDER = 'results/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Utility Functions
def hitung_kemiringan(point1, point2):
    delta_x = point2[0] - point1[0]
    delta_y = point2[1] - point1[1]
    angle = np.arctan2(delta_y, delta_x) * (180.0 / np.pi)
    return angle

def diagnosa_skoliosis(angle):
    if abs(angle) < 10:
        return "Normal"
    elif 10 <= abs(angle) <= 25:
        return "Skoliosis Ringan"
    else:
        return "Skoliosis Berat"

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a JPG or PNG image.")
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    equalized = cv2.equalizeHist(blurred)
    edges = cv2.Canny(equalized, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        spine_contour = max(contours, key=cv2.contourArea)
        top_point = tuple(spine_contour[spine_contour[:, :, 1].argmin()][0])
        bottom_point = tuple(spine_contour[spine_contour[:, :, 1].argmax()][0])
        angle = hitung_kemiringan(top_point, bottom_point)
        diagnosis = diagnosa_skoliosis(angle)

        img_result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        cv2.line(img_result, top_point, bottom_point, (0, 255, 0), 2)
        cv2.drawContours(img_result, [spine_contour], -1, (255, 0, 0), 2)

        result_filename = f"result_{file.filename}"
        result_path = os.path.join(RESULT_FOLDER, result_filename)
        cv2.imwrite(result_path, img_result)

        return JSONResponse({
            'angle': angle,
            'diagnosis': diagnosis,
            'result_image': result_filename
        })

    else:
        raise HTTPException(status_code=400, detail="Kontur tulang belakang tidak ditemukan.")
