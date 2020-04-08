from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from app import app

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure SQLite database
db = SQL("sqlite:///app/league.db")

@app.route('/')
def home():
    # load announcements
    result = db.execute(
        "SELECT * FROM Announcements \
            ORDER BY a_id DESC"
        )
    return render_template("home.html", announcements = result)


# pass info in to index.html
@app.route('/index')
def index():
    test = db.execute(
        "SELECT * FROM league"
    )
    print(test)
    return render_template("index.html", var1=None, var2=None, var3=None)

@app.route('/players', methods=['GET', 'POST'])
def roster():
    team_names = db.execute(
        "SELECT Team.team_name\
            FROM Team\
                ORDER BY Team.team_name"
    )
    players = []
    selected = '' # saves selected value of dropdown list
    if request.method == 'GET':
        return render_template("players.html", teams=team_names, players=players, selection=selected)
    if request.method == 'POST':
        team_name = request.form['Team']
        players = db.execute(
        "SELECT User.first_name, User.last_name, Player.points, Player.assists, Player.rebounds\
            FROM Player\
            LEFT JOIN User ON Player.user_id = User.user_id\
            LEFT JOIN Roster ON Player.roster_id = Roster.roster_id\
            LEFT JOIN Team ON Team.roster_id = Player.roster_id\
            WHERE Team.team_name=?\
            ORDER BY User.first_name", 
            team_name
        )
        selected = team_name if len(players) != 0 else selected
        return render_template("players.html", teams=team_names, players=players, selection=selected)
        
@app.route('/addPlayer', methods =['GET', 'POST'])
def addPlayer():

    if request.method == 'POST':
        playerDetails = request.form
        Roster_id = playerDetails['Roster_id']
        First_name = playerDetails['First_name']
        Last_name = playerDetails['Last_name']
        Birth_year = playerDetails['Birth_year']
        Email = playerDetails['Email']
        Phone_num = playerDetails['Phone_num']
        
    return render_template('addPlayer.html')
    
    

@app.route('/manage', methods =['GET', 'POST'])
def manage():

        
    return render_template('manage.html')
