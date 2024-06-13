from pymongo import MongoClient
import os
from bson.objectid import ObjectId
from openai import OpenAI
import json

def get_user_course_completion(user_id: str, course_name: str="Biology"):
    client = MongoClient(os.getenv("MONGODB_URL"))
    db = client['exam_prep']
    userId = ObjectId(user_id)
    selected_courses = list(db.courses.find({"name": course_name}))
    user_ana = []
    for course in selected_courses:
        user_courses_analytics = db.usercourseanalyses.find_one({"userId": userId, "courseId": course["_id"]})
        # completedChapters
        user_ana.append({
            "subject": course_name,
            "grade": course["grade"],
            "completedChapters": user_courses_analytics["completedChapters"] if user_courses_analytics else 0,
            "totalChapters": course['noOfChapters']
        })
        
    return user_ana

def get_user_questions_completion_by_year(user_id: str, course_name: str="Biology"):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['exam_prep']
    collection = db['questions']
    questions = list(collection.find({"subject": course_name}))
      
    grouped_questions = {}
    for question in questions:
        year = question.get('year') or question.get('Year')
        if year not in grouped_questions:
            grouped_questions[year] = []

        grouped_questions[year].append(question)
         
    response = []

    total = 0
    for year, questions in grouped_questions.items():
        completedQuestions = 0
        for que in questions:
            ques_user = db.questionuseranswers.find_one({"userId": ObjectId(user_id), "questionId": que["_id"]})
            if ques_user: completedQuestions += 1
            
        total += len(questions)
        response.append({
            "subject": course_name,
            "year": year,
            "completedQuestions": completedQuestions,
            "totalQuestions": len(questions),
            
        })
    
    return response

def get_user_detailed_analysis(user_id: str="653f7ab56573ad474f150261", course_id: str="6530d803128c1e08e946def8") -> dict:
    client = MongoClient(os.getenv("MONGODB_URL"))
    db = client['exam_prep']
    course = db.courses.find_one({"_id":ObjectId(course_id) })
    chapters = list(db.chapters.find({"courseId": {"$in": [course_id, ObjectId(course_id)]}}))
    
    user_solved_questions = list(db.questionuseranswers.find({"userId": {"$in": [user_id, ObjectId(user_id)]}}))
    user_solved_course_questions = []
    correctly_answered = 0
    for user_q in user_solved_questions:
        question = db.questions.find_one({"_id": {"$in": [user_q["questionId"], ObjectId(user_q["questionId"])]}})
        if question and str(question["courseId"]) == course_id:
            question["is_answered"] =  str(question["answer"]) == str(user_q["userAnswer"])
            if question["is_answered"]:
                correctly_answered += 1
            
            user_solved_course_questions.append(question)
        
    total_difficulty = sum(q["difficulty"] for q in user_solved_course_questions)
    user_answered_total_difficulty =  sum(q["difficulty"] for q in user_solved_course_questions if q["is_answered"])
    
    
    user_chapters = []
    for chapter in chapters:
        chapter_total_questions = [q for q in user_solved_course_questions if str(q["chapterId"]) == str(chapter["_id"])]
        chapter_correct_answered = len([q for q in chapter_total_questions if q["is_answered"]])
        user_subchapters = []
        subchapters = list(db.subchapters.find({"chapterId": {"$in": [str(chapter["_id"]), ObjectId(chapter["_id"])]}}))
        
        chapter_total_difficulty  = sum([q["difficulty"] for q in chapter_total_questions])
        chapter_answered_total_difficulty = sum([q["difficulty"] for q in chapter_total_questions if q["is_answered"]])
        
        
        for subchapter in subchapters:
            subchapter_total_questions = [q for q in user_solved_course_questions if str(q["subChapterId"]) == str(subchapter["_id"])]
            subchapter_correct_answered = len([q for q in subchapter_total_questions if q["is_answered"]])
            
            subchapter_total_difficulty  = sum([q["difficulty"] for q in subchapter_total_questions])
            subchapter_answered_total_difficulty = sum([q["difficulty"] for q in subchapter_total_questions if q["is_answered"]])
            
            user_subchapters.append({
                "order": subchapter["order"],
                "sub chapter name": subchapter['name'],
                "user solved total questions on the chapter": len(chapter_total_questions),
                "user correctly answer questions on the chapter": chapter_correct_answered,
                "user average answer score on subchapter": subchapter_correct_answered/(len(subchapter_total_questions) if len(subchapter_total_questions) !=0 else 1),
                "user answered questions average difficulty on subchapter": subchapter_answered_total_difficulty/(subchapter_total_difficulty if subchapter_total_difficulty!=0 else 1),
            })
            
            
        user_chapters.append({
            "order": chapter["order"],
            "chapter name": chapter["name"],
            "user solved total questions on the chapter": len(chapter_total_questions),
            "user correctly answer questions on the chapter": chapter_correct_answered,
            "user average answer score": chapter_correct_answered/(len(chapter_total_questions) if len(chapter_total_questions) !=0 else 1),
            "user answered questions average difficulty": chapter_answered_total_difficulty/(chapter_total_difficulty if chapter_total_difficulty!=0 else 1),
            "subchapters": user_subchapters
        })
        

    
    response = {
        "course name": course["name"],
        "course description": course["description"],
        "grade": course["grade"],
        "user solved total questions on the course": len(user_solved_course_questions),
        "user correctly answer questions on the course": correctly_answered,
        "user answered questions average difficulty": user_answered_total_difficulty/(total_difficulty if total_difficulty!=0 else 1),
        "chapters": user_chapters
    }
    

    return response
    


