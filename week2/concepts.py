from datetime import date,datetime,timedelta


def calculatedate():
    end=date.today()
    start=end - timedelta(days=30)
    end_str=end.strftime("%Y-%m-%d")
    start_str=start.strftime("%Y-%m-%d")
    return start_str,end_str



start_date,end_date=calculatedate()
print(f"start-date:{start_date}")
print(f"End-date:{end_date}")