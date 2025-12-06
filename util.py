def calculate_score(reaction_time_sec):
    ms = reaction_time_sec * 1000
    if ms < 180:
        return 0
    elif ms < 200:
        return 3
    elif ms < 225:
        return 2
    elif ms < 250:
        return 1
    else:
        return 0
