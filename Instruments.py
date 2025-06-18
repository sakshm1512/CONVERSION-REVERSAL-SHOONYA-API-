import datetime

def nifty_month(date):
    
    # Calculate the last day of the current month
    last_day_of_month = datetime.date(date.year, date.month, 1) + datetime.timedelta(days=32)
    last_day_of_month = last_day_of_month.replace(day=1) - datetime.timedelta(days=1)

    # Calculate the last Thursday of the current month
    last_thursday = last_day_of_month - datetime.timedelta(days=(last_day_of_month.weekday() - 3 + 7) % 7)

    # Calculate the second last Thursday of the current month
    if last_thursday.weekday() == 3:  # If the last Thursday is the last day of the month
        second_last_thursday = last_thursday - datetime.timedelta(days=7)
    else:
        second_last_thursday = last_thursday - datetime.timedelta(days=14)

    # Determine which Thursday to return based on today's date
    if date > second_last_thursday:
        # Add 14 days to today's date and recalculate the last Thursday of the month
        new_date = date + datetime.timedelta(days=14)
        return nifty_month(new_date)
    else:
        return last_thursday

def generate_nifty_token_month_symbols(strikes, expiry_date):
    expiry_str = expiry_date.strftime('%d%b%y').upper()
    token_symbols = []

    for strike in strikes:
        token_symbols.append(f"NIFTY{expiry_str}C{strike}")
        token_symbols.append(f"NIFTY{expiry_str}P{strike}")

    return token_symbols

def generate_nifty_token_symbols(strikes,date,holiday):
    # today = datetime.date.today()
    today = date

    # Calculate the nearest Thursday expiry date
    days_until_expiry = ((3 - today.weekday() + 7) - holiday) % 7  # 3 is Thursday

    expiry_date = today + datetime.timedelta(days=days_until_expiry)

    # If today is after the calculated expiry date, move to the next week
    if today >= expiry_date:
        expiry_date += datetime.timedelta(days=days_until_expiry)

    expiry_str = expiry_date.strftime('%d%b%y').upper()
    token_symbols = []

    for strike in strikes:
        token_symbols.append(f"NIFTY{expiry_str}C{strike}")
        token_symbols.append(f"NIFTY{expiry_str}P{strike}")

    return token_symbols

def bank_nifty_month(date):
    
    # Calculate the last day of the current month
    last_day_of_month = datetime.date(date.year, date.month, 1) + datetime.timedelta(days=32)
    last_day_of_month = last_day_of_month.replace(day=1) - datetime.timedelta(days=1)

    # Calculate the last Wednesday of the current month
    last_wednesday = last_day_of_month - datetime.timedelta(days=(last_day_of_month.weekday() - 2 + 7) % 7)

    # Calculate the second last Wednesday of the current month
    if last_wednesday.weekday() == 2:  # If the last Wednesday is the last day of the month
        second_last_wednesday = last_wednesday - datetime.timedelta(days=7)
    else:
        second_last_wednesday = last_wednesday - datetime.timedelta(days=14)

    # Determine which Wednesday to return based on today's date
    if date > second_last_wednesday:
        # Add 14 days to today's date and recalculate the last Wednesday of the month
        new_date = date + datetime.timedelta(days=14)
        return bank_nifty_month(new_date)
    else:
        return last_wednesday
    
def generate_banknifty_token_month_symbols(strikes, expiry_date):
    expiry_str = expiry_date.strftime('%d%b%y').upper()
    token_symbols = []

    for strike in strikes:
        token_symbols.append(f"BANKNIFTY{expiry_str}C{strike}")
        token_symbols.append(f"BANKNIFTY{expiry_str}P{strike}")

    return token_symbols

def generate_banknifty_token_symbols(strikes,date):
    today = date

    # Calculate the nearest Wednesday expiry date
    days_until_expiry = (2 - today.weekday() + 7) % 7  # 2 is Wednesday

    expiry_date = today + datetime.timedelta(days=days_until_expiry)

    # If today is after the calculated expiry date, move to the next week
    if today >= expiry_date:
        expiry_date += datetime.timedelta(days=days_until_expiry)

    expiry_str = expiry_date.strftime('%d%b%y').upper()
    token_symbols = []

    for strike in strikes:
        token_symbols.append(f"BANKNIFTY{expiry_str}C{strike}")
        token_symbols.append(f"BANKNIFTY{expiry_str}P{strike}")

    return token_symbols

def fin_nifty_month(date):

    # Calculate the last day of the current month
    last_day_of_month = datetime.date(date.year, date.month, 1) + datetime.timedelta(days=32)
    last_day_of_month = last_day_of_month.replace(day=1) - datetime.timedelta(days=1)

    # Calculate the last Tuesday of the current month
    last_tuesday = last_day_of_month - datetime.timedelta(days=(last_day_of_month.weekday() - 1 + 7) % 7)

    # Calculate the second last Tuesday of the current month
    if last_tuesday.weekday() == 1:  # If the last Tuesday is the last day of the month
        second_last_tuesday = last_tuesday - datetime.timedelta(days=7)
    else:
        second_last_tuesday = last_tuesday - datetime.timedelta(days=14)

    # Determine which Tuesday to return based on today's date
    if date > second_last_tuesday:
        # Add 14 days to today's date and recalculate the last Tuesday of the month
        new_date = date + datetime.timedelta(days=14)
        return fin_nifty_month(new_date)
    else:
        return last_tuesday
    
def generate_finnifty_token_month_symbols(strikes, expiry_date):
    expiry_str = expiry_date.strftime('%d%b%y').upper()
    token_symbols = []

    for strike in strikes:
        token_symbols.append(f"FINNIFTY{expiry_str}C{strike}")
        token_symbols.append(f"FINNIFTY{expiry_str}P{strike}")

    return token_symbols

def generate_fin_nifty_token_symbols(strikes,date):
    today = date

    # Calculate the nearest Tuesday expiry date
    days_until_expiry = (1 - today.weekday() + 7) % 7  # 1 is Tuesday

    expiry_date = today + datetime.timedelta(days=days_until_expiry)

    # If today is after the calculated expiry date, move to the next week
    if today >= expiry_date:
        expiry_date += datetime.timedelta(days=days_until_expiry)

    expiry_str = expiry_date.strftime('%d%b%y').upper()
    token_symbols = []

    for strike in strikes:
        token_symbols.append(f"FINNIFTY{expiry_str}C{strike}")
        token_symbols.append(f"FINNIFTY{expiry_str}P{strike}")

    return token_symbols










