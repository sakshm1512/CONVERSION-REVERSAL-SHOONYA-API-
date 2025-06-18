import logging
import datetime
import pyotp
import pandas as pd
from NorenRestApiPy.NorenApi import NorenApi
from api_helper import ShoonyaApiPy
import time
import os
import Shoonya as shoon
import pickle

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

# Login
ret = api_try(api.login, 5, userid=user, password=pwd, twoFA=pyotp.TOTP(token).now(), vendor_code=vc, api_secret=app_key, imei=imei)
print("Login Response:", ret['stat'])

file_path_variables = 'variables.csv'
variables_df = pd.read_csv(file_path_variables)

current_time = datetime.datetime.now()
target_time = datetime.datetime(
    year=current_time.year, month=current_time.month, day=current_time.day, hour=23, minute=30, second=0)
start_time = datetime.datetime(
    year=current_time.year, month=current_time.month, day=current_time.day, hour=9, minute=15, second=00)
time_buy = datetime.datetime(
    year=current_time.year, month=current_time.month, day=current_time.day, hour=9, minute=30, second=0)

# Initialize active order book and order book
file_name_aob = "ActiveOrderBook.csv"
file_path_aob = file_name_aob

# Check if the file exists
if not os.path.exists(file_path_aob):
    # Create the file with headers if it doesn't exist
    aob = pd.DataFrame(columns=['Token', 'Symbol', 'OrderNo', 'Buy/Sell', 'Time Of Order', 'No of lots', 'Price'])
    aob.to_csv(file_path_aob, index=False)
else:
    # Load the existing data
    aob = pd.read_csv(file_path_aob)

file_name_ob = "OrderBook.csv"
file_path_ob = file_name_ob

if not os.path.exists(file_path_ob):
    ob = pd.DataFrame(columns=['Token', 'Symbol', 'OrderNo', 'Buy/Sell', 'Time Of Order', 'No of lots', 'Price'])
    ob.to_csv(file_path_ob, index=False)
else:
    ob = pd.read_csv(file_path_ob)

feed_opened = False
tokenbp1 = {}  # Dictionary to store tokens and their 'bp1' values
tokensp1 = {}  # Dictionary to store tokens and their 'sp1' values
lp_token = {}  # Dictionary to store tokens and their 'lp' values

def event_handler_feed_update(tick_data):
    token = tick_data.get('tk', None)
    if token:
        bp1 = tick_data.get('bp1', None)
        sp1 = tick_data.get('sp1', None)
        lp = tick_data.get('lp', None)
        
        # Update 'bp1' in the dictionary if a new value is present
        if bp1 is not None:
            tokenbp1[token] = float(bp1)
        
        # Update 'sp1' in the dictionary if a new value is present
        if sp1 is not None:
            tokensp1[token] = float(sp1)
        
        # Update 'lp' in the dictionary if a new value is present
        if lp is not None:
            lp_token[token] = float(lp)


def event_handler_order_update(tick_data):
    print(f"Order update: {tick_data}")

def open_callback():
    global feed_opened
    feed_opened = True
    print("WebSocket connection opened")

def round_to_nearest_0_05(value):
    return round(value * 20) / 20.0

def save_lists(filename, *lists):
    with open(filename, 'wb') as file:
        pickle.dump(lists, file)

def load_lists(filename):
    with open(filename, 'rb') as file:
        lists = pickle.load(file)
    return lists

def empty_lists(filename):
    empty_list1 = []
    empty_list2 = []
    empty_list3 = []
    save_lists(filename, empty_list1, empty_list2, empty_list3)

def price_changer(value1, value, percentage):
    # Calculate the increased value
    increased_value = value1 + (value * percentage / 100)
    
    # Round to the nearest 0.05
    rounded_value = round(increased_value * 20) / 20.0
    
    return rounded_value

token_data = pd.read_csv('token_symbols.csv')
print("Token Data:")
print(token_data.head())  # Print the first few rows of the CSV to verify it's read correctly

# Create the dictionaries for Nifty token to close price
nifty_dict = {}
nifty_nm_dict = {}
entry_limit = len(token_data)
entry_limit = entry_limit/2

# Fill dictionaries with token and strike values
for i, row in token_data.iterrows():
    symbol = row['Symbol']
    token = row['Token']
    strike = row['Strike']

    if i < entry_limit:
        nifty_dict[token] = strike
    else:
        nifty_nm_dict[token] = strike
    
