# from typing import List
# from pymongo import MongoClient
# import pandas as pd


# def extract_courses_contents(subject: str) -> list:
#     print("hi")
#     client = MongoClient('mongodb://localhost:27017/')
#     db = client['exam_prep']
    
#     courses = pd.DataFrame(list(db.courses.find({"name": subject})))
#     print(courses)
    
# extract_courses_contents("Biology")

# from openai import OpenAI
import openai