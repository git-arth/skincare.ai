import os
import json
import csv
import requests
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import tempfile
import cv2
from roboflow import Roboflow
from dotenv import load_dotenv
import questionary
from bs4 import BeautifulSoup
import openai
from openai import OpenAI
from serpapi import GoogleSearch
# calendar1.py

from nicegui import ui

def get_ui():
    ui.label('This is the Calendar module').classes('text-lg')
    # Add more UI components related to calendar1.py here
    with ui.calendar().props('start-date="2023-01-01"'):
        ui.label('Calendar Component')
# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key not found. Please check your .env file.")

# Set up Roboflow
rf = Roboflow(api_key="wCHx9674j995X7Bg0jJx")
project = rf.workspace().project("acne-kbm0q-zb6cu")
model = project.version(2).model

# Path to the Skincare Products CSV
PRODUCTS_CSV = "skincare_products_clean.csv"

# History file to store weekly acne counts
HISTORY_FILE = "acne_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        if os.path.getsize(HISTORY_FILE) == 0:
            return []  # Return an empty list if the file is empty
        with open(HISTORY_FILE, 'r') as file:
            return json.load(file)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as file:
        json.dump(history, file, indent=2)

def load_products():
    products = []
    with open(PRODUCTS_CSV, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            # Skip empty lines or invalid rows
            if not row['product_name']:
                continue
            # Parse the ingredients string to a list
            ingredients_str = row['clean_ingreds']
            try:
                ingredients = eval(ingredients_str)
                ingredients = [ingredient.strip().lower() for ingredient in ingredients]
            except:
                ingredients = []
            products.append({
                'product_name': row['product_name'],
                'product_url': row['product_url'],
                'product_type': row['product_type'],
                'ingredients': ingredients,
                'price': row['price']
            })
    return products

def categorize_products(products):
    categories = {}
    for product in products:
        category = product['product_type'].capitalize()
        if category not in categories:
            categories[category] = []
        categories[category].append(product)
    return categories

def select_product(categories):
    # Step 1: Select Category
    category = questionary.select(
        "Select the product category:",
        choices=list(categories.keys())
    ).ask()

    if not category:
        print("No category selected. Exiting.")
        return None

    # Step 2: Select Product from Category
    product_choices = [
        product['product_name'] for product in categories[category]
    ]

    product_selection = questionary.select(
        f"Select a product from {category}:",
        choices=product_choices
    ).ask()

    if not product_selection:
        print("No product selected. Exiting.")
        return None

    # Find the selected product details
    selected_product = next(
        (product for product in categories[category] if product['product_name'] == product_selection),
        None
    )

    return selected_product, category

def add_new_product():
    print("\n--- Add a New Skincare Product ---")
    product_name = questionary.text("Enter the product name:").ask()
    product_url = questionary.text("Enter the product URL:").ask()
    product_type = questionary.select(
        "Select the product type:",
        choices=['Cleanser', 'Moisturiser', 'Serum', 'Toner', 'Treatment', 'Mask', 'Oil', 'Peel', 'Other']
    ).ask()

    if not product_name or not product_url or not product_type:
        print("All fields are required. Exiting product addition.")
        return None

    # Scrape ingredients from the product URL
    print("Scraping ingredients from the product URL...")
    ingredients = scrape_ingredients(product_url)
    if not ingredients:
        print("Failed to scrape ingredients. Please ensure the URL is correct and try again.")
        return None

    # Input price
    price = questionary.text("Enter the product price (e.g., £19.99):").ask()
    if not price:
        print("Price is required. Exiting product addition.")
        return None

    # Append the new product to the CSV
    with open(PRODUCTS_CSV, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Format ingredients as a list string
        ingredients_formatted = f"'{str(ingredients)}'"
        writer.writerow([product_name, product_url, product_type, ingredients_formatted, price])

    print(f"Product '{product_name}' added successfully!\n")
    return {
        'product_name': product_name,
        'product_url': product_url,
        'product_type': product_type,
        'ingredients': [ingredient.lower() for ingredient in ingredients],
        'price': price
    }

def scrape_ingredients(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve the product page. Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # This part depends on the website's structure.
        # For lookfantastic.com, ingredients are usually listed under a specific HTML element.
        # You may need to inspect the page to find the correct selectors.

        # Example for lookfantastic.com:
        ingredients_section = soup.find('div', {'class': 'product-ingredients__content'})
        if not ingredients_section:
            print("Could not find the ingredients section on the page.")
            return None

        ingredients_text = ingredients_section.get_text(separator=',').lower()
        # Split ingredients by comma and strip whitespace
        ingredients = [ingredient.strip() for ingredient in ingredients_text.split(',') if ingredient.strip()]
        return ingredients

    except Exception as e:
        print(f"An error occurred while scraping ingredients: {e}")
        return None

def capture_image():
    image_path = None
    cap = cv2.VideoCapture(0)  # 0 is usually the default camera
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None

    print("Press SPACE to capture the image or ESC to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        cv2.imshow('Take a picture of your face', frame)

        key = cv2.waitKey(1)
        if key == 32:  # SPACE key
            # Save the image to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                cv2.imwrite(temp_file.name, frame)
                image_path = temp_file.name
            print(f"Image captured and saved to {image_path}")
            break
        elif key == 27:  # ESC key
            print("Image capture canceled.")
            break

    cap.release()
    cv2.destroyAllWindows()

    return image_path

def analyze_image(image_path):
    result = model.predict(image_path, confidence=5, overlap=30).json()
    predictions = result.get('predictions', [])
    acne_classes = set()
    for prediction in predictions:
        acne_classes.add(prediction['class'])
    print(f"Detected Acne Types: {', '.join(acne_classes)}")
    return list(acne_classes), result

def display_detections(image_path, result):
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
    legend_elements = []
    for prediction in result.get('predictions', []):
        x, y, width, height = prediction['x'], prediction['y'], prediction['width'], prediction['height']
        class_name = prediction['class']
        color = color_map.get(class_name, 'white')
        rect = patches.Rectangle((x - width/2, y - height/2), width, height, linewidth=2, edgecolor=color, facecolor='none')
        ax.add_patch(rect)
        if class_name not in [elem.get_label() for elem in legend_elements]:
            legend_elements.append(patches.Patch(facecolor=color, edgecolor=color, label=class_name))

    # Create legend
    ax.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()
    plt.show()

def get_recommendations(selected_product_name, acne_classes):
    acne_types = ', '.join(acne_classes)
    prompt = (
        f"Based on the increase in acne count and the detected acne types ({acne_types}), "
        f"suggest alternative skincare products to '{selected_product_name}':\n\n"
        "Provide 3 product recommendations with brief explanations, including how each product can help treat the specific acne types detected. "
        "Include the product name, description, and an Amazon link. "
        "Ensure the output is well-formatted in HTML, using <ul> for lists and <a> for links. "
        "For each product, use the format: <a href=\"https://www.amazon.com/s?k=Product+Name\">Product Name</a>. "
        "Leave a line between each product and sentence, and use <strong> tags to bold any keywords you think are important.\n"
    )

    # Initialize the OpenAI client
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY")
    )

    # Use the new chat completion method
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="gpt-4o"
    )

    # Extract the response and replace ** with <strong> tags
    recommendations = chat_completion.choices[0].message.content.strip()
    recommendations = recommendations.replace('**', '<strong>').replace('**', '</strong>')

    # Return only the recommendations without fetching images
    return recommendations, {}

def warn_acne_causing_ingredients(ingredients):
    # Prepare the prompt for the GPT-3.5 model
    prompt = (
        "The following is a list of skincare product ingredients:\n"
        f"{', '.join(ingredients)}\n\n"
        "First, identify and list the ingredients that can help cure specific types of acne. "
        "Then, identify and list only the ingredients that are known to potentially cause acne. "
        "Provide a brief explanation for each ingredient if possible. "
        "Ensure the output is well-formatted in HTML, using <ul> for lists and <strong> tags to bold any keywords you think are important.\n"
    )

    # Initialize the OpenAI client
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY")
    )

    # Use the chat completion method
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="gpt-4o"
    )

    # Extract the response and clean it up
    response = chat_completion.choices[0].message.content.strip()
    response = response.replace('**', '<strong>').replace('**', '</strong>')

    # Remove unwanted lines and HTML markers
    lines = response.splitlines()
    cleaned_response = "\n".join(line for line in lines if line.strip() and not line.startswith("```"))

    print("Ingredients that may cause acne:")
    return cleaned_response

