import os

API_BASE_URL =              os.getenv("API_BASE_URL", "http://gluetun:3128")
DEBUG =                     os.getenv("DEBUG", "0") == "1"
REQUEST_TIMEOUT_SECONDS =   10
WAIT_TIMEOUT_SECONDS =      120
FOLDERWATCH_ID =            "folderwatch"
FOLDERWATCH_FOLDER =        '["/watch"]'
EXTRACTION_PASSWORDS =      os.getenv("EXTRACTION_PASSWORDS","")
PREMIUM_ACCOUNT_HOSTER =    os.getenv("PREMIUM_ACCOUNT_HOSTER","")
PREMIUM_ACCOUNT_USERNAME =  os.getenv("PREMIUM_ACCOUNT_USERNAME","")
PREMIUM_ACCOUNT_PASSWORD =  os.getenv("PREMIUM_ACCOUNT_PASSWORD","")
