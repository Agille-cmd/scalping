from collections import defaultdict

user_pairs = defaultdict(set)
user_rsi_period = defaultdict(lambda: 14)

def add_pair(user_id, pair):
    user_pairs[user_id].add(pair)

def remove_pair(user_id, pair):
    user_pairs[user_id].discard(pair)

def clear_pairs(user_id):
    user_pairs[user_id].clear()

def set_rsi_period(user_id, period):
    user_rsi_period[user_id] = period

def get_rsi_period(user_id):
    return user_rsi_period[user_id]

def get_user_pairs(user_id):
    return list(user_pairs[user_id])