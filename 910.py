import logging
import datetime
from datetime import date
import pyotp
from collections import OrderedDict
import numpy as np
from NorenRestApiPy.NorenApi import NorenApi
from api_helper import ShoonyaApiPy
import time
import calendar
import Instruments as ins 
import pandas as pd
import os

# Start of our program
class ShoonyaApiPy(NorenApi):
    def __init__(self):
        super().__init__(host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')

# Initialize the API
api = ShoonyaApiPy()

# Credentials_KUNNU
user = ''
pwd = ''
vc = ''
app_key = ''
imei = ''
token = ''

# Function to attempt an API call with retries
def api_try(call_func, max_retries=5, *args, **kwargs):
    for attempt in range(max_retries):
        try:
            result = call_func(*args, **kwargs)
            return result
        except Exception as e:
            logging.error(f"Error on attempt {attempt + 1} for {call_func.__name__}: {str(e)}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)  # Wait a bit before retrying

# Login
ret = api_try(api.login, 5, userid=user, password=pwd, twoFA=pyotp.TOTP(token).now(), vendor_code=vc, api_secret=app_key, imei=imei)
print("Login Response:", ret['stat'])

def round_to_nearest_fifty(price):
    return round(price / 50.0) * 50

def round_to_nearest_hundred(price):
    return round(price / 100.0) * 100

def generate_strikes(atm, count, step):
    return [atm + i * step for i in range(-count, count + 1)]

nifty_atm = float(api_try(api.get_quotes, 5, exchange='NSE', token='26000')['lp'])
nifty_atm = round_to_nearest_fifty(nifty_atm)

# bank_nifty_atm = float(api_try(api.get_quotes, 5, exchange='NSE', token='26009')['lp'])
# bank_nifty_atm = round_to_nearest_hundred(bank_nifty_atm)

# finnifty_atm = float(api_try(api.get_quotes, 5, exchange='NSE', token='26037')['lp'])
# finnifty_atm = round_to_nearest_fifty(finnifty_atm)

nifty_strikes = generate_strikes(nifty_atm, 10, 50)
# bank_nifty_strikes = generate_strikes(bank_nifty_atm, 10, 100)
# fin_nifty_strikes = generate_strikes(finnifty_atm, 10, 50)

today = datetime.date(2024,8,16)
nifty_month_expiry = ins.nifty_month(today)
nifty_symbols = ins.generate_nifty_token_symbols(nifty_strikes,today,0)
nifty_month_symbols = ins.generate_nifty_token_month_symbols(nifty_strikes, nifty_month_expiry)
nifty_month_symbols = [symbol for symbol in nifty_month_symbols if not symbol.endswith('50')]
nifty_symbols = [symbol for symbol in nifty_symbols if not symbol.endswith('50')]
print(nifty_symbols)
print(nifty_month_symbols)
# bank_nifty_month_expiry = ins.bank_nifty_month(today)
# bank_nifty_symbols = ins.generate_banknifty_token_symbols(bank_nifty_strikes,today)
# bank_nifty_month_symbols = ins.generate_banknifty_token_month_symbols(bank_nifty_strikes, bank_nifty_month_expiry)
# print(bank_nifty_symbols)
# print(bank_nifty_month_symbols)
# fin_nifty_month_expiry = ins.fin_nifty_month(today)
# fin_nifty_symbols = ins.generate_fin_nifty_token_symbols(fin_nifty_strikes, today)
# fin_nifty_month_symbols = ins.generate_finnifty_token_month_symbols(fin_nifty_strikes, fin_nifty_month_expiry)
# print(fin_nifty_symbols)
# print(fin_nifty_month_symbols)

data = []

def get_token(symbol):
    try:
        result = api_try(api.searchscrip, 5, exchange='NFO', searchtext=symbol)
        if result and 'values' in result and len(result['values']) > 0:
            token = result['values'][0]['token']
            return token
        else:
            logging.warning(f"No token found for {symbol}")
            return None
    except Exception as e:
        logging.error(f"Error fetching token for {symbol}: {str(e)}")
        return None

for symbol in nifty_symbols:
    token= get_token(symbol)
    strike = symbol[-5:]
    if token is not None:
        data.append({'Symbol': symbol, 'Token': token, 'Strike': strike})

for symbol in nifty_month_symbols:
    token= get_token(symbol)
    strike = symbol[-5:]
    if token is not None:
        data.append({'Symbol': symbol, 'Token': token, 'Strike': strike})

# for symbol in bank_nifty_symbols:
#     token= get_token(symbol)
#     strike = symbol[-5:]
#     if token is not None:
#         data.append({'Symbol': symbol, 'Token': token, 'Strike': strike})

# for symbol in bank_nifty_month_symbols:
#     token= get_token(symbol)
#     strike = symbol[-5:]
#     if token is not None:
#         data.append({'Symbol': symbol, 'Token': token, 'Strike': strike})

# for symbol in fin_nifty_symbols:
#     token= get_token(symbol)
#     strike = symbol[-5:]
#     if token is not None:
#         data.append({'Symbol': symbol, 'Token': token, 'Strike': strike})

# for symbol in fin_nifty_month_symbols:
#     token= get_token(symbol)
#     strike = symbol[-5:]
#     if token is not None:
#         data.append({'Symbol': symbol, 'Token': token, 'Strike': strike})

df = pd.DataFrame(data)
csv_filename = 'token_symbols.csv'
file_path = os.path.join(os.getcwd(), csv_filename)
df.to_csv(file_path, index=False)
print("DataFrame with Symbols, Tokens, Strikes, and Close Prices:")
print(df)