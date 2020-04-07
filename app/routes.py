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
@app.route('/index')
def index():
    test = db.execute(
        "SELECT * FROM league"
    )
    print(test)
    return render_template("index.html", var1=None, var2=None, var3=None)

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
    query = "SELECT Game.date, Game.time, Game.location, HomeTeam.team_name as home_team, AwayTeam.team_name as away_team, WinTeam.team_name as win_team\
                FROM Game\
                LEFT JOIN Team as HomeTeam ON Game.home_id = HomeTeam.team_id\
                LEFT JOIN Team as AwayTeam on Game.away_id = AwayTeam.team_id\
                LEFT JOIN Team as WinTeam on Game.winner_id = WinTeam.team_id"
    order = "\nORDER BY Game.date, Game.time"

    if request.method == 'GET':
        games = db.execute(query + order)
        return render_template("schedule.html", teams=team_names, games=games, selection=selected)
    
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

def get_teams():
    team_names = db.execute(
        "SELECT Team.team_name\
            FROM Team\
                ORDER BY Team.team_name"
    )
    return team_names