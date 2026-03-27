import os
import base64
import time
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pydantic import BaseModel
from typing import List
from PIL import Image
import io
from app import get_recommendations, analyze_image, get_user_input, get_skincare_routine
from challenge import load_products, categorize_products, analyze_image as challenge_analyze_image, get_recommendations as challenge_get_recommendations, warn_acne_causing_ingredients
from yelp_api import get_lat_long_from_zip, get_yelp_data, format_dermatologists, main as yelp_api_main
from fastapi.responses import HTMLResponse, JSONResponse
# ... existing code ...
import matplotlib.pyplot as plt
from matplotlib import patches  # Add this line
import json
import asyncio
import logging

logger = logging.getLogger("uvicorn.error")

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Create uploads directory if it doesn't exist
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class AcneAnalysisResult(BaseModel):
    acne_classes: List[str]
    image: str

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze_acne")
async def analyze_acne(
    request: Request,
    webcam_image: str = Form(...),
    hours_workout: str = Form(...),
    age: str = Form(...),
    skin_type: str = Form(...),
    skincare_routine: List[str] = Form(...)
):
    try:
        # Process the webcam image
        image_data = webcam_image.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        
        # Save the image
        file_path = os.path.join(UPLOAD_DIR, f"webcam_{int(time.time())}.jpg")
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        # Analyze the image
        class_counts, result, analyzed_image_buf = analyze_image(file_path)

        # Get recommendations
        recommendations = get_recommendations(class_counts, hours_workout, age, skin_type, skincare_routine)

        # Convert analyzed image to base64 if available, otherwise use the original image
        if analyzed_image_buf:
            analyzed_image_base64 = base64.b64encode(analyzed_image_buf.getvalue()).decode('utf-8')
        else:
            analyzed_image_base64 = webcam_image.split(",")[1]  # Use the original image data

        return templates.TemplateResponse(
            "acne_analysis_result.html",
            {
                "request": request,
                "acne_classes": list(class_counts.keys()),
                "recommendations": recommendations,
                "image": analyzed_image_base64
            }
        )
    except Exception as e:
        print(f"Error in analyze_acne: {str(e)}")
        return {"error": str(e)}
