import numpy as np
import pandas as pd
import json

class NpEncoder(json.JSONEncoder):
    """
    Custom encoder to handle Numpy data types which are not JSON serializable by default.
    Essential for returning Pandas results to React.
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super(NpEncoder, self).default(obj)

def clean_filename(filename: str) -> str:
    return "".join(x for x in filename if x.isalnum() or x in "._-")