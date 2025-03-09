# cwaf-performance-metrics-uploader
This repo holds a demo script for sending Imperva CWAF performance metrics to Splunk.

## Overview

This script fetches performance statistics from the Imperva API, processes the data into a flattened JSON format, and sends it to Splunk for monitoring and analysis. The script runs continuously, fetching new data every minute and sending it to Splunk.

## Requirements

- Python 3.6+
- `requests` module (install using `pip install requests`)

## Configuration

Before running the script, replace all placeholder values (`<...>`) with your actual values:

- `<api-id>`: Your Imperva API ID
- `<api-key>`: Your Imperva API Key
- `<splunk-address-collector>`: Your Splunk HTTP Event Collector (HEC) address
- `<splunk-token>`: Your Splunk authentication token
- `SITE_IDS`: Replace with the relevant site IDs for your organization

Example:

```python
API_ID = "your-api-id"
API_KEY = "your-api-key"
SPLUNK_ADDRESS = "https://your-splunk-server:8088/services/collector"
SPLUNK_TOKEN = "your-splunk-token"
SITE_IDS = ["111111", "2222222"]
```

## How It Works

1. The script fetches performance statistics from Imperva’s API using the provided API credentials.
2. It processes the response and extracts three key metrics:
   - `errorResponseTypes`
   - `originResponseTime`
   - `popLatency`
3. The extracted metrics are converted into a flat JSON format.
4. Each flattened JSON object is sent directly to Splunk.
5. The script repeats this process every 60 seconds.

## Running the Script

To run the script, use the following command:

```sh
python3 upload_splunk_script.py
```

The script will continue running and sending data to Splunk. To stop execution, use `CTRL+C`.

## Troubleshooting

- If you encounter an SSL error, try disabling SSL verification by modifying the `requests.post` call:
  ```python
  response = requests.post(splunk_address, headers=headers, data=json.dumps(splunk_event), verify=False)
  ```
- If the script does not send data to Splunk, ensure that your Splunk HEC is configured to accept events.
- If you see an authentication error, verify that your Splunk token and API credentials are correct.

## Notes

- The script runs every minute at exactly **MM:00 UTC** to ensure consistent execution.
- Ensure that your Splunk HEC endpoint is reachable from the system running this script.
- If running in production, consider using a logging mechanism instead of printing errors to stdout.
- The retry parameters (`RETRY_COUNT` and `RETRY_DELAY`) can be adjusted to fine-tune error handling and API request retries.