print("Nifty Dictionary:")
print(nifty_dict)
print("Nifty Nm Dictionary:")
print(nifty_nm_dict)


# Create the subscription list
subscription_list = [f'NFO|{token}' for token in token_data['Token']]
# print("Subscription List:")
# print(subscription_list)

# Start WebSocket
api_try(api.start_websocket, 5,
        order_update_callback=event_handler_order_update,
        subscribe_callback=event_handler_feed_update,
        socket_open_callback=open_callback)

# Wait for WebSocket connection to open
while not feed_opened:
    time.sleep(0.1)

# Subscribe to tokens from CSV
subscription_response = api_try(api.subscribe, 5, subscription_list)
# print("Subscription Response:", subscription_response)

count = 1
traded_keys = set()
niftysp1 = {}
niftybp1 = {}
niftymsp1 = {}
niftymbp1 = {}

while start_time < datetime.datetime.now() < target_time:
    
    if count<5:
        time.sleep(.5)
    print(f"Count: {count}")
    count += 1
    # print("tokenbp1:", tokenbp1)
    # print("tokensp1:", tokensp1)
    file_path_variables = 'variables.csv'
    variables_df = pd.read_csv(file_path_variables)
    ENTRY = int(variables_df[variables_df['VARIABLE'] == 'ENTRY']['VALUE'].values[0])
    EXIT_DIFF = int(variables_df[variables_df['VARIABLE'] == 'EXIT_DIFF']['VALUE'].values[0])
    PER_ENTRY = int(variables_df[variables_df['VARIABLE'] == 'PER_ENTRY']['VALUE'].values[0])
    PER_EXIT = int(variables_df[variables_df['VARIABLE'] == 'PER_EXIT']['VALUE'].values[0])
    aob = pd.read_csv(file_path_aob)
    ob = pd.read_csv(file_path_ob)
    if aob.empty:
        # Update niftysp1 and niftybp1 dictionaries
        for index, (token, strike) in enumerate(nifty_dict.items()):
            token_str = str(token)
            if index % 2 == 0:  # Even index (2nd, 4th, 6th, ...)
                sp1 = tokensp1.get(token_str, None)
                if sp1 is not None:
                    niftysp1[strike] = sp1
                else:
                    if strike not in niftysp1:  # Only set 0.0 if the strike is not already in the dictionary
                        niftysp1[strike] = 0.0
            else:  # Odd index (1st, 3rd, 5th, ...)
                bp1 = tokenbp1.get(token_str, None)
                if bp1 is not None:
                    niftybp1[strike] = bp1
                else:
                    if strike not in niftybp1:  # Only set 0.0 if the strike is not already in the dictionary
                        niftybp1[strike] = 0.0

        nifty_synthetic = {}
        for strike in niftysp1:
            if strike in niftybp1:  # Ensure the key exists in both dictionaries
                diff_value = int(strike) + niftysp1[strike] - niftybp1[strike]
                rounded_value = round_to_nearest_0_05(diff_value)
                nifty_synthetic[strike] = rounded_value

        # print("Nifty synthetic Dictionary:", nifty_synthetic) 

        for index, (token, strike) in enumerate(nifty_nm_dict.items()):
            token_str = str(token)
            if index % 2 == 0:  # Even index (2nd, 4th, 6th, ...)
                bp1 = tokenbp1.get(token_str, None)
                if bp1 is not None:
                    niftymbp1[strike] = bp1
                else:
                    if strike not in niftymbp1:  # Only set 0.0 if the strike is not already in the dictionary
                        niftymbp1[strike] = 0.0
            else:  # Odd index (1st, 3rd, 5th, ...)
                sp1 = tokensp1.get(token_str, None)
                if sp1 is not None:
                    niftymsp1[strike] = sp1
                else:
                    if strike not in niftymsp1:  # Only set 0.0 if the strike is not already in the dictionary
                        niftymsp1[strike] = 0.0

        nifty_m_synthetic = {}
        for strike in niftymsp1:
            if strike in niftymbp1:  # Ensure the key exists in both dictionaries
                diff_value = int(strike) + niftymbp1[strike] - niftymsp1[strike]
                rounded_value = round_to_nearest_0_05(diff_value)
                nifty_m_synthetic[strike] = rounded_value

        # print("Nifty month synthetic Dictionary:", nifty_m_synthetic) 

        max_nifty_m_value = max(nifty_m_synthetic.values(), default=0)
        min_nifty_value = min(nifty_synthetic.values(), default=0)

        # Calculate the difference and round it
        difference = max_nifty_m_value - min_nifty_value
        rounded_difference = round_to_nearest_0_05(difference)

        max_key_nifty_m = next((k for k, v in nifty_m_synthetic.items() if v == max_nifty_m_value), None)
        min_key_nifty = next((k for k, v in nifty_synthetic.items() if v == min_nifty_value), None)
        # Create nifty_syn_final dictionary
        nifty_syn_final = {rounded_difference: f"{min_key_nifty},{max_key_nifty_m}"}
        print("Nifty Syn Final Dictionary:", nifty_syn_final)
        entry_point = rounded_difference
    
    aob = pd.read_csv(file_path_aob)
    ob = pd.read_csv(file_path_ob)
    if aob.empty and count>5:
        if int(rounded_difference) > ENTRY:
            first_42_rows = token_data.head(42)
            next_42_rows = token_data.iloc[42:84]
            min_key_nifty_rows = first_42_rows[first_42_rows['Strike'] == min_key_nifty]
            max_key_nifty_m_rows = next_42_rows[next_42_rows['Strike'] == max_key_nifty_m]
            symbols_list = list(min_key_nifty_rows['Symbol']) + list(max_key_nifty_m_rows['Symbol'])
            tokens_list = list(min_key_nifty_rows['Token']) + list(max_key_nifty_m_rows['Token'])
            print("Symbols List:", symbols_list)
            print("Tokens List:", tokens_list)
            # Define the order types
            order_types = ['BUY', 'SELL', 'SELL', 'BUY']
            # Create the order_sequence dictionary
            order_sequence = {symbols_list[i]: (tokens_list[i], order_types[i]) for i in range(4)}
            order_sequence = dict(sorted(order_sequence.items(), key=lambda item: lp_token[str(item[1][0])], reverse=True))
            print(order_sequence)
            # Extract symbols and tokens from sorted order sequence
            sorted_symbols = list(order_sequence.keys())
            sorted_tokens = [order_sequence[symbol][0] for symbol in sorted_symbols]
            sorted_order_types = [order_sequence[symbol][1] for symbol in sorted_symbols]

            # Place first order
            symbol = sorted_symbols[0]
            token = sorted_tokens[0]
            order_type = sorted_order_types[0]
            if order_type == 'BUY':
                currentsp1 =  float(tokensp1[str(token)])
                price = price_changer(currentsp1, ENTRY, PER_ENTRY)
                buy = shoon.IOC_BUY(str(symbol), 25, price)
                if buy[0] == 'COMPLETE':
                    aob.loc[len(aob)] = [token, symbol, buy[1], 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    ob.loc[len(ob)] = [token, symbol, buy[1], 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]

                    # Place second order 
                    symbol = sorted_symbols[1]
                    token = sorted_tokens[1]
                    order_type = sorted_order_types[1]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    # Place third order 
                    symbol = sorted_symbols[2]
                    token = sorted_tokens[2]
                    order_type = sorted_order_types[2]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    # Place fourth order 
                    symbol = sorted_symbols[3]
                    token = sorted_tokens[3]
                    order_type = sorted_order_types[3]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    list3 = [entry_point]
                    save_lists('saved_lists.pkl', symbols_list, tokens_list, entry_point)
                    
            elif order_type == 'SELL':
                currentbp1 = float(tokenbp1[str(token)])
                price = price_changer(currentbp1, ENTRY, -PER_ENTRY)
                sell = shoon.IOC_SELL(str(symbol), 25 , price)
                if sell[0] == 'COMPLETE':
                    aob.loc[len(aob)] = [token, symbol, sell[1], 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]
                    ob.loc[len(ob)] = [token, symbol, sell[1], 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    # Place second order 
                    symbol = sorted_symbols[1]
                    token = sorted_tokens[1]
                    order_type = sorted_order_types[1]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    # Place third order 
                    symbol = sorted_symbols[2]
                    token = sorted_tokens[2]
                    order_type = sorted_order_types[2]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    # Place fourth order 
                    symbol = sorted_symbols[3]
                    token = sorted_tokens[3]
                    order_type = sorted_order_types[3]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        aob.loc[len(aob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    list3 = [entry_point]
                    save_lists('saved_lists.pkl', symbols_list, tokens_list, entry_point)

            # Save the updated DataFrames to CSV
            aob.to_csv(file_path_aob, index=False)
            ob.to_csv(file_path_ob, index=False)

    aob = pd.read_csv(file_path_aob)
    ob = pd.read_csv(file_path_ob)
    if not aob.empty and count>5:
        loaded_lists = load_lists('saved_lists.pkl')
        symbols_list, tokens_list, list3 = loaded_lists
        print(list3)
        entry_point = list3
        bp1 = tokenbp1[str(tokens_list[0])]
        sp1 = tokensp1[str(tokens_list[1])]
        sp1m = tokensp1[str(tokens_list[2])]
        bp1m = tokenbp1[str(tokens_list[3])]

        strike_m = int(symbols_list[2][-5:])
        strike_w = int(symbols_list[0][-5:])

        syn_month = strike_m + sp1m - bp1m
        syn_week = strike_w + bp1 - sp1
        difference = round_to_nearest_0_05(syn_month - syn_week)
        print (difference)

        exit_difference = round_to_nearest_0_05(entry_point-difference)
        print(exit_difference)

        order_types = ['SELL', 'BUY', 'BUY', 'SELL']
        order_sequence = {symbols_list[i]: (tokens_list[i], order_types[i]) for i in range(4)}
        order_sequence = dict(sorted(order_sequence.items(), key=lambda item: lp_token[str(item[1][0])], reverse=True))
        sorted_symbols = list(order_sequence.keys())
        sorted_tokens = [order_sequence[symbol][0] for symbol in sorted_symbols]
        sorted_order_types = [order_sequence[symbol][1] for symbol in sorted_symbols]
        if exit_difference > EXIT_DIFF:
            print('exit')
            #['Token', 'Symbol', 'OrderNo', 'Buy/Sell', 'Time Of Order', 'No of lots', 'Price']
            # Place first order
            symbol = sorted_symbols[0]
            token = sorted_tokens[0]
            order_type = sorted_order_types[0]
            if order_type == 'BUY':
                currentsp1 = float(tokensp1[str(token)])
                price = price_changer(currentsp1, EXIT_DIFF, PER_EXIT)
                buy = shoon.IOC_BUY(str(symbol), 25, price)
                if buy[0] == 'COMPLETE':
                    ob.loc[len(ob)] = [token, symbol, buy[1], 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]

                    # Place second order 
                    symbol = sorted_symbols[1]
                    token = sorted_tokens[1]
                    order_type = sorted_order_types[1]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    # Place third order 
                    symbol = sorted_symbols[2]
                    token = sorted_tokens[2]
                    order_type = sorted_order_types[2]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    # Place fourth order 
                    symbol = sorted_symbols[3]
                    token = sorted_tokens[3]
                    order_type = sorted_order_types[3]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]
                    aob = aob.drop(aob.index)
                    empty_lists('saved_lists.pkl')

            elif order_type == 'SELL':
                currentbp1 = float(tokenbp1[str(token)])
                price = price_changer(currentbp1, EXIT_DIFF, -PER_EXIT)
                sell = shoon.IOC_SELL(str(symbol), 25 , price)
                if sell[0] == 'COMPLETE':
                    ob.loc[len(ob)] = [token, symbol, sell[1], 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    # Place second order 
                    symbol = sorted_symbols[1]
                    token = sorted_tokens[1]
                    order_type = sorted_order_types[1]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    # Place third order 
                    symbol = sorted_symbols[2]
                    token = sorted_tokens[2]
                    order_type = sorted_order_types[2]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]

                    # Place fourth order 
                    symbol = sorted_symbols[3]
                    token = sorted_tokens[3]
                    order_type = sorted_order_types[3]
                    if order_type == 'BUY':
                        buy = shoon.MKT_BUY(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, buy, 'BUY', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokensp1[str(token)]]
                    elif order_type == 'SELL':
                        sell = shoon.MKT_SELL(str(symbol), 25)
                        ob.loc[len(ob)] = [token, symbol, sell, 'SELL', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 1, tokenbp1[str(token)]]
                    aob = aob.drop(aob.index)
                    empty_lists('saved_lists.pkl')
                    
            # Save the updated DataFrames to CSV
            aob.to_csv(file_path_aob, index=False)
            ob.to_csv(file_path_ob, index=False)
    # time.sleep(.05)

