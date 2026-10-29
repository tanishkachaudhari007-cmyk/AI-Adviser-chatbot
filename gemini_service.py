from google import genai
import os


def generate_local_analysis(financial_data):
    """
    Generates a local financial analysis when Gemini AI
    is unavailable because of quota, server, or API issues.
    """

    total_income = float(financial_data.get("Total Income", 0))
    total_expenses = float(financial_data.get("Total Expenses", 0))
    current_savings = float(financial_data.get("Current Savings", 0))

    category_spending = financial_data.get(
        "Category-wise Spending", {}
    )

    budgets = financial_data.get("Budgets", [])
    saving_goals = financial_data.get("Saving Goals", [])

    # --------------------------------------------------
    # Savings Rate
    # --------------------------------------------------

    if total_income > 0:
        savings_rate = (current_savings / total_income) * 100
    else:
        savings_rate = 0

    # --------------------------------------------------
    # Highest Spending Category
    # --------------------------------------------------

    highest_category = None
    highest_amount = 0

    if category_spending:
        highest_category = max(
            category_spending,
            key=category_spending.get
        )
        highest_amount = category_spending[highest_category]

    # --------------------------------------------------
    # Budget Analysis
    # --------------------------------------------------

    budget_warnings = []

    for budget in budgets:

        category = budget.get("category")
        budget_amount = float(budget.get("amount", 0))

        spent = float(
            category_spending.get(category, 0)
        )

        if budget_amount > 0:

            percentage_used = (
                spent / budget_amount
            ) * 100

            if percentage_used > 100:

                budget_warnings.append(
                    f"⚠️ {category}: spending is "
                    f"{percentage_used:.1f}% of the budget."
                )

            elif percentage_used >= 80:

                budget_warnings.append(
                    f"🟡 {category}: spending has reached "
                    f"{percentage_used:.1f}% of the budget."
                )

    # --------------------------------------------------
    # Build Analysis
    # --------------------------------------------------

    analysis = []

    analysis.append("🧠 PERSONAL FINANCIAL ANALYSIS")
    analysis.append("=" * 35)

    # Overall summary

    analysis.append("\n💰 1. Overall Financial Summary")

    analysis.append(
        f"• Total Income: ₹{total_income:,.2f}"
    )

    analysis.append(
        f"• Total Expenses: ₹{total_expenses:,.2f}"
    )

    analysis.append(
        f"• Current Savings: ₹{current_savings:,.2f}"
    )

    analysis.append(
        f"• Savings Rate: {savings_rate:.1f}%"
    )

    # Financial health

    analysis.append("\n📊 2. Financial Health")

    if total_income == 0:

        analysis.append(
            "• No income has been recorded yet."
        )

        analysis.append(
            "• Add your income to receive a more accurate analysis."
        )

    elif current_savings < 0:

        analysis.append(
            "⚠️ Your expenses are currently higher than your income."
        )

        analysis.append(
            "• Focus on reducing non-essential expenses."
        )

    elif savings_rate < 10:

        analysis.append(
            "🟡 Your current savings rate is relatively low."
        )

        analysis.append(
            "• Try to gradually increase the amount saved each month."
        )

    elif savings_rate < 20:

        analysis.append(
            "🟢 You are saving, but there is room to improve."
        )

        analysis.append(
            "• Look for categories where spending can be reduced."
        )

    else:

        analysis.append(
            "✅ Your current savings rate is healthy."
        )

        analysis.append(
            "• Continue monitoring expenses and maintaining your saving habit."
        )

    # Spending observations

    analysis.append("\n💸 3. Spending Observations")

    if highest_category:

        analysis.append(
            f"• Highest spending category: "
            f"{highest_category} "
            f"(₹{highest_amount:,.2f})"
        )

        if total_expenses > 0:

            category_percentage = (
                highest_amount / total_expenses
            ) * 100

            analysis.append(
                f"• This represents approximately "
                f"{category_percentage:.1f}% of your total expenses."
            )

    else:

        analysis.append(
            "• No expense records are available yet."
        )

    # Budget warnings

    analysis.append("\n📊 4. Budget Analysis")

    if budget_warnings:

        for warning in budget_warnings:
            analysis.append(f"• {warning}")

    else:

        if budgets:

            analysis.append(
                "✅ Your recorded categories are currently within their budgets."
            )

        else:

            analysis.append(
                "• No category budgets have been created yet."
            )

    # Possible unnecessary spending

    analysis.append("\n🔍 5. Spending Improvement")

    if category_spending:

        sorted_categories = sorted(
            category_spending.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_categories = sorted_categories[:3]

        analysis.append(
            "• Review your highest-spending categories first:"
        )

        for category, amount in top_categories:

            analysis.append(
                f"  - {category}: ₹{amount:,.2f}"
            )

        analysis.append(
            "• Consider reducing non-essential spending "
            "in categories that are frequently high."
        )

    else:

        analysis.append(
            "• Add some expenses to identify spending patterns."
        )

    # Saving suggestions

    analysis.append("\n💡 6. Saving Suggestions")

    if current_savings > 0:

        suggested_saving = total_income * 0.20

        if current_savings < suggested_saving:

            analysis.append(
                f"• Consider gradually targeting around "
                f"₹{suggested_saving:,.2f} in savings."
            )

            analysis.append(
                "• Start by reducing one or two non-essential expenses."
            )

        else:

            analysis.append(
                "• Continue maintaining your current saving habit."
            )

            analysis.append(
                "• Consider assigning savings to specific financial goals."
            )

    else:

        analysis.append(
            "• Focus first on balancing income and expenses."
        )

    # Saving goals

    analysis.append("\n🎯 7. Saving Goals")

    if saving_goals:

        for goal in saving_goals:

            name = goal.get("name", "Goal")

            target = float(
                goal.get("target", 0)
            )

            saved = float(
                goal.get("saved", 0)
            )

            if target > 0:

                progress = (
                    saved / target
                ) * 100

                if progress > 100:
                    progress = 100

                analysis.append(
                    f"• {name}: {progress:.1f}% completed "
                    f"(₹{saved:,.2f} / ₹{target:,.2f})"
                )

    else:

        analysis.append(
            "• No saving goals have been created yet."
        )

    # Actionable tip

    analysis.append("\n🚀 8. One Actionable Tip")

    if highest_category:

        analysis.append(
            f"👉 Review your {highest_category} expenses "
            "and identify at least one expense you can reduce "
            "this month."
        )

    else:

        analysis.append(
            "👉 Start recording your daily expenses so the system "
            "can identify your spending patterns."
        )

    analysis.append(
        "\n⚠️ This analysis is for general financial guidance "
        "and is not professional financial advice."
    )

    return "\n".join(analysis)


def get_financial_advice(financial_data):

    api_key = os.getenv("GEMINI_API_KEY")

    # --------------------------------------------------
    # If Gemini API key is missing
    # --------------------------------------------------

    if not api_key:

        return {
            "success": True,
            "source": "Local Analysis",
            "message": generate_local_analysis(financial_data)
        }

    # --------------------------------------------------
    # Try Gemini AI
    # --------------------------------------------------

    try:

        client = genai.Client(
            api_key=api_key
        )

        prompt = f"""
You are an AI personal finance assistant.

Analyze the following user's financial information:

{financial_data}

Provide a clear and practical financial analysis.

Include these sections:

1. Overall Financial Summary
2. Spending Observations
3. Possible Unnecessary Spending
4. Budget Analysis
5. Saving Suggestions
6. Saving Goal Analysis
7. One Actionable Tip

Important instructions:

- Use the actual numbers provided.
- Explain the analysis in simple language.
- Do not invent financial information.
- Do not make risky investment recommendations.
- Do not claim to be a professional financial advisor.
- Focus on budgeting, spending habits and saving.
- Use Indian Rupee (₹) formatting where appropriate.
"""

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        # Make sure Gemini actually returned text

        if response and response.text:

            return {
                "success": True,
                "source": "Gemini AI",
                "message": response.text
            }

        # If Gemini returns an empty response,
        # use local analysis.

        return {
            "success": True,
            "source": "Local Analysis",
            "message": generate_local_analysis(financial_data)
        }

    # --------------------------------------------------
    # Gemini unavailable → Local fallback
    # --------------------------------------------------

    except Exception:

        return {
            "success": True,
            "source": "Local Analysis",
            "message": generate_local_analysis(financial_data)
        }