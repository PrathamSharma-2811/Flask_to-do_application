from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///todo.db'
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('todos', lazy=True))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Task {self.id}>'

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        todos = Todo.query.filter_by(user_id=user.id).order_by(Todo.date_created.desc()).all()
        return render_template('index.html', user=user, todos=todos)
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect('/')
        else:
            return '<script>alert("Invalid username/password combination.");window.location.href="/login";</script>'
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return '<script>alert("Username already exists. Please choose a different username.");window.location.href="/signup";</script>'
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return redirect('/')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

@app.route('/add', methods=["POST"])
def add_task():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        task_content = request.form["content"]
        new_task = Todo(content=task_content, user=user, date_created=datetime.utcnow())

        try:
            db.session.add(new_task)
            db.session.commit()
        except Exception as e:
            print("Could not add task:", e)
    return redirect('/')

@app.route('/delete/<int:id>')
def delete_task(id):
    if 'user_id' in session:
        task_delete = Todo.query.get_or_404(id)
        db.session.delete(task_delete)
        db.session.commit()
    return redirect('/')

@app.route('/update/<int:id>', methods=["GET", "POST"])
def update_task(id):
    if 'user_id' in session:
        task = Todo.query.get_or_404(id)
        if task.user_id == session['user_id']:
            if request.method == "POST":
                task.content = request.form["content"]

                try:
                    db.session.commit()
                    return redirect("/")
                except Exception as e:
                    print("Could not update task:", e)
                    return redirect("/")
            else:
                return render_template("update.html", task=task)
        else:
            return redirect('/')
    else:
        return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
