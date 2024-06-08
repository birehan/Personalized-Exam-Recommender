import pandas as pd
import numpy as np
import nltk
import textstat
from textstat.textstat import textstat

from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import seaborn as sns
from pymongo import MongoClient
import logging

class QuestionDifficultyEstimator:
    """
    A class to estimate the difficulty of questions stored in a MongoDB collection.

    Args:
    - mongodb_uri (str): The MongoDB URI.
    - database_name (str): The name of the database containing the questions.
    - collection_name (str): The name of the collection containing the questions.

    Attributes:
    - mongodb_uri (str): The MongoDB URI.
    - database_name (str): The name of the database containing the questions.
    - collection_name (str): The name of the collection containing the questions.
    - client (pymongo.MongoClient): The MongoDB client.
    - db (pymongo.database.Database): The MongoDB database.
    - collection (pymongo.collection.Collection): The MongoDB collection.
    """
    def __init__(self, mongodb_uri: str, database_name: str, collection_name: str):
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = MongoClient(self.mongodb_uri)
        self.db = self.client[self.database_name]
        self.collection = self.db[self.collection_name]

    def extract_questions_from_mongodb(self) -> pd.DataFrame:
        try:
            cursor = self.collection.find({})
            questions = []
            for doc in cursor:
                description = doc.get('description', '')
                choices = [doc.get('choiceA', ''), doc.get('choiceB', ''), doc.get('choiceC', ''), doc.get('choiceD', '')]
                choices_str = ' '.join(filter(None, choices))  # Filter out empty choices
                question = {
                    '_id': doc['_id'],
                    'question': f"{description} {choices_str}"
                }
                questions.append(question)
            df = pd.DataFrame(questions)
            return df
        except Exception as e:
            print(f"Error extracting questions from MongoDB: {str(e)}")
            return None

    def extract_features(self, text: str) -> pd.Series:
        """
        Extracts features from a question.

        Args:
        - text (str): The question text.

        Returns:
        - pd.Series: A pandas Series containing the extracted features.
        """
        try:
            words = nltk.word_tokenize(text)
            sentences = nltk.sent_tokenize(text)
            num_words = len(words)
            num_sentences = len(sentences)
            avg_word_length = np.mean([len(word) for word in words])
            unique_words = len(set(words))
            flesch_kincaid = textstat.flesch_kincaid_grade(text)
            gunning_fog = textstat.gunning_fog(text)
            smog_index = textstat.smog_index(text)
            ari = textstat.automated_readability_index(text)
            
            return pd.Series([
                num_words, num_sentences, avg_word_length, unique_words,
                flesch_kincaid, gunning_fog, smog_index, ari
            ])
            
        except Exception as e:
            print(f"Error extracting features: {str(e)}")
            return None

    def estimate_question_difficulty(self) -> pd.DataFrame:
        """
        Estimates the difficulty of questions in the MongoDB collection.

        Returns:
        - pd.DataFrame: A DataFrame containing the questions and their estimated difficulty.
        """
        questions = self.extract_questions_from_mongodb()
        if questions is None:
            return None

        df = pd.DataFrame(questions, columns=['question', "_id"])
        df_features = df['question'].apply(self.extract_features)
        df_features.columns = [
            
            'num_words', 'num_sentences', 'avg_word_length', 'unique_words',
            'flesch_kincaid', 'gunning_fog', 'smog_index', 'ari'
        ]

        scaler = MinMaxScaler()
        df_scaled = pd.DataFrame(scaler.fit_transform(df_features), columns=df_features.columns)

        df_combined = pd.concat([df, df_scaled], axis=1)

        df_combined['estimated_difficulty'] = df_combined[['flesch_kincaid', 'gunning_fog', 'smog_index', 'ari']].mean(axis=1)
        df_combined['normalized_difficulty'] = (df_combined['estimated_difficulty'] - df_combined['estimated_difficulty'].min()) / (df_combined['estimated_difficulty'].max() - df_combined['estimated_difficulty'].min())
        return df_combined[['question', 'normalized_difficulty']]


    def update_question_difficulty(self):
        """
        Updates the difficulty of questions in the MongoDB collection.
        """
        questions = self.extract_questions_from_mongodb()
        if questions is None:
            return

        df = pd.DataFrame(questions, columns=['question', '_id'])
        df_features = df['question'].apply(self.extract_features)
        df_features.columns = [
            'num_words', 'num_sentences', 'avg_word_length', 'unique_words',
            'flesch_kincaid', 'gunning_fog', 'smog_index', 'ari'
        ]

        scaler = MinMaxScaler()
        df_scaled = pd.DataFrame(scaler.fit_transform(df_features), columns=df_features.columns)

        df_combined = pd.concat([df, df_scaled], axis=1)

        df_combined['estimated_difficulty'] = df_combined[['flesch_kincaid', 'gunning_fog', 'smog_index', 'ari']].mean(axis=1)
        df_combined['normalized_difficulty'] = (df_combined['estimated_difficulty'] - df_combined['estimated_difficulty'].min()) / (
                df_combined['estimated_difficulty'].max() - df_combined['estimated_difficulty'].min())
        # print(list(df_combined.columns))
        for _, row in df_combined.iterrows():
            question_id = row['_id']
            difficulty = row['normalized_difficulty']
            self.collection.update_one({'_id': question_id}, {'$set': {'difficulty': difficulty}})
            

        