def get_image_for_product(product_name):
    params = {
        "engine": "google_images",
        "q": product_name,
        "api_key": "YOUR_SERPAPI_KEY",
        "num": 1  # Get only one image
    }
    response = requests.get("https://serpapi.com/search.json", params=params)
    data = response.json()
    
    if "images_results" in data:
        image_url = data["images_results"][0]["original"]
        return image_url
    else:
        return None

def main():
    history = load_history()
    products = load_products()
    categorized_products = categorize_products(products)

    while True:
        action = questionary.select(
            "What would you like to do?",
            choices=[
                "Select an existing product and analyze acne",
                "Exit"
            ]
        ).ask()

        if action == "Select an existing product and analyze acne":
            selected_product, category = select_product(categorized_products)

            if not selected_product:
                continue

            print(f"\nSelected Product: {selected_product['product_name']}")
            print(f"Key Ingredients: {', '.join(selected_product['ingredients'])}\n")

            # Warn user about acne-causing ingredients
            warn_acne_causing_ingredients(selected_product['ingredients'])

            # Step: Choose Image Source
            image_source = questionary.select(
                "How would you like to provide the image?",
                choices=[
                    "Upload an image file",
                    "Capture image from webcam"
                ]
            ).ask()

            if image_source == "Upload an image file":
                image_path = questionary.path("Please provide the path to the image file:").ask()
            else:
                print("Please take a picture of your face.")
                image_path = capture_image()

            if image_path is None:
                print("No image provided. Exiting this action.\n")
                continue

            # Step: Analyze Image
            acne_classes, result = analyze_image(image_path)
            print("Detected Acne Types:")
            for acne_class in acne_classes:
                print(f"- {acne_class}")

            # Display detections
            display_detections(image_path, result)

            # Step: Compare with Previous Weeks
            if history:
                previous_acne = history[-1]['acne_count']
                current_acne_count = len(acne_classes)
                if current_acne_count == 0:
                    print("Keep up the good work! No acne detected this week.\n")
                elif current_acne_count < previous_acne:
                    print("Good job! Your acne has reduced this week. The product seems to be working well.\n")
                elif current_acne_count == previous_acne:
                    print(f"Your acne count remains the same at {current_acne_count}. Keep up the routine.\n")
                else:
                    print(f"Noticeably, your acne has increased from {previous_acne} to {current_acne_count}. Consider reviewing your skincare routine.\n")
                    # Step: Get Product Recommendations
                    recommendations, product_images = get_recommendations(selected_product['product_name'], acne_classes)
                    print("Alternative Product Recommendations:")
                    print(recommendations)
                    print("\n")
            else:
                if len(acne_classes) == 0:
                    print("Keep up the good work! No acne detected this week.\n")
                else:
                    print("This is your first entry. Keep tracking your progress weekly.\n")

            # Step: Update History
            history.append({
                'week': len(history) + 1,
                'acne_count': len(acne_classes)
            })
            save_history(history)

            # Clean up the captured image if it was taken from the webcam
            if image_source == "Capture image from webcam":
                os.unlink(image_path)

        elif action == "Exit":
            print("Exiting the application. Goodbye!")
            break



if __name__ == "__main__":
    main()

