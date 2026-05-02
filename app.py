from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Project, Task
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return redirect(url_for('login'))


# -----------------------------
# Signup
# -----------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists!", "danger")
            return redirect(url_for('signup'))

        new_user = User(
            name=name,
            email=email,
            password=password,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


# -----------------------------
# Login
# -----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "danger")

    return render_template('login.html')


# -----------------------------
# Dashboard
# -----------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        tasks = Task.query.all()
    else:
        tasks = Task.query.filter_by(assigned_to=current_user.id).all()

    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == "Completed"])
    pending_tasks = len([t for t in tasks if t.status != "Completed"])

    overdue_tasks = len([
        t for t in tasks
        if t.due_date
        and t.due_date < datetime.utcnow().date()
        and t.status != "Completed"
    ])

    return render_template(
        'dashboard.html',
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks
    )


# -----------------------------
# Create Project
# -----------------------------
@app.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    if current_user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        project = Project(
            title=title,
            description=description,
            created_by=current_user.id
        )

        db.session.add(project)
        db.session.commit()

        flash("Project created successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('create_project.html')


# -----------------------------
# Create Task
# -----------------------------
@app.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    if current_user.role.lower() != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        print("FORM SUBMITTED")  # Debug line

        title = request.form['title']
        description = request.form['description']
        due_date = datetime.strptime(
            request.form['due_date'],
            "%Y-%m-%d"
        ).date()

        assigned_to = int(request.form['assigned_to'])
        project_id = int(request.form['project_id'])

        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            assigned_to=assigned_to,
            project_id=project_id,
            status="Pending"
        )

        db.session.add(task)
        db.session.commit()

        flash("Task created successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('create_task.html')
# -----------------------------
# View Tasks
# -----------------------------
@app.route('/view_tasks')
@login_required
def view_tasks():
    if current_user.role == 'admin':
        tasks = Task.query.all()
    else:
        tasks = Task.query.filter_by(
            assigned_to=current_user.id
        ).all()

    return render_template(
        'view_tasks.html',
        tasks=tasks
    )


# -----------------------------
# Update Task Status
# -----------------------------
@app.route('/update_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)

    if current_user.role != 'admin' and task.assigned_to != current_user.id:
        flash("Access denied!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        task.status = request.form['status']
        db.session.commit()

        flash("Task status updated successfully!", "success")
        return redirect(url_for('view_tasks'))

    return render_template(
        'update_task.html',
        task=task
    )


# -----------------------------
# Logout
# -----------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)