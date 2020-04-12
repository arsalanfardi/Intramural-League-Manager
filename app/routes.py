from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL
from app import app
import datetime

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
    result = db.execute(
        "SELECT Team.team_name, Roster.roster_size, User.first_name AS captain_first_name, User.last_name AS captain_last_name\
            FROM Team\
            LEFT JOIN Roster\
            ON Team.roster_id = Roster.roster_id\
            LEFT JOIN User\
            ON Roster.captain_id = User.user_id\
            ORDER BY Roster.roster_id"
    )

    wins = db.execute(
        "SELECT roster_id, COUNT(*) As wins FROM Game, Roster \
        WHERE roster_id = winner_id GROUP BY roster_id"
    )
    losses = db.execute(
        "SELECT roster_id, COUNT(*) As losses FROM Game, Roster \
        WHERE roster_id = loser_id GROUP BY roster_id"
    )
    for i in range(len(result)):
        result[i]['record'] = str(wins[i]['wins']) + "-" + str(losses[i]['losses'])

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
    games_query = "SELECT Game.date, Game.time, Game.location, HomeTeam.team_name as home_team, \
                AwayTeam.team_name as away_team, WinTeam.team_name as win_team, Game.score\
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
def add_player():
    team_names = get_teams()
    if request.method == 'POST':
        print(request.form)
        if not null_request(request.form):
            playerDetails = request.form
            Roster_id = playerDetails['Team']
            First_name = playerDetails['First_name']
            Last_name = playerDetails['Last_name']
            Birth_year = playerDetails['Birth_year']
            Email = playerDetails['Email']
            Phone_num = playerDetails['Phone_num']
            db.execute("INSERT INTO User(first_name, last_name, email, phone) VALUES(?, ?, ?, ?)", First_name, Last_name, Email, Phone_num)
            user_id = db.execute("SELECT max(user_id) FROM User")[0]['max(user_id)']
            db.execute("INSERT INTO Player(user_id, birth_year, roster_id) VALUES (?, ?, ?)", user_id, Birth_year, Roster_id)
            new_size = db.execute("SELECT roster_id, COUNT(*) As size FROM Player WHERE roster_id = ?", Roster_id)
            db.execute("UPDATE Roster SET roster_size = ? WHERE roster_id = ?", new_size[0]['size'], Roster_id)
            flash("Successful submission!")
        else:
            flash("Please enter all fields")
    return render_template('addPlayer.html', teams=team_names)

@app.route('/editPlayer', methods =['GET', 'POST'])
def editPlayer():
    players = get_players()
    if request.method == 'POST':
        if 'select_player' in request.form:
            player_id = request.form['Player']
            player_details = get_player(player_id)
            # Selected player to persist in drop down menu during the next render
            # Populate the page with data from the selected game, denoted by variables beginning with curr
            return render_template('editPlayer.html', players=players, selected_player=player_details[0])
        elif 'submit' in request.form:
            if not null_request(request.form):
                updated = request.form
                db.execute("UPDATE Player SET birth_year = ? WHERE user_id = ?", updated['Birth_year'], updated['User_id'])
                db.execute( "UPDATE User SET first_name = ?, last_name = ?, email = ?, phone = ? \
                             WHERE user_id = ?", updated['First_name'], updated['Last_name'], \
                                                 updated['Email'], updated['Phone_num'], updated['User_id'])
                flash("Successful submission!")
            else:
                flash("Please enter all fields")
        elif 'delete' in request.form:
            if not null_request(request.form):
            # Delete player and update roster size
                db.execute(
                    "DELETE FROM User WHERE user_id=?", request.form['User_id']
                )
                db.execute(
                    "DELETE FROM Player WHERE user_id=?", request.form['User_id']
                )
                new_size = db.execute("SELECT roster_id, COUNT(*) As size FROM Player WHERE roster_id = ?", request.form['Roster_id'])
                db.execute("UPDATE Roster SET roster_size = ? WHERE roster_id = ?", new_size[0]['size'], request.form['Roster_id'])
                flash("Deleted Player!")
            else:
                flash("No Player Selected")
    return render_template('editPlayer.html', players=players)

@app.route('/addGame', methods =['GET', 'POST'])
def add_game():
    team_names = get_teams()
    referees = get_referees()
    if request.method == 'POST':
        if not null_request(request.form):
            game_details = request.form
            ref_first_name, ref_last_name = game_details['Referee'].split()
            # Ensure the same team has not been inputted twice
            if game_details['Home_team'] != game_details['Away_team']:
                db.execute(
                    "INSERT INTO Game (schedule_id, date, time, location, home_id, away_id, ref_id) \
                        VALUES (1, ?, ?, ?, \
                        (SELECT Team.team_id FROM Team WHERE Team.team_name=?),\
                        (SELECT Team.team_id FROM Team WHERE Team.team_name=?),\
                        (SELECT User.user_id FROM Referee LEFT JOIN User WHERE User.first_name=? AND User.last_name=?))",
                        game_details['Date'], game_details['Time'], game_details['Location'],
                        game_details['Home_team'], game_details['Away_team'], ref_first_name, ref_last_name
                )
                flash("Successful submission!")
            else:
                flash("Invalid team entry")
        else:
            flash("Please enter all fields")
    return render_template('addGame.html', teams=team_names, referees=referees)

