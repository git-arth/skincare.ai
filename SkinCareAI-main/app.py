import cv2
import tempfile
from roboflow import Roboflow
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import openai
import os
from dotenv import load_dotenv
from openai import OpenAI
import io
# Load environment variables
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key not found. Please check your .env file.")

rf = Roboflow(api_key="wCHx9674j995X7Bg0jJx")
project = rf.workspace().project("acne-kbm0q-zb6cu")
model = project.version(2).model

client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
)

def capture_image():
    image_path = None
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        cv2.imshow('Take a picture of your acne (Press SPACE to capture, ESC to quit)', frame)

        key = cv2.waitKey(1)
        if key == 32:  # SPACE key
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                cv2.imwrite(temp_file.name, frame)
                image_path = temp_file.name
            break
        elif key == 27:  # ESC key
            break

    cap.release()
    cv2.destroyAllWindows()

    return image_path

def analyze_image(image_path):
    result = model.predict(image_path, confidence=5, overlap=30).json()
    predictions = result['predictions']

    class_counts = {}
    for pred in predictions:
        class_name = pred['class']
        if class_name in class_counts:
            class_counts[class_name] += 1
        else:
            class_counts[class_name] = 1

    if not predictions:
        print("No acne detected.")
        return class_counts, result, None

    # Create the image with bounding boxes
    img = Image.open(image_path)
    fig, ax = plt.subplots(1)
    ax.imshow(img)

    for pred in predictions:
        x, y, width, height = pred['x'], pred['y'], pred['width'], pred['height']
        rect = patches.Rectangle((x - width / 2, y - height / 2), width, height, linewidth=1, edgecolor='r', facecolor='none')
        ax.add_patch(rect)

    # Save the figure to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return class_counts, result, buf

def get_user_input():
    hours_workout = input("Enter the number of hours you workout in a week: ")
    age = input("Enter your age: ")
    skin_type = input("Enter your skin type (e.g., oily, dry, combination): ")
    return hours_workout, age, skin_type

def get_skincare_routine():
    max_steps = 7
    essential_products = ["cleanser", "moisturizer", "sunscreen"]
    available_products = ["cleanser", "moisturizer", "exfoliator", "toner", "essence", "eye cream", "sunscreen"]

    num_steps = int(input(f"Enter the number of steps in your skincare routine (max {max_steps}): "))
    if num_steps > max_steps:
        print(f"Please enter a number less than or equal to {max_steps}.")
        return get_skincare_routine()

    print("Select the products you use in your routine from the following options:")
    for i, product in enumerate(available_products, 1):
        print(f"{i}. {product}")

    selected_products = []
    for _ in range(num_steps):
        choice = int(input("Enter the number corresponding to the product: "))
        if 1 <= choice <= len(available_products):
            selected_products.append(available_products[choice - 1])
        else:
            print("Invalid choice. Please try again.")
            return get_skincare_routine()

    return selected_products

def get_recommendations(class_counts, hours_workout, age, skin_type, skincare_routine):
    essential_products = ["cleanser", "moisturizer", "sunscreen"]
    missing_essentials = [product for product in essential_products if product not in skincare_routine]

    prompt = (
        "You are a dermatologist. Based on the following acne analysis and user information, suggest skincare products:\n"
        "(Please format your response as a list of products with brief explanations and include an Amazon search link for each product)\n\n"
        "Acne Analysis:\n"
    )
    for class_name, count in class_counts.items():
        prompt += f"- {class_name}: {count}\n"
    
    prompt += (
        "\nUser Information:\n"
        f"- Hours Workout: {hours_workout} (Note: Regular exercise can help reduce acne)\n"
        f"- Age: {age} (Note: Teenagers often experience hormonal acne)\n"
        f"- Skin Type: {skin_type} (Note: Different skin types require different care)\n"
        f"- Skincare Routine: {', '.join(skincare_routine)}\n"
    )

    if missing_essentials:
        prompt += (
            "\nNote: The following essential products are missing from the user's routine: "
            f"{', '.join(missing_essentials)}. Please recommend suitable options for these products.\n"
        )

    prompt += (
        "\nApart from the selected products, try incorporating the following into your routine.\n"
        "As a dermatologist, I recommend you provide 3 product recommendations with brief explanations and include an Amazon search link for each product.\n"
        "Please ensure the response is formatted in HTML, using <ul> for lists and <a> for links.\n"
        "For each product, use the format: <a href=\"https://www.amazon.com/s?k=Product+Name\">Product Name</a>.\n"
        "Leave a line between each product and sentence, and use <strong> tags to bold any keywords you think are important.\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}],
        max_tokens=1000  # Adjust this value as needed
    )
    recommendations = response.choices[0].message.content
    recommendations = recommendations.replace('**', '<strong>').replace('**', '</strong>')
    return recommendations

def get_image_source():
    choice = input("Would you like to (1) upload a picture or (2) use your webcam? Enter 1 or 2: ")
    if choice == '1':
        return upload_image()
    elif choice == '2':
        return capture_image()
    else:
        print("Invalid choice. Please enter 1 or 2.")
        return get_image_source()

def upload_image():
    image_path = input("Enter the path to the image file: ")
    if not os.path.exists(image_path):
        print("File not found. Please try again.")
        return upload_image()
    return image_path

if __name__ == "__main__":
    image_path = get_image_source()
    if image_path:
        classes, result = analyze_image(image_path)
        hours_workout, age, skin_type = get_user_input()
        skincare_routine = get_skincare_routine()
        recommendations = get_recommendations(classes, hours_workout, age, skin_type, skincare_routine)
        print(recommendations)
