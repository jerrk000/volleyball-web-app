from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Player
from . import db
from .utils import slice_n_dice as snd
import json

views = Blueprint('views', __name__)

current_players = []

teamRed_current_match = []

teamBlue_current_match = []

#####################################################################
# First page of website


@views.route('/', methods=['GET', 'POST'])
def start():
    current_players.clear()
    teamRed_current_match.clear()
    teamBlue_current_match.clear()
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
                #filter database ,without players from current_players
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
    # TODO if this layout is used for multiple teams, change checks for min-teamsize
    if len(current_players) < 4:
        flash('At least four players needed', category='error')
        players = Player.query.filter(Player.name.notin_(current_players))
        return render_template("start.html", players=players, current_players=current_players)

    if len(current_players) > 12: # TODO change this check when implementing multiple teams
        flash('No more than 12 players allowed', category='error')
        players = Player.query.filter(Player.name.notin_(current_players))
        return render_template("start.html", players=players, current_players=current_players)

    global teamRed_current_match, teamBlue_current_match
    teamRed_current_match, teamBlue_current_match = snd.make_teams(current_players, 0, 2)

    return render_template("versus.html", teamRed=teamRed_current_match, teamBlue=teamBlue_current_match)


####################################################################
# currently only used for in versus.html, when a winner is declared


@views.route('/update-stats', methods=['POST'])
def update_stats():
    winning_team = request.form.get('newWin')

    if winning_team == 'winRed':
        print("Red Team won, now updating")
    elif winning_team == 'winBlue':
        print("Blue Team won, now updating")
    else:
        flash("This functionality is not implemented!", category='error')

    # we either have to re-render page here, or use fetch API
    return render_template("versus.html", teamRed=teamRed_current_match, teamBlue=teamBlue_current_match)


#####################################################################
