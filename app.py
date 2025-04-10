from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models import db, User, Complaint, Feedback
from flask_migrate import Migrate
from flask_socketio import SocketIO, send
from textblob import TextBlob
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///railway_grievance.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a secure key
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
socketio = SocketIO(app)

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def analyze_sentiment(feedback_text):
    blob = TextBlob(feedback_text)
    sentiment = blob.sentiment.polarity
    if sentiment > 0:
        return "Positive"
    elif sentiment < 0:
        return "Negative"
    else:
        return "Neutral"

def generate_feedback_trend_graph(trend_data):
    # Generate the graph for feedback trend
    months = [data[0] for data in trend_data]
    counts = [data[1] for data in trend_data]

    plt.figure(figsize=(10, 5))
    plt.plot(months, counts, marker='o', color='b')
    plt.title("Feedback Trend Over Time")
    plt.xlabel("Month")
    plt.ylabel("Number of Feedbacks")
    
    # Save the plot to a BytesIO object and convert it to base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    
    return plot_url
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def calculate_urgency(complaint):     
    department_weights = {
        "Safety and Security": 10,
        "Medical Assistance": 10,
        "Cleaning and Maintenance": 8,
        "Lost and Found": 7,
        "Food Services": 6,
        "Passenger Services": 5,
        "Ticket Booking": 4,
        "Reservation": 4,
        "Customer Support": 4,
        "Complaints": 3,
        "Train Operations": 3
    }

    # Default keyword scoring system
    keywords_scores = {"safety": 10, "emergency": 10, "accident": 10, "injury": 10, "fire": 10, "medical": 9, "danger": 9, "attack": 9, "violence": 9, "terrorism": 9, "bomb": 9, "explosion": 9, "collide": 8, "crash": 8, "emergency services": 8, "broken": 7, "damage": 7, "fault": 7, "disaster": 7, "system failure": 7, "train malfunction": 7, "power outage": 6, "service interruption": 6, "delayed": 6, "late": 6, "missed connection": 6, "disruption": 6, "schedule issue": 6, 
                       "transportation issue": 6, "ticketing issue": 6, "strike": 6, "late arrival": 5, "wrong ticket": 5, "wrong information": 5, "confusion": 5, "error": 5, "lost luggage": 5, "lost property": 5, "missing item": 5, "damaged property": 5, "lost reservation": 5, "incorrect booking": 5, "wrong booking": 5, "overbooked": 5, "sick": 5, "ill": 5, "miscommunication": 4, 
                       "misunderstanding": 4, "poor service": 4, "bad experience": 4, "unhelpful": 4, "unprofessional": 4, "rude staff": 4, "long wait": 4, "unorganized": 4, "uncomfortable": 4, "slow service": 4, "disrespectful": 4, "unavailable": 4, "noise": 4, "unhygienic": 4, "dirty": 4, "unreliable": 4, "unresolved": 4, "unsatisfactory": 4, "poor quality": 4, "insufficient": 4, 
                       "misplaced": 4, "not functioning": 4, "unresolved issue": 4, "inconvenient": 3, "unreliable system": 3, "inefficient": 3, "poor condition": 3, "poorly maintained": 3, "broken equipment": 3, "slow response": 3, "lack of information": 3, "lack of communication": 3, "inadequate": 3, "incompetent": 3, "unaccommodating": 3, "unhelpful staff": 3, "unprepared": 3, "unresponsive": 3, 
                       "confusing": 3, "complicated": 3, "displeased": 3, "frustrated": 3, "inconvenience": 3, "poor support": 3, "lacking": 3, "negative experience": 3, "disorganized": 3, "unavailable staff": 3, "broken facility": 3, "unhappy": 3, "noisy environment": 3, "discomfort": 3, "mistake": 3, "inaccurate": 3, "poor treatment": 3, "overcrowded": 3, "unsuitable": 3, "inappropriate": 3, 
                       "misleading": 3, "faulty": 3, "unpleasant": 3, "conflicting": 3, "defective": 3, "unskilled": 3, "untrained": 3, "poor infrastructure": 3, "incorrect information": 3, "long delays": 2, "missed opportunity": 2, "wrong timing": 2, "inconsistent": 2, "mismatched": 2, "insufficient support": 2, "bad scheduling": 2, "long queue": 2, "no response": 2, "unqualified": 2, "insufficient staff": 2, 
                       "no alternative": 2, "unattractive": 2, "unfriendly": 2, "not helpful": 2, "delay response": 2, "not fixed": 2, "stressed": 2, "unacceptable": 2, "poor condition of service": 2, "unbalanced": 2, "unsatisfactory condition": 2, "neglected": 2, "poorly executed": 2, "worn out": 2, "old": 2, "bothering": 2, "damaged goods": 2, "incomplete": 2, "not up to mark": 2, "low quality": 2, "bad experience overall": 2, 
                       "poor facilities": 2, "unmotivated": 2, "horrible": 2, "undelivered": 2, "unconfirmed": 2, "missed opportunity": 2, "incomplete order": 2, "improper": 2, "failed": 2, "subpar": 2, "unsatisfactory service": 2, "terrible": 2, "mismanagement": 2, "unsure": 2, "unfocused": 2, "offensive": 2, "incompetence": 2, "frustration": 2, "unrealistic": 2, "unbelievable": 2, "faulty equipment": 2, "dissatisfied": 2, "lack of cleanliness": 1, 
                       "problem": 1, "issue": 1, "complaint": 1, "concern": 1, "other": 1}

    
    impact_score = 1  # Default impact score for non-critical keywords
    for keyword, score in keywords_scores.items():
        if keyword in complaint.additional_info.lower():
            impact_score = score
            break

    # Time Sensitivity Factor
    time_elapsed = datetime.now() - datetime.combine(complaint.date, complaint.time)
    hours_elapsed = time_elapsed.total_seconds() / 3600
    if hours_elapsed <= 1:
        time_sensitivity = 3
    elif hours_elapsed <= 6:
        time_sensitivity = 2
    else:
        time_sensitivity = 1

    # Age Factor
    age_factor = 2 if complaint.age > 65 else (1 if complaint.age < 18 else 0)

    # Department Weight
    department_weight = department_weights.get(complaint.department, 3)  # Default weight 3 for undefined departments

    # Calculate Urgency
    urgency = (impact_score * time_sensitivity) + age_factor + department_weight
    return urgency


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            # Redirect based on role and department
            if user.role.lower() == 'admin':
                return redirect(url_for('admin_dashboard', department=user.department))
            elif user.role.lower() == 'employee':
                return redirect(url_for('employee_dashboard'))  # Adjust accordingly
            return redirect(url_for('user_dashboard'))  # Assuming there's a user role
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])  # Hash password
        role = request.form['role']
        department = request.form['department'] if role in ['Admin', 'Employee'] else None         
        new_user = User(username=username, password=password, role=role, department=department)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can log in now.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    complaints = Complaint.query.filter_by(user_id=current_user.id).all()
    return render_template('user_dashboard.html', complaints=complaints)


