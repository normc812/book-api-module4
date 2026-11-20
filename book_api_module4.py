# book_api_mopdule4.py
# author: n blizard with help from AI and Caleb Curry videos on API
# date: Nov 19 2026
# github url: https://github.com/normc812/book-api-module4/book_api_module4.py

# purpose: This module implements a RESTful API for managing 
# a collection of books using Flask and SQLAlchemy.
#
# procedure:
# 1. Import necessary libraries and modules.    
# 2. Import tools needed to build the API.
# 3. Flask creates web application.
# 4. jsonify converts Python data into JSON responses.
# 5. request reads data sent by the client.
# 6. SQLAlchemy works with database records using Python objects.
#
# must run: python -m pip install Flask Flask-SQLAlchemy
# must also run (to resolve where Flask-SQLAlchemy is installed)
# python -m pip install Flask Flask-SQLAlchemy (to install Flask and SQLAlchemy)
# python .\book_api_module4.py  (to run the server)

from flask import Flask, jsonify, request  # AI suggested to import jsonify and request from flask

# SQLAlchemy works with database records using Python objects.
from flask_sqlalchemy import SQLAlchemy

# Create the Flask application.
app = Flask(__name__)

# Point to use a SQLite database named books.db.
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"

# Connect SQLAlchemy to Flask app.  db is the database object to define models
# and interact with the database.  It is used to define the Book model 
# and perform CRUD operations.
db = SQLAlchemy(app)

# List the editable book fields and their maximum text lengths.
# Reuse this dictionary to validate, create, and update books.
FIELDS = {
    "book_name": 200,
    "author": 150,
    "publisher": 150,
}

# Book is class to describe the books table in the database.
# Each Book object represents one row in that table.
class Book(db.Model):
    __tablename__ = "books"

    # The primary key uniquely identifies each book.
    # The database generates this ID when a new book is saved.
    id = db.Column(db.Integer, primary_key=True)

    # These columns store text.
    # nullable=False prevents these columns from storing NULL.
    # Validation function also checks for empty text (null).
    
    book_name = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    publisher = db.Column(db.String(150), nullable=False)

    def to_dict(self):
        # Convert Book object into a Python dictionary.
        # Later, we can turn the dictionary into a JSON response.
        return {
            "id": self.id,
            "book_name": self.book_name,
            "author": self.author,
            "publisher": self.publisher,
        }

# Check incoming data before saving it to the database.
def validate_book(data):
    # The request must contain a JSON object, which becomes a dictionary.
    if not isinstance(data, dict):
        return "Request body must be a JSON object."

    # Check each required field and its maximum length.
    for field, limit in FIELDS.items():
        # .get() returns None if the field is missing.
        value = data.get(field)

        # Require text that contains more than spaces.
        # .strip() removes spaces from the beginning and end.
        if not isinstance(value, str) or not value.strip():
            return f"'{field}' must be a nonempty string."

        # Reject text that is longer than the allowed limit.
        if len(value.strip()) > limit:
            return f"'{field}' must be {limit} characters or fewer."

    # None means that no validation errors were found.
    return None


# The home page displays a welcome message.
# Routes use GET by default when no methods are specified.
@app.route("/") # decorator to define the route for the home page
def home():
    return jsonify({
        "message": "Welcome to the Book API",
        "books_endpoint": "/books",
    })

# READ: Get every book in the database.
@app.route("/books") # decorator to define the route for getting all books
def get_books():
    # Select all Book records, ordered by their IDs.
    # .scalars() gives us Book objects.
    # .all() collects the results into a list.
    books = db.session.scalars(
        db.select(Book).order_by(Book.id)
    ).all()

    # Convert every Book object into a dictionary.
    # Return those dictionaries as a JSON list inside "books".
    return jsonify({"books": [book.to_dict() for book in books]})

# READ: Get one book using its ID.
# <int:book_id> takes an integer from the URL and passes it to this function.
@app.route("/books/<int:book_id>") # decorator to define the route for getting a specific book by its ID
def get_book(book_id):
    # Look up the book by its primary key.
    book = db.session.get(Book, book_id)

    # If the book does not exist, return an error.
    # HTTP status 404 means "Not Found."
    if book is None:
        return jsonify({"error": "Book not found."}), 404

    return jsonify(book.to_dict())

# CREATE: Add a new book using a POST request.
@app.route("/books", methods=["POST"]) # decorator to define the route for creating a new book
def create_book():
    # Read the JSON sent by the client.
    # silent=True returns None if the request does not contain valid JSON.
    data = request.get_json(silent=True)

    # Check that all required fields contain valid text.
    error = validate_book(data)

    # HTTP status 400 means "Bad Request."
    if error:
        return jsonify({"error": error}), 400

    # Build a dictionary containing only the allowed book fields.
    # Strip extra spaces from each value.
    # ** passes the dictionary entries as named arguments to Book().
    book = Book(**{field: data[field].strip() for field in FIELDS})

    # Add the new book to the database session.
    db.session.add(book)

    # Commit saves the change to the database.
    db.session.commit()

    # Return the saved book, including its generated ID.
    # HTTP status 201 means "Created."
    return jsonify(book.to_dict()), 201

# UPDATE: Change an existing book using a PUT request.
@app.route("/books/<int:book_id>", methods=["PUT"]) # decorator to define the route for updating an existing book by its ID
def update_book(book_id):
    # Find the book that the client wants to update.
    book = db.session.get(Book, book_id)

    if book is None:
        return jsonify({"error": "Book not found."}), 404

    # Read and validate the new book information.
    # This route requires all three editable fields.
    data = request.get_json(silent=True)
    error = validate_book(data)

    if error:
        return jsonify({"error": error}), 400

    # Update each editable field.
    # setattr() changes an attribute using its name as a string.
    for field in FIELDS:
        setattr(book, field, data[field].strip())

    # Save the updated values.
    db.session.commit()

    return jsonify(book.to_dict())


# DELETE: Remove a book using its ID.
@app.route("/books/<int:book_id>", methods=["DELETE"]) # de
def delete_book(book_id):
    # Find the book to delete.
    book = db.session.get(Book, book_id)

    if book is None:
        return jsonify({"error": "Book not found."}), 404

    # Mark the book for deletion, then save that change.
    db.session.delete(book)
    db.session.commit()

    return jsonify({
        "message": "Book deleted successfully.",
        "id": book_id,
    })


# Make SQLAlchemy access to this application's configuration.
# Create the database tables if they do not already exist.
with app.app_context():
    db.create_all()

# Start the server only when this file is run directly.
# This block does not run if another Python file imports this file.
if __name__ == "__main__":  # check if this file is being run directly
    # Start the Flask development server.   
    app.run()