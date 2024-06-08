from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)



def format_user(event):
    return {
        "user_name": event.user_name,
        "email": event.email,
        "id": event.id,
        "password":event.password
    }


# Route to get a user by ID
# @app.route('/users/<string:user_id>', methods=['GET'])
# def get_user_by_id(user_id):
#     # Find the user in the database by ID
#     user = User.query.get(user_id)

#     if user:
#         # If the user is found, format and return the user data
#         return jsonify({"user": format_user(user)})
#     else:
#         # If the user is not found, return a 404 response
#         return jsonify({"message": "User not found"}), 404



# Routes for User CRUD operations
@app.route('/', methods=['GET'])
def create_user():
    return jsonify({"message": "User created successfully", "data": "get success"})


# ... Other routes and code ...

if __name__ == '__main__':
    app.run()
