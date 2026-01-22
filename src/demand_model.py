def predict_demand(stipend):
    if stipend > 20000:
        return "High"
    elif stipend > 10000:
        return "Medium"
    return "Low"