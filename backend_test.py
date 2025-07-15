#!/usr/bin/env python3
"""
Backend API Testing for Survey Making Tool
Tests all CRUD operations, template system, response collection, and question types
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import os

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("ERROR: Could not get backend URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BASE_URL}/api"

print(f"Testing backend at: {API_BASE}")

class SurveyAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            'survey_crud': {'passed': 0, 'failed': 0, 'errors': []},
            'template_system': {'passed': 0, 'failed': 0, 'errors': []},
            'response_collection': {'passed': 0, 'failed': 0, 'errors': []},
            'question_types': {'passed': 0, 'failed': 0, 'errors': []},
            'enhanced_responses': {'passed': 0, 'failed': 0, 'errors': []},
            'response_analytics': {'passed': 0, 'failed': 0, 'errors': []}
        }
        self.created_surveys = []
        self.created_responses = []

    def log_result(self, category, test_name, success, error_msg=None):
        if success:
            self.test_results[category]['passed'] += 1
            print(f"✅ {test_name}")
        else:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['errors'].append(f"{test_name}: {error_msg}")
            print(f"❌ {test_name}: {error_msg}")

    def test_survey_crud_apis(self):
        print("\n=== Testing Survey CRUD APIs ===")
        
        # Test 1: Create Survey
        survey_data = {
            "title": "Customer Experience Survey",
            "description": "Help us improve our services",
            "questions": [
                {
                    "type": "text",
                    "title": "What is your name?",
                    "description": "Please enter your full name",
                    "required": True
                },
                {
                    "type": "multiple_choice",
                    "title": "How satisfied are you with our service?",
                    "required": True,
                    "options": [
                        {"text": "Very Satisfied", "value": "very_satisfied"},
                        {"text": "Satisfied", "value": "satisfied"},
                        {"text": "Neutral", "value": "neutral"},
                        {"text": "Dissatisfied", "value": "dissatisfied"}
                    ]
                },
                {
                    "type": "rating",
                    "title": "Rate our product quality",
                    "required": True,
                    "min_rating": 1,
                    "max_rating": 5
                }
            ]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/surveys", json=survey_data)
            if response.status_code == 200:
                survey = response.json()
                self.created_surveys.append(survey['id'])
                self.log_result('survey_crud', 'Create Survey', True)
                survey_id = survey['id']
            else:
                self.log_result('survey_crud', 'Create Survey', False, f"Status: {response.status_code}, Response: {response.text}")
                return
        except Exception as e:
            self.log_result('survey_crud', 'Create Survey', False, str(e))
            return

        # Test 2: Get All Surveys
        try:
            response = self.session.get(f"{API_BASE}/surveys")
            if response.status_code == 200:
                surveys = response.json()
                if isinstance(surveys, list) and len(surveys) > 0:
                    self.log_result('survey_crud', 'Get All Surveys', True)
                else:
                    self.log_result('survey_crud', 'Get All Surveys', False, "No surveys returned")
            else:
                self.log_result('survey_crud', 'Get All Surveys', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('survey_crud', 'Get All Surveys', False, str(e))

        # Test 3: Get Specific Survey
        try:
            response = self.session.get(f"{API_BASE}/surveys/{survey_id}")
            if response.status_code == 200:
                survey = response.json()
                if survey['id'] == survey_id and survey['title'] == survey_data['title']:
                    self.log_result('survey_crud', 'Get Specific Survey', True)
                else:
                    self.log_result('survey_crud', 'Get Specific Survey', False, "Survey data mismatch")
            else:
                self.log_result('survey_crud', 'Get Specific Survey', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('survey_crud', 'Get Specific Survey', False, str(e))

        # Test 4: Update Survey
        updated_data = {
            "title": "Updated Customer Experience Survey",
            "description": "Updated description for better feedback",
            "questions": survey_data['questions']
        }
        
        try:
            response = self.session.put(f"{API_BASE}/surveys/{survey_id}", json=updated_data)
            if response.status_code == 200:
                updated_survey = response.json()
                if updated_survey['title'] == updated_data['title']:
                    self.log_result('survey_crud', 'Update Survey', True)
                else:
                    self.log_result('survey_crud', 'Update Survey', False, "Title not updated")
            else:
                self.log_result('survey_crud', 'Update Survey', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('survey_crud', 'Update Survey', False, str(e))

        # Test 5: Delete Survey (will be done at cleanup)
        # We'll keep the survey for response testing and delete later

    def test_template_system(self):
        print("\n=== Testing Template System ===")
        
        # Test 1: Initialize Templates
        try:
            response = self.session.post(f"{API_BASE}/init-templates")
            if response.status_code == 200:
                result = response.json()
                self.log_result('template_system', 'Initialize Templates', True)
            else:
                self.log_result('template_system', 'Initialize Templates', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('template_system', 'Initialize Templates', False, str(e))

        # Test 2: Get Templates
        try:
            response = self.session.get(f"{API_BASE}/templates")
            if response.status_code == 200:
                templates = response.json()
                if isinstance(templates, list) and len(templates) >= 3:
                    self.log_result('template_system', 'Get Templates', True)
                    self.template_id = templates[0]['id']  # Store for next test
                else:
                    self.log_result('template_system', 'Get Templates', False, f"Expected at least 3 templates, got {len(templates) if isinstance(templates, list) else 0}")
            else:
                self.log_result('template_system', 'Get Templates', False, f"Status: {response.status_code}")
                return
        except Exception as e:
            self.log_result('template_system', 'Get Templates', False, str(e))
            return

        # Test 3: Create Survey from Template
        try:
            # Use query parameter for title
            response = self.session.post(f"{API_BASE}/templates/{self.template_id}/create-survey?title=Survey from Customer Feedback Template")
            if response.status_code == 200:
                survey = response.json()
                self.created_surveys.append(survey['id'])
                if survey['title'] == "Survey from Customer Feedback Template" and not survey.get('is_template', True):
                    self.log_result('template_system', 'Create Survey from Template', True)
                else:
                    self.log_result('template_system', 'Create Survey from Template', False, "Survey not created properly from template")
            else:
                self.log_result('template_system', 'Create Survey from Template', False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result('template_system', 'Create Survey from Template', False, str(e))

    def test_response_collection_system(self):
        print("\n=== Testing Response Collection System ===")
        
        if not self.created_surveys:
            self.log_result('response_collection', 'Submit Response', False, "No surveys available for testing")
            return

        survey_id = self.created_surveys[0]
        
        # Test 1: Submit Response
        response_data = {
            "survey_id": survey_id,
            "responses": {
                "question_1": "John Smith",
                "question_2": "very_satisfied",
                "question_3": 5
            }
        }
        
        try:
            response = self.session.post(f"{API_BASE}/responses", json=response_data)
            if response.status_code == 200:
                response_obj = response.json()
                self.created_responses.append(response_obj['id'])
                if response_obj['survey_id'] == survey_id:
                    self.log_result('response_collection', 'Submit Response', True)
                else:
                    self.log_result('response_collection', 'Submit Response', False, "Response survey_id mismatch")
            else:
                self.log_result('response_collection', 'Submit Response', False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result('response_collection', 'Submit Response', False, str(e))

        # Test 2: Submit Another Response
        response_data2 = {
            "survey_id": survey_id,
            "responses": {
                "question_1": "Jane Doe",
                "question_2": "satisfied",
                "question_3": 4
            }
        }
        
        try:
            response = self.session.post(f"{API_BASE}/responses", json=response_data2)
            if response.status_code == 200:
                response_obj = response.json()
                self.created_responses.append(response_obj['id'])
                self.log_result('response_collection', 'Submit Multiple Responses', True)
            else:
                self.log_result('response_collection', 'Submit Multiple Responses', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('response_collection', 'Submit Multiple Responses', False, str(e))

        # Test 3: Get Survey Responses
        try:
            response = self.session.get(f"{API_BASE}/surveys/{survey_id}/responses")
            if response.status_code == 200:
                responses = response.json()
                if isinstance(responses, list) and len(responses) >= 2:
                    self.log_result('response_collection', 'Get Survey Responses', True)
                else:
                    self.log_result('response_collection', 'Get Survey Responses', False, f"Expected at least 2 responses, got {len(responses) if isinstance(responses, list) else 0}")
            else:
                self.log_result('response_collection', 'Get Survey Responses', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('response_collection', 'Get Survey Responses', False, str(e))

    def test_question_types_support(self):
        print("\n=== Testing Question Types Support ===")
        
        # Create a comprehensive survey with all question types
        comprehensive_survey = {
            "title": "Comprehensive Question Types Test",
            "description": "Testing all supported question types",
            "questions": [
                {
                    "type": "text",
                    "title": "What is your full name?",
                    "description": "Enter your complete name",
                    "required": True
                },
                {
                    "type": "email",
                    "title": "What is your email address?",
                    "description": "We'll use this to contact you",
                    "required": True
                },
                {
                    "type": "multiple_choice",
                    "title": "What is your preferred contact method?",
                    "required": True,
                    "options": [
                        {"text": "Email", "value": "email"},
                        {"text": "Phone", "value": "phone"},
                        {"text": "Text Message", "value": "sms"},
                        {"text": "Mail", "value": "mail"}
                    ]
                },
                {
                    "type": "checkbox",
                    "title": "Which services are you interested in?",
                    "required": False,
                    "options": [
                        {"text": "Web Development", "value": "web_dev"},
                        {"text": "Mobile Apps", "value": "mobile_apps"},
                        {"text": "Consulting", "value": "consulting"},
                        {"text": "Support", "value": "support"}
                    ]
                },
                {
                    "type": "rating",
                    "title": "How would you rate our website?",
                    "description": "Rate from 1 to 10",
                    "required": True,
                    "min_rating": 1,
                    "max_rating": 10
                }
            ]
        }
        
        # Test 1: Create Survey with All Question Types
        try:
            response = self.session.post(f"{API_BASE}/surveys", json=comprehensive_survey)
            if response.status_code == 200:
                survey = response.json()
                self.created_surveys.append(survey['id'])
                
                # Verify all question types are present
                question_types = [q['type'] for q in survey['questions']]
                expected_types = ['text', 'email', 'multiple_choice', 'checkbox', 'rating']
                
                if all(qtype in question_types for qtype in expected_types):
                    self.log_result('question_types', 'Create Survey with All Question Types', True)
                    comprehensive_survey_id = survey['id']
                else:
                    missing_types = [qtype for qtype in expected_types if qtype not in question_types]
                    self.log_result('question_types', 'Create Survey with All Question Types', False, f"Missing question types: {missing_types}")
                    return
            else:
                self.log_result('question_types', 'Create Survey with All Question Types', False, f"Status: {response.status_code}, Response: {response.text}")
                return
        except Exception as e:
            self.log_result('question_types', 'Create Survey with All Question Types', False, str(e))
            return

        # Test 2: Submit Response with All Question Types
        comprehensive_response = {
            "survey_id": comprehensive_survey_id,
            "responses": {
                "question_1": "Alice Johnson",
                "question_2": "alice.johnson@example.com",
                "question_3": "email",
                "question_4": ["web_dev", "consulting"],
                "question_5": 8
            }
        }
        
        try:
            response = self.session.post(f"{API_BASE}/responses", json=comprehensive_response)
            if response.status_code == 200:
                response_obj = response.json()
                self.created_responses.append(response_obj['id'])
                self.log_result('question_types', 'Submit Response with All Question Types', True)
            else:
                self.log_result('question_types', 'Submit Response with All Question Types', False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result('question_types', 'Submit Response with All Question Types', False, str(e))

        # Test 3: Verify Question Options and Validation
        try:
            response = self.session.get(f"{API_BASE}/surveys/{comprehensive_survey_id}")
            if response.status_code == 200:
                survey = response.json()
                
                # Check multiple choice options
                mc_question = next((q for q in survey['questions'] if q['type'] == 'multiple_choice'), None)
                if mc_question and mc_question.get('options') and len(mc_question['options']) == 4:
                    self.log_result('question_types', 'Multiple Choice Options Validation', True)
                else:
                    self.log_result('question_types', 'Multiple Choice Options Validation', False, "Multiple choice options not properly stored")
                
                # Check checkbox options
                cb_question = next((q for q in survey['questions'] if q['type'] == 'checkbox'), None)
                if cb_question and cb_question.get('options') and len(cb_question['options']) == 4:
                    self.log_result('question_types', 'Checkbox Options Validation', True)
                else:
                    self.log_result('question_types', 'Checkbox Options Validation', False, "Checkbox options not properly stored")
                
                # Check rating min/max
                rating_question = next((q for q in survey['questions'] if q['type'] == 'rating'), None)
                if rating_question and rating_question.get('min_rating') == 1 and rating_question.get('max_rating') == 10:
                    self.log_result('question_types', 'Rating Min/Max Validation', True)
                else:
                    self.log_result('question_types', 'Rating Min/Max Validation', False, "Rating min/max not properly stored")
                    
            else:
                self.log_result('question_types', 'Question Options Validation', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('question_types', 'Question Options Validation', False, str(e))

    def test_enhanced_response_endpoints(self):
        print("\n=== Testing Enhanced Response Endpoints (Grid View Features) ===")
        
        if not self.created_surveys:
            self.log_result('enhanced_responses', 'Enhanced Response Tests', False, "No surveys available for testing")
            return

        survey_id = self.created_surveys[0]
        
        # Create multiple responses for pagination testing
        response_data_list = [
            {
                "survey_id": survey_id,
                "responses": {
                    "question_1": "Alice Smith",
                    "question_2": "very_satisfied",
                    "question_3": 5
                }
            },
            {
                "survey_id": survey_id,
                "responses": {
                    "question_1": "Bob Johnson",
                    "question_2": "satisfied",
                    "question_3": 4
                }
            },
            {
                "survey_id": survey_id,
                "responses": {
                    "question_1": "Carol Davis",
                    "question_2": "neutral",
                    "question_3": 3
                }
            },
            {
                "survey_id": survey_id,
                "responses": {
                    "question_1": "David Wilson",
                    "question_2": "dissatisfied",
                    "question_3": 2
                }
            },
            {
                "survey_id": survey_id,
                "responses": {
                    "question_1": "Eva Brown",
                    "question_2": "very_satisfied",
                    "question_3": 5
                }
            }
        ]
        
        # Submit multiple responses
        for i, response_data in enumerate(response_data_list):
            try:
                response = self.session.post(f"{API_BASE}/responses", json=response_data)
                if response.status_code == 200:
                    response_obj = response.json()
                    self.created_responses.append(response_obj['id'])
                else:
                    self.log_result('enhanced_responses', f'Submit Test Response {i+1}', False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result('enhanced_responses', f'Submit Test Response {i+1}', False, str(e))
        
        # Test 1: Basic Enhanced GET with default parameters
        try:
            response = self.session.get(f"{API_BASE}/surveys/{survey_id}/responses")
            if response.status_code == 200:
                responses = response.json()
                if isinstance(responses, list) and len(responses) >= 5:
                    self.log_result('enhanced_responses', 'Enhanced GET Responses (Default)', True)
                else:
                    self.log_result('enhanced_responses', 'Enhanced GET Responses (Default)', False, f"Expected at least 5 responses, got {len(responses) if isinstance(responses, list) else 0}")
            else:
                self.log_result('enhanced_responses', 'Enhanced GET Responses (Default)', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('enhanced_responses', 'Enhanced GET Responses (Default)', False, str(e))

        # Test 2: Pagination - Page 1 with limit 3
        try:
            response = self.session.get(f"{API_BASE}/surveys/{survey_id}/responses?page=1&limit=3")
            if response.status_code == 200:
                responses = response.json()
                if isinstance(responses, list) and len(responses) == 3:
                    self.log_result('enhanced_responses', 'Pagination (Page 1, Limit 3)', True)
                else:
                    self.log_result('enhanced_responses', 'Pagination (Page 1, Limit 3)', False, f"Expected 3 responses, got {len(responses) if isinstance(responses, list) else 0}")
            else:
                self.log_result('enhanced_responses', 'Pagination (Page 1, Limit 3)', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('enhanced_responses', 'Pagination (Page 1, Limit 3)', False, str(e))

        # Test 3: Pagination - Page 2 with limit 3
        try:
            response = self.session.get(f"{API_BASE}/surveys/{survey_id}/responses?page=2&limit=3")
            if response.status_code == 200:
                responses = response.json()
                if isinstance(responses, list) and len(responses) >= 2:  # Should have at least 2 more responses
                    self.log_result('enhanced_responses', 'Pagination (Page 2, Limit 3)', True)
                else:
                    self.log_result('enhanced_responses', 'Pagination (Page 2, Limit 3)', False, f"Expected at least 2 responses on page 2, got {len(responses) if isinstance(responses, list) else 0}")
            else:
                self.log_result('enhanced_responses', 'Pagination (Page 2, Limit 3)', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('enhanced_responses', 'Pagination (Page 2, Limit 3)', False, str(e))

        # Test 4: Sorting - Ascending by submitted_at
        try:
            response = self.session.get(f"{API_BASE}/surveys/{survey_id}/responses?sort_by=submitted_at&sort_order=asc")
            if response.status_code == 200:
                responses = response.json()
                if isinstance(responses, list) and len(responses) >= 2:
                    # Check if responses are sorted by submitted_at in ascending order
                    timestamps = [resp['submitted_at'] for resp in responses]
                    is_sorted = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
                    if is_sorted:
                        self.log_result('enhanced_responses', 'Sorting (Ascending by submitted_at)', True)
                    else:
                        self.log_result('enhanced_responses', 'Sorting (Ascending by submitted_at)', False, "Responses not properly sorted")
                else:
                    self.log_result('enhanced_responses', 'Sorting (Ascending by submitted_at)', False, "Not enough responses to test sorting")
            else:
                self.log_result('enhanced_responses', 'Sorting (Ascending by submitted_at)', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('enhanced_responses', 'Sorting (Ascending by submitted_at)', False, str(e))

        # Test 5: Sorting - Descending by submitted_at (default)
        try:
            response = self.session.get(f"{API_BASE}/surveys/{survey_id}/responses?sort_by=submitted_at&sort_order=desc")
            if response.status_code == 200:
                responses = response.json()
                if isinstance(responses, list) and len(responses) >= 2:
                    # Check if responses are sorted by submitted_at in descending order
                    timestamps = [resp['submitted_at'] for resp in responses]
                    is_sorted = all(timestamps[i] >= timestamps[i+1] for i in range(len(timestamps)-1))
                    if is_sorted:
                        self.log_result('enhanced_responses', 'Sorting (Descending by submitted_at)', True)
                    else:
                        self.log_result('enhanced_responses', 'Sorting (Descending by submitted_at)', False, "Responses not properly sorted")
                else:
                    self.log_result('enhanced_responses', 'Sorting (Descending by submitted_at)', False, "Not enough responses to test sorting")
            else:
                self.log_result('enhanced_responses', 'Sorting (Descending by submitted_at)', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('enhanced_responses', 'Sorting (Descending by submitted_at)', False, str(e))

        # Test 6: Combined Pagination and Sorting
        try:
            response = self.session.get(f"{API_BASE}/surveys/{survey_id}/responses?page=1&limit=2&sort_by=submitted_at&sort_order=asc")
            if response.status_code == 200:
                responses = response.json()
                if isinstance(responses, list) and len(responses) == 2:
                    # Check if responses are sorted and limited correctly
                    timestamps = [resp['submitted_at'] for resp in responses]
                    is_sorted = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
                    if is_sorted:
                        self.log_result('enhanced_responses', 'Combined Pagination and Sorting', True)
                    else:
                        self.log_result('enhanced_responses', 'Combined Pagination and Sorting', False, "Responses not properly sorted with pagination")
                else:
                    self.log_result('enhanced_responses', 'Combined Pagination and Sorting', False, f"Expected 2 responses, got {len(responses) if isinstance(responses, list) else 0}")
            else:
                self.log_result('enhanced_responses', 'Combined Pagination and Sorting', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('enhanced_responses', 'Combined Pagination and Sorting', False, str(e))

    def test_response_analytics_endpoint(self):
        print("\n=== Testing Response Analytics Endpoint ===")
        
        if not self.created_surveys:
            self.log_result('response_analytics', 'Response Analytics Tests', False, "No surveys available for testing")
            return

        survey_id = self.created_surveys[0]
        
        # Test 1: Get Response Statistics
        try:
            response = self.session.get(f"{API_BASE}/surveys/{survey_id}/responses/stats")
            if response.status_code == 200:
                stats = response.json()
                
                # Verify basic structure
                required_fields = ['total_responses', 'survey_title', 'question_stats']
                if all(field in stats for field in required_fields):
                    self.log_result('response_analytics', 'Get Response Statistics (Basic Structure)', True)
                else:
                    missing_fields = [field for field in required_fields if field not in stats]
                    self.log_result('response_analytics', 'Get Response Statistics (Basic Structure)', False, f"Missing fields: {missing_fields}")
                    return
                
                # Verify total responses count
                if isinstance(stats['total_responses'], int) and stats['total_responses'] >= 5:
                    self.log_result('response_analytics', 'Total Responses Count', True)
                else:
                    self.log_result('response_analytics', 'Total Responses Count', False, f"Expected at least 5 responses, got {stats['total_responses']}")
                
                # Verify survey title
                if isinstance(stats['survey_title'], str) and len(stats['survey_title']) > 0:
                    self.log_result('response_analytics', 'Survey Title in Stats', True)
                else:
                    self.log_result('response_analytics', 'Survey Title in Stats', False, "Survey title missing or invalid")
                
                # Verify question stats structure
                question_stats = stats.get('question_stats', {})
                if isinstance(question_stats, dict) and len(question_stats) > 0:
                    self.log_result('response_analytics', 'Question Stats Structure', True)
                    
                    # Test question-wise completion rates
                    completion_rates_valid = True
                    for question_id, q_stats in question_stats.items():
                        required_q_fields = ['question_title', 'question_type', 'answered_count', 'completion_rate']
                        if not all(field in q_stats for field in required_q_fields):
                            completion_rates_valid = False
                            break
                        
                        # Check completion rate is a valid percentage
                        if not (0 <= q_stats['completion_rate'] <= 100):
                            completion_rates_valid = False
                            break
                    
                    if completion_rates_valid:
                        self.log_result('response_analytics', 'Question-wise Completion Rates', True)
                    else:
                        self.log_result('response_analytics', 'Question-wise Completion Rates', False, "Invalid completion rate data")
                    
                    # Test option distribution for multiple choice questions
                    mc_question_found = False
                    option_distribution_valid = True
                    for question_id, q_stats in question_stats.items():
                        if q_stats.get('question_type') == 'multiple_choice':
                            mc_question_found = True
                            option_dist = q_stats.get('option_distribution', {})
                            if not isinstance(option_dist, dict):
                                option_distribution_valid = False
                                break
                            
                            # Check if we have valid option counts
                            for option, count in option_dist.items():
                                if not isinstance(count, int) or count < 0:
                                    option_distribution_valid = False
                                    break
                    
                    if mc_question_found and option_distribution_valid:
                        self.log_result('response_analytics', 'Option Distribution for Multiple Choice', True)
                    elif not mc_question_found:
                        self.log_result('response_analytics', 'Option Distribution for Multiple Choice', False, "No multiple choice questions found")
                    else:
                        self.log_result('response_analytics', 'Option Distribution for Multiple Choice', False, "Invalid option distribution data")
                    
                    # Test average ratings for rating questions
                    rating_question_found = False
                    average_rating_valid = True
                    for question_id, q_stats in question_stats.items():
                        if q_stats.get('question_type') == 'rating':
                            rating_question_found = True
                            avg_rating = q_stats.get('average_rating')
                            if avg_rating is not None:
                                if not isinstance(avg_rating, (int, float)) or avg_rating < 1 or avg_rating > 5:
                                    average_rating_valid = False
                                    break
                    
                    if rating_question_found and average_rating_valid:
                        self.log_result('response_analytics', 'Average Ratings for Rating Questions', True)
                    elif not rating_question_found:
                        self.log_result('response_analytics', 'Average Ratings for Rating Questions', False, "No rating questions found")
                    else:
                        self.log_result('response_analytics', 'Average Ratings for Rating Questions', False, "Invalid average rating data")
                        
                else:
                    self.log_result('response_analytics', 'Question Stats Structure', False, "Question stats missing or invalid")
                    
            else:
                self.log_result('response_analytics', 'Get Response Statistics', False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result('response_analytics', 'Get Response Statistics', False, str(e))

        # Test 2: Analytics for Non-existent Survey
        try:
            fake_survey_id = str(uuid.uuid4())
            response = self.session.get(f"{API_BASE}/surveys/{fake_survey_id}/responses/stats")
            if response.status_code == 404:
                self.log_result('response_analytics', 'Analytics for Non-existent Survey (404 Error)', True)
            else:
                self.log_result('response_analytics', 'Analytics for Non-existent Survey (404 Error)', False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result('response_analytics', 'Analytics for Non-existent Survey (404 Error)', False, str(e))

        # Test 3: Analytics with No Responses
        # Create a new survey with no responses
        empty_survey_data = {
            "title": "Empty Survey for Analytics Test",
            "description": "Testing analytics with no responses",
            "questions": [
                {
                    "type": "text",
                    "title": "Test question",
                    "required": True
                }
            ]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/surveys", json=empty_survey_data)
            if response.status_code == 200:
                empty_survey = response.json()
                empty_survey_id = empty_survey['id']
                self.created_surveys.append(empty_survey_id)
                
                # Get analytics for empty survey
                response = self.session.get(f"{API_BASE}/surveys/{empty_survey_id}/responses/stats")
                if response.status_code == 200:
                    stats = response.json()
                    if stats.get('total_responses') == 0:
                        self.log_result('response_analytics', 'Analytics with No Responses', True)
                    else:
                        self.log_result('response_analytics', 'Analytics with No Responses', False, f"Expected 0 responses, got {stats.get('total_responses')}")
                else:
                    self.log_result('response_analytics', 'Analytics with No Responses', False, f"Status: {response.status_code}")
            else:
                self.log_result('response_analytics', 'Analytics with No Responses', False, f"Could not create empty survey: {response.status_code}")
        except Exception as e:
            self.log_result('response_analytics', 'Analytics with No Responses', False, str(e))
        print("\n=== Cleaning up test data ===")
        
        # Delete created surveys (this will also test delete functionality)
        for survey_id in self.created_surveys:
            try:
                response = self.session.delete(f"{API_BASE}/surveys/{survey_id}")
                if response.status_code == 200:
                    self.log_result('survey_crud', 'Delete Survey', True)
                else:
                    self.log_result('survey_crud', 'Delete Survey', False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result('survey_crud', 'Delete Survey', False, str(e))

    def run_all_tests(self):
        print("🚀 Starting Backend API Tests for Survey Making Tool")
        print(f"Backend URL: {API_BASE}")
        
        # Test backend connectivity first
        try:
            response = self.session.get(f"{API_BASE}/surveys")
            print(f"✅ Backend connectivity test passed (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ Backend connectivity failed: {e}")
            return False

        self.test_survey_crud_apis()
        self.test_template_system()
        self.test_response_collection_system()
        self.test_question_types_support()
        self.test_enhanced_response_endpoints()
        self.test_response_analytics_endpoint()
        self.cleanup_test_data()
        
        return True

    def print_summary(self):
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results['passed']
            failed = results['failed']
            total_passed += passed
            total_failed += failed
            
            status = "✅ PASS" if failed == 0 else "❌ FAIL"
            print(f"{category.upper().replace('_', ' ')}: {status} ({passed} passed, {failed} failed)")
            
            if results['errors']:
                for error in results['errors']:
                    print(f"  ❌ {error}")
        
        print("-" * 60)
        print(f"OVERALL: {total_passed} passed, {total_failed} failed")
        
        if total_failed == 0:
            print("🎉 All backend tests passed successfully!")
            return True
        else:
            print(f"⚠️  {total_failed} tests failed. Please check the errors above.")
            return False

def main():
    tester = SurveyAPITester()
    
    if tester.run_all_tests():
        success = tester.print_summary()
        sys.exit(0 if success else 1)
    else:
        print("❌ Could not run tests due to connectivity issues")
        sys.exit(1)

if __name__ == "__main__":
    main()