import faas_profiler_python as fp

import numpy as np
import sys

array = None
call = 0

@fp.profile()
def handler(event, context):
    global call
    global array

    new_array = np.array([1] * 10 ** (call % 8))
    if array is None:
        array = new_array
    else:
        array = np.concatenate([array,new_array])

    call += 1

    return {
        "size": sys.getsizeof(array),
        "call": call
    }
