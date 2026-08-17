import os

from dotenv import load_dotenv


load_dotenv()

uri = os.getenv("COGNODB_URI")
username = os.getenv("COGNODB_USERNAME")
password = os.getenv("COGNODB_PASSWORD")

print("URI configured:", bool(uri))
print("Username configured:", bool(username))
print("Password configured:", bool(password))