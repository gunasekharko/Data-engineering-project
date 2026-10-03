from datetime import timedelta
from datetime import datetime
from pathlib import Path
import json
import logging
import requests

BASE_DIR = Path(__file__).resolve().parent
output_path = BASE_DIR / "output" / "day2_historical_rates.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_latest_rates():
    query_params={
        "base":"EUR",
        # "base":"INVALID",
        "symbols": "USD"
    }
    start_str=datetime.today() - timedelta(days=30)
    start_date=start_str.strftime("%Y-%m-%d")
    end_str=datetime.today()
    end_date=end_str.strftime("%Y-%m-%d")
    try:
        response=requests.get(url=f"https://api.frankfurter.dev/v1/{start_date}..{end_date}",timeout=5,params=query_params)
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
        nested_rates=data.get('rates',{})
        start_date=data.get('start_date','')
        end_date=data.get('end_date')
        print(nested_rates)
        flat_records=[]
        base_currency = data.get("base")
        for rate_date, currencies in nested_rates.items():
          for currency_code, rate_value in currencies.items():
           flat_records.append({
            "date": rate_date,
            "base": base_currency,
            "target": currency_code,
            "rate": rate_value
        })
        output_payload={
            "ingested_at":datetime.now().isoformat(),
            "base_currency":data.get("base"),
            "rate_date":data.get('end_date'),
            "rates":flat_records
        }
        with open(output_path,mode='w',encoding='utf-8') as f:
            json_str=json.dumps(output_payload,indent=2)
            f.write(json_str)


if __name__=="__main__":
    response=get_latest_rates()
    save_response(response)



