from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os
from datetime import datetime
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ============= DATABASE MODELS =============

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    income = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    __tablename__ = "expense"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), default="Other")
    date = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============= CATEGORY AUTOMATION =============

def categorize(description):
    """Automatically categorize expenses based on keywords"""
    description = str(description).lower()
    
    categories = {
        "Food": ["zomato", "swiggy", "restaurant", "food", "pizza", "burger", "cafe", "coffee"],
        "Shopping": ["amazon", "flipkart", "mall", "store", "shop", "ebay", "clothing"],
        "Travel": ["uber", "ola", "taxi", "flight", "train", "bus", "petrol", "gas"],
        "Bills": ["electricity", "water", "phone", "internet", "gas", "utility"],
        "Entertainment": ["netflix", "spotify", "movie", "cinema", "game", "youtube"],
        "Health": ["pharmacy", "hospital", "doctor", "medicine", "gym", "health"],
        "Education": ["school", "college", "book", "course", "tuition"],
    }
    
    for category, keywords in categories.items():
        if any(keyword in description for keyword in keywords):
            return category
    
    return "Other"

# ============= ROUTES =============

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        income = request.form.get("income", "0")
        
        if not username or not password:
            flash("Username and password are required!", "error")
            return render_template("register.html")
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "error")
            return render_template("register.html")
        
        try:
            user = User(
                username=username,
                password=generate_password_hash(password),
                income=float(income) if income else 0
            )
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error during registration: {str(e)}", "error")
            return render_template("register.html")
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("dashboard"))
        
        flash("Invalid username or password!", "error")
    
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)
    savings = current_user.income - total
    
    # Category breakdown
    category_breakdown = {}
    for exp in expenses:
        category_breakdown[exp.category] = category_breakdown.get(exp.category, 0) + exp.amount
    
    # Get highest category
    max_category = max(category_breakdown.items(), key=lambda x: x[1]) if category_breakdown else ('N/A', 0)
    
    return render_template("dashboard.html",
                           income=current_user.income,
                           total=total,
                           savings=savings,
                           expenses=expenses,
                           category_breakdown=category_breakdown,
                           max_category=max_category,
                           avg_spending=total / len(expenses) if expenses else 0)

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    if "file" not in request.files:
        flash("No file selected!", "error")
        return redirect(url_for("dashboard"))
    
    file = request.files["file"]
    
    if file.filename == "":
        flash("No file selected!", "error")
        return redirect(url_for("dashboard"))
    
    try:
        path = os.path.join(UPLOAD_FOLDER, f"{current_user.id}_{file.filename}")
        file.save(path)
        
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        
        count = 0
        for _, row in df.iterrows():
            exp = Expense(
                user_id=current_user.id,
                description=row.get("Description", "Unknown"),
                amount=float(row.get("Amount", 0)),
                category=categorize(row.get("Description", ""))
            )
            db.session.add(exp)
            count += 1
        
        db.session.commit()
        flash(f"Successfully uploaded {count} expenses!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error uploading file: {str(e)}", "error")
    
    return redirect(url_for("dashboard"))

@app.route("/savings_plan")
@login_required
def savings_plan():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    total = sum(e.amount for e in expenses)
    income = current_user.income
    savings = income - total
    
    recommended_save = income * 0.20
    save_percentage = (savings / income * 100) if income > 0 else 0
    
    # Calculate top spending categories
    category_breakdown = {}
    for exp in expenses:
        category_breakdown[exp.category] = category_breakdown.get(exp.category, 0) + exp.amount
    
    # Sort and get top 5 categories
    top_categories = sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
    
    advice = ""
    if income == 0:
        advice = "Please set your income to get personalized savings advice."
    elif save_percentage < 20:
        advice = "⚠️ You need to reduce spending and aim to save at least 20% of income."
    elif save_percentage < 30:
        advice = "✓ Good! You are saving, but try to increase savings to 30%."
    else:
        advice = "✅ Excellent! You are saving well. Keep up the good work!"
    
    return render_template("savings_plan.html",
                           income=income,
                           total=total,
                           savings=savings,
                           save_percentage=round(save_percentage, 2),
                           recommended=recommended_save,
                           advice=advice,
                           expenses=expenses,
                           top_categories=top_categories)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        try:
            current_user.income = float(request.form.get("income", current_user.income))
            db.session.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {str(e)}", "error")
    
    return render_template("profile.html", user=current_user)

@app.route("/delete_expense/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if expense and expense.user_id == current_user.id:
        db.session.delete(expense)
        db.session.commit()
        flash("Expense deleted successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/api/category_stats")
@login_required
def category_stats():
    """API endpoint for category statistics"""
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    stats = {}
    for exp in expenses:
        stats[exp.category] = stats.get(exp.category, 0) + exp.amount
    
    return jsonify(stats)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)