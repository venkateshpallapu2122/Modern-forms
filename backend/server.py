from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Survey Models
class QuestionOption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    value: str

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # text, multiple_choice, rating, checkbox, email, phone
    title: str
    description: Optional[str] = None
    required: bool = False
    options: Optional[List[QuestionOption]] = None  # For multiple choice/checkbox
    min_rating: Optional[int] = None  # For rating questions
    max_rating: Optional[int] = None  # For rating questions

class Survey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    questions: List[Question]
    is_template: bool = False
    template_category: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    questions: List[Question]
    is_template: bool = False
    template_category: Optional[str] = None

class SurveyResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    survey_id: str
    responses: Dict[str, Any]  # question_id -> response
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

class SurveyResponseCreate(BaseModel):
    survey_id: str
    responses: Dict[str, Any]

# Survey API Routes
@api_router.post("/surveys", response_model=Survey)
async def create_survey(survey_data: SurveyCreate):
    survey_dict = survey_data.dict()
    survey_obj = Survey(**survey_dict)
    await db.surveys.insert_one(survey_obj.dict())
    return survey_obj

@api_router.get("/surveys", response_model=List[Survey])
async def get_surveys():
    surveys = await db.surveys.find({"is_template": False}).to_list(1000)
    return [Survey(**survey) for survey in surveys]

@api_router.get("/surveys/{survey_id}", response_model=Survey)
async def get_survey(survey_id: str):
    survey = await db.surveys.find_one({"id": survey_id})
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return Survey(**survey)

