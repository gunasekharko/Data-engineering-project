from datetime import datetime
from pathlib import Path
import json
import logging
import requests

BASE_DIR = Path(__file__).resolve().parent
output_path = BASE_DIR / "output" / "day1_rates.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_latest_rates():
    query_params={
        "base":"USD",
        # "base":"INVALID",
        "symbols": "EUR,GBP,INR,CAD"
    }
    try:
        response=requests.get(url="https://api.frankfurter.dev/v1/latest",timeout=10,params=query_params)
        response.raise_for_status()
        return response.json()
    except requests.Timeout as e:
        logging.critical(f"remote server timed out: {e}")
    except requests.HTTPError as e:
        logging.critical(f"client side error: {e}")
    except requests.RequestException as e:
        logging.critical(f"request error occurred: {e}")


def save_response(data):
    if(data is not None):
        output_payload={
            "ingested_at":datetime.now().isoformat(),
            "base_currency":data.get("base"),
            "rate_date":data.get('date'),
            "rates":data.get('rates')
        }
        with open(output_path,mode='w',encoding='utf-8') as f:
            json_str=json.dumps(output_payload,indent=2)
            f.write(json_str)


if __name__=="__main__":
    response=get_latest_rates()
    print(response)
    save_response(response)



