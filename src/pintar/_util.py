

def dict_deep_update(d, u):
    if u is None:
        return d

    for k, v in u.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            dict_deep_update(d[k], v)
        else:
            d[k] = v
    return d



