
from typing import List
from pymongo import MongoClient
import pandas as pd
import os
from openai import OpenAI
import json


def read_subchapters_ids(file_path="completed_subchapters.json"):
    with open(file_path, 'r') as file:
        data = json.load(file)
        subchapters_ids = data.get('subchaptersIds', [])
    return subchapters_ids

def append_to_subchapters_ids(new_subchapter_id, file_path="completed_subchapters.json"):
    subchapters_ids = read_subchapters_ids(file_path)
    subchapters_ids.append(new_subchapter_id)
    with open(file_path, 'w') as file:
        json.dump({"subchaptersIds": subchapters_ids}, file, indent=4)



def save_questions_to_db(questions: list) -> None:
    try:
        client = MongoClient(os.getenv("MONGODB_URL"))
        db = client['exam_prep']
        result = db.questions.insert_many(questions)
        print(f"Successfully inserted {len(result.inserted_ids)} questions.")
    except Exception as e:
        print(f"An error occurred: {e}")

def save_json_list(json_list, file_path):
    with open(file_path, 'w') as file:
        json.dump(json_list, file, indent=4)
        
'''

   Generate {num_questions} multiple-choice questions with four options from choice A to choice D for each question, 
        provide the correct answer, question difficulty level (range(0, 1) with two decimal point float), explanation for the answer, 
        and related topic for each question from the following biology content:\n\n{content}\n\nFormat the output as follows:\n
        \nQuestion 1: <question content>\nA. <option 1>\nB. <option 2>\nC. <option 3>\nD. <option 4>\nAnswer: <correct option>\nDifficulty: <difficulty level>\nExplanation: <explanation>\nTopic: <related topic>\n\nQuestions:\n
        make the response format consistent
        
        
        '''
        
def generate_questions(client, content, num_questions=5):
    
    prompt = '''
        Generate {num_questions} multiple-choice questions with four options from choice A to choice D for each question, 
        provide the correct answer, question difficulty level (range(0, 1) with two decimal point float), explanation for the answer, 
        and related topic for each question from the following biology content:\n\n{content}
        return the answer in json format like given below:
        {'questions': [{
            'description': '',
            'choiceA': '',
            'choiceB': '',
            "choiceC": '',
            "choiceD": '',
            "answer": '<choice_A, choice_B, choice_C, choice_D>'  ,
            "difficulty": "',
            "explanation": "",
            "relatedTopic": ""
            }]}
        
        the answer for each question is one of the following: choice_A, choice_B,choice_C, choice_D. make it like answer: choice_A
        return a json object
        '''

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use the cheapest model
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.7
    )
    questions = json.loads(response.choices[0].message.content)
  
    return questions

def extract_courses_contents(subject: str) -> list:
    sub_chapter_ids = read_subchapters_ids()
    client = MongoClient(os.getenv("MONGODB_URL"))
    db = client['exam_prep']
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    
    
    courses = list(db.courses.find({"name": subject}))
    generated_questions = []
    
    for course in courses:
        departmentId = course["departmentId"]
        courseId = course["_id"]
         
        chapters = list(db.chapters.find({"courseId": course["_id"]}))
        for chapter in chapters:
            chapterId = chapter["_id"]
            subchapters = list(db.subchapters.find({"chapterId": chapter["_id"]}))
            for subchapter in subchapters:
                
                subChapterId = subchapter["_id"]
                
                if str(subChapterId) in sub_chapter_ids:
                    continue
                
                subchapterContents = list(db.subchaptercontents.find({"subChapterId": subchapter["_id"]}))
                content = "".join([subchapterContent["title"] + subchapterContent["content"] for subchapterContent in subchapterContents])
                cur_generated_questions = generate_questions(openai_client, content, 5)
                subchapter_questions = []
                for question in cur_generated_questions["questions"]:
                    subchapter_questions.append({
                        "description": question["description"],
                        "choiceA": question["choiceA"],
                        "choiceB": question["choiceB"],
                        "choiceC": question["choiceC"],
                        "choiceD": question["choiceD"],
                        "answer": question["answer"],
                        "explanation": question["explanation"],
                        "difficulty": question["difficulty"],
                        "relatedTopic": question["relatedTopic"],                        
                        "subChapterId": subChapterId,
                        "chapterId": chapterId,
                        "courseId": courseId,
                        "departmentId": departmentId,
                        
                        "subject": "Biology",
                        "year":  "AI",
                        "isForQuiz":  False,
                        "isForMock": True,
                        "adminApproval":  True
                    })
                
                save_questions_to_db(subchapter_questions)
                
                for q in subchapter_questions:
                    q["subChapterId"] = str(q["subChapterId"])
                    q["chapterId"] = str(q["chapterId"])
                    q["courseId"] = str(q["courseId"])
                    q["departmentId"] = str(q["departmentId"])
                    q["_id"] = str(q["_id"])
                    
                    
                
                save_json_list(subchapter_questions, "generated_questions.json")

            
                sub_chapter_ids.append(str(subChapterId))
                append_to_subchapters_ids(str(subChapterId))
                
                generated_questions.append(subchapter_questions)
                return
                
    return generated_questions