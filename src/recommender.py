from src.data_retriver import get_data
from src.collaborative_filtering import collaborative_filter
from pymongo import MongoClient
from bson.objectid import ObjectId


def get_user_by_id(user_id: str):
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['exam_prep']

    # Fetch courses related to the specified department_id
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    # Extract unique subjects
    
    return user

def get_subjects_by_department(department_id: str):
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['exam_prep']
    department_object_id = ObjectId(department_id)

    # Fetch courses related to the specified department_id
    courses = db.courses.find({"departmentId": department_object_id})
    
    # Extract unique subjects
    subjects = set(course["name"] for course in courses)
    
    return list(subjects)

def getUserExistingQuestionRecommendation(user_id: str, department_id: str):
    data = get_data()
    subjects = get_subjects_by_department(department_id)
    
    recommends = []
    for subject in subjects:
        recommended_questions = collaborative_filter(user_id, subject, data)
        recommends.append({
            "subject": str(subject),
            "departmentId": str(department_id),
            "questions": [str(q) for q in recommended_questions]
        })
    
    return recommends