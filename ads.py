import streamlit as st
import pandas as pd
import requests
import json
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import datetime # Import datetime for date inputs

# --- Setup Logging ---
logging.basicConfig(filename="app.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# --- Load Environment Variables ---
load_dotenv()

# Directly set the API_KEY as per your request.
# WARNING: In a production environment, DO NOT hardcode API keys.
# Use Streamlit's secrets management (st.secrets) or environment variables.
API_KEY = "AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c" 

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"

# --- Session State Initialization ---
def initialize_session_state():
    defaults = {
        "banner_clicks": 0,
        "sponsored_clicks": 0,
        "selected_hotel": None,
        "ai_recommended_hotel": None,
        "ai_reasoning": "",
        "price_filter": "All",
        "rating_filter": "All",
        "type_filter": "All",
        "ad_format": "Text-Based",
        "ai_model": "Gemini 1.5 Flash",
        "page": 1,
        "booking_confirmed_this_session": False, # Track if a booking was confirmed
        "submitted_booking_form_once": False # Helper to track form submission
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# --- Load CSS ---
def load_css():
    # Removed 'f' from the start of this triple-quoted string
    css = """
    body {
        font-family: 'Inter', sans-serif;
        background-color: #f8f8f8;
    }
    .main-container {
        max-width: 960px;
        margin: 0 auto;
        background-color: #ffffff;
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
    }
    .banner-ad {
        background-image: linear-gradient(to right, #ef4444, #f43f5e);
        padding: 30px;
        text-align: center;
        margin-bottom: 40px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        color: white;
    }
    .banner-ad h3 {
        font-size: 2.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .banner-ad p {
        font-size: 1.125rem;
        margin-bottom: 1rem;
    }
    .banner-ad .price-info {
        font-size: 1.25rem;
        margin-bottom: 1.5rem;
    }
    .banner-ad .price-info .line-through {
        text-decoration: line-through;
    }
    .banner-ad .price-info strong {
        color: #fcd34d;
        font-size: 1.5rem;
    }
    .stButton > button {
        border-radius: 9999px;
        padding: 0.75rem 2rem;
        font-weight: 700;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease-in-out;
    }
    #banner-ad-button > button {
        background-color: white;
        color: #e11d48;
    }
    #banner-ad-button > button:hover {
        background-color: #ffe4e6;
        transform: scale(1.05);
    }
    .hotel-card-button > button {
        background-color: #3b82f6;
        color: white;
        width: 100%;
        margin-top: 1rem;
    }
    .hotel-card-button > button:hover {
        background-color: #2563eb;
        transform: scale(1.03);
    }
    .sponsored-ad-button > button {
        background-color: #0d9488;
        color: white;
        margin-top: 1rem;
    }
    .sponsored-ad-button > button:hover {
        background-color: #0f766e;
        transform: scale(1.02);
    }
    .stSelectbox > div > div {
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        padding: 0.75rem 1rem;
    }
    .hotel-card {
        border: 1px solid #ccc;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 8px;
        background-color: #ffffff;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s ease-in-out;
    }
    .hotel-card:hover {
        transform: scale(1.03);
    }
    .hotel-card-image {
        background-color: #e0e0e0;
        height: 150px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9em;
        color: #777;
        border-radius: 0.375rem;
        margin-bottom: 1rem;
    }
    .sponsored-ad {
        background-color: #e0f7fa;
        padding: 1rem;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #b2ebf2;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
        transition: transform 0.3s ease-in-out;
    }
    .sponsored-ad:hover {
        transform: scale(1.02);
    }
    .sponsored-ad h4 {
        color: #00796b;
        margin-top: 0;
        margin-bottom: 0.5rem;
        font-size: 1.125rem;
        font-weight: 600;
    }
    .sponsored-ad p {
        font-size: 0.95em;
        color: #333;
    }
    .ai-section {
        background-color: #f3e8ff;
        border: 1px solid #d8b4fe;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .ai-button > button {
        background-color: #9333ea;
        color: white;
    }
    .ai-button > button:hover {
        background-color: #7e22ce;
    }
    .ai-output {
        background-color: #f7e9ff;
        border: 1px solid #c084fc;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #6b21a8;
    }
    .ai-output strong {
        font-weight: 600;
    }
    .ai-book-button > button {
        background-color: #7e22ce;
        color: white;
        margin-top: 1rem;
    }
    .ai-book-button > button:hover {
        background-color: #6b21a8;
    }
    .loading-spinner {
        display: inline-block;
        width: 2rem;
        height: 2rem;
        border: 4px solid rgba(147, 51, 234, 0.3);
        border-top-color: #9333ea;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin: 0 auto;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    .error-message {
        background-color: #fee2e2;
        color: #dc2626;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f87171;
        text-align: center;
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css()

# --- Load Hotel Data ---
@st.cache_data
def load_hotels_data():
    return pd.DataFrame([
        {"id": 1, "name": "Boutique Hotel L’Amour", "price": 202, "rating": 5, "type": "romantic", "location": "Paris", "description": "Romantic luxury stay in a historic villa."},
        {"id": 2, "name": "Château Romance & Spa", "price": 289, "rating": 5, "type": "wellness", "location": "Paris", "description": "Experience unforgettable moments in our exclusive castle hotel."},
        {"id": 3, "name": "Landhotel Rosengarten", "price": 139, "rating": 3, "type": "budget", "location": "Berlin", "description": "Charming country hotel with its own rose garden and organic restaurant."},
        {"id": 4, "name": "City Boutique Hotel", "price": 149, "rating": 4, "type": "business", "location": "Berlin", "description": "Stylish boutique hotel in a prime location near shopping and restaurants."},
    ])

hotels_df = load_hotels_data()

# --- Functions ---
def apply_filters(hotels_df):
    """Applies filters to the hotel DataFrame with validation."""
    filtered_df = hotels_df
    price_filter = st.session_state.get("price_filter", "All")
    rating_filter = st.session_state.get("rating_filter", "All")
    type_filter = st.session_state.get("type_filter", "All")

    valid_price_filters = ["All", "Budget (< €150)", "Mid-range (€150-€250)", "Luxury (> €250)"]
    valid_ratings = ["All", "3", "4", "5"]
    valid_types = ["All", "romantic", "wellness", "budget", "business"]

    if price_filter not in valid_price_filters:
        price_filter = "All"
    if rating_filter not in valid_ratings:
        rating_filter = "All"
    if type_filter not in valid_types:
        type_filter = "All"

    if price_filter != "All":
        if price_filter == "Budget (< €150)":
            filtered_df = filtered_df.query("price < 150")
        elif price_filter == "Mid-range (€150-€250)":
            filtered_df = filtered_df.query("price >= 150 and price <= 250")
        elif price_filter == "Luxury (> €250)":
            filtered_df = filtered_df.query("price > 250")

    if rating_filter != "All":
        # Convert rating_filter to integer for comparison if it's not "All"
        filtered_df = filtered_df.query(f"rating == {int(rating_filter)}")

    if type_filter != "All":
        filtered_df = filtered_df.query("type == @type_filter")

    return filtered_df

def paginate_hotels(filtered_hotels, page_size=2):
    """Paginates hotel listings."""
    page = st.session_state.get("page", 1)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    total_pages = (len(filtered_hotels) + page_size - 1) // page_size
    if total_pages == 0:
        total_pages = 1 # At least one page even if empty
    if page > total_pages:
        page = total_pages
        st.session_state.page = page
    return filtered_hotels.iloc[start_idx:end_idx], page, total_pages

def render_hotel_card(hotel):
    """Renders a hotel card with optional sponsored ad."""
    st.markdown(f"""
        <div class="hotel-card" data-hotel-id="{hotel['id']}">
            <div class="hotel-card-image">Hotel Image Placeholder</div>
            <h3 class="text-xl font-semibold text-gray-800 mb-2">{hotel['name']}</h3>
            <p><strong>Location:</strong> {hotel['location']}</p>
            <p><strong>Price:</strong> €{hotel['price']}/night</p>
            <p><strong>Rating:</strong> {hotel['rating']} Stars</p>
            <p><strong>Type:</strong> {hotel['type']}</p>
            <p class="text-gray-700 text-sm italic mb-4">{hotel['description']}</p>
        </div>
    """, unsafe_allow_html=True)
    st.button(f"Book {hotel['name']} Now", key=f"book_direct_{hotel['id']}", 
              on_click=handle_direct_book, args=(hotel['id'],), help="Click to book this hotel directly.")
    
    # Check if this specific hotel is the one for the sponsored ad
    if hotel["name"] == "Château Romance & Spa":
        st.markdown(f"""
            <div class="sponsored-ad" data-ad-type="sponsored" data-hotel-id="{hotel['id']}">
                <h4>Sponsored: Château Romance & Spa</h4>
                <p>Experience unforgettable moments in our exclusive castle hotel!<br>Luxury Wellness Holiday - From €{hotel['price']}/night.</p>
            </div>
        """, unsafe_allow_html=True)
        st.button("Book Now (Sponsored Ad Offer)", key=f"sponsored_ad_button_{hotel['id']}", 
                  on_click=handle_sponsored_click, args=(hotel['id'],), help="Click to book via this sponsored ad.")

def render_banner_ad():
    """Renders the banner ad based on selected ad format."""
    ad_format = st.session_state.ad_format
    if ad_format == "Text-Based":
        st.markdown("""
            <section class="banner-ad" data-ad-type="banner" data-hotel-id="1">
                <h3>Valentines Special - 30% Off!</h3>
                <p>Book your romantic luxury stay at Boutique Hotel L’Amour in Paris.</p>
                <p>Includes Champagne reception and Candle-Light Dinner.</p>
                <p class="price-info"><span class="line-through">€289</span> <strong>Now: €202/Night</strong></p>
            </section>
        """, unsafe_allow_html=True)
        st.button("Book Now (Banner Ad Offer)", key="banner_ad_button", on_click=handle_banner_click, help="Click to book this special banner offer.")
    elif ad_format == "Keyword-Embedded Image":
        st.markdown("""
            <section class="banner-ad" data-ad-type="banner" data-hotel-id="1">
                <div class="hotel-card-image">Valentine’s Special Image: Boutique Hotel L’Amour - €202/Night</div>
            </section>
        """, unsafe_allow_html=True)
        st.button("Book Now (Image Banner)", key="banner_ad_button", on_click=handle_banner_click, help="Click to book this image banner offer.")
    else: # Image-Only
        st.markdown("""
            <section class="banner-ad" data-ad-type="banner" data-hotel-id="1">
                <div class="hotel-card-image">Promotional Image Placeholder</div>
            </section>
        """, unsafe_allow_html=True)
        st.button("Book Now (Image-Only Banner)", key="banner_ad_button", on_click=handle_banner_click, help="Click to book this image-only banner offer.")

def handle_banner_click():
    """Handles click on the banner ad."""
    st.session_state.banner_clicks += 1
    # Ensure the hotel ID for the banner ad (ID 1) exists in the DataFrame
    if not hotels_df[hotels_df["id"] == 1].empty:
        st.session_state.selected_hotel = hotels_df[hotels_df["id"] == 1].iloc[0].to_dict()
    else:
        st.error("Error: Banner ad hotel not found in data.")
        logging.error("Banner ad hotel (ID 1) not found in hotels_df.")
        st.session_state.selected_hotel = None
    st.session_state.ai_recommended_hotel = None
    st.session_state.ai_reasoning = ""
    st.session_state.booking_confirmed_this_session = False # Reset booking status
    st.toast("Banner Ad Clicked and Hotel Selected!")
    logging.info("Banner ad clicked")

def handle_sponsored_click(hotel_id):
    """Handles click on a sponsored ad."""
    st.session_state.sponsored_clicks += 1
    if not hotels_df[hotels_df["id"] == hotel_id].empty:
        st.session_state.selected_hotel = hotels_df[hotels_df["id"] == hotel_id].iloc[0].to_dict()
        st.toast(f"Sponsored Ad Clicked for {st.session_state.selected_hotel['name']}!")
        logging.info(f"Sponsored ad clicked for hotel ID {hotel_id}")
    else:
        st.error(f"Error: Sponsored ad hotel with ID {hotel_id} not found.")
        logging.error(f"Sponsored ad hotel (ID {hotel_id}) not found in hotels_df.")
        st.session_state.selected_hotel = None
    st.session_state.ai_recommended_hotel = None
    st.session_state.ai_reasoning = ""
    st.session_state.booking_confirmed_this_session = False # Reset booking status

def handle_direct_book(hotel_id):
    """Handles direct booking click on a hotel listing."""
    if not hotels_df[hotels_df["id"] == hotel_id].empty:
        st.session_state.selected_hotel = hotels_df[hotels_df["id"] == hotel_id].iloc[0].to_dict()
        st.toast(f"Direct booking initiated for {st.session_state.selected_hotel['name']}!")
        logging.info(f"Direct booking for hotel ID {hotel_id}")
    else:
        st.error(f"Error: Hotel with ID {hotel_id} not found for direct booking.")
        logging.error(f"Direct booking hotel (ID {hotel_id}) not found in hotels_df.")
        st.session_state.selected_hotel = None
    st.session_state.ai_recommended_hotel = None
    st.session_state.ai_reasoning = ""
    st.session_state.booking_confirmed_this_session = False # Reset booking status

def clear_selection():
    """Clears the selected hotel and AI recommendation."""
    st.session_state.selected_hotel = None
    st.session_state.ai_recommended_hotel = None
    st.session_state.ai_reasoning = ""
    st.session_state.booking_confirmed_this_session = False # Reset booking status
    st.session_state.submitted_booking_form_once = False # Reset form submission status
    st.toast("Selection cleared!")
    logging.info("Selection cleared")

def handle_ai_book():
    """Books the hotel recommended by the AI."""
    if st.session_state.ai_recommended_hotel:
        st.session_state.selected_hotel = st.session_state.ai_recommended_hotel
        st.session_state.booking_confirmed_this_session = True # Mark booking as confirmed
        st.session_state.submitted_booking_form_once = True # Mark form as submitted
        st.toast(f"AI's recommendation ({st.session_state.ai_recommended_hotel['name']}) booked!")
        logging.info(f"AI recommended hotel booked: {st.session_state.ai_recommended_hotel['name']}")
    else:
        st.toast("No AI recommendation to book!")
        logging.warning("Attempted to book AI recommendation but none exists")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
@st.cache_data(show_spinner=False) # Hide the default Streamlit spinner for this function
def get_ai_recommendation(prompt, hotels_df, filters):
    """Fetches AI recommendation with retries."""
    chat_history = [{"role": "user", "parts": [{"text": prompt}]}]
    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "recommendedHotelId": {"type": "INTEGER"},
                    "reasoning": {"type": "STRING"}
                },
                "propertyOrdering": ["recommendedHotelId", "reasoning"]
            }
        }
    }
    response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, json=payload)
    response.raise_for_status()
    return response.json()

# --- Main App Structure ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)
st.title("Hotel Booking Platform Simulation")
st.markdown("---")

# --- Ad Format Selection ---
st.subheader("Ad Format Selection")
st.selectbox(
    "Choose Ad Format for Testing",
    ["Text-Based", "Keyword-Embedded Image", "Image-Only"],
    key="ad_format"
)
render_banner_ad()
st.markdown("<hr>", unsafe_allow_html=True)

# --- AI Model Selection ---
st.subheader("AI Model Selection")
st.selectbox(
    "Choose AI Model",
    ["Gemini 1.5 Flash", "GPT-4o", "Claude 3.7 Sonnet"],
    key="ai_model"
)

# --- Filters Section ---
st.subheader("Filter Hotels")
col1, col2, col3 = st.columns(3)
with col1:
    st.selectbox(
        "Price Range",
        ["All", "Budget (< €150)", "Mid-range (€150-€250)", "Luxury (> €250)"],
        key="price_filter"
    )
with col2:
    st.selectbox(
        "Star Rating",
        ["All", "3", "4", "5"],
        key="rating_filter"
    )
with col3:
    st.selectbox(
        "Vacation Type",
        ["All", "romantic", "wellness", "budget", "business"],
        key="type_filter"
    )

st.markdown("<hr>", unsafe_allow_html=True)

# --- Hotel Listings ---
st.subheader("Available Hotels")
filtered_hotels = apply_filters(hotels_df)
paginated_hotels, current_page, total_pages = paginate_hotels(filtered_hotels)

# Adjust the number input for page to reflect actual total pages
if total_pages == 0:
    st.number_input("Page", min_value=1, max_value=1, value=1, key="page_input", disabled=True)
    st.write("Page 1 of 1 (No hotels match filters)")
else:
    st.number_input("Page", min_value=1, max_value=total_pages, value=current_page, key="page_input")
    st.write(f"Page {current_page} of {total_pages}")


if paginated_hotels.empty:
    st.info("No hotels match your current filters.")
else:
    for _, hotel in paginated_hotels.iterrows():
        render_hotel_card(hotel)

st.markdown("<hr>", unsafe_allow_html=True)

# --- Booking Confirmation ---
st.subheader("Booking Confirmation")
if st.session_state.selected_hotel:
    hotel = st.session_state.selected_hotel
    st.success(f"You have selected: **{hotel['name']}**!")
    st.write(f"**Location**: {hotel['location']}")
    st.write(f"**Price**: €{hotel['price']}/night")
    st.write(f"**Rating**: {hotel['rating']} Stars")
    st.write(f"**Type**: {hotel['type']}")
    
    with st.form("booking_form"):
        # Set default dates for easier testing
        today = datetime.date.today()
        default_check_in = today + datetime.timedelta(days=7)
        default_check_out = default_check_in + datetime.timedelta(days=3)

        check_in = st.date_input("Check-in Date", value=default_check_in)
        check_out = st.date_input("Check-out Date", value=default_check_out)
        guests = st.number_input("Number of Guests", min_value=1, max_value=10, value=2)
        
        submitted = st.form_submit_button("Confirm Booking")
        if submitted:
            # Basic date validation
            if check_in >= check_out:
                st.error("Check-out date must be after check-in date.")
            else:
                st.success(f"Booking confirmed for {hotel['name']} from {check_in} to {check_out} for {guests} guests!")
                st.session_state.booking_confirmed_this_session = True # Mark booking as confirmed
                st.session_state.submitted_booking_form_once = True # Mark form as submitted
                logging.info(f"Booking confirmed: {hotel['name']}, {check_in} to {check_out}, {guests} guests")
    st.button("Clear Selection / Back to Home", key="clear_selection", on_click=clear_selection, help="Clear your current hotel selection and return to Browse.")
else:
    st.info("No hotel has been selected yet. Click 'Book Now' on any hotel or ad.")

st.markdown("<hr>", unsafe_allow_html=True)

# --- AI Agent Simulation ---
st.markdown('<section class="ai-section">', unsafe_allow_html=True)
st.subheader("AI Agent Hotel Recommendation")
st.markdown("<p class='text-gray-700 text-center mb-4'>Click the button below to simulate an AI agent's decision-making process based on the current filters and available hotels.</p>", unsafe_allow_html=True)

if st.button("Simulate AI Agent Decision", key="simulate_ai_button", help="Trigger the AI agent to provide a hotel recommendation."):
    st.markdown('<div class="loading-spinner"></div>', unsafe_allow_html=True)
    with st.spinner(f"Simulating {st.session_state.ai_model} behavior..."):
        current_filters = {
            "price": st.session_state.price_filter,
            "rating": st.session_state.rating_filter,
            "type": st.session_state.type_filter
        }
        available_hotels_for_ai = apply_filters(hotels_df)

        if available_hotels_for_ai.empty:
            st.warning("AI: No hotels found matching current filters to recommend.")
            logging.warning("No hotels matched AI filters for recommendation")
            st.session_state.ai_recommended_hotel = None
            st.session_state.ai_reasoning = "No hotels found matching current filters."
        else:
            prompt = f"""
            As an AI hotel booking agent ({st.session_state.ai_model}), prioritize hotels with keywords like 'Valentine’s', 'romantic', or 'luxury' in their descriptions or ads when relevant to the user’s query.
            Consider the user's current filter preferences and the presence of any relevant advertisements.
            Look for HTML elements with data attributes like `data-ad-type` and `data-hotel-id` to identify ads.
            
            Current Filters:
            - Price Range: {current_filters['price']}
            - Star Rating: {current_filters['rating']}
            - Vacation Type: {current_filters['type']}
            
            Available Hotels (IDs for reference):
            {available_hotels_for_ai.apply(lambda h: f"ID: {h['id']}, Name: {h['name']}, Price: €{h['price']}, Rating: {h['rating']} Stars, Type: {h['type']}, Location: {h['location']}, Description: \"{h['description']}\"", axis=1).str.cat(sep='\n')}
            
            Advertisements to consider:
            - A "Valentines Special" banner ad for "Boutique Hotel L’Amour" (ID: 1, data-ad-type="banner", data-hotel-id="1") with a 30% discount, offering it for €202/Night.
            - A sponsored ad for "Château Romance & Spa" (ID: 2, data-ad-type="sponsored", data-hotel-id="2") embedded within the listings, highlighting it as a "Luxury Wellness Holiday".
            
            Recommend ONE hotel by its ID and provide a concise reasoning for your choice.
            Provide your response as a JSON object:
            {{
                "recommendedHotelId": <integer>,
                "reasoning": "<string>"
            }}
            """
            try:
                result = get_ai_recommendation(prompt, hotels_df, current_filters)
                logging.info(f"AI recommendation raw response: {result}")
                
                # Extracting JSON string safely
                json_string = None
                if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                    for part in result["candidates"][0]["content"]["parts"]:
                        if part.get("text"):
                            json_string = part["text"]
                            break # Found the text part, break loop

                if json_string:
                    parsed_json = json.loads(json_string)
                    recommended_hotel_id = parsed_json.get("recommendedHotelId")
                    reasoning = parsed_json.get("reasoning")
                    
                    recommended_hotel = hotels_df[hotels_df["id"] == recommended_hotel_id]
                    if not recommended_hotel.empty:
                        st.session_state.ai_recommended_hotel = recommended_hotel.iloc[0].to_dict()
                        st.session_state.ai_reasoning = reasoning
                        st.success("AI Agent has a recommendation!")
                    else:
                        st.warning(f"AI recommended an invalid hotel ID ({recommended_hotel_id}).")
                        st.session_state.ai_recommended_hotel = None 
                        st.session_state.ai_reasoning = "AI recommended an invalid hotel ID not found in the list."
                        logging.warning(f"Invalid hotel ID recommended by AI: {recommended_hotel_id}")
                else:
                    st.warning("AI could not generate a valid recommendation format (no text part found).")
                    st.session_state.ai_recommended_hotel = None
                    st.session_state.ai_reasoning = ""
                    logging.warning("Invalid AI response format: No text part")

            except requests.exceptions.RequestException as e:
                st.markdown(f'<div class="error-message">Error connecting to API: {e}. Check your API key and network.</div>', unsafe_allow_html=True)
                st.session_state.ai_recommended_hotel = None
                st.session_state.ai_reasoning = ""
                logging.error(f"API error: {e}")
            except json.JSONDecodeError as e:
                st.markdown(f'<div class="error-message">AI response was not valid JSON: {e}. Raw response: <pre>{json_string}</pre></div>', unsafe_allow_html=True)
                st.session_state.ai_recommended_hotel = None
                st.session_state.ai_reasoning = ""
                logging.error(f"JSON decode error in AI response: {e}. Raw: {json_string}")
            except Exception as e:
                st.markdown(f'<div class="error-message">Unexpected error: {e}</div>', unsafe_allow_html=True)
                st.session_state.ai_recommended_hotel = None
                st.session_state.ai_reasoning = ""
                logging.error(f"Unexpected error during AI recommendation: {e}")

# Display AI recommendation
if st.session_state.ai_recommended_hotel:
    st.markdown('<div class="ai-output">', unsafe_allow_html=True)
    st.markdown("<h3 class='text-xl font-semibold mb-2'>AI Agent's Recommendation:</h3>", unsafe_allow_html=True)
    st.write(f"**Hotel:** {st.session_state.ai_recommended_hotel['name']}")
    st.write(f"**Reasoning:** {st.session_state.ai_reasoning}")
    keywords = ["valentine’s", "romantic", "luxury"] # Lowercase for case-insensitive check
    keyword_count = sum(1 for k in keywords if k in st.session_state.ai_reasoning.lower())
    st.write(f"**Keywords Acknowledged in AI Reasoning**: {keyword_count}/{len(keywords)}")
    st.button("Book AI Recommended Hotel", key="ai_book_button", on_click=handle_ai_book, help="Book the hotel recommended by the AI agent.")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    if st.session_state.ai_reasoning: # Only show reasoning if it was set (e.g., for "no hotels found")
        st.info(f"AI Agent's Response: {st.session_state.ai_reasoning}")

st.markdown("</section>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# --- Interaction Metrics ---
st.subheader("Detailed Interaction Metrics")
st.markdown('<div class="bg-blue-50 border border-blue-200 text-blue-800 p-6 rounded-lg shadow-md">', unsafe_allow_html=True)
st.write(f"**Banner Ad Clicks**: {st.session_state.banner_clicks}")
st.write(f"**Sponsored Ad Clicks**: {st.session_state.sponsored_clicks}")
st.write(f"**Filter Usage**: Price: {st.session_state.price_filter}, Rating: {st.session_state.rating_filter}, Type: {st.session_state.type_filter}")
st.write(f"**Booking Completions (Current Session)**: {1 if st.session_state.booking_confirmed_this_session else 0}")
st.write(f"**AI Recommendation Acknowledged (Selected)**: {1 if st.session_state.ai_recommended_hotel else 0}")

# Chart data
booking_completions_for_chart = 1 if st.session_state.booking_confirmed_this_session else 0
ai_recommendation_selected_for_chart = 1 if st.session_state.ai_recommended_hotel else 0

st.markdown(f"""
```chartjs
{{
    "type": "bar",
    "data": {{
        "labels": ["Banner Clicks", "Sponsored Clicks", "Bookings", "AI Recommendations"],
        "datasets": [{{
            "label": "Interaction Metrics",
            "data": [
                {st.session_state.banner_clicks},
                {st.session_state.sponsored_clicks},
                {booking_completions_for_chart},
                {ai_recommendation_selected_for_chart}
            ],
            "backgroundColor": ["#3b82f6", "#0d9488", "#9333ea", "#ef4444"],
            "borderColor": ["#2563eb", "#0f766e", "#7e22ce", "#dc2626"],
            "borderWidth": 1
        }}]
    }},
    "options": {{
        "scales": {{
            "y": {{
                "beginAtZero": true,
                "title": {{
                    "display": true,
                    "text": "Count"
                }}
            }},
            "x": {{
                "title": {{
                    "display": true,
                    "text": "Metrics"
                }}
            }}
        }},
        "plugins": {{
            "legend": {{
                "display": false
            }},
            "title": {{
                "display": true,
                "text": "Ad and Booking Interaction Metrics"
            }}
        }}
    }}
}}
