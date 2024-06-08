from pymongo import MongoClient
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def collaborative_filter(user_id, subject, data):
    # Filter data for the specified subject
    subject_data = data[data['subject'] == subject]
    
    # Create user-item interaction matrix
    user_item_matrix = subject_data.pivot_table(index='userId', columns='questionId', values='userAnswer', aggfunc='count', fill_value=0)
    
    # Compute similarity between users
    user_similarities = cosine_similarity(user_item_matrix)
    user_similarities_df = pd.DataFrame(user_similarities, index=user_item_matrix.index, columns=user_item_matrix.index)
    
    # Get the top similar users
    similar_users = user_similarities_df[user_id].sort_values(ascending=False).index[1:]
    
    # Filter out questions already answered by the user and where the user answered correctly
    user_questions = subject_data[(subject_data['userId'] == user_id) & (subject_data['userAnswer'] == subject_data['answer'])]['questionId']
    questions_not_answered_correctly = user_item_matrix.columns[~user_item_matrix.columns.isin(user_questions)]
    
    # Recommend questions based on similar users' interactions and user's failing points
    recommended_questions = user_item_matrix.loc[similar_users, questions_not_answered_correctly].sum().sort_values(ascending=False).index[:100]
    return recommended_questions