@api_router.put("/surveys/{survey_id}", response_model=Survey)
async def update_survey(survey_id: str, survey_data: SurveyCreate):
    survey_dict = survey_data.dict()
    survey_dict["updated_at"] = datetime.utcnow()
    
    result = await db.surveys.update_one(
        {"id": survey_id},
        {"$set": survey_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    updated_survey = await db.surveys.find_one({"id": survey_id})
    return Survey(**updated_survey)

@api_router.delete("/surveys/{survey_id}")
async def delete_survey(survey_id: str):
    result = await db.surveys.delete_one({"id": survey_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Survey not found")
    return {"message": "Survey deleted successfully"}

# Template API Routes
@api_router.get("/templates", response_model=List[Survey])
async def get_templates():
    templates = await db.surveys.find({"is_template": True}).to_list(1000)
    return [Survey(**template) for template in templates]

@api_router.post("/templates/{template_id}/create-survey", response_model=Survey)
async def create_survey_from_template(template_id: str, title: str):
    template = await db.surveys.find_one({"id": template_id, "is_template": True})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create new survey from template
    new_survey = Survey(
        title=title,
        description=template.get("description", ""),
        questions=[Question(**q) for q in template["questions"]],
        is_template=False
    )
    
    await db.surveys.insert_one(new_survey.dict())
    return new_survey

# Response API Routes
@api_router.post("/responses", response_model=SurveyResponse)
async def submit_response(response_data: SurveyResponseCreate):
    # Verify survey exists
    survey = await db.surveys.find_one({"id": response_data.survey_id})
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    response_obj = SurveyResponse(**response_data.dict())
    await db.responses.insert_one(response_obj.dict())
    return response_obj

@api_router.get("/surveys/{survey_id}/responses", response_model=List[SurveyResponse])
async def get_survey_responses(survey_id: str, page: int = 1, limit: int = 100, sort_by: str = "submitted_at", sort_order: str = "desc"):
    # Calculate skip value for pagination
    skip = (page - 1) * limit
    
    # Define sort order
    sort_direction = -1 if sort_order == "desc" else 1
    
    # Get responses with pagination and sorting
    responses = await db.responses.find({"survey_id": survey_id}).sort(sort_by, sort_direction).skip(skip).limit(limit).to_list(limit)
    
    return [SurveyResponse(**response) for response in responses]

@api_router.get("/surveys/{survey_id}/responses/stats")
async def get_survey_response_stats(survey_id: str):
    # Get total response count
    total_responses = await db.responses.count_documents({"survey_id": survey_id})
    
    # Get survey details
    survey = await db.surveys.find_one({"id": survey_id})
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Calculate completion rate and other stats
    responses = await db.responses.find({"survey_id": survey_id}).to_list(1000)
    
    # Calculate question-wise response stats
    question_stats = {}
    for question in survey.get("questions", []):
        question_id = question["id"]
        answered_count = 0
        response_data = []
        
        for response in responses:
            if question_id in response.get("responses", {}):
                answered_count += 1
                response_data.append(response["responses"][question_id])
        
        completion_rate = (answered_count / total_responses * 100) if total_responses > 0 else 0
        
        # For multiple choice questions, calculate option distribution
        option_distribution = {}
        if question["type"] == "multiple_choice":
            for resp in response_data:
                if resp:
                    option_distribution[resp] = option_distribution.get(resp, 0) + 1
        
        # For rating questions, calculate average
        average_rating = None
        if question["type"] == "rating":
            numeric_responses = [r for r in response_data if isinstance(r, (int, float))]
            if numeric_responses:
                average_rating = sum(numeric_responses) / len(numeric_responses)
        
        question_stats[question_id] = {
            "question_title": question["title"],
            "question_type": question["type"],
            "answered_count": answered_count,
            "completion_rate": completion_rate,
            "option_distribution": option_distribution,
            "average_rating": average_rating
        }
    
    return {
        "total_responses": total_responses,
        "survey_title": survey["title"],
        "question_stats": question_stats
    }

# Initialize default templates
@api_router.post("/init-templates")
async def initialize_templates():
    # Check if templates already exist
    existing_templates = await db.surveys.count_documents({"is_template": True})
    if existing_templates > 0:
        return {"message": "Templates already initialized"}
    
    # Customer Feedback Template
    customer_feedback = Survey(
        title="Customer Feedback Survey",
        description="Collect valuable feedback from your customers",
        is_template=True,
        template_category="Customer Service",
        questions=[
            Question(
                type="rating",
                title="How would you rate our service?",
                description="Rate from 1 to 5",
                required=True,
                min_rating=1,
                max_rating=5
            ),
            Question(
                type="multiple_choice",
                title="How did you hear about us?",
                required=True,
                options=[
                    QuestionOption(text="Social Media", value="social_media"),
                    QuestionOption(text="Search Engine", value="search_engine"),
                    QuestionOption(text="Word of Mouth", value="word_of_mouth"),
                    QuestionOption(text="Advertisement", value="advertisement"),
                    QuestionOption(text="Other", value="other")
                ]
            ),
            Question(
                type="text",
                title="What can we improve?",
                description="Please share your suggestions",
                required=False
            ),
            Question(
                type="email",
                title="Email (optional)",
                description="We may contact you for follow-up",
                required=False
            )
        ]
    )
    
    # Employee Satisfaction Template
    employee_satisfaction = Survey(
        title="Employee Satisfaction Survey",
        description="Measure employee satisfaction and engagement",
        is_template=True,
        template_category="HR",
        questions=[
            Question(
                type="rating",
                title="How satisfied are you with your current role?",
                required=True,
                min_rating=1,
                max_rating=5
            ),
            Question(
                type="multiple_choice",
                title="What motivates you most at work?",
                required=True,
                options=[
                    QuestionOption(text="Career Growth", value="career_growth"),
                    QuestionOption(text="Compensation", value="compensation"),
                    QuestionOption(text="Work-Life Balance", value="work_life_balance"),
                    QuestionOption(text="Team Environment", value="team_environment"),
                    QuestionOption(text="Recognition", value="recognition")
                ]
            ),
            Question(
                type="checkbox",
                title="What benefits are most important to you?",
                required=False,
                options=[
                    QuestionOption(text="Health Insurance", value="health_insurance"),
                    QuestionOption(text="Remote Work", value="remote_work"),
                    QuestionOption(text="Professional Development", value="professional_development"),
                    QuestionOption(text="Flexible Hours", value="flexible_hours"),
                    QuestionOption(text="Retirement Plans", value="retirement_plans")
                ]
            ),
            Question(
                type="text",
                title="Additional comments or suggestions",
                required=False
            )
        ]
    )
    
    # Event Feedback Template
    event_feedback = Survey(
        title="Event Feedback Survey",
        description="Gather feedback about your event",
        is_template=True,
        template_category="Events",
        questions=[
            Question(
                type="rating",
                title="How would you rate the overall event?",
                required=True,
                min_rating=1,
                max_rating=5
            ),
            Question(
                type="multiple_choice",
                title="Which session did you find most valuable?",
                required=True,
                options=[
                    QuestionOption(text="Opening Keynote", value="opening_keynote"),
                    QuestionOption(text="Panel Discussion", value="panel_discussion"),
                    QuestionOption(text="Workshop", value="workshop"),
                    QuestionOption(text="Networking Session", value="networking"),
                    QuestionOption(text="Closing Remarks", value="closing_remarks")
                ]
            ),
            Question(
                type="text",
                title="What topics would you like to see in future events?",
                required=False
            ),
            Question(
                type="multiple_choice",
                title="Would you recommend this event to others?",
                required=True,
                options=[
                    QuestionOption(text="Definitely", value="definitely"),
                    QuestionOption(text="Probably", value="probably"),
                    QuestionOption(text="Maybe", value="maybe"),
                    QuestionOption(text="Probably Not", value="probably_not"),
                    QuestionOption(text="Definitely Not", value="definitely_not")
                ]
            )
        ]
    )
    
    # Insert templates
    await db.surveys.insert_one(customer_feedback.dict())
    await db.surveys.insert_one(employee_satisfaction.dict())
    await db.surveys.insert_one(event_feedback.dict())
    
    return {"message": "Templates initialized successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()