@app.route('/complaint', methods=['GET', 'POST'])
@login_required
def complaint():
    if request.method == 'POST':
        # Ensure the 'age' field is present in the form data
        if 'age' not in request.form:
            flash('Age is required.', 'error')
            return redirect(url_for('complaint'))

        age = request.form['age']
        
        # Convert age to integer
        try:
            age = int(age)
        except ValueError:
            flash('Invalid age. Please enter a valid number.', 'error')
            return redirect(url_for('complaint'))

        # Ensure the upload directory exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        unique_id = str(datetime.now().timestamp())  # Generate a unique ID based on the current timestamp
        department = request.form['department']
        pnr_no = request.form['pnr_no']
        additional_info = request.form['additional_info']

        # Handle image upload
        images = request.files.getlist('images')
        image_paths = []
        for image in images:
            if image:
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_paths.append(filename)
        images_str = ','.join(image_paths)

        # Find the employee with the fewest unsolved complaints in the same department
        employee = (
            User.query.filter_by(role='Employee', department=department)
            .outerjoin(Complaint, (Complaint.assigned_employee_id == User.id) & (Complaint.status == 'Unsolved'))
            .group_by(User.id)
            .order_by(db.func.count(Complaint.id))
            .first()
        )

        # Create the complaint with the assigned employee
        complaint = Complaint(
            unique_id=unique_id,
            department=department,
            date=datetime.now().date(),
            time=datetime.now().time(),
            pnr_no=pnr_no,
            age=age,
            additional_info=additional_info,
            images=images_str,
            user_id=current_user.id,
            assigned_employee_id=employee.id if employee else None  # Assign if an employee is available
        )

        complaint.urgency = calculate_urgency(complaint)

        db.session.add(complaint)
        db.session.commit()

        if employee:
            flash(f'Complaint submitted successfully and assigned to {employee.username}!', 'success')
        else:
            flash('Complaint submitted successfully, but no employee is available for assignment.', 'warning')

        return redirect(url_for('user_dashboard'))

    return render_template('complaint.html')


