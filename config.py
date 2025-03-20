import os

class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://akila:admin123@cluster0.onqcq.mongodb.net/de-id?retryWrites=true&w=majority&appName=Cluster0")
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')
