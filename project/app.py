from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import pandas as pd
import json
from bson.objectid import ObjectId
from datetime import datetime
import hashlib
import random
from pymongo import MongoClient
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
import pickle

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB setup
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['zenify_db']
    print("Connected to MongoDB")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    # Fallback to file-based storage for demo if MongoDB connection fails
    print("Using file-based storage as fallback")

# Load survey data
survey_data = None
try:
    survey_data = pd.read_csv('survey_data.csv')
    print(f"Loaded survey data with {len(survey_data)} responses")
except Exception as e:
    print(f"Error loading survey data: {e}")
    # Create empty dataframe if file doesn't exist
    survey_data = pd.DataFrame()

# Activity categories and recommendations
activity_categories = [
    "meditation", "physical_exercise", "breathing_exercises", 
    "journaling", "social_connection", "nature", "creative_expression",
    "mindfulness", "gratitude", "self_compassion"
]

activities = {
    "meditation": [
        {"name": "5-Minute Breath Awareness", "description": "Focus on your breath for just 5 minutes to center yourself.", "difficulty": "beginner"},
        {"name": "Body Scan Meditation", "description": "Progressively relax your body from head to toe.", "difficulty": "beginner"},
        {"name": "Loving-Kindness Meditation", "description": "Generate feelings of love and kindness toward yourself and others.", "difficulty": "intermediate"},
        {"name": "Mindful Walking Meditation", "description": "Practice mindfulness while walking slowly and deliberately.", "difficulty": "intermediate"},
        {"name": "Transcendental Meditation", "description": "Use a mantra to achieve a state of relaxed awareness.", "difficulty": "advanced"},
    ],
    "physical_exercise": [
        {"name": "Gentle Morning Stretching", "description": "Easy stretches to wake up your body.", "difficulty": "beginner"},
        {"name": "15-Minute Yoga Flow", "description": "A short sequence to energize your body and mind.", "difficulty": "beginner"},
        {"name": "Nature Walk", "description": "Take a 30-minute walk in nature to clear your mind.", "difficulty": "beginner"},
        {"name": "HIIT Workout", "description": "High-intensity interval training to boost your mood.", "difficulty": "intermediate"},
        {"name": "Dance Workout", "description": "Dance to your favorite music for 20 minutes.", "difficulty": "intermediate"},
    ],
    "breathing_exercises": [
        {"name": "4-7-8 Breathing", "description": "Inhale for 4 counts, hold for 7, exhale for 8.", "difficulty": "beginner"},
        {"name": "Box Breathing", "description": "Equal parts inhale, hold, exhale, and hold.", "difficulty": "beginner"},
        {"name": "Alternate Nostril Breathing", "description": "Balance your nervous system with this yogic breathing technique.", "difficulty": "intermediate"},
        {"name": "Diaphragmatic Breathing", "description": "Deep belly breathing to activate the relaxation response.", "difficulty": "beginner"},
        {"name": "Lion's Breath", "description": "Release tension and stress with this powerful exhale.", "difficulty": "intermediate"},
    ],
    "journaling": [
        {"name": "Gratitude Journal", "description": "Write down 3 things you're grateful for today.", "difficulty": "beginner"},
        {"name": "Stream of Consciousness", "description": "Write whatever comes to mind without judgment for 10 minutes.", "difficulty": "beginner"},
        {"name": "Worry Dump", "description": "Write down all your worries to get them out of your head.", "difficulty": "beginner"},
        {"name": "Achievement Journal", "description": "Document your daily wins, no matter how small.", "difficulty": "beginner"},
        {"name": "Letter to Your Future Self", "description": "Write a supportive letter to read when you're struggling.", "difficulty": "intermediate"},
    ],
    "social_connection": [
        {"name": "Reach Out to a Friend", "description": "Send a message to someone you haven't talked to in a while.", "difficulty": "beginner"},
        {"name": "Virtual Coffee Date", "description": "Schedule a video call with a friend or family member.", "difficulty": "beginner"},
        {"name": "Join an Online Community", "description": "Find a group that shares your interests or challenges.", "difficulty": "intermediate"},
        {"name": "Random Acts of Kindness", "description": "Do something nice for someone else to boost your mood.", "difficulty": "beginner"},
        {"name": "Volunteer Virtually", "description": "Find ways to help others from home.", "difficulty": "intermediate"},
    ],
    "nature": [
        {"name": "Plant Care", "description": "Spend time tending to a houseplant or garden.", "difficulty": "beginner"},
        {"name": "Cloud Watching", "description": "Lie down and watch the clouds move across the sky.", "difficulty": "beginner"},
        {"name": "Nature Sounds", "description": "Listen to recordings of natural environments like forests or oceans.", "difficulty": "beginner"},
        {"name": "Earthing", "description": "Walk barefoot on grass, sand, or soil to connect with the earth.", "difficulty": "beginner"},
        {"name": "Forest Bathing", "description": "Immerse yourself in the atmosphere of a forest.", "difficulty": "intermediate"},
    ],
    "creative_expression": [
        {"name": "Coloring", "description": "Use an adult coloring book to focus your mind.", "difficulty": "beginner"},
        {"name": "Free Drawing", "description": "Draw whatever comes to mind without judgment.", "difficulty": "beginner"},
        {"name": "Creative Writing", "description": "Write a short story or poem about how you feel.", "difficulty": "intermediate"},
        {"name": "DIY Craft Project", "description": "Create something with your hands to focus your mind.", "difficulty": "intermediate"},
        {"name": "Music Creation", "description": "Play an instrument or create a playlist that reflects your mood.", "difficulty": "varies"},
    ],
    "mindfulness": [
        {"name": "Mindful Eating", "description": "Pay full attention to the experience of eating a single piece of food.", "difficulty": "beginner"},
        {"name": "5 Senses Check-in", "description": "Notice something you can see, hear, smell, taste, and touch.", "difficulty": "beginner"},
        {"name": "Single-Task Focus", "description": "Do one activity with your full attention for 15 minutes.", "difficulty": "intermediate"},
        {"name": "Mindful Observation", "description": "Choose an object and examine it in detail for 5 minutes.", "difficulty": "beginner"},
        {"name": "Body Awareness", "description": "Scan your body and notice sensations without judgment.", "difficulty": "intermediate"},
    ],
    "gratitude": [
        {"name": "Three Good Things", "description": "Write down three positive things that happened today.", "difficulty": "beginner"},
        {"name": "Thank You Note", "description": "Write a letter of appreciation to someone who helped you.", "difficulty": "beginner"},
        {"name": "Gratitude Walk", "description": "Walk while focusing on things you're thankful for.", "difficulty": "beginner"},
        {"name": "Gratitude Jar", "description": "Add notes about things you're grateful for to a special container.", "difficulty": "beginner"},
        {"name": "Gratitude Meditation", "description": "Meditate while focusing on feelings of thankfulness.", "difficulty": "intermediate"},
    ],
    "self_compassion": [
        {"name": "Self-Compassion Break", "description": "Acknowledge suffering, remember you're not alone, and offer kindness to yourself.", "difficulty": "beginner"},
        {"name": "Forgiveness Practice", "description": "Practice forgiving yourself for perceived failures or mistakes.", "difficulty": "intermediate"},
        {"name": "Comfort Touch", "description": "Place your hand on your heart when you're struggling.", "difficulty": "beginner"},
        {"name": "Self-Care Inventory", "description": "List ways you currently care for yourself and new ideas to try.", "difficulty": "beginner"},
        {"name": "Compassionate Letter", "description": "Write to yourself as you would to a loved one who's struggling.", "difficulty": "intermediate"},
    ]
}

