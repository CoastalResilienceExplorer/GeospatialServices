

def get_resolution(ds):
    return [
        abs(ds.x.values[1] - ds.x.values[0]),
        abs(ds.y.values[1] - ds.y.values[0])
    ]