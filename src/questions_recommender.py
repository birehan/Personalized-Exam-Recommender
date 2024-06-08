from pymongo import MongoClient
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from flask import Flask, request, jsonify

# app = Flask(__name__)

def get_data():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
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
    collaborative_filtering

    return data


def collaborative_filtering(user_id, data):
    # Create user-item interaction matrix
    user_item_matrix = data.pivot_table(index='userId', columns='questionId', values='userAnswer', aggfunc='count', fill_value=0)
    
    # Compute similarity between users
    user_similarities = cosine_similarity(user_item_matrix)
    user_similarities_df = pd.DataFrame(user_similarities, index=user_item_matrix.index, columns=user_item_matrix.index)
    
    # Get the top similar users
    similar_users = user_similarities_df[user_id].sort_values(ascending=False).index[1:]
    
    # Recommend questions based on similar users' interactions
    recommended_questions = user_item_matrix.loc[similar_users].sum().sort_values(ascending=False).index
    return recommended_questions

def content_based_filtering(user_id, data):
    # Combine question descriptions and related topics into a single string
    data['question_content'] = data['description'] + " " + data['relatedTopic']
    
    # Compute TF-IDF matrix
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(data['question_content'])
    
    # Compute similarity between questions
    question_similarities = cosine_similarity(tfidf_matrix)
    question_similarities_df = pd.DataFrame(question_similarities, index=data['questionId'], columns=data['questionId'])
    
    # Get the user's answered questions
    user_answers = data[data['userId'] == user_id]['questionId']
    
    # Recommend questions based on content similarity
    recommended_questions = question_similarities_df.loc[user_answers].sum().sort_values(ascending=False).index
    return recommended_questions

def hybrid_recommendation(user_id, data, alpha=0.5):
    cf_recommendations = collaborative_filtering(user_id, data)
    cb_recommendations = content_based_filtering(user_id, data)
    
    # Check if recommendations are empty or not
    if cf_recommendations.empty or cb_recommendations.empty:
        return pd.Series()  # Return an empty Series
    
    # Convert recommendations to Series if they are not already
    cf_recommendations = cf_recommendations.to_series()
    cb_recommendations = cb_recommendations.to_series()
    
    # Combine the recommendations with a weighted average
    # combined_recommendations = (alpha * cf_recommendations + (1 - alpha) * cb_recommendations).sort_values(ascending=False)
    return cf_recommendations



# @app.route('/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    data = get_data()
    if data is None:
        return
        # return jsonify({"error": "Insufficient data to generate recommendations"}), 400
    
    print(list(data.columns))
    # Check if user ID exists in the data
    if user_id not in data['userId'].values:
        return 
        return jsonify({"error": f"User ID {user_id} not found"}), 404
        
         
    recommendations = hybrid_recommendation(user_id, data)
    return jsonify(recommendations.tolist())

# if __name__ == '__main__':
#     app.run(debug=True)