def create_analyzed_image(image_path, result):
    # Define color map for classes
    color_map = {
        'blackheads': 'blue',
        'dark spot': 'green',
        'nodules': 'red',
        'papules': 'cyan',
        'pustules': 'magenta',
        'whiteheads': 'yellow'
    }

    # Display the image with bounding boxes
    image = Image.open(image_path)
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    ax.imshow(image)
    ax.set_title("Image with Detections")
    ax.axis('off')

    # Draw bounding boxes
    for prediction in result.get('predictions', []):
        x, y, width, height = prediction['x'], prediction['y'], prediction['width'], prediction['height']
        class_name = prediction['class']
        color = color_map.get(class_name, 'white')
        rect = patches.Rectangle((x - width/2, y - height/2), width, height, linewidth=2, edgecolor=color, facecolor='none')
        ax.add_patch(rect)
        ax.text(x - width/2, y - height/2 - 5, class_name, color=color, fontsize=8, weight='bold')

    # Save the analyzed image
    analyzed_image_path = os.path.join(UPLOAD_DIR, f"analyzed_{os.path.basename(image_path)}")
    plt.savefig(analyzed_image_path, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

    return analyzed_image_path
class ZipCode(BaseModel):
    zipcode: str

@app.post("/find_dermatologists", response_class=HTMLResponse)
async def find_dermatologists(zipcode: ZipCode):
    try:
        # Call the synchronous main function in a separate thread
        result = await asyncio.to_thread(yelp_api_main, zipcode.zipcode)
        return HTMLResponse(content=result)
    except Exception as e:
        logger.exception("Error processing find_dermatologists request")
        return HTMLResponse(content=f"<p>Error: {str(e)}</p>")
# Other routes (challenge_analysis, find_dermatologists) remain unchanged
class ChallengeAnalysis(BaseModel):
    product_name: str
    image: UploadFile
@app.get("/get_products", response_class=JSONResponse)
async def get_products():
    products = load_products()
    categorized_products = categorize_products(products)
    return categorized_products

HISTORY_FILE = "acne_history.json"

def load_history():
    try:
        if os.path.exists(HISTORY_FILE) and os.path.getsize(HISTORY_FILE) > 0:
            with open(HISTORY_FILE, 'r') as file:
                return json.load(file)
        else:
            return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {HISTORY_FILE}. Returning empty list.")
        return []


def save_history(history):
    with open(HISTORY_FILE, 'w') as file:
        json.dump(history, file, indent=2)

@app.post("/challenge_analysis")
async def challenge_analysis(
    request: Request,
    product_name: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        # Save the uploaded image
        file_path = os.path.join(UPLOAD_DIR, f"challenge_{int(time.time())}.jpg")
        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # Load products and categorize them
        products = load_products()
        categorized_products = categorize_products(products)

        # Find the selected product
        selected_product = next((product for product in categorized_products[category] if product['product_name'] == product_name), None)

        if not selected_product:
            return {"error": "Selected product not found"}

        # Analyze the image
        acne_classes, result = challenge_analyze_image(file_path)

        # Create the analyzed image with bounding boxes
        analyzed_image_path = create_analyzed_image(file_path, result)

        # Get recommendations
        recommendations, _ = challenge_get_recommendations(selected_product['product_name'], acne_classes)
        ingredient_analysis = warn_acne_causing_ingredients(selected_product['ingredients'])
        # Warn about acne-causing ingredients
        warnings = warn_acne_causing_ingredients(selected_product['ingredients'])

        # Load acne history
        history = load_history()

        # Update history
        current_acne_count = len(acne_classes)
        history.append({
            'week': len(history) + 1,
            'acne_count': current_acne_count
        })
        save_history(history)

        # Generate history output
        history_output = generate_history_output(history)

        # Convert analyzed image to base64 for displaying in HTML
        with open(analyzed_image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

        return templates.TemplateResponse(
            "challenge_analysis_result.html",
            {
                "request": request,
                "acne_classes": acne_classes,
                "recommendations": recommendations,
                "warnings": warnings,
                "ingredient_analysis": ingredient_analysis,
                "image": encoded_image,
                "selected_product": selected_product,
                "history_output": history_output
            }
        )
    except Exception as e:
        print(f"Error in challenge_analysis: {str(e)}")
        return {"error": str(e)}

def create_analyzed_image(image_path, result):
    # Define color map for classes
    color_map = {
        'blackheads': 'blue',
        'dark spot': 'green',
        'nodules': 'red',
        'papules': 'cyan',
        'pustules': 'magenta',
        'whiteheads': 'yellow'
    }

    # Display the image with bounding boxes
    image = Image.open(image_path)
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    ax.imshow(image)
    ax.set_title("Image with Detections")
    ax.axis('off')

    # Draw bounding boxes
    for prediction in result.get('predictions', []):
        x, y, width, height = prediction['x'], prediction['y'], prediction['width'], prediction['height']
        class_name = prediction['class']
        color = color_map.get(class_name, 'white')
        rect = patches.Rectangle((x - width/2, y - height/2), width, height, linewidth=2, edgecolor=color, facecolor='none')
        ax.add_patch(rect)
        ax.text(x - width/2, y - height/2 - 5, class_name, color=color, fontsize=8, weight='bold')

    # Save the analyzed image
    analyzed_image_path = os.path.join(UPLOAD_DIR, f"analyzed_{os.path.basename(image_path)}")
    plt.savefig(analyzed_image_path, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

    return analyzed_image_path

def generate_history_output(history):
    if len(history) == 1:
        return "This is your first entry. Keep tracking your progress weekly."
    
    current_acne_count = history[-1]['acne_count']
    previous_acne_count = history[-2]['acne_count']

    if current_acne_count == 0:
        return "Keep up the good work! No acne detected this week."
    elif current_acne_count < previous_acne_count:
        return f"Good job! Your acne has reduced from {previous_acne_count} to {current_acne_count} this week. The product seems to be working well."
    elif current_acne_count == previous_acne_count:
        return f"Your acne count remains the same at {current_acne_count}. Keep up the routine."
    else:
        return f"Noticeably, your acne has increased from {previous_acne_count} to {current_acne_count}. Consider reviewing your skincare routine."
if __name__ == "__main__":
    port = int(getenv("PORT", 8000))
    uvicorn.run("app.api:app", host="0.0.0.0", port=port, reload=True)

