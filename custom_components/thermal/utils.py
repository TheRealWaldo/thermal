'''Utils'''

def constrain(val, min_val, max_val):
  return min(max_val, max(min_val, val))


def map_value(x, in_min, in_max, out_min, out_max):
  if type(x) == str:
    x = float(x)
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min