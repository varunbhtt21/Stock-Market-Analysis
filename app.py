import streamlit as st
import os
from dotenv import load_dotenv
import requests
import google.generativeai as genai
import json
from datetime import datetime
import statistics
import streamlit as st


# Load environment variables
# load_dotenv()
# genai_api_key = os.getenv('GENAI_API_KEY')
# rapidapi_key = os.getenv('RAPIDAPI_KEY')

genai_api_key = st.secrets["GENAI_API_KEY"]
rapidapi_key = st.secrets["RAPIDAPI_KEY"]

# Check if API keys are loaded
if not genai_api_key or not rapidapi_key:
    st.error("API keys are not set. Please check your .env file.")
    st.stop()

# Configure the GEMINI API
genai.configure(api_key=genai_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Core Functions (Unchanged)

def ask_gemini(question):
    try:
        response = model.generate_content(question)
        return response.text
    except Exception as e:
        st.error(f"Error during GEMINI analysis: {e}")
        return None

def fetch_historical_data(company_name, period='1yr'):
    base_url = "https://indian-stock-exchange-api2.p.rapidapi.com/"
    endpoint = f"{base_url}historical_data"
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "indian-stock-exchange-api2.p.rapidapi.com"
    }
    params = {
        "stock_name": company_name,
        "period": period,
        "filter": "price"
    }
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.error(f"An error occurred: {err}")
    return None

def calculate_price_statistics(historical_data):
    prices = []
    dates = []
    for entry in historical_data.get('datasets', [])[0].get('values', []):
        date_str, price_str = entry
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        price = float(price_str)
        dates.append(date_obj)
        prices.append(price)
    if prices:
        growth_rate = ((prices[-1] - prices[0]) / prices[0]) * 100
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
        return {
            "Price Growth Rate (%)": round(growth_rate, 2),
            "Average Price": round(avg_price, 2),
            "Minimum Price": min_price,
            "Maximum Price": max_price,
            "Price Volatility (Std Dev)": round(std_dev, 2)
        }
    else:
        return None

# Streamlit Interface

st.title("Stock Analysis Application")
st.write("Analyze stock performance and get data-driven insights for informed investment decisions.")

# User Inputs
company_name = st.text_input("Enter the company name:", "Reliance")
period = st.selectbox("Select the historical data period:", ["1yr", "5yr", "10yr"], index=0)
risk_tolerance = st.selectbox("Select your risk tolerance:", ["Low", "Medium", "High"], index=1)
investment_goal = st.text_input("Enter your investment goal:", "Long-term growth")

if st.button("Analyze Stock"):
    st.write("Fetching data...")

    # Fetch historical data
    historical_data = fetch_historical_data(company_name, period)
    if not historical_data:
        st.error("Failed to retrieve historical data.")
    else:
        # Process historical data
        price_stats = calculate_price_statistics(historical_data)
        if not price_stats:
            st.error("Failed to calculate price statistics.")
        else:
            st.subheader("Price Statistics")
            st.json(price_stats)

            # Prepare GEMINI prompt
            data_summary = {
                "Historical Price Statistics": price_stats
            }
            prompt = (
                f"As a financial analyst, analyze the stock performance of {company_name} based on the following data summary:\n"
                f"{json.dumps(data_summary, indent=2)}\n"
                f"The investor has a '{risk_tolerance}' risk tolerance and is aiming for '{investment_goal}'.\n"
                "Please focus on answering these questions:\n"
                "1. What does the historical price trend indicate about the stock's past performance?\n"
                "2. Based on the data, what are the potential risks and rewards associated with investing in this stock?\n"
                "3. Considering past trends and forecasts, what is the estimated time frame for potential returns?\n"
                "4. How does the company's performance compare with its industry peers?\n"
                "Provide your analysis based on the data, focusing on data-driven insights.\n"
                "Conclusion: Should I invest - Yes or No? If Yes, then how much?"
            )

            # Get GEMINI analysis
            analysis = ask_gemini(prompt)
            if analysis:
                st.subheader("GEMINI Analysis")
                st.write(analysis)
            else:
                st.error("Failed to obtain analysis from GEMINI.")
