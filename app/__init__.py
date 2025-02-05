from flask import Flask
from config import Config
from .database import mongo

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize MongoDB
    mongo.init_app(app)
    
    # Ensure MongoDB is connected
    with app.app_context():
        db = mongo.cx  # Get the client
        if db:
            print(f"MongoDB connected to {db.address}")
        else:
            print("Failed to connect to MongoDB")
    
    # Now import routes AFTER initializing mongo
    from .routes import api_blueprint
    app.register_blueprint(api_blueprint)

    return app
