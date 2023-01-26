from flask import Blueprint, render_template, request, flash, jsonify
from .models import Player
from . import db, slice_n_dice as snd

views = Blueprint('views', __name__)

current_players = []

teamRed_current_match = []

teamBlue_current_match = []

win_rate_teamRed = 0

win_rate_teamBlue = 0

fairness_counter = 0


#####################################################################
# First page of website


@views.route('/', methods=['GET', 'POST'])
def start():
    current_players.clear()
    teamRed_current_match.clear()
    teamBlue_current_match.clear()
    global fairness_counter, win_rate_teamRed, win_rate_teamBlue
    fairness_counter = 0
    win_rate_teamRed = 0
    win_rate_teamBlue = 0
    players = Player.query.all()
    return render_template("start.html", players=players, current_players=current_players)


####################################################################


@views.route('/new-player', methods=['GET', 'POST'])
def new_player():
    if request.method == 'POST':
        name = request.form.get('name')

        if len(name) < 2:
            flash('Name is too short!', category='error')
        else:
            name_already_in_db = Player.query.filter_by(name=name).first()
            if name_already_in_db:
                flash('Name already exists.', category='error')
            else:
                new_player_to_insert = Player(name=name)
                db.session.add(new_player_to_insert)
                db.session.commit()
                flash('Player added!', category='success')

    players = Player.query.all()
    print(players)
    return render_template("new_player.html", players=players)


####################################################################


@views.route('/hidden-delete-player', methods=['GET', 'POST'])
def delete_player():
    if request.method == 'POST':
        name = request.form.get('name')

        name_in_db = Player.query.filter_by(name=name).first()
        if name_in_db:
            db.session.delete(name_in_db)
            db.session.commit()
            flash('Player deleted!', category='success')
        else:
            flash('Name does not exist.', category='error')

    players = Player.query.all()
    return render_template("delete_player.html", players=players)


#####################################################################
# returning either the current_players list, or the start-page with modified teams


@views.route('/team-building', methods=['GET', 'POST'])
def team_building():
    if request.method == 'POST':
        name = request.form.get('myPlayer')
        print(name)
        name_in_db = Player.query.filter_by(name=name).first()
        if name_in_db:
            if name in current_players:  # should not happen I think?
                flash('Player already chosen.', category='error')
            else:
                current_players.append(name)
                # filter database ,without players from current_players
                players = Player.query.filter(Player.name.notin_(current_players))
                # flash('Player added to game!', category='success')
                return render_template("start.html", players=players, current_players=current_players)
        else:
            flash('Name does not exist.', category='error')

    if request.method == 'GET':
        # filter database ,without players from current_players
        players = Player.query.filter(Player.name.notin_(current_players)).with_entities(Player.name)
        players = [i[0] for i in players]
        return jsonify(players)

    print("we are here, weirdly")
    players = Player.query.all()
    return render_template("start.html", players=players, current_players=current_players)


#####################################################################


@views.route('/versus', methods=['GET', 'POST'])
def versus():
    global teamRed_current_match, teamBlue_current_match, fairness_counter, win_rate_teamRed, win_rate_teamBlue

    # TODO if this layout is used for multiple teams, change checks for min-teamsize
    if len(current_players) < 4:
        flash('At least four players needed', category='error')
        players = Player.query.filter(Player.name.notin_(current_players))
        return render_template("start.html", players=players, current_players=current_players)

    if len(current_players) > 12:  # TODO change this check when implementing multiple teams
        flash('No more than 12 players allowed', category='error')
        players = Player.query.filter(Player.name.notin_(current_players))
        return render_template("start.html", players=players, current_players=current_players)

    teams, win_rates = snd.make_teams(current_players, fairness_counter, 2)
    # print(teams)
    # print(fairness_counter)
    fairness_counter += 1
    teamRed_current_match = teams[0]
    teamBlue_current_match = teams[1]
    win_rate_teamRed = win_rates[0]  # TODO round after comma
    win_rate_teamBlue = win_rates[1]  # TODO round after comma
    return render_template("versus.html", teamRed=teamRed_current_match, teamBlue=teamBlue_current_match,
                           winrateRed=win_rate_teamRed, winrateBlue=win_rate_teamBlue)


####################################################################
# currently only used for in versus.html, when a winner is declared


@views.route('/update-stats', methods=['POST'])
def update_stats():
    if request.method == 'POST':

        winning_team = request.form.get('newWin')

        winners = []
        losers = []
        if winning_team == 'winRed':
            print("Red Team won, now updating")
            winners = teamRed_current_match
            losers = teamBlue_current_match
        elif winning_team == 'winBlue':
            print("Blue Team won, now updating")
            winners = teamBlue_current_match
            losers = teamRed_current_match
        else:
            flash("This functionality is not implemented!", category='error')
            return render_template("versus.html", teamRed=teamRed_current_match, teamBlue=teamBlue_current_match,
                                   winrateRed=win_rate_teamRed, winrateBlue=win_rate_teamBlue)

        for winner_name in winners:
            winner = Player.query.filter_by(name=winner_name).first()
            # this updates the values on DB-side (prevents race conditions)
            winner.played_matches = Player.played_matches + 1
            winner.won_matches = Player.won_matches + 1
        for loser_name in losers:
            loser = Player.query.filter_by(name=loser_name).first()
            loser.played_matches = Player.played_matches + 1
            loser.lost_matches = Player.lost_matches + 1
        db.session.commit()

        # TODO update win_rate here
        # TODO calculate not individual win-rate of team, but

        # we either have to re-render page here, or use fetch API
        return render_template("versus.html", teamRed=teamRed_current_match, teamBlue=teamBlue_current_match,
                               winrateRed=win_rate_teamRed, winrateBlue=win_rate_teamBlue)

#####################################################################
