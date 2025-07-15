import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Question Type Components
const TextQuestion = ({ question, response, onChange }) => (
  <div className="mb-6">
    <label className="block text-sm font-medium text-gray-700 mb-2">
      {question.title}
      {question.required && <span className="text-red-500 ml-1">*</span>}
    </label>
    {question.description && (
      <p className="text-sm text-gray-500 mb-2">{question.description}</p>
    )}
    <input
      type={question.type === 'email' ? 'email' : question.type === 'phone' ? 'tel' : 'text'}
      value={response || ''}
      onChange={(e) => onChange(question.id, e.target.value)}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      required={question.required}
    />
  </div>
);

const MultipleChoiceQuestion = ({ question, response, onChange }) => (
  <div className="mb-6">
    <label className="block text-sm font-medium text-gray-700 mb-2">
      {question.title}
      {question.required && <span className="text-red-500 ml-1">*</span>}
    </label>
    {question.description && (
      <p className="text-sm text-gray-500 mb-2">{question.description}</p>
    )}
    <div className="space-y-2">
      {question.options?.map((option) => (
        <label key={option.id} className="flex items-center">
          <input
            type="radio"
            name={question.id}
            value={option.value}
            checked={response === option.value}
            onChange={(e) => onChange(question.id, e.target.value)}
            className="mr-2"
            required={question.required}
          />
          <span className="text-gray-700">{option.text}</span>
        </label>
      ))}
    </div>
  </div>
);

