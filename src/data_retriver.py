from pymongo import MongoClient
import pandas as pd
import os

def get_data():
    # Connect to MongoDB
    client = MongoClient(os.getenv("MONGODB_URL"))
    db = client['exam_prep']

    # Fetch data from collections
    users = pd.DataFrame(list(db.users.find()))
    questions = pd.DataFrame(list(db.questions.find()))
    question_user_answers = pd.DataFrame(list(db.questionuseranswers.find()))

    # Check if collections are empty and handle accordingly
    if users.empty or questions.empty or question_user_answers.empty:
        return None

    # Data preprocessing
    # Ensure that user IDs and question IDs are converted to string
    users['_id'] = users['_id'].astype(str)
    questions['_id'] = questions['_id'].astype(str)
    question_user_answers['userId'] = question_user_answers['userId'].astype(str)
    question_user_answers['questionId'] = question_user_answers['questionId'].astype(str)

    # Merge user answers with question and user data
    data = question_user_answers.merge(questions, left_on='questionId', right_on='_id', suffixes=('_answer', '_question'))
    data = data.merge(users, left_on='userId', right_on='_id', suffixes=('', '_user'))

    return data