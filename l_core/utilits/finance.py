def get_pdv(value):
    return round(value/120*20,2)

def calculate_pdv(value):
    return round(value*0.2,2)

def get_without_pdw(value):
    return round(value-get_pdv(value),2)