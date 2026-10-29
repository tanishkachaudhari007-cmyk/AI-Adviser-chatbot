from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from dotenv import load_dotenv
from functools import wraps
from datetime import date

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import os

from models.models import (
    db,
    User,
    Income,
    Expense,
    Budget,
    SavingGoal
)

from services.gemini_service import get_financial_advice


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "personal-finance-secret-key"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# =========================================================
# LOGIN REQUIRED DECORATOR
# =========================================================

def login_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view


# =========================================================
# GLOBAL SIDEBAR DATA
# Available on every page
# =========================================================

@app.context_processor
def inject_sidebar_data():

    # If user is not logged in
    if "user_id" not in session:

        return {
            "alert_count": 0,
            "sidebar_alerts": []
        }

    user_id = session["user_id"]

    alerts = []

    # -----------------------------------------------------
    # Get user's financial data
    # -----------------------------------------------------

    incomes = Income.query.filter_by(
        user_id=user_id
    ).all()

    expenses = Expense.query.filter_by(
        user_id=user_id
    ).all()

    budgets = Budget.query.filter_by(
        user_id=user_id
    ).all()

    # -----------------------------------------------------
    # Calculate totals
    # -----------------------------------------------------

    total_income = sum(
        income.amount
        for income in incomes
    )

    total_expenses = sum(
        expense.amount
        for expense in expenses
    )

    savings = total_income - total_expenses

    # -----------------------------------------------------
    # Spending alert
    # -----------------------------------------------------

    if total_income > 0 and total_expenses > total_income:

        alerts.append({

            "type": "danger",

            "title": "Spending Alert",

            "message":
                "Your total expenses are higher "
                "than your recorded income."

        })

    # -----------------------------------------------------
    # Low savings alert
    # -----------------------------------------------------

    elif total_income > 0:

        savings_rate = (
            savings / total_income
        ) * 100

        if savings_rate < 20:

            alerts.append({

                "type": "warning",

                "title": "Low Savings Rate",

                "message":
                    f"Your current savings rate is "
                    f"{savings_rate:.1f}%."

            })

    # -----------------------------------------------------
    # Budget alerts
    # -----------------------------------------------------

    for budget in budgets:

        spent = sum(

            expense.amount

            for expense in expenses

            if expense.category == budget.category

        )

        # Budget exceeded
        if spent > budget.amount:

            alerts.append({

                "type": "danger",

                "title":
                    f"{budget.category} Budget Exceeded",

                "message":
                    f"You spent ₹{spent:,.2f} "
                    f"against a budget of "
                    f"₹{budget.amount:,.2f}."

            })

        # Budget almost reached
        elif (
            budget.amount > 0
            and spent >= budget.amount * 0.8
        ):

            alerts.append({

                "type": "warning",

                "title":
                    f"{budget.category} Budget Warning",

                "message":
                    f"You have used "
                    f"{(spent / budget.amount) * 100:.0f}% "
                    f"of this budget."

            })

    return {

        "alert_count": len(alerts),

        "sidebar_alerts": alerts

    }


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # Already logged in
    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        # Find user
        user = User.query.filter_by(
            email=email
        ).first()

        if not user:

            flash(
                "No account found with this email.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        # Check password
        password_valid = False

        try:

            password_valid = check_password_hash(
                user.password,
                password
            )

        except Exception:

            password_valid = False

        # Compatibility for an old plain-text password
        if not password_valid:

            if user.password == password:

                password_valid = True

                user.password = generate_password_hash(
                    password
                )

                db.session.commit()

        if not password_valid:

            flash(
                "Incorrect password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        # Create login session
        session["user_id"] = user.id

        session["user_name"] = user.name

        session["user_email"] = user.email

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "login.html"
    )


# =========================================================
# SIGN UP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not name or not email or not password:

            flash(
                "Please fill in all required fields.",
                "danger"
            )

            return render_template(
                "signup.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "signup.html"
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "signup.html"
            )

        # Check existing account
        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return render_template(
                "signup.html"
            )

        # -------------------------------------------------
        # Create account
        # -------------------------------------------------

        new_user = User(

            name=name,

            email=email,

            password=generate_password_hash(
                password
            )

        )

        db.session.add(new_user)

        db.session.commit()

        flash(
            "Account created successfully. Please log in.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "signup.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
@login_required
def dashboard():

    user_id = session["user_id"]

    today = date.today()

    # -----------------------------------------------------
    # User income
    # -----------------------------------------------------

    all_incomes = Income.query.filter_by(
        user_id=user_id
    ).all()

    monthly_incomes = [

        income

        for income in all_incomes

        if income.entry_date.year == today.year

        and income.entry_date.month == today.month

    ]

    # -----------------------------------------------------
    # User expenses
    # -----------------------------------------------------

    all_expenses = Expense.query.filter_by(
        user_id=user_id
    ).all()

    monthly_expenses = [

        expense

        for expense in all_expenses

        if expense.expense_date.year == today.year

        and expense.expense_date.month == today.month

    ]

    # -----------------------------------------------------
    # Financial totals
    # -----------------------------------------------------

    total_income = sum(

        income.amount

        for income in monthly_incomes

    )

    total_expenses = sum(

        expense.amount

        for expense in monthly_expenses

    )

    savings = (
        total_income - total_expenses
    )

    if total_income > 0:

        savings_rate = (
            savings / total_income
        ) * 100

    else:

        savings_rate = 0

    # -----------------------------------------------------
    # Chart data
    # -----------------------------------------------------

    chart_income = round(
        total_income,
        2
    )

    chart_expenses = round(
        total_expenses,
        2
    )

    chart_savings = round(
        max(savings, 0),
        2
    )

    # -----------------------------------------------------
    # Budgets
    # -----------------------------------------------------

    budgets = Budget.query.filter_by(
        user_id=user_id
    ).all()

    # -----------------------------------------------------
    # Dashboard alerts
    # -----------------------------------------------------

    alerts = []

    if (
        total_income > 0
        and total_expenses > total_income
    ):

        alerts.append({

            "type": "danger",

            "title": "Spending Alert",

            "message":
                "Your monthly expenses are higher "
                "than your monthly income."

        })

    elif (
        total_income > 0
        and savings_rate < 20
    ):

        alerts.append({

            "type": "warning",

            "title": "Low Savings Rate",

            "message":
                f"Your current savings rate is "
                f"{savings_rate:.1f}%."

        })

    # Budget alerts
    for budget in budgets:

        spent = sum(

            expense.amount

            for expense in monthly_expenses

            if expense.category == budget.category

        )

        if spent > budget.amount:

            alerts.append({

                "type": "danger",

                "title":
                    f"{budget.category} Budget Exceeded",

                "message":
                    f"You spent ₹{spent:,.2f} "
                    f"against a budget of "
                    f"₹{budget.amount:,.2f}."

            })

        elif (
            budget.amount > 0
            and spent >= budget.amount * 0.8
        ):

            alerts.append({

                "type": "warning",

                "title":
                    f"{budget.category} Budget Warning",

                "message":
                    f"You have used "
                    f"{(spent / budget.amount) * 100:.0f}% "
                    f"of this budget."

            })

    return render_template(

        "index.html",

        total_income=total_income,

        total_expenses=total_expenses,

        savings=savings,

        savings_rate=savings_rate,

        alerts=alerts,

        alert_count=len(alerts),

        chart_income=chart_income,

        chart_expenses=chart_expenses,

        chart_savings=chart_savings

    )


# =========================================================
# INCOME
# =========================================================

@app.route("/income", methods=["GET", "POST"])
@login_required
def income():

    user_id = session["user_id"]

    if request.method == "POST":

        source = request.form.get(
            "source",
            ""
        ).strip()

        amount_text = request.form.get(
            "amount",
            "0"
        )

        try:

            amount = float(amount_text)

        except ValueError:

            flash(
                "Please enter a valid income amount.",
                "danger"
            )

            return redirect(
                url_for("income")
            )

        if not source:

            flash(
                "Please enter an income source.",
                "danger"
            )

            return redirect(
                url_for("income")
            )

        if amount <= 0:

            flash(
                "Income amount must be greater than zero.",
                "danger"
            )

            return redirect(
                url_for("income")
            )

        new_income = Income(

            source=source,

            amount=amount,

            user_id=user_id

        )

        db.session.add(new_income)

        db.session.commit()

        flash(
            "Income added successfully.",
            "success"
        )

        return redirect(
            url_for("income")
        )

    incomes = Income.query.filter_by(
        user_id=user_id
    ).order_by(
        Income.entry_date.desc()
    ).all()

    return render_template(

        "income.html",

        incomes=incomes

    )


# =========================================================
# EXPENSES
# =========================================================

@app.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():

    user_id = session["user_id"]

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        amount_text = request.form.get(
            "amount",
            "0"
        )

        try:

            amount = float(amount_text)

        except ValueError:

            flash(
                "Please enter a valid expense amount.",
                "danger"
            )

            return redirect(
                url_for("expenses")
            )

        if not title or not category:

            flash(
                "Please fill in all expense details.",
                "danger"
            )

            return redirect(
                url_for("expenses")
            )

        if amount <= 0:

            flash(
                "Expense amount must be greater than zero.",
                "danger"
            )

            return redirect(
                url_for("expenses")
            )

        new_expense = Expense(

            title=title,

            category=category,

            amount=amount,

            user_id=user_id

        )

        db.session.add(new_expense)

        db.session.commit()

        flash(
            "Expense added successfully.",
            "success"
        )

        return redirect(
            url_for("expenses")
        )

    expenses_list = Expense.query.filter_by(
        user_id=user_id
    ).order_by(
        Expense.expense_date.desc()
    ).all()

    return render_template(

        "expenses.html",

        expenses=expenses_list

    )


# =========================================================
# BUDGET
# =========================================================

@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():

    user_id = session["user_id"]

    if request.method == "POST":

        category = request.form.get(
            "category",
            ""
        ).strip()

        amount_text = request.form.get(
            "amount",
            "0"
        )

        try:

            amount = float(amount_text)

        except ValueError:

            flash(
                "Please enter a valid budget amount.",
                "danger"
            )

            return redirect(
                url_for("budget")
            )

        if not category:

            flash(
                "Please select a budget category.",
                "danger"
            )

            return redirect(
                url_for("budget")
            )

        if amount <= 0:

            flash(
                "Budget amount must be greater than zero.",
                "danger"
            )

            return redirect(
                url_for("budget")
            )

        existing_budget = Budget.query.filter_by(

            category=category,

            user_id=user_id

        ).first()

        if existing_budget:

            existing_budget.amount = amount

        else:

            new_budget = Budget(

                category=category,

                amount=amount,

                user_id=user_id

            )

            db.session.add(new_budget)

        db.session.commit()

        flash(
            "Budget saved successfully.",
            "success"
        )

        return redirect(
            url_for("budget")
        )

    budgets = Budget.query.filter_by(
        user_id=user_id
    ).all()

    expenses_list = Expense.query.filter_by(
        user_id=user_id
    ).all()

    budget_data = []

    for budget_item in budgets:

        spent = sum(

            expense.amount

            for expense in expenses_list

            if expense.category ==
            budget_item.category

        )

        remaining = (
            budget_item.amount - spent
        )

        budget_data.append({

            "category":
                budget_item.category,

            "budget":
                budget_item.amount,

            "spent":
                spent,

            "remaining":
                remaining

        })

    return render_template(

        "budget.html",

        budget_data=budget_data

    )


# =========================================================
# SAVING GOALS
# =========================================================

@app.route("/savings", methods=["GET", "POST"])
@login_required
def savings():

    user_id = session["user_id"]

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        target_text = request.form.get(
            "target",
            "0"
        )

        saved_text = request.form.get(
            "saved",
            "0"
        )

        try:

            target = float(target_text)

            saved = float(saved_text)

        except ValueError:

            flash(
                "Please enter valid goal amounts.",
                "danger"
            )

            return redirect(
                url_for("savings")
            )

        if not name:

            flash(
                "Please enter a goal name.",
                "danger"
            )

            return redirect(
                url_for("savings")
            )

        if target <= 0:

            flash(
                "Target amount must be greater than zero.",
                "danger"
            )

            return redirect(
                url_for("savings")
            )

        if saved < 0:

            flash(
                "Saved amount cannot be negative.",
                "danger"
            )

            return redirect(
                url_for("savings")
            )

        new_goal = SavingGoal(

            name=name,

            target=target,

            saved=saved,

            user_id=user_id

        )

        db.session.add(new_goal)

        db.session.commit()

        flash(
            "Saving goal added successfully.",
            "success"
        )

        return redirect(
            url_for("savings")
        )

    goals = SavingGoal.query.filter_by(
        user_id=user_id
    ).all()

    goal_data = []

    for goal in goals:

        remaining = (
            goal.target - goal.saved
        )

        if goal.target > 0:

            progress = (
                goal.saved / goal.target
            ) * 100

        else:

            progress = 0

        progress = min(
            max(progress, 0),
            100
        )

        goal_data.append({

            "name":
                goal.name,

            "target":
                goal.target,

            "saved":
                goal.saved,

            "remaining":
                remaining,

            "progress":
                progress

        })

    return render_template(

        "savings.html",

        goal_data=goal_data

    )


# =========================================================
# AI FINANCIAL ADVISOR
# =========================================================

@app.route("/advisor", methods=["GET", "POST"])
@login_required
def advisor():

    user_id = session["user_id"]

    # -----------------------------------------------------
    # User data
    # -----------------------------------------------------

    incomes = Income.query.filter_by(
        user_id=user_id
    ).all()

    expenses = Expense.query.filter_by(
        user_id=user_id
    ).all()

    budgets = Budget.query.filter_by(
        user_id=user_id
    ).all()

    goals = SavingGoal.query.filter_by(
        user_id=user_id
    ).all()

    # -----------------------------------------------------
    # Financial calculations
    # -----------------------------------------------------

    total_income = sum(

        income.amount

        for income in incomes

    )

    total_expenses = sum(

        expense.amount

        for expense in expenses

    )

    savings = (
        total_income - total_expenses
    )

    # -----------------------------------------------------
    # AI response
    # -----------------------------------------------------

    advice = None

    if request.method == "POST":

        category_spending = {}

        for expense in expenses:

            category = expense.category

            category_spending[category] = (

                category_spending.get(
                    category,
                    0
                )

                + expense.amount

            )

        financial_data = {

            "User":
                session.get(
                    "user_name",
                    "User"
                ),

            "Total Income":
                total_income,

            "Total Expenses":
                total_expenses,

            "Current Savings":
                savings,

            "Category-wise Spending":
                category_spending,

            "Budgets": [

                {
                    "category":
                        budget.category,

                    "amount":
                        budget.amount
                }

                for budget in budgets

            ],

            "Saving Goals": [

                {
                    "name":
                        goal.name,

                    "target":
                        goal.target,

                    "saved":
                        goal.saved
                }

                for goal in goals

            ]

        }

        advice = get_financial_advice(
            financial_data
        )

    return render_template(

        "advisor.html",

        advice=advice,

        total_income=total_income,

        total_expenses=total_expenses,

        savings=savings

    )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

with app.app_context():

    db.create_all()


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )
