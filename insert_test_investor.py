from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection string from environment variables
mongo_uri = os.getenv("MONGO_URI")  # Ensure this is set in your .env file

# Connect to MongoDB using the URI
client = MongoClient(mongo_uri, tls=True, tlsCAFile=certifi.where())

# Select the database and collection
db = client["auth_roles"]  # Replace with your actual database name
social_trends_collection = db["social"]  # Collection name

# Sample data to insert
sample_data = {
    "symbol": "BTC",
    "trend": "Rising",
    "mentions": 1000,
    "positive_sentiment": 85,
    "date": "2023-11-29"
}

# Insert the sample data into the collection
social_trends_collection.insert_one(sample_data)

print("Test social trend data inserted successfully!")





# import certifi
# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Get MongoDB connection string from environment variables
# mongo_uri = os.getenv("MONGO_URI")  # Ensure this is set in your .env file

# try:
#     # Connect to MongoDB Atlas using the URI with TLS enabled
#     client = MongoClient(mongo_uri, tls=True, tlsCAFile=certifi.where())  # Use tls=True, not ssl=True
#     db = client["auth_roles"]  # This is the specific database you're using
#     collection = db["investors"]  # This is the collection where you want to insert data
    
#     # Test document to insert
#     test_investor = {
#         "name": "Test Investor",
#         "investment_amount": 1000000,
#         "investment_date": "2023-01-01T00:00:00",
#         "coin_symbol": "BTC",
#         "category": "Institution"
#     }
    
#     # Insert the test document
#     collection.insert_one(test_investor)
    
#     print("Test document inserted successfully!")
    
# except Exception as e:
#     print("Error connecting to MongoDB:", e)