@app.route('/track_complaints')
@login_required
def track_complaints():
    # Get all complaints filed by the logged-in user that are either unsolved or completed without feedback
    complaints = Complaint.query.filter(
        (Complaint.user_id == current_user.id) &
        ((Complaint.status == 'Unsolved') | (~Complaint.feedbacks.any()))
    ).all()

    return render_template('track_complaints.html', complaints=complaints)




@app.route('/submit_feedback/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def submit_feedback(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    # Ensure the complaint is completed before allowing feedback
    if complaint.status != 'Completed':
        flash('You can only submit feedback for completed complaints.', 'warning')
        return redirect(url_for('track_complaints'))

    if request.method == 'POST':
        feedback_text = request.form['feedback_text']
        rating = request.form.get('rating', type=int)  # Get rating from form
        sentiment = analyze_sentiment(feedback_text)

        # Check if feedback already exists for the complaint
        existing_feedback = Feedback.query.filter_by(complaint_id=complaint.id).first()
        if existing_feedback:
            flash('Feedback for this complaint has already been submitted.', 'info')
            return redirect(url_for('track_complaints'))

        # Create new feedback entry
        feedback = Feedback(
            complaint_id=complaint.id,
            feedback_text=feedback_text,
            sentiment=sentiment,
            rating=rating  # Include rating
        )
        db.session.add(feedback)

        # Update complaint status if needed
        complaint.feedback_status = 'Completed'
        db.session.commit()
        
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('feedback_form.html', complaint=complaint)


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/admin_dashboard/<department>')
@login_required
def admin_dashboard(department):
    # Fetch complaints for the specified department
    complaints = Complaint.query.filter_by(department=department).all()
    
    # Attach feedback to each complaint
    for complaint in complaints:
        feedback = Feedback.query.filter_by(complaint_id=complaint.id).first()
        complaint.feedback = feedback

    # Sentiment analysis statistics
    feedbacks = Feedback.query.join(Complaint).filter(Complaint.department == department).all()
    sentiment_counts = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
    for feedback in feedbacks:
        if feedback.sentiment in sentiment_counts:
            sentiment_counts[feedback.sentiment] += 1

    # Average user rating for the department
    ratings = [feedback.rating for feedback in feedbacks if feedback.rating is not None]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else "No ratings yet"

    # Prepare data for feedback trend graph (feedback count per day)
    feedback_dates = [feedback.created_at.date().isoformat() for feedback in feedbacks if feedback.created_at]
    feedback_trend = Counter(feedback_dates)
    sorted_trend_data = sorted(feedback_trend.items())
    trend_data = {
        "labels": [date for date, _ in sorted_trend_data],
        "data": [count for _, count in sorted_trend_data]
    }

    return render_template('admin_dashboard.html', complaints=complaints, sentiment_counts=sentiment_counts, avg_rating=avg_rating, trend_data=json.dumps(trend_data))



@app.route('/admin/employees')
@login_required
def view_employees():
    # Ensure the current user is an admin
    if current_user.role != 'Admin':
        flash("Access denied: Only admins can view this page.", 'danger')
        return redirect(url_for('home'))
    
    # Filter employees by the admin's department
    employees = User.query.filter_by(role='Employee', department=current_user.department).all()
    
    return render_template('view_employees.html', employees=employees, department=current_user.department)

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/employee_dashboard')
@login_required
def employee_dashboard():
    if current_user.role != 'Employee':
        flash("Access denied: Only employees can view this page.", 'danger')
        return redirect(url_for('home'))
    
    # Fetch complaints assigned to the current employee
    assigned_complaints = Complaint.query.filter_by(assigned_employee_id=current_user.id).order_by(Complaint.urgency.desc()).all()
    
    return render_template('employee_dashboard.html', complaints=assigned_complaints)

@app.route('/mark_as_solved/<complaint_id>', methods=['POST'])
@login_required
def mark_as_solved(complaint_id):
    # Find the complaint by unique ID
    complaint = Complaint.query.filter_by(unique_id=complaint_id).first()

    if complaint:
        # Delete the complaint from the database
        complaint.status = 'Completed'
        db.session.commit()

    return redirect(url_for('employee_dashboard'))

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/chatbot_message', methods=['POST'])
@login_required
def chatbot_message():
    user_message = request.form['message']
    
    bot_response = "Sorry, I didn't understand that."
    
    if "track" in user_message.lower():
        bot_response = "You can track your complaints on the [Track Complaints page]({}).".format(url_for('track_complaints'))
    elif "complaint" in user_message.lower():
        bot_response = "You can submit a complaint by visiting the [Complaint page]({}).".format(url_for('complaint'))
    elif "help" in user_message.lower():
        bot_response = "How can I assist you today? Feel free to ask any questions!"
    elif "feedback" in user_message.lower():
        bot_response = "You can submit feedback once your complaint is resolved on the [Feedback page]({}).".format(url_for('submit_feedback', complaint_id=123))  # Replace '123' with dynamic complaint ID if needed
    return bot_response

@socketio.on('message')
def handle_message(msg):
    print('Message from user: ' + msg)
    response = "I am a simple bot. You said: " + msg  # Simple response
    send(response, broadcast=True)


@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form['message']
    
    bot_response = chatbot_message()  # Get the bot's response
    
    return render_template('chat.html', user_message=user_message, bot_response=bot_response)

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/admin/statistics/<department>')
@login_required
def statistics(department):
    # Get feedback data for the department
    feedbacks = Feedback.query.filter(Complaint.department == department).join(Complaint).all()

    # Calculate average rating per user or department
    avg_rating = sum(feedback.rating for feedback in feedbacks) / len(feedbacks) if feedbacks else 0

    # Get the sentiment counts
    sentiment_counts = {
        'Positive': sum(1 for feedback in feedbacks if feedback.sentiment == 'Positive'),
        'Negative': sum(1 for feedback in feedbacks if feedback.sentiment == 'Negative'),
        'Neutral': sum(1 for feedback in feedbacks if feedback.sentiment == 'Neutral'),
    }

    # Feedback trend
    trend_data = db.session.query(
        db.func.strftime('%Y-%m', Feedback.timestamp).label('month'),
        db.func.count().label('count')
    ).group_by('month').all()

    # Generate feedback trend graph
    trend_graph = generate_feedback_trend_graph(trend_data)

    return render_template('admin_statistics.html', avg_rating=avg_rating, sentiment_counts=sentiment_counts, trend_data=trend_data, trend_graph=trend_graph)

@app.route('/admin/statistics/employee_performance/<department>')
@login_required
def employee_performance(department):
    # Get feedback data with the employees responsible for each complaint
    feedbacks = Feedback.query.join(Complaint).filter(Complaint.department == department).all()
    
    # Create a dictionary to store employee performance data
    employee_performance = {}
    for feedback in feedbacks:
        employee = feedback.complaint.assigned_employee
        if employee:
            if employee.id not in employee_performance:
                employee_performance[employee.id] = {'positive': 0, 'negative': 0, 'total': 0}
            employee_performance[employee.id]['total'] += 1
            if feedback.sentiment == 'Positive':
                employee_performance[employee.id]['positive'] += 1
            elif feedback.sentiment == 'Negative':
                employee_performance[employee.id]['negative'] += 1

    # Pass employee performance data to the template
    return render_template('employee_performance.html', employee_performance=employee_performance)

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/view_database')
def view_database():
    users = User.query.all()  # Fetch all users from the User table
    complaints = Complaint.query.all()  # Fetch all complaints from the Complaint table
    feedbacks = Feedback.query.all()
    return render_template('database.html', users=users, complaints=complaints, feedbacks=feedbacks)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure the database is initialized
    socketio.run(app, debug=True)  # Use SocketIO to run the app