def get_user_analysis(user_id: str, course_name:str="Biology") -> dict:
    client = MongoClient(os.getenv("MONGODB_URL"))
    db = client['exam_prep']
    selected_courses = list(db.courses.find({"name": course_name}))
    response = []
    
    for course in selected_courses:
        detaild_data = get_user_detailed_analysis(user_id, str(course["_id"]))
        response.append( detaild_data)
    
    return response
    

# Set your OpenAI API key
def get_llm_content(user_data: str):    
    from openai import OpenAI
    client = OpenAI(os.getenv("OPENAI_API_KEY"))
 
    # Craft the prompt for the OpenAI model
    prompt =  '''
        Make user you are talking with the user. 
        Based on the following user performance data, provide a recommendation on which topics or subchapters the user should focus on improving. 
        The recommendation should consider both the number of questions answered and the user's overall performance in each subchapter.
        And also give him some summary about his faild topics for example if his performance is low in <Biotechnolgoy>, give him an explantion about it.
        return a json object with format: {"recommendation": {"paragraph": "", "key_points": ["", ""]}}
        User Data:
        {user_data}

        Recommendation:
        '''
  
    # Use OpenAI's API to get the recommendation using client.chat.completions.create
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # Specify the GPT-3.5 Turbo model
    response_format={ "type": "json_object" },
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=300,
    n=1,
    stop=None,
    temperature=0.7
    )
    
    recommendation = json.loads(response.choices[0].message.content)
    return recommendation["recommendation"]

def get_recommended_content(user_id: str="653f7ab56573ad474f150261", course_name: str="Biology") -> dict:
    client = MongoClient(os.getenv("MONGODB_URL"))
    db = client['exam_prep']
    selected_courses = list(db.courses.find({"name": course_name}))
    response = []
    datas = []
    
    for course in selected_courses:
        detaild_data = get_user_detailed_analysis(user_id, str(course["_id"]))
        datas.append(detaild_data)
        llm_response = get_llm_content(detaild_data)        
        response.append({
            "course_data": detaild_data,
            "content_recommended": llm_response
        })
    
    return response
    
    '''
    {
        message: "textual"
        existing_recommended_questions: [],
        ai_generated_recommened_questions: []
    }
    '''


# get_user_questions_completion_by_year("653f7ab56573ad474f150261")

# get_recommended_content()