# SkinCareAI

Remember to add .env file with API Keys
## Inspiration
As young adults, we have seen so many friends and people around us all facing issues with acne and skincare. One option can be going to the dermatologist but knowing which doctor is the best for you is another task. Plus, we all know from experience that skincare is a long battle where a proper routine and right products are your biggest allies. The inspiration for Skincare.ai is to simplify the challenge of building a proper routine and choosing the right products for you to get the perfect clear skin you always wanted.

## What it does
Step 1: You sign up and provide the app details of your skincare routine, sleep schedule and activity level.
Step 2: You upload a photo of your acne into the app. 
Step 3: The app analyzes your acne, tells you the different types of acne it detects, and recommends the best products for you specifically from a database.
Step 4: You start following the suggested skincare routine and provide photos of your ance's progression for the weekly challenge.
Step 5: You achieve the ideal clear skin you have always wanted!

## How we built it
We built this application using the following tech stack:
Programming Language: Python
Backend Framework
FastAPI: A modern, fast (high-performance) web framework for building APIs with Python.
Web Server
Uvicorn: An ASGI web server implementation for Python, used to run the FastAPI application.
Frontend
Jinja2 Templates: For server-side rendering of HTML pages.
Tailwind CSS: A utility-first CSS framework used for styling the web pages.
HTML and JavaScript: For structuring web content and adding interactivity on the client side.
Machine Learning & AI
OpenAI API: Utilized GPT-4 models to generate ingredient analyses and skincare product recommendations.
Roboflow API: Integrated an acne detection model to analyze user-uploaded facial images.
Image Processing
OpenCV (cv2): For image processing tasks like reading and manipulating images.
Pillow (PIL): Used for image handling and processing.
Matplotlib: For displaying images and plotting detection results.
APIs and External Services
Yelp API: (If applicable in your codebase) To find and display nearby dermatologists.
Data Handling
CSV Files: Used csv module to read skincare product data from files like skincare_products_clean.csv.
JSON Files: Used for storing and retrieving user acne history in acne_history.json.

Environment Management
python-dotenv: Utilized dotenv to manage environment variables securely, such as API keys.
Web Scraping
Requests: For making HTTP requests to external websites.
BeautifulSoup: For parsing HTML content to scrape product ingredients from web pages.
Additional Libraries
Matplotlib Patches: For drawing bounding boxes around detected acne in images.
Tempfile: For handling temporary files securely.
Asyncio: For asynchronous operations within the application.
Logging: To capture and record events and errors during application execution.
Deployment
Uvicorn: Running the FastAPI application as an ASGI server.


## Challenges we ran into
One of our biggest challenges was narrowing our idea down from the list of ideas we had. We knew we wanted to do something applying Computer Vision to Healthcare, but figuring out what specifically was a great task. Some other challenges were with creating an outstanding User Interface. Our team did not have anyone with extensive UI/UX experience. We thus had to get creative, enlist the help of tools and online resources, even teaching ourselves a lot of web design in the process.

## Accomplishments that we're proud of and What's next
After overcoming all these challenges, we came up with something truly remarkable. Skincare.ai solves a real-world problem, a real-need. The app has a very intuitive design, is remarkable in terms of functionality, and has a modern and beautiful user interface. We especially love Skincare.ai's viability in the business world. This can easily be turned into a startup with revenue generated from a subscription based model and affiliates from the products the app recommends its users to buy.
