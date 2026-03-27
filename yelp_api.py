import requests
from geopy.geocoders import Nominatim
import openai  # Ensure you have the OpenAI library installed
from openai import OpenAI
import os
from dotenv import load_dotenv
# Set your OpenAI API key
load_dotenv()
client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
)
def get_yelp_data(latitude, longitude, radius, total_results):
    api_key = "bS5CCkvBt0i5l7A6XdjE4HboYkMHFwLfQqG3dYvplvcoh_QnfTG8dLbkDH-Dx7_w82h0F6e1Hf7k_dE6smiQfxC3Mu1cCx9HF5dcFNyfN5Wi7vH5eaP3K9IKeLGmZHYx"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    url = "https://api.yelp.com/v3/businesses/search"

    all_businesses = []
    offset = 0
    limit = 50  # Yelp API allows a maximum of 50 results per request

    while len(all_businesses) < total_results:
        params = {
            "term": "dermatologists",
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "limit": min(limit, 240 - offset),  # Ensure limit + offset <= 240
            "offset": offset
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if response.status_code != 200:
            print(f"Error: API request failed with status code {response.status_code}")
            print(f"Response content: {data}")
            break

        if "businesses" not in data:
            print("Error: 'businesses' key not found in API response")
            print(f"Response content: {data}")
            break

        businesses = data["businesses"]
        all_businesses.extend(businesses)

        if len(businesses) < params["limit"]:
            break  # No more results available

        offset += len(businesses)
        if offset >= 240:  # Yelp API's maximum offset
            break

    return all_businesses[:total_results]

def get_lat_long_from_zip(zip_code):
    geolocator = Nominatim(user_agent="yelp_api")
    location = geolocator.geocode({"postalcode": zip_code, "country": "United States"})
    
    if location:
        return location.latitude, location.longitude
    else:
        print("Error: Could not find location for the given zip code.")
        return None, None

def format_dermatologists(businesses):
    prompt = (
        "Please format the following list of dermatologists into a properly structured HTML list. "
        "Use <ul> for the unordered list and <li> for each list item. "
        "For each dermatologist, include the following information: "
        "- Name (as a clickable link to their Yelp page) "
        "- Rating "
        "- Distance (in miles) "
        "- Location "
        "- Yelp Link (as a clickable link) "
        "Use <strong> tags to bold any keywords you think are important. "
        "Ensure there is a line break after each Yelp link for better readability. "
        "Do not include any additional text or explanations. "
        "Here’s the list:\n\n"
    )
    
    for business in businesses:
        name = business['name']
        rating = business.get('rating', 'N/A')
        distance = business.get('distance', 0) / 1609.34  # Convert meters to miles
        location = ", ".join(business['location']['display_address'])
        url = business.get('url', 'N/A')
        
        # Shorten the Yelp link
        short_url = url.split('?')[0] if url != 'N/A' else 'N/A'
        
        # Add each business to the prompt
        prompt += f"- Name: {name}, Rating: {rating}, Distance: {distance:.2f} miles, Location: {location}, Yelp Link: {short_url}\n"

    # Call the GPT model with the prompt
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Extract the formatted output from the model's response
    formatted_output = response.choices[0].message.content.strip()

    return formatted_output


def main(zip_code):
    latitude, longitude = get_lat_long_from_zip(zip_code)
    if latitude is None or longitude is None:
        return "Error: Could not find location for the given zip code."

    radius = 10000  # Example radius in meters
    total_results = 100  # Example total results desired

    businesses = get_yelp_data(latitude, longitude, radius, total_results)
    sorted_businesses = sorted(businesses, key=lambda x: x.get('rating', 0), reverse=True)

    # Filter businesses with a rating of 4.0 or higher
    high_rated_businesses = [b for b in sorted_businesses if b.get('rating', 0) >= 4.0]

    # Limit to top 10 high-rated businesses
    top_10_high_rated_businesses = high_rated_businesses[:10]

    # Step 1: Get formatted text from GPT
    formatted_text = format_dermatologists(top_10_high_rated_businesses)
    
    # Step 2: Clean the GPT output
    cleaned_output = clean_gpt_output(formatted_text)
    
    return cleaned_output

def clean_gpt_output(gpt_output):
    # Remove markdown code fences
    if gpt_output.startswith("```html"):
        gpt_output = gpt_output[7:]  # Remove the first 7 characters
    if gpt_output.endswith("```"):
        gpt_output = gpt_output[:-3]  # Remove the last 3 characters
    return gpt_output.strip()

if __name__ == "__main__":
    zip_code = input("Enter your zip code: ")
    print(main(zip_code))
