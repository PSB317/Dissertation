import os

from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "test"


def load_users():
    users = {}
    with open("users.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line or "," not in line:
                continue
            username, password = line.split(",", 1)
            users[username.strip()] = password.strip()
    return users


# ONLY budget maths here
def calculate_remaining_budget(overall, project, team_cut):
    team_cut_amount = (team_cut / 100.0) * overall
    remaining = overall - project - team_cut_amount
    return team_cut_amount, remaining

#Weighting system 
def project_duration_estimate(project,people,expertise):
    basecost_perday = 500 
    expertise_factor = 1.6 - (0.15 * expertise)
    if people <=0:
     people = 1

    days = (project / (people * basecost_perday)) * expertise_factor
    duration_days = max(1, int(days))
    return duration_days

#Calculating risk score 

def calculate_risk_score(remaining_budget , expertise, estimated_days,days_to_deadline):
    score = 1 
    if expertise <=2:
        score += 1

    if days_to_deadline <=0:
        score += 2

    else:
        pressure = estimated_days / days_to_deadline
        if pressure > 1.0:
            score += 1
        if pressure >1.25:
            score += 1

    if remaining_budget < 0:
        score +=1

    score = max(1, min(5, score))
    if score <=2:
        level = "Low risk"
    elif score == 3:
        level = "Medium risk"
    else:
        level = "High risk"
    return score, level
# ---------- Routes ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        users = load_users()

        if username in users and users[username] == password:
            session["user"] = username
            return redirect("/")
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
def calculator():
    if "user" not in session:
        return redirect(url_for("login"))

    result = None
    error = None

    if request.method == "POST":
        try:
            overall = float(request.form["overall"])
            project = float(request.form["project"])
            people = int(request.form["people"])
            team_cut = float(request.form["team_cut"])

            expertise = int(request.form["expertise"])
            days_to_deadline = int(request.form["days_to_deadline"])

            if overall < 0 or project < 0 or team_cut < 0:
                raise ValueError("Values must be 0 or greater.")
            if people < 1:
                raise ValueError("People must be at least 1.")
            if not (1 <= expertise <= 5):
                raise ValueError("Expertise must be between 1 and 5.")
            if days_to_deadline < 0:
                raise ValueError("Days until deadline must be 0 or greater.")

            team_cut_amount, remaining = calculate_remaining_budget(
                overall, project, team_cut)

            estimated_days = project_duration_estimate(project, people, expertise)

            risk_score, risk_level = calculate_risk_score(
                remaining_budget=remaining,
                expertise=expertise,
                estimated_days=estimated_days,
                days_to_deadline=days_to_deadline
            )

            

            result = {
                "team_cut": team_cut_amount,
                "per_person": team_cut_amount / people,
                "remaining": remaining,
                "expertise": expertise,
                "days_to_deadline": days_to_deadline,
                "estimated_days":estimated_days ,
                "risk_score": risk_score,
                "risk_level": risk_level,
            }

        except (ValueError, KeyError) as e:
            error = str(e)

    return render_template("index.html", result=result, error=error)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)
