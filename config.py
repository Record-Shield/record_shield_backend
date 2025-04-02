import os

class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://admin:admin1234@cluster0.bd4gchk.mongodb.net/de-id?retryWrites=true&w=majority&appName=Cluster0")
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')
    AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN', 'dev-4xalqwtpzkjsisfj.au.auth0.com')
    CLIENT_ID = os.environ.get('CLIENT_ID', 'XdIWkZTnVSf5qdsxVMRLZWBVuhokGv8s')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET', 'aZZwlHzsnJFvDvoYJPCd43hLscLVpKHLv6TmiJ-e1Ip4epAipgiL5ok40CzCFCP5')
