from pydantic import field_validator,ValidationError
from datetime import timedelta,datetime
from pathlib import Path
import json
import logging
import requests
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
output_path = BASE_DIR / "output" / "day2_historical_rates.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RateRecord(BaseModel):
    date:datetime
    base:str
    target:str
    rate:float

    @field_validator("rate")
    @classmethod
    def rate_checker(cls,rate):
       if(rate<0):
         raise ValueError('Given error as negetive')
       return rate
    @field_validator("base","target")
    @classmethod
    def currency_validator(cls,value):
        if not (len(value)==3 and value.isupper()):
            raise ValueError('Currency code must be exactly 3 uppercase letters')
        return value

            


def get_latest_rates(start_date,end_date):
    query_params={
        "base":"EUR",
        # "base":"INVALID",
        "symbols": "USD"
    }

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



if __name__=="__main__":
    start_date=(datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date=datetime.today().strftime("%Y-%m-%d")

    response=get_latest_rates(start_date,end_date)   
    if response is None:
        raise SystemExit("No data received from API")
    validated_records=[]
    print(response)
    for date,daily_rates in response["rates"].items():
        for target,rate in daily_rates.items():
            try:
                validated_record=RateRecord(
                    date=date,
                    base=response["base"],
                    target=target,
                    rate=rate,
                )
                validated_records.append(validated_record.model_dump(mode="json"))
            except ValidationError as e:
                logging.error(f"Invalid record skipped ({date}, {target}): {e}")

    logging.info(f"Validated {len(validated_records)} records")
    print(validated_records[:3])

    with open(output_path,"w") as f:
        json.dump(validated_records,f,indent=2)
    logging.info(f"Saved to {output_path}")
