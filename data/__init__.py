from pathlib import Path

def path(filename):
    # __file__ is the path to this __init__.py file
    # e.g., /project/wildfires/data/__init__.py
    data_dir = Path(__file__).parent  # Gets /project/wildfires/data/
    return data_dir / filename  # Returns /project/wildfires/data/filename