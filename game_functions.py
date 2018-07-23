import random
import socket
import pickle
import zlib
import time

def print_loading_dots(delay, amount=3, spacing=3):
    for i in range(amount - 1):
        print("."+" "*spacing,end="",flush=True)
        time.sleep(delay)
    print(".",end="",flush=True)
    time.sleep(delay)
    print()

def print_properties(obj):
    print("\n".join(["{}: {}".format(v, w)
    for v,w in filter(lambda x: type(x[1]).__name__ != "builtin_function_or_method",
    [(y, getattr(obj, y)) for y in filter(lambda z: z[:2] != "__", dir(obj))])]))

def getRandomLineWeighted(filename):
    with open(filename, "r") as f:
        types = [x.split(",") for x in f.read().splitlines()]

    for i in range(len(types)):
        types[i][1] = int(types[i][1])

    probability_sum = sum([x[1] for x in types])
    roll = random.randint(1, probability_sum)
    cumulative_sum = 0
    for t in types:
        cumulative_sum += t[1]
        if cumulative_sum >= roll:
            return t[0]

def restrictive_input(prompt, process, condition, default=None):
    valid = False
    while not valid:
        if default:
            x = input("{} (default: {}): ".format(prompt, default))
            if len(x) == 0:
                return default
        else:
            x = input(prompt)
        try:
            x = process(x)
            valid = condition(x)
            if not valid:
                print("Invalid input!!")
        except:
            valid = False
    return x

def encode_DP(DP):
    return zlib.compress(pickle.dumps(DP),9)

def decode_DP(_DP):
    return pickle.loads(zlib.decompress(_DP))