const CheckboxQuestion = ({ question, response, onChange }) => {
  const handleCheckboxChange = (value, checked) => {
    const currentResponse = response || [];
    if (checked) {
      onChange(question.id, [...currentResponse, value]);
    } else {
      onChange(question.id, currentResponse.filter(item => item !== value));
    }
  };

  return (
    <div className="mb-6">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {question.title}
        {question.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {question.description && (
        <p className="text-sm text-gray-500 mb-2">{question.description}</p>
      )}
      <div className="space-y-2">
        {question.options?.map((option) => (
          <label key={option.id} className="flex items-center">
            <input
              type="checkbox"
              value={option.value}
              checked={(response || []).includes(option.value)}
              onChange={(e) => handleCheckboxChange(option.value, e.target.checked)}
              className="mr-2"
            />
            <span className="text-gray-700">{option.text}</span>
          </label>
        ))}
      </div>
    </div>
  );
};

const RatingQuestion = ({ question, response, onChange }) => (
  <div className="mb-6">
    <label className="block text-sm font-medium text-gray-700 mb-2">
      {question.title}
      {question.required && <span className="text-red-500 ml-1">*</span>}
    </label>
    {question.description && (
      <p className="text-sm text-gray-500 mb-2">{question.description}</p>
    )}
    <div className="flex space-x-2">
      {Array.from({ length: question.max_rating || 5 }, (_, i) => i + 1).map((rating) => (
        <button
          key={rating}
          type="button"
          onClick={() => onChange(question.id, rating)}
          className={`w-10 h-10 rounded-full border-2 flex items-center justify-center font-semibold ${
            response === rating
              ? 'bg-blue-500 text-white border-blue-500'
              : 'border-gray-300 text-gray-700 hover:border-blue-300'
          }`}
        >
          {rating}
        </button>
      ))}
    </div>
  </div>
);

// Survey Builder Component
const SurveyBuilder = ({ onSave, editingSurvey = null }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [questions, setQuestions] = useState([]);

  useEffect(() => {
    if (editingSurvey) {
      setTitle(editingSurvey.title);
      setDescription(editingSurvey.description || '');
      setQuestions(editingSurvey.questions || []);
    }
  }, [editingSurvey]);

  const addQuestion = (type) => {
    const newQuestion = {
      id: Date.now().toString(),
      type,
      title: '',
      description: '',
      required: false,
      options: type === 'multiple_choice' || type === 'checkbox' ? [
        { id: Date.now().toString(), text: 'Option 1', value: 'option1' }
      ] : undefined,
      min_rating: type === 'rating' ? 1 : undefined,
      max_rating: type === 'rating' ? 5 : undefined
    };
    setQuestions([...questions, newQuestion]);
  };

  const updateQuestion = (questionId, field, value) => {
    setQuestions(questions.map(q => 
      q.id === questionId ? { ...q, [field]: value } : q
    ));
  };

  const removeQuestion = (questionId) => {
    setQuestions(questions.filter(q => q.id !== questionId));
  };

  const addOption = (questionId) => {
    setQuestions(questions.map(q => 
      q.id === questionId ? {
        ...q,
        options: [...(q.options || []), {
          id: Date.now().toString(),
          text: `Option ${(q.options || []).length + 1}`,
          value: `option${(q.options || []).length + 1}`
        }]
      } : q
    ));
  };

  const updateOption = (questionId, optionId, field, value) => {
    setQuestions(questions.map(q => 
      q.id === questionId ? {
        ...q,
        options: q.options?.map(o => 
          o.id === optionId ? { ...o, [field]: value } : o
        )
      } : q
    ));
  };

  const removeOption = (questionId, optionId) => {
    setQuestions(questions.map(q => 
      q.id === questionId ? {
        ...q,
        options: q.options?.filter(o => o.id !== optionId)
      } : q
    ));
  };

  const handleSave = () => {
    onSave({ title, description, questions });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">
          {editingSurvey ? 'Edit Survey' : 'Create New Survey'}
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Survey Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter survey title"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
              placeholder="Enter survey description"
            />
          </div>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Add Questions</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => addQuestion('text')}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Text Question
          </button>
          <button
            onClick={() => addQuestion('multiple_choice')}
            className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
          >
            Multiple Choice
          </button>
          <button
            onClick={() => addQuestion('checkbox')}
            className="px-4 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600"
          >
            Checkbox
          </button>
          <button
            onClick={() => addQuestion('rating')}
            className="px-4 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600"
          >
            Rating
          </button>
          <button
            onClick={() => addQuestion('email')}
            className="px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600"
          >
            Email
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {questions.map((question, index) => (
          <div key={question.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-4">
              <h4 className="text-lg font-medium">Question {index + 1}</h4>
              <button
                onClick={() => removeQuestion(question.id)}
                className="text-red-500 hover:text-red-700"
              >
                Remove
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Question Title
                </label>
                <input
                  type="text"
                  value={question.title}
                  onChange={(e) => updateQuestion(question.id, 'title', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter question title"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (optional)
                </label>
                <input
                  type="text"
                  value={question.description || ''}
                  onChange={(e) => updateQuestion(question.id, 'description', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter question description"
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={question.required}
                  onChange={(e) => updateQuestion(question.id, 'required', e.target.checked)}
                  className="mr-2"
                />
                <label className="text-sm text-gray-700">Required</label>
              </div>

              {(question.type === 'multiple_choice' || question.type === 'checkbox') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Options
                  </label>
                  {question.options?.map((option) => (
                    <div key={option.id} className="flex items-center space-x-2 mb-2">
                      <input
                        type="text"
                        value={option.text}
                        onChange={(e) => updateOption(question.id, option.id, 'text', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Option text"
                      />
                      <input
                        type="text"
                        value={option.value}
                        onChange={(e) => updateOption(question.id, option.id, 'value', e.target.value)}
                        className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Value"
                      />
                      <button
                        onClick={() => removeOption(question.id, option.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => addOption(question.id)}
                    className="px-3 py-1 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                  >
                    Add Option
                  </button>
                </div>
              )}

              {question.type === 'rating' && (
                <div className="flex space-x-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Min Rating
                    </label>
                    <input
                      type="number"
                      value={question.min_rating || 1}
                      onChange={(e) => updateQuestion(question.id, 'min_rating', parseInt(e.target.value))}
                      className="w-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Rating
                    </label>
                    <input
                      type="number"
                      value={question.max_rating || 5}
                      onChange={(e) => updateQuestion(question.id, 'max_rating', parseInt(e.target.value))}
                      className="w-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="1"
                      max="10"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 flex justify-end">
        <button
          onClick={handleSave}
          className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          disabled={!title || questions.length === 0}
        >
          {editingSurvey ? 'Update Survey' : 'Save Survey'}
        </button>
      </div>
    </div>
  );
};

// Survey Response Component
const SurveyResponse = ({ survey, onSubmit }) => {
  const [responses, setResponses] = useState({});
  const [submitted, setSubmitted] = useState(false);

  const handleResponseChange = (questionId, value) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await onSubmit(responses);
      setSubmitted(true);
    } catch (error) {
      console.error('Error submitting response:', error);
    }
  };

  if (submitted) {
    return (
      <div className="max-w-2xl mx-auto p-6 text-center">
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          <h3 className="text-lg font-semibold mb-2">Thank you!</h3>
          <p>Your response has been submitted successfully.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">{survey.title}</h1>
        {survey.description && (
          <p className="text-gray-600">{survey.description}</p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {survey.questions.map((question) => {
          const QuestionComponent = {
            text: TextQuestion,
            email: TextQuestion,
            phone: TextQuestion,
            multiple_choice: MultipleChoiceQuestion,
            checkbox: CheckboxQuestion,
            rating: RatingQuestion
          }[question.type];

          return QuestionComponent ? (
            <QuestionComponent
              key={question.id}
              question={question}
              response={responses[question.id]}
              onChange={handleResponseChange}
            />
          ) : null;
        })}

        <div className="pt-6">
          <button
            type="submit"
            className="w-full px-6 py-3 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Submit Survey
          </button>
        </div>
      </form>
    </div>
  );
};

// Main App Component
function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [surveys, setSurveys] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedSurvey, setSelectedSurvey] = useState(null);
  const [editingSurvey, setEditingSurvey] = useState(null);
  const [surveyResponses, setSurveyResponses] = useState([]);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Initialize templates
      await axios.post(`${API}/init-templates`);
      
      // Load surveys and templates
      await loadSurveys();
      await loadTemplates();
    } catch (error) {
      console.error('Error initializing app:', error);
    }
  };

  const loadSurveys = async () => {
    try {
      const response = await axios.get(`${API}/surveys`);
      setSurveys(response.data);
    } catch (error) {
      console.error('Error loading surveys:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  const handleSaveSurvey = async (surveyData) => {
    try {
      if (editingSurvey) {
        await axios.put(`${API}/surveys/${editingSurvey.id}`, surveyData);
      } else {
        await axios.post(`${API}/surveys`, surveyData);
      }
      
      setCurrentView('dashboard');
      setEditingSurvey(null);
      await loadSurveys();
    } catch (error) {
      console.error('Error saving survey:', error);
    }
  };

  const handleDeleteSurvey = async (surveyId) => {
    if (window.confirm('Are you sure you want to delete this survey?')) {
      try {
        await axios.delete(`${API}/surveys/${surveyId}`);
        await loadSurveys();
      } catch (error) {
        console.error('Error deleting survey:', error);
      }
    }
  };

  const handleCreateFromTemplate = async (templateId) => {
    const title = prompt('Enter survey title:');
    if (title) {
      try {
        await axios.post(`${API}/templates/${templateId}/create-survey?title=${encodeURIComponent(title)}`);
        await loadSurveys();
      } catch (error) {
        console.error('Error creating survey from template:', error);
      }
    }
  };

  const handleSubmitResponse = async (responses) => {
    try {
      await axios.post(`${API}/responses`, {
        survey_id: selectedSurvey.id,
        responses
      });
    } catch (error) {
      console.error('Error submitting response:', error);
      throw error;
    }
  };

  const loadSurveyResponses = async (surveyId) => {
    try {
      const response = await axios.get(`${API}/surveys/${surveyId}/responses`);
      setSurveyResponses(response.data);
    } catch (error) {
      console.error('Error loading survey responses:', error);
    }
  };

  const renderDashboard = () => (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Survey Dashboard</h1>
        <div className="flex space-x-4">
          <button
            onClick={() => setCurrentView('create')}
            className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Create New Survey
          </button>
          <button
            onClick={() => setCurrentView('templates')}
            className="px-6 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
          >
            Browse Templates
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {surveys.map((survey) => (
          <div key={survey.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-semibold mb-2">{survey.title}</h3>
            {survey.description && (
              <p className="text-gray-600 mb-4">{survey.description}</p>
            )}
            <div className="text-sm text-gray-500 mb-4">
              Created: {new Date(survey.created_at).toLocaleDateString()}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  setSelectedSurvey(survey);
                  setCurrentView('respond');
                }}
                className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
              >
                View
              </button>
              <button
                onClick={() => {
                  setEditingSurvey(survey);
                  setCurrentView('create');
                }}
                className="px-3 py-1 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600"
              >
                Edit
              </button>
              <button
                onClick={() => {
                  loadSurveyResponses(survey.id);
                  setSelectedSurvey(survey);
                  setCurrentView('responses');
                }}
                className="px-3 py-1 bg-purple-500 text-white rounded text-sm hover:bg-purple-600"
              >
                Responses
              </button>
              <button
                onClick={() => handleDeleteSurvey(survey.id)}
                className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {surveys.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No surveys yet. Create your first survey!</p>
        </div>
      )}
    </div>
  );

  const renderTemplates = () => (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Survey Templates</h1>
        <button
          onClick={() => setCurrentView('dashboard')}
          className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
        >
          Back to Dashboard
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <div key={template.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-semibold mb-2">{template.title}</h3>
            {template.description && (
              <p className="text-gray-600 mb-4">{template.description}</p>
            )}
            <div className="text-sm text-blue-600 mb-4">
              Category: {template.template_category}
            </div>
            <div className="text-sm text-gray-500 mb-4">
              {template.questions.length} questions
            </div>
            <button
              onClick={() => handleCreateFromTemplate(template.id)}
              className="w-full px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
            >
              Use This Template
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderResponses = () => (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Survey Responses: {selectedSurvey?.title}
        </h1>
        <button
          onClick={() => setCurrentView('dashboard')}
          className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
        >
          Back to Dashboard
        </button>
      </div>

      {surveyResponses.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No responses yet.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {surveyResponses.map((response, index) => (
            <div key={response.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="mb-4">
                <h3 className="text-lg font-semibold">Response #{index + 1}</h3>
                <p className="text-sm text-gray-500">
                  Submitted: {new Date(response.submitted_at).toLocaleString()}
                </p>
              </div>
              <div className="space-y-4">
                {selectedSurvey?.questions.map((question) => (
                  <div key={question.id} className="border-l-4 border-blue-500 pl-4">
                    <h4 className="font-medium text-gray-900">{question.title}</h4>
                    <p className="text-gray-700 mt-1">
                      {Array.isArray(response.responses[question.id]) 
                        ? response.responses[question.id].join(', ')
                        : response.responses[question.id] || 'No response'
                      }
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case 'create':
        return (
          <div>
            <div className="mb-4">
              <button
                onClick={() => {
                  setCurrentView('dashboard');
                  setEditingSurvey(null);
                }}
                className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
              >
                Back to Dashboard
              </button>
            </div>
            <SurveyBuilder onSave={handleSaveSurvey} editingSurvey={editingSurvey} />
          </div>
        );
      case 'templates':
        return renderTemplates();
      case 'respond':
        return (
          <div>
            <div className="mb-4">
              <button
                onClick={() => setCurrentView('dashboard')}
                className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
              >
                Back to Dashboard
              </button>
            </div>
            <SurveyResponse survey={selectedSurvey} onSubmit={handleSubmitResponse} />
          </div>
        );
      case 'responses':
        return renderResponses();
      default:
        return renderDashboard();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {renderCurrentView()}
    </div>
  );
}

export default App;