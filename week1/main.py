from typing_extensions import clear_overloads
from datetime import datetime
import csv
import json
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CSV_parser:
    def __init__(self,filepath):
        self.filepath=filepath
    def CSV_Reader(self):
        with open(self.filepath,mode='r',encoding='utf-8') as f:
            reader=csv.DictReader(f)
            for row in reader:
                yield row
#     | `customer_name` | Leading/trailing spaces | String. Clean whitespace (`.strip()`), capitalize/title format. |
# | `customer_email`| Raw email, empty, casing | Lowercase string. If missing or invalid format (missing `@`), flag or default to `null`. |
    def validate_records(self,data):
        valid_data=[]
        invalid_data=[]
        customer_id=data.get('customer_id','').strip() or 'GUEST'
        customer_name=data.get('customer_name','').strip().title()
        raw_email = data.get('customer_email', '').strip().lower()
        customer_email = raw_email if '@' in raw_email else None
        raw_price = data.get('unit_price', '').replace('$', '').strip()
        try:
            order_id = int(data.get('order_id', ''))
            item_count=int(data.get('item_count',''))
            unit_price=float(raw_price)
            if order_id <= 0:
                invalid_data.append({'order_id': order_id, 'customer_id': customer_id, 'customer_name': customer_name,
                 'customer_email': customer_email, 'reason': 'Order_id must be greater than 0', 'order_date': data.get('order_date'),
                 'item_count':item_count})
                return valid_data, invalid_data


        except (ValueError, TypeError):
            invalid_data.append({'order_id': data.get('order_id'), 'customer_id': customer_id, 'customer_name': customer_name, 
            'customer_email': customer_email, 
            'reason': 'Invalid order_id, item_count, or unit_price', 'order_date': data.get('order_date'),
            'item_count': data.get('item_count'), "unit_price": data.get('unit_price')})
            return valid_data, invalid_data

        if item_count <= 0:
            invalid_data.append({'order_id': data.get('order_id'), 'customer_id': customer_id, 'customer_name': customer_name, 
            'customer_email': customer_email, 
            'reason': 'item_count must be greater than 0', 'order_date': data.get('order_date'),
            'item_count': item_count, "unit_price": unit_price})
            return valid_data, invalid_data

        if unit_price <= 0.0:
            invalid_data.append({'order_id': data.get('order_id'), 'customer_id': customer_id, 'customer_name': customer_name, 
            'customer_email': customer_email, 
            'reason': 'unit_price must be greater than 0.0', 'order_date': data.get('order_date'),
            'item_count': item_count, "unit_price": unit_price})
            return valid_data, invalid_data

        raw_date = data.get('order_date', '').strip()
        parsed_date = None
        for date_format in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y'):
            try:
                parsed_date = datetime.strptime(raw_date, date_format).date()
                break  # Stop as soon as a format matches
            except ValueError:
                continue

        if not parsed_date:
            invalid_data.append({'order_id': order_id, 'customer_id': customer_id, 'customer_name': customer_name, 'customer_email': customer_email, 'reason': f'Invalid or unparseable order_date: {raw_date}', 'order_date': raw_date})
            return valid_data, invalid_data

        status = data.get('status', '').strip().upper()
        total_amount = round(item_count * unit_price, 2)

        valid_data.append({
            'order_id': order_id,
            'customer_id': customer_id,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'order_date': parsed_date.strftime('%Y-%m-%d'),
            'item_count': item_count,
            'unit_price': unit_price,
            'status': status,
            'total_amount': total_amount
        })
        return valid_data, invalid_data

def deduplicate_records(clean_orders):
    unique_records = {}
    duplicate_data = []

    for x in clean_orders:
        oid = x['order_id']
        if oid not in unique_records:
            unique_records[oid] = x
        else:
            existing_date = unique_records[oid]['order_date']
            new_date = x['order_date']
            if new_date > existing_date:
                unique_records[oid] = x
            duplicate_data.append(x)

    return list(unique_records.values()), duplicate_data


def generate_outputs(clean_orders, quarantine, duplicates_dropped, output_dir):
    """
    Milestone 5: Output Generation & Summary Report
    Creates output directory and generates:
      1. clean_orders.json (indented JSON array)
      2. clean_orders.ndjson (streaming newline-delimited JSON)
      3. quarantine_records.json (rejected records with failure reasons)
      4. pipeline_summary.json (execution metrics report)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(output_path / 'clean_orders.json', mode='w', encoding='utf-8') as f:
        json.dump(clean_orders, f, indent=2)

    with open(output_path / 'clean_orders.ndjson', mode='w', encoding='utf-8') as f:
        for order in clean_orders:
            f.write(json.dumps(order) + '\n')
    with open(output_path / 'quarantine_records.json', mode='w', encoding='utf-8') as f:
        json.dump(quarantine, f, indent=2)


    total_processed = len(clean_orders) + len(quarantine) + len(duplicates_dropped)
    total_revenue = round(sum(order['total_amount'] for order in clean_orders), 2)

    status_breakdown = {}
    for order in clean_orders:
        s = order['status']
        status_breakdown[s] = status_breakdown.get(s, 0) + 1

    summary = {
        "total_rows_processed": total_processed,
        "valid_rows_count": len(clean_orders),
        "quarantined_rows_count": len(quarantine),
        "duplicates_dropped_count": len(duplicates_dropped),
        "total_revenue_usd": total_revenue,
        "status_breakdown": status_breakdown
    }
    with open(output_path / 'pipeline_summary.json', mode='w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    input_file = base_dir / 'data' / 'raw_orders_messy.csv'
    output_dir = base_dir / 'output'

    if not input_file.exists():
        input_file = base_dir / 'data' / 'sample_data.csv'

    logging.info(f"Ingesting raw data from: {input_file}")
    parser = CSV_parser(input_file)
    data = parser.CSV_Reader()

    staged_clean = []
    quarantine = []

    for record in data:
        valid, invalid = parser.validate_records(record)
        staged_clean.extend(valid)
        quarantine.extend(invalid)

    # Milestone 4: Deduplicate
    valid_orders, duplicate_orders = deduplicate_records(staged_clean)

    # Milestone 5: Output Generation
    summary = generate_outputs(valid_orders, quarantine, duplicate_orders, output_dir)

    logging.info("Pipeline executed successfully! Output generated in output/")
    print(f"\nPipeline Summary:\n{json.dumps(summary, indent=2)}")

