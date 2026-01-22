import os

from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "test"

def load_users():
    users = {}
    with open("users.txt", "r") as f:
        for line in f:
            username, password = line.strip().split(",")
            users[username] = password
    return users


def calculate_remaining_budget(overall, project, team_cut):
    team_cut_amount = (team_cut / 100.0) * overall
    remaining = overall - project - team_cut_amount
    return team_cut_amount, remaining


# ---------- Routes ----------


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_users()

        if username in users and users[username] == password:
            session["user"] = username
            print("LOGIN OK, session user =", session.get("user"))
            return redirect("/")

        else:
            error = "Invalid username or password"
            print("LOGIN FAIL for:", username)

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
def calculator():
    print("ON /, session user =", session.get("user"))
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

            if overall < 0 or project < 0 or team_cut < 0:
                raise ValueError("Values must be 0 or greater.")
            if people < 1:
                raise ValueError("People must be at least 1.")

            team_cut_amount, remaining = calculate_remaining_budget(
                overall, project, team_cut)

            result = {
                "team_cut": team_cut_amount,
                "per_person": team_cut_amount / people,
                "remaining": remaining,
            }

        except ValueError as e:
            error = str(e)

    return render_template("index.html", result=result, error=error)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)