@app.route('/editGame', methods=['GET', 'POST'])
def edit_game():
    games = get_games()
    if request.method == 'POST':
        # Selecting a game to edit
        if 'select_game' in request.form:
            game_id = request.form['Game']
            game_details = get_game(game_id)
            # Selected game to persist in drop down menu during the next render
            selected_game = {'game_id': game_id, 'home_team': game_details['home_team'], 'away_team': game_details['away_team'], 'date': game_details['date']}
            curr_ref = game_details['ref_first_name'] + " " + game_details['ref_last_name']
            teams = [game_details['home_team'], game_details['away_team']]
            # Populate the page with data from the selected game, denoted by variables beginning with curr
            return render_template('editGame.html', games=games, selected_game=selected_game, curr_ref=curr_ref, curr_location=game_details['location'],
                referees=get_referees(), curr_date=game_details['date'], curr_time=game_details['time'], curr_win_team=game_details['win_team'], teams=teams, score=game_details['score'])
        # Submitting updates
        elif 'submit' in request.form:
            if not null_request(request.form):
                game_id = request.form['Game']
                updates = request.form
                game_details = get_game(game_id)
                selected_game = {'home_team': game_details['home_team'], 'away_team': game_details['away_team']}
                if selected_game['home_team'] == updates['Win_team']:
                    loser = selected_game['away_team']
                else:
                    loser = selected_game['home_team']
                ref_first_name, ref_last_name = updates['Referee'].split()
                db.execute(
                    "UPDATE Game\
                    SET winner_id = (SELECT Team.team_id FROM Team WHERE Team.team_name=?),\
                    loser_id = (SELECT Team.team_id FROM Team WHERE Team.team_name=?),\
                    location=?, date=?, time=?, score=?, \
                    ref_id = (SELECT User.user_id FROM Referee LEFT JOIN User WHERE User.first_name=? AND User.last_name=?)\
                    WHERE Game.game_id=?",
                    updates['Win_team'], loser, updates['Location'], updates['Date'], updates['Time'], updates['Score'],
                    ref_first_name, ref_last_name, game_id
                )
                flash("Successful submission!")
            else:
                flash("Please enter all fields")
        elif 'delete' in request.form:
            if not null_request(request.form):
            # Delete player and update roster size
                db.execute(
                    "DELETE FROM Game WHERE game_id=?", request.form['Game']
                )
                flash("Game deleted!")
                return render_template('editGame.html', games=games, selected_game=None)
            else:
                flash("No Game Selected")
            
    # Default render with no selected game (fields on page will be blank)
    return render_template('editGame.html', games=games, selected_game=None)

@app.route('/newAnnouncement', methods=['GET', 'POST'])
def add_announcement():
    if request.method == 'POST':
        if not null_request(request.form):
            announcement = request.form
            # Get today's date in proper format
            today = datetime.date.today()
            today_str = today.strftime("%B %d, %Y")
            db.execute("INSERT INTO Announcements(title, date, message) VALUES(?, ?, ?)", \
                        announcement['Title'], today_str, announcement['Body'])
            flash("Successful submission!")
        else:
            flash("Please enter all fields")
    # Default render 
    return render_template('newAnnouncement.html')

def get_teams():
    team_names = db.execute(
        "SELECT Team.team_name, Team.roster_id\
            FROM Team\
                ORDER BY Team.team_name"
    )
    return team_names

def get_players():
    players = db.execute(
          "SELECT User.first_name, User.last_name, Player.user_id \
            FROM Player\
            LEFT JOIN User on User.user_id = Player.user_id"
    )
    return players

def get_player(pid):
    player = db.execute(
        "SELECT Player.user_id, Player.roster_id, User.first_name, User.last_name, \
            Player.birth_year, User.email, User.phone\
            FROM Player\
            LEFT JOIN User ON Player.user_id = User.user_id\
			WHERE Player.user_id = ?", pid
    )
    return player

def get_referees():
    referees = db.execute(
          "SELECT User.first_name, User.last_name\
            FROM Referee\
            LEFT JOIN User on User.user_id = Referee.user_id"
    )
    return referees

def get_games():
    games = db.execute(
        "SELECT Game.game_id, Game.date, HomeTeam.team_name as home_team, AwayTeam.team_name as away_team\
        FROM Game\
        LEFT JOIN Team as HomeTeam ON Game.home_id = HomeTeam.team_id\
        LEFT JOIN Team as AwayTeam on Game.away_id = AwayTeam.team_id\
        ORDER BY Game.game_id"
    )
    return games

def get_game(game_id):
    game = db.execute(
        "SELECT Game.date, Game.time, Game.location, HomeTeam.team_name as home_team, AwayTeam.team_name as away_team,\
        User.first_name as ref_first_name, User.last_name as ref_last_name, WinTeam.team_name as win_team, Game.score as score \
        FROM Game\
        LEFT JOIN Team as HomeTeam ON Game.home_id = HomeTeam.team_id\
        LEFT JOIN Team as AwayTeam on Game.away_id = AwayTeam.team_id\
        LEFT JOIN Team as WinTeam on Game.winner_id = WinTeam.team_id\
        LEFT JOIN User on User.user_id = Game.ref_id\
        WHERE Game.game_id=?",
        game_id
    )
    return game[0] # query returns a one element list

def null_request(request_form):
    for k, v in request_form.items():
        if len(request_form[k]) == 0 or request_form[k] == 'NULL':
            return True
    return False
