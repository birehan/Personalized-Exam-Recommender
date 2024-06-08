from pymongo import MongoClient
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def collaborative_filter(user_id, subject, data):
    try:
        logging.info(f"Starting collaborative filtering for user_id: {user_id} and subject: {subject}")
        
        # Filter data for the specified subject
        subject_data = data[data['subject'] == subject]
        
        if subject_data.empty:
            logging.warning(f"No data found for subject: {subject}")
            return []

        # Create user-item interaction matrix
        user_item_matrix = subject_data.pivot_table(index='userId', columns='questionId', values='userAnswer', aggfunc='count', fill_value=0)
        
        if user_item_matrix.empty:
            logging.warning("User-item interaction matrix is empty")
            return []

        # Check if user_id is in user_item_matrix
        if user_id not in user_item_matrix.index:
            logging.warning(f"user_id: {user_id} not found in user-item interaction matrix")
            return []

        # Compute similarity between users
        user_similarities = cosine_similarity(user_item_matrix)
        user_similarities_df = pd.DataFrame(user_similarities, index=user_item_matrix.index, columns=user_item_matrix.index)
        
        # Get the top similar users
        similar_users = user_similarities_df[user_id].sort_values(ascending=False).index[1:]
        
        if similar_users.empty:
            logging.warning("No similar users found")
            return []

        # Filter out questions already answered by the user and where the user answered correctly
        user_questions = subject_data[(subject_data['userId'] == user_id) & (subject_data['userAnswer'] == subject_data['answer'])]['questionId']
        questions_not_answered_correctly = user_item_matrix.columns[~user_item_matrix.columns.isin(user_questions)]
        
        if questions_not_answered_correctly.empty:
            logging.warning("No questions found that were not answered correctly")
            return []

        # Recommend questions based on similar users' interactions and user's failing points
        recommended_questions = user_item_matrix.loc[similar_users, questions_not_answered_correctly].sum().sort_values(ascending=False).index[:100]
        logging.info(f"Recommended questions for {subject}: {len(recommended_questions.tolist())}")
        return recommended_questions.tolist()
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return []

# Example usage:
# data = get_data()
# recommendations = collaborative_filter(user_id='some_user_id', subject='Mathematics', data=data)
