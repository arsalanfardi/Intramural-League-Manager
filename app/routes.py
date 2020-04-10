from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from app import app

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Set secret key for session (enables flash functionality)
app.secret_key = "secret key"

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
@app.route('/index')
def index():
    result = db.execute(
        "SELECT Team.team_name, Roster.roster_size, User.first_name AS captain_first_name, User.last_name AS captain_last_name\
            FROM Team\
            LEFT JOIN Roster\
            ON Team.roster_id = Roster.roster_id\
            LEFT JOIN User\
            ON Roster.captain_id = User.user_id"
    )
    return render_template("index.html", db_result=result)

@app.route('/players', methods=['GET', 'POST'])
def roster():
    team_names = get_teams()
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

@app.route('/schedule', methods = ['GET', 'POST'])
def schedule():
    selected=''
    team_names = get_teams()
    games_query = "SELECT Game.date, Game.time, Game.location, HomeTeam.team_name as home_team, AwayTeam.team_name as away_team, WinTeam.team_name as win_team\
                FROM Game\
                LEFT JOIN Team as HomeTeam ON Game.home_id = HomeTeam.team_id\
                LEFT JOIN Team as AwayTeam on Game.away_id = AwayTeam.team_id\
                LEFT JOIN Team as WinTeam on Game.winner_id = WinTeam.team_id"
    order_query = "\nORDER BY Game.date, Game.time"
        
    if request.method == 'POST':
        team_name = request.form['Team']
        if team_name != 'View all': # a specific team was selected
            team_selection_query = "\nWHERE HomeTeam.team_name=? OR AwayTeam.team_name=?"
            games = db.execute(games_query + team_selection_query + order_query, team_name, team_name)
            selected = team_name if len(games) != 0 else selected
            return render_template("schedule.html", teams=team_names, games=games, selection=selected)
    
    #Below is executed for GET requests and 'View all', returns all games
    games = db.execute(games_query + order_query)
    return render_template("schedule.html", teams=team_names, games=games, selection=selected)

@app.route('/manage', methods =['GET', 'POST'])
def manage():
    return render_template('manage.html')

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
    
    
@app.route('/addGame', methods =['GET', 'POST'])
def addGame():
    team_names = get_teams()
    referees = get_referees()
    if request.method == 'POST':
        if not null_request(request.form):
            game_details = request.form
            home_team = game_details['Home_team']
            away_team = game_details['Away_team']
            date = game_details['Date']
            time = game_details['Time']
            ref_first_name, ref_last_name = game_details['Referee'].split()
            location = game_details['Location']
            if home_team != away_team:
                db.execute(
                    "INSERT INTO Game (schedule_id, date, time, location, home_id, away_id, ref_id) \
                        VALUES (1, ?, ?, ?, \
                        (SELECT Team.team_id FROM Team WHERE Team.team_name=?),\
                        (SELECT Team.team_id FROM Team WHERE Team.team_name=?),\
                        (SELECT User.user_id FROM User WHERE User.first_name=? AND User.last_name=?))",
                        date, time, location, home_team, away_team, ref_first_name, ref_last_name
                )
                flash("Successful submission!")
            else:
                flash("Invalid team entry")
        else:
            flash("Please enter all fields")
    return render_template('addGame.html', teams=team_names, referees=referees)


def get_teams():
    team_names = db.execute(
        "SELECT Team.team_name\
            FROM Team\
                ORDER BY Team.team_name"
    )
    return team_names

def get_referees():
    referees = db.execute(
          "SELECT User.first_name, User.last_name\
            FROM Referee\
            LEFT JOIN User on User.user_id = Referee.user_id"
    )
    return referees

def null_request(request_form):
    for k, v in request_form.items():
        if len(request_form[k]) == 0:
            print("Null found")
            return True
    print("no nulls")
    return False