# User routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Simple validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('register'))
            
        # Check if user exists
        existing_user = db.users.find_one({'email': email})
        if existing_user:
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
            
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Create new user
        new_user = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.now(),
            'survey_completed': False,
            'preferences': {},
            'activity_history': [],
            'recommendations': []
        }
        
        try:
            db.users.insert_one(new_user)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error during registration: {str(e)}', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Simple validation
        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('login'))
            
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Check credentials
        user = db.users.find_one({'email': email, 'password': hashed_password})
        
        if user:
            # Create session
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            
            flash('Login successful!', 'success')
            
            # Redirect based on survey completion
            if user.get('survey_completed', False):
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('survey'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if 'user_id' not in session:
        flash('Please log in to access the survey', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        survey_responses = {
            'age_group': request.form.get('age_group'),
            'gender': request.form.get('gender'),
            'doubt_frequency': request.form.get('doubt_frequency'),
            'stress_frequency': request.form.get('stress_frequency'),
            'anxiety_frequency': request.form.get('anxiety_frequency'),
            'self_appreciation': request.form.get('self_appreciation'),
            'self_care_frequency': request.form.get('self_care_frequency'),
            'meditation_frequency': request.form.get('meditation_frequency'),
            'exercise_frequency': request.form.get('exercise_frequency'),
            'mental_health_importance': request.form.get('mental_health_importance'),
            'app_openness': request.form.get('app_openness'),
            'existing_practices': request.form.get('existing_practices')
        }
        
        # Update user record
        user_id = ObjectId(session['user_id'])
        db.users.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'survey_responses': survey_responses,
                    'survey_completed': True,
                    'survey_date': datetime.now()
                }
            }
        )
        
        # Generate initial recommendations
        generate_recommendations(user_id)
        
        flash('Thank you for completing the survey!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('survey.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to view your dashboard', 'error')
        return redirect(url_for('login'))
    
    user_id = ObjectId(session['user_id'])
    user = db.users.find_one({'_id': user_id})
    
    if not user.get('survey_completed', False):
        flash('Please complete the survey first', 'info')
        return redirect(url_for('survey'))
    
    # Get recommendations
    recommendations = user.get('recommendations', [])
    
    activity_history = user.get('activity_history', [])
    
    stats = {
        'activities_completed': len(activity_history),
        'favorite_category': get_favorite_category(activity_history),
        'streak': calculate_streak(activity_history),
        'last_activity': get_last_activity(activity_history)
    }
    
    return render_template(
        'dashboard.html', 
        user=user,
        recommendations=recommendations[:5],
        stats=stats,
        activity_categories=activity_categories
    )

@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session:
        flash('Please log in to view your recommendations', 'error')
        return redirect(url_for('login'))
    
    user_id = ObjectId(session['user_id'])
    user = db.users.find_one({'_id': user_id})
    
    if not user.get('survey_completed', False):
        flash('Please complete the survey first', 'info')
        return redirect(url_for('survey'))
    
    # Get all recommendations
    recommendations = user.get('recommendations', [])
    
    # Get filtered recommendations if category is specified
    category = request.args.get('category')
    if category and category in activity_categories:
        recommendations = [r for r in recommendations if r.get('category') == category]
    
    return render_template(
        'recommendations.html',
        recommendations=recommendations,
        categories=activity_categories,
        selected_category=category
    )

@app.route('/activity/<activity_id>')
def activity_detail(activity_id):
    if 'user_id' not in session:
        flash('Please log in to view activity details', 'error')
        return redirect(url_for('login'))
    
    # Get user
    user_id = ObjectId(session['user_id'])
    user = db.users.find_one({'_id': user_id})
    
    # Find activity in recommendations
    recommendations = user.get('recommendations', [])
    activity = None
    for rec in recommendations:
        if rec.get('id') == activity_id:
            activity = rec
            break
    
    if not activity:
        flash('Activity not found', 'error')
        return redirect(url_for('recommendations'))
    
    # Get related activities (same category)
    related = [r for r in recommendations if r.get('category') == activity.get('category') and r.get('id') != activity_id][:3]
    
    # Check if activity is in history (completed)
    activity_history = user.get('activity_history', [])
    completed = any(h.get('activity_id') == activity_id for h in activity_history)
    
    return render_template(
        'activity_detail.html',
        activity=activity,
        related=related,
        completed=completed
    )

@app.route('/complete_activity', methods=['POST'])
def complete_activity():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.json
    activity_id = data.get('activity_id')
    rating = data.get('rating', 0)  # Explicit rating
    
    if not activity_id:
        return jsonify({'success': False, 'message': 'Activity ID required'})
    
    user_id = ObjectId(session['user_id'])
    
    # Add to activity history
    completion = {
        'activity_id': activity_id,
        'completed_at': datetime.now(),
        'rating': rating
    }
    
    db.users.update_one(
        {'_id': user_id},
        {'$push': {'activity_history': completion}}
    )
    
    # Update recommendations based on new data
    update_recommendations(user_id, activity_id, rating)
    
    return jsonify({'success': True})

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile', 'error')
        return redirect(url_for('login'))
    
    user_id = ObjectId(session['user_id'])
    user = db.users.find_one({'_id': user_id})
    
    # Calculate stats
    activity_history = user.get('activity_history', [])
    stats = {
        'activities_completed': len(activity_history),
        'favorite_category': get_favorite_category(activity_history),
        'streak': calculate_streak(activity_history),
        'categories_tried': len(set(get_activity_category(h.get('activity_id')) for h in activity_history if h.get('activity_id')))
    }
    
    return render_template('profile.html', user=user, stats=stats)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash('Please log in to update your profile', 'error')
        return redirect(url_for('login'))
    
    user_id = ObjectId(session['user_id'])
    
    # Get form data
    username = request.form.get('username')
    email = request.form.get('email')
    
    # Update user record
    db.users.update_one(
        {'_id': user_id},
        {'$set': {
            'username': username,
            'email': email
        }}
    )
    
    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

# Helper functions for recommendation system
def generate_recommendations(user_id):
    """Generate initial recommendations based on survey responses"""
    user = db.users.find_one({'_id': user_id})
    survey_responses = user.get('survey_responses', {})
    
    # Initial content-based recommendations
    recommendations = []
    
    # Tailor recommendations based on survey responses
    if survey_responses.get('stress_frequency') in ['Almost Every Day', 'A Few Times a Week']:

        add_recommendations(recommendations, 'breathing_exercises', 3)
        add_recommendations(recommendations, 'meditation', 3)
        add_recommendations(recommendations, 'nature', 2)
    
    if survey_responses.get('anxiety_frequency') in ['Always', 'Often']:

        add_recommendations(recommendations, 'mindfulness', 3)
        add_recommendations(recommendations, 'physical_exercise', 2)
    
    if survey_responses.get('self_appreciation') in ['Hardly Ever', 'Once in a While']:

        add_recommendations(recommendations, 'self_compassion', 3)
        add_recommendations(recommendations, 'gratitude', 2)
    
    if survey_responses.get('meditation_frequency') in ['Never', 'Rarely']:
  
        beginner_meditations = [a for a in activities['meditation'] if a['difficulty'] == 'beginner']
        for activity in beginner_meditations:
            recommendations.append({
                'id': f"meditation_{activities['meditation'].index(activity)}",
                'name': activity['name'],
                'description': activity['description'],
                'category': 'meditation',
                'difficulty': 'beginner',
                'relevance_score': 0.9,
                'recommended_at': datetime.now()
            })
    
    categories_to_fill = [cat for cat in activity_categories if not any(r['category'] == cat for r in recommendations)]
    for category in categories_to_fill:
        add_recommendations(recommendations, category, 1)

    while len(recommendations) < 10:
        category = random.choice(activity_categories)
        add_recommendations(recommendations, category, 1)
    
    db.users.update_one(
        {'_id': user_id},
        {'$set': {'recommendations': recommendations}}
    )

def add_recommendations(recommendations, category, count):
    """Add a specified number of activities from a category to recommendations"""
    category_activities = activities.get(category, [])
    selected = []
    
    # First try to get activities that aren't already recommended
    existing_ids = [r['id'] for r in recommendations if r['category'] == category]
    available = [a for i, a in enumerate(category_activities) if f"{category}_{i}" not in existing_ids]
    
    # If we need more than available, allow duplicates
    if len(available) < count:
        selected = available + random.sample(category_activities, count - len(available))
    else:
        selected = random.sample(available, count)
    
    for activity in selected:
        idx = category_activities.index(activity)
        if not any(r['id'] == f"{category}_{idx}" for r in recommendations):
            recommendations.append({
                'id': f"{category}_{idx}",
                'name': activity['name'],
                'description': activity['description'],
                'category': category,
                'difficulty': activity['difficulty'],
                'relevance_score': 0.8,
                'recommended_at': datetime.now()
            })

def update_recommendations(user_id, completed_activity_id, rating):
    """Update recommendations based on user activity and ratings"""
    user = db.users.find_one({'_id': user_id})
    
    # Parse activity ID to get category
    if '_' in completed_activity_id:
        category = completed_activity_id.split('_')[0]
        
        # If user rated activity highly, recommend more from same category
        if rating >= 4:
            current_recommendations = user.get('recommendations', [])
            add_recommendations(current_recommendations, category, 2)
            
            # Update relevance scores for similar activities
            for i, rec in enumerate(current_recommendations):
                if rec['category'] == category:
                    current_recommendations[i]['relevance_score'] = min(1.0, rec.get('relevance_score', 0.8) + 0.1)
            
            # Update user's recommendations
            db.users.update_one(
                {'_id': user_id},
                {'$set': {'recommendations': current_recommendations}}
            )

def get_favorite_category(activity_history):
    """Determine user's favorite activity category based on history"""
    if not activity_history:
        return None
    
    categories = [get_activity_category(h.get('activity_id')) for h in activity_history if h.get('activity_id')]
    if not categories:
        return None
    
    # Count occurrences of each category
    category_counts = {}
    for cat in categories:
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Return the most frequent category
    if category_counts:
        return max(category_counts, key=category_counts.get)
    return None

def get_activity_category(activity_id):
    """Extract category from activity ID"""
    if activity_id and '_' in activity_id:
        return activity_id.split('_')[0]
    return None

def calculate_streak(activity_history):
    """Calculate user's current activity streak"""
    if not activity_history:
        return 0
    
    # Sort by completion date
    sorted_history = sorted(activity_history, key=lambda x: x.get('completed_at', datetime.min), reverse=True)
    
    # Get dates of activities
    dates = [h.get('completed_at').date() for h in sorted_history if h.get('completed_at')]
    
    if not dates:
        return 0
    
    # Calculate streak
    streak = 1
    today = datetime.now().date()
    
    # Check if user did something today
    if dates[0] != today:
        return 0
    
    # Check consecutive days
    for i in range(len(dates) - 1):
        if (dates[i] - dates[i+1]).days == 1:
            streak += 1
        elif (dates[i] - dates[i+1]).days > 1:
            break
    
    return streak

# def get_last_activity(activity_history):
#     """Get the user's most recent activity"""
#     if not activity_history:
#         return None
    
#     # Sort by completion date
#     sorted_history = sorted(activity_history, key=lambda x: x.get('completed_at', datetime.min), reverse=True)
    
#     if sorted_history:
#         last = sorted_history[0]
#         activity_id = last.get('activity_id')
        
#         if activity_id and '_' in activity_id:
#             category = activity_id.split('_')[0]
#             index = int(activity_id.split('_')[1])
            
#             if category in activities and index < len(activities[category]):
#                 activity = activities[category][index]
#                 return {
#                     'name': activity['name'],
#                     'category': category,
#                     'completed_at': last.get('completed_at')
#                 }
    
#     return None

def get_last_activity(activity_history):
    """Get the user's most recent activity with proper error handling"""
    if not activity_history:
        return None
    
    try:
        # Sort by completion date safely
        sorted_history = sorted(
            [x for x in activity_history if isinstance(x, dict)],
            key=lambda x: x.get('completed_at', datetime.min),
            reverse=True
        )
        
        if not sorted_history:
            return None
            
        last = sorted_history[0]
        activity_id = last.get('activity_id')
        
        if not activity_id or not isinstance(activity_id, str):
            return None
            
        # Handle both "category_index" and free-form IDs
        if '_' in activity_id:
            parts = activity_id.split('_')
            if len(parts) >= 2:
                category = parts[0]
                try:
                    index = int(parts[1])
                    if category in activities and 0 <= index < len(activities.get(category, [])):
                        activity = activities[category][index]
                        return {
                            'name': activity.get('name', 'Unknown'),
                            'category': category,
                            'completed_at': last.get('completed_at')
                        }
                except (ValueError, IndexError):
                    pass  # Fall through to return basic info
        
        # Fallback for invalid/missing structured IDs
        return {
            'name': str(activity_id),
            'category': 'general',
            'completed_at': last.get('completed_at')
        }
        
    except Exception as e:
        print(f"Error processing activity history: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)