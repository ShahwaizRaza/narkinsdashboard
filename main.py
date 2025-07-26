from flask import Flask, render_template, request, jsonify
import requests
import threading
import time
from datetime import datetime
import asyncio
import httpx
import pandas as pd
import subprocess

app = Flask(__name__)

# Store the latest fetched data
latest_data = {}
#current_month = datetime.now().strftime("%b")
first_day = datetime.now().replace(day=1).strftime("%Y-%m-%d")
current_date = datetime.now().strftime("%Y-%m-%d")
print(first_day, current_date)

# API Credentials
HEADERS = {
    "accept": "*/*",
    "X-Api-Key": "4fbf65204fd440599dd3817b45cd869a",
    "X-Api-Secret": "bjHFJT6TbFz2egCjuffpMtnjCizckbYyAZmYKUyVFhMjARRhE8F4c67ATF72ddGgeb8f6wjQoSTqZuuGLv6dvhjqzPtwjfWAv25H",
    "X-App-Id": "4BC9199C-5C12-420A-8279-01B1C57CCE5D",
    "Content-Type": "application/json-patch+json"
}

# Define API URLs and Payloads for Different Reports
REPORTS = {
    "ProductDateWiseSale": {
        "url": "https://narkins.splendidaccounts.com/api/narkins-textile-industries/2125/Reports/ProductDateWiseSaleReport",
        "payload": {
            
            "fromDate": first_day,
            "endDate": current_date,
            "branchIds": [2248, 2249, 5574, 5701, 7965, 13468, 13469, 21578, 24709, 24710, 24711, 25762, 2994, 23405, 12721, 25762, 26777, 26778, 26779, 26780],
            "ascending": True,
            "orderBy": "Date"
        }
    }
}

def fetch_api_data(report_type):
    """Fetch data from API based on report type."""
    global latest_data

    print(f"Fetching data for: {report_type}")  # Debugging log

    if report_type not in REPORTS:
        latest_data[report_type] = {"error": "Invalid report type"}
        return

    url = REPORTS[report_type]["url"]
    payload = REPORTS[report_type]["payload"]

    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        print(f"Response [{report_type}] Status Code: {response.status_code}")  # Debugging log
        #print(f"Response [{report_type}] Data: {response.text[:200]}")  # Print first 500 characters of response
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract specific details based on report type
            if report_type == "ProductDateWiseSale":
                latest_data[report_type] = [
                    {   
                        "Date": item.get("date", ""),
                        "Month": item.get("monthName", ""),
                        "Branch": item.get("branchName", ""),
                        "Code": item.get("productCode", ""),
                        "Product Name": item.get("productName", ""),
                        "Category": item.get("productCategoryName", ""),
                        "SOLD QTY": item.get("soldQuantity", 0),
                        "Type": item.get("symbol", ""),
                        "Total Sales": item.get("includingTaxAmount", 0)
                    }
                    for item in data
                ]
                
            else:
                latest_data[report_type] = data  # Keep full data for other reports
        else:
            latest_data[report_type] = {
                "error": "Failed to fetch data",
                "status_code": response.status_code,
                "response": response.text
            }
            
            
    except Exception as e:
        latest_data[report_type] = {"error": "Request failed", "message": str(e)}
        
        
def auto_refresh_data(interval=60):
    """Auto refresh data every interval (in seconds)."""
    with app.app_context():
        while True:
            for report in REPORTS.keys():
                fetch_api_data(report)
            time.sleep(interval)

# Start background data fetch
threading.Thread(target=auto_refresh_data, daemon=True).start()

@app.route('/api/data', methods=['GET'])
def get_data():
    """API Endpoint to get the latest data."""
    report_type = request.args.get('reportType')

    print("Received reportType:", report_type)  # Debugging line
    print("Available reports:", list(latest_data.keys()))  # Debugging line

    if not report_type:
        return jsonify({"error": "Missing reportType parameter"}), 400

    if report_type not in latest_data:
        return jsonify({"error": "Invalid report type"}), 400

    return jsonify(latest_data[report_type])

def fetch_product_sales_data():
    report_type = "ProductDateWiseSale"
    fetch_api_data(report_type)

    if report_type in latest_data and isinstance(latest_data[report_type], list):
        df = pd.DataFrame(latest_data[report_type])

        # Convert 'Date' to datetime and drop rows where conversion fails
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        return df
    else:
        print("Error or no data found for report type:", report_type)
        return pd.DataFrame()  # return empty DataFrame if no data

if __name__ == '__main__':
    app.run(debug=True, port=5000)

#Links
#http://127.0.0.1:5000/api/data?reportType=ProductDateWiseSale
