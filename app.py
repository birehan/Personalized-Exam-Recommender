from flask import Flask, jsonify, request
from flask_cors import CORS
from src.recommender import get_user_by_id, getUserExistingQuestionRecommendation
from user_analysis.user_analytics import get_recommended_content, get_user_analysis
import time

app = Flask(__name__)
CORS(app)

# Routes for User CRUD operations
@app.route('/', methods=['GET'])
def create_user():
    return jsonify({"message": "User created successfully", "data": "get success"})


# ... Other routes and code ...

if __name__ == '__main__':
    app.run()

def format_user(event):
    return {
        "user_name": event.user_name,
        "email": event.email,
        "id": event.id,
        "password":event.password
    }

# get_recommended_content

@app.route('/get_user_content_recommendation/<string:user_id>', methods=['GET'])
def get_user_content_recommendation(user_id):
    start_time = time.time()
    # Get user from database, if not exist handle the error
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            "data": None,
            "success": False,
            "message": f"User with id {user_id} not found",
            "errors": []
        }), 404
    
    
    
    response = get_recommended_content(user_id)
    end_time = time.time()
    
    # Calculate the total time taken
    total_time = end_time - start_time
    print(f"Total time taken: {total_time} seconds")
    
    return jsonify({
        "data": response,
        "success": True,
        "message": "Recommendations retrieved successfully",
        "errors": []
    })
    
    
@app.route('/get_user_analysis/<string:user_id>', methods=['GET'])
def get_user_an(user_id):
    start_time = time.time()
    # Get user from database, if not exist handle the error
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            "data": None,
            "success": False,
            "message": f"User with id {user_id} not found",
            "errors": []
        }), 404
    
    
    
    response = get_user_analysis(user_id)
    end_time = time.time()
    
    # Calculate the total time taken
    total_time = end_time - start_time
    print(f"Total time taken: {total_time} seconds")
    
    return jsonify({
        "data": response,
        "success": True,
        "message": "Recommendations retrieved successfully",
        "errors": []
    })
    


@app.route('/get_user_recommended_questions/<string:user_id>', methods=['GET'])
def get_user_recommended_questions(user_id):
    # Get user from database, if not exist handle the error
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            "data": None,
            "success": False,
            "message": f"User with id {user_id} not found",
            "errors": []
        }), 404
    
    # Get user departmentId from user
    print(user)
    department_id = user["department"]
    
    # Get subjects for the department
    
    # Get user recommendations
    recommendations = getUserExistingQuestionRecommendation(user_id, department_id)
    # print(recommendations)
    
    return jsonify({
        "data": recommendations,
        "success": True,
        "message": "Recommendations retrieved successfully",
        "errors": []
    })