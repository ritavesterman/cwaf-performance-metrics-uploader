import json
import requests
import time
from urllib.parse import urlencode
from datetime import datetime
import threading
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE_URL = "https://api.imperva.com/appdlv-dashboards-ui/v3/performance/statistics"
API_ID = "<api-id>"
API_KEY = "<api-key>"
SPLUNK_ADDRESS = "<splunk-address-collector>"
SPLUNK_TOKEN = "<splunk-token>"
SITE_IDS = ["1", "2"]

VERBOSE = False  # Set to True for detailed logs
RETRY_COUNT = 3  # Number of retries for API requests
RETRY_DELAY = 5  # Delay (seconds) before retrying a failed request

def format_splunk_event(flat_json):
    return {
        "event": flat_json,
        "sourcetype": "json_http",
        "index": "main"
    }

def send_to_splunk(splunk_address, splunk_token, flat_json):
    headers = {
        "Authorization": f"Splunk {splunk_token}",
        "Content-Type": "application/json"
    }
    splunk_event = format_splunk_event(flat_json)

    if VERBOSE:
        print(f"Sending to Splunk: {json.dumps(splunk_event, indent=2)}")

    response = requests.post(splunk_address, headers=headers, data=json.dumps(splunk_event), verify=False)

    if not VERBOSE:
        print(f"{flat_json['timestamp']} - Response from Splunk: {response.status_code} - {response.text}")

    response.raise_for_status()
    return response.status_code

def flatten_error_response_types(timestamp, account_id, site):
    site_id = site["siteId"]
    site_name = site["siteName"]
    statistics = site.get("statistics", {})
    error_response_types = statistics.get("errorResponseTypes", {})
    
    for error_type, value in error_response_types.items():
        flat_json = {
            "timestamp": timestamp,
            "accountId": account_id,
            "siteId": site_id,
            "siteName": site_name,
            "metricName": "errorResponseTypes",
            "errorType": error_type,
            "value": value
        }
        send_to_splunk(SPLUNK_ADDRESS, SPLUNK_TOKEN, flat_json)

def flatten_origin_response_time(timestamp, account_id, site):
    site_id = site["siteId"]
    site_name = site["siteName"]
    statistics = site.get("statistics", {})
    origin_response_time = statistics.get("originResponseTime", [])
    
    for entry in origin_response_time:
        flat_json = {
            "timestamp": timestamp,
            "accountId": account_id,
            "siteId": site_id,
            "siteName": site_name,
            "metricName": "originResponseTime",
            "value": entry["avgResponseTime"],
            "server": entry["server"],
            "dataCenterName": entry["dataCenterName"]
        }
        send_to_splunk(SPLUNK_ADDRESS, SPLUNK_TOKEN, flat_json)

def flatten_pop_latency(timestamp, account_id, site):
    site_id = site["siteId"]
    site_name = site["siteName"]
    statistics = site.get("statistics", {})
    pop_latency = statistics.get("popLatency", [])
    
    for region_entry in pop_latency:
        region = region_entry["region"]
        for pop_entry in region_entry.get("pops", []):
            flat_json = {
                "timestamp": timestamp,
                "accountId": account_id,
                "siteId": site_id,
                "siteName": site_name,
                "metricName": "popLatency",
                "value": pop_entry["valuePerPop"],
                "region": region,
                "pop": pop_entry["pop"]
            }
            send_to_splunk(SPLUNK_ADDRESS, SPLUNK_TOKEN, flat_json)

def fetch_performance_statistics(api_id, api_key, site_ids, current_time):
    headers = {
        "x-API-Id": api_id,
        "x-API-Key": api_key
    }
    params = {"siteIds": ",".join(site_ids)}
    url = f"{API_BASE_URL}?{urlencode(params)}"

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            response = requests.get(url, headers=headers, verify=False)
            
            if response.status_code == 200:
                return response.json()
            
            print(f"[{current_time}:Attempt {attempt}/{RETRY_COUNT}] Error fetching data: {response.status_code} - {response.text}")
        
        except requests.RequestException as e:
            print(f"[Attempt {attempt}/{RETRY_COUNT}] Network error: {e}")

        if attempt < RETRY_COUNT:
            time.sleep(RETRY_DELAY)  # Wait before retrying

    print(f"[{current_time}] Max retries reached. Failed to fetch performance statistics.")
    return None  # Return None if all retries fail
    

def process_and_send():
    current_time = datetime.utcnow()
    current_timestamp = int(current_time.timestamp() * 1000)  # Convert to milliseconds
    print(f"[{current_time}] Fetching performance data... (Timestamp: {current_timestamp})")

    try:
        raw_data = fetch_performance_statistics(API_ID, API_KEY, SITE_IDS, current_time)

        if raw_data is None:  # Handle failed API fetch
            return  # Exit function if data fetch failed

        for entry in raw_data.get("data", []):
            timestamp = entry["timestamp"]
            account_id = entry["accountId"]
            sites_statistics = entry.get("sitesStatistics", [])

            for site in sites_statistics:
                if not site.get("statistics"):  # Skip if statistics is empty
                    continue

                flatten_error_response_types(timestamp, account_id, site)
                flatten_origin_response_time(timestamp, account_id, site)
                flatten_pop_latency(timestamp, account_id, site)

        print(f"[{current_time}] Done sending to Splunk successfully.")

    except Exception as e:
        print(f"[{current_time}] Error occurred: {e}")

def scheduled_task():
    while True:
        now = datetime.utcnow()
        # Calculate seconds until the next `MM:00`
        seconds_until_next_execution = (60 - now.second) - now.microsecond / 1_000_000
        time.sleep(seconds_until_next_execution)  # Sleep until the next MM:00

        thread = threading.Thread(target=process_and_send)
        thread.start()

if __name__ == "__main__":
    scheduled_task()
