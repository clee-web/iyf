from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import os

# Initialize App
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Models
class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    contact = db.Column(db.String(15))
    area_of_residence = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    session = db.Column(db.String(20))
    payments = db.relationship('Payment', backref='student', lazy=True)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    academic_qualification = db.Column(db.String(200))
    uploaded_file = db.Column(db.String(200))

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    payment_type = db.Column(db.String(50))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Admin Login Route
@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin@iyf':
            session['admin'] = True
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

# Admin Dashboard
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Dashboard Chart Data API
@app.route('/api/charts', methods=['GET'])
def charts_data():
    # Student Enrollment per Class
    class_enrollment = db.session.query(Class.name, db.func.count(Student.id)).join(Student).group_by(Class.name).all()
    enrollment_data = {cls: count for cls, count in class_enrollment}
    
    # Payment Data
    payment_data = db.session.query(Payment.payment_type, db.func.sum(Payment.amount)).group_by(Payment.payment_type).all()
    payments = {ptype: float(amount) for ptype, amount in payment_data}
    
    # Gender Distribution
    gender_data = db.session.query(Student.gender, db.func.count(Student.id)).group_by(Student.gender).all()
    gender_distribution = {gender: count for gender, count in gender_data}
    
    # Session Enrollment
    session_data = db.session.query(Student.session, db.func.count(Student.id)).group_by(Student.session).all()
    session_enrollment = {session: count for session, count in session_data}
    
    return jsonify({
        'enrollment_data': enrollment_data,
        'payments': payments,
        'gender_distribution': gender_distribution,
        'session_enrollment': session_enrollment
    })

# Add Class
@app.route('/add_class', methods=['GET', 'POST'])
def add_class():
    if request.method == 'POST':
        name = request.form['name']
        new_class = Class(name=name)
        db.session.add(new_class)
        db.session.commit()
        flash('Class added successfully', 'success')
        return redirect(url_for('view_classes'))
    return render_template('add_class.html')

@app.route('/view_classes')
def view_classes():
    classes = Class.query.all()
    return render_template('view_classes.html', classes=classes)

# Add Student
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    classes = Class.query.all()
    if request.method == 'POST':
        name = request.form['name']
        class_id = request.form['class_id']
        contact = request.form['contact']
        area_of_residence = request.form['area_of_residence']
        gender = request.form['gender']
        session_info = request.form['session']
        admin_number = f'ST{int(datetime.utcnow().timestamp())}'
        new_student = Student(
            admin_number=admin_number, name=name, class_id=class_id,
            contact=contact, area_of_residence=area_of_residence,
            gender=gender, session=session_info
        )
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully', 'success')
        return redirect(url_for('view_students'))
    return render_template('add_student.html', classes=classes)

@app.route('/view_students')
def view_students():
    students = Student.query.all()
    return render_template('view_students.html', students=students)

# Serve Static Files for Charts
@app.route('/charts')
def charts():
    return render_template('charts.html')

# Run Server
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
