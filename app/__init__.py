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
        db = mongo.db  # Access the database
        if db is not None:
            print(f"MongoDB connected to database: {db.name}")
            # Check if the 'records' collection exists
            if 'records' in db.list_collection_names():
                print("'records' collection exists.")
            else:
                print("'records' collection does not exist.")
        else:
            print("Failed to connect to MongoDB.")
    
    # Now import routes AFTER initializing mongo
    from .routes import api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
