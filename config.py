import os

class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://admin:admin1234@cluster0.bd4gchk.mongodb.net/de-id?retryWrites=true&w=majority&appName=Cluster0")
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')
