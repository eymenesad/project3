from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UserForm
from django.contrib.auth.decorators import login_required, user_passes_test
import mysql.connector
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.db import IntegrityError, transaction
from datetime import datetime
from django.contrib import messages

mydb = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  password="abcd1234",
  database="volleydb"
)

#Command needed to modify/access inside database(s)
cursor = mydb.cursor()


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        
       
        # Check if user is a Player
        cursor.execute("SELECT * FROM player WHERE username = %s AND password = %s", [username, password])
        if cursor.fetchone():
            request.session['username'] = username
            return HttpResponseRedirect('/player_dashboard/')

        # Check if user is a Coach
        cursor.execute("SELECT * FROM coach WHERE username = %s AND password = %s", [username, password])
        if cursor.fetchone():
            request.session['username'] = username
            return HttpResponseRedirect('/coach_dashboard/')

        # Check if user is a Jury
        cursor.execute("SELECT * FROM jury WHERE username = %s AND password = %s", [username, password])
        if cursor.fetchone():
            request.session['username'] = username
            return HttpResponseRedirect('/jury_dashboard/')
        
        cursor.execute("SELECT * FROM manager WHERE username = %s AND password = %s", [username, password])
        if cursor.fetchone():
            request.session['username'] = username
            return HttpResponseRedirect('/manager_dashboard/')
        return render(request, 'login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'login/index.html')

def dashboard_view(request):
    return render(request, 'login/dashboard.html', {'user': request.user})


def jury_dashboard_view(request):

    jury_username = request.session.get('username')


    # Query to find average rating and count of rated sessions
    cursor.execute("""
        SELECT AVG(rating) as average_rating, COUNT(*) as total_sessions
        FROM MatchSession
        WHERE assigned_jury_username = %s AND rating IS NOT NULL
    """, [jury_username])
    result = cursor.fetchone()

    average_rating = result[0] if result[0] is not None else "No ratings yet"
    total_sessions = result[1]

    # Passing the results to the template
    return render(request, 'jury_dashboard.html', {
        'average_rating': average_rating,
        'total_sessions': total_sessions
    })

def coach_dashboard_view(request):
    

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_squad':
            session_id = request.POST.get('session_id')
            player_username = request.POST.get('player_username')
            position_id = request.POST.get('position_id')

            # Get the coach's username from the session or another source
            coach_username = request.session.get('username')
            
            
            # Check if the player is in the coach's team
            cursor.execute("""
                SELECT COUNT(*)
                FROM PlayerTeams PT
                JOIN Team T ON PT.team = T.team_ID
                WHERE PT.username = %s AND T.coach_username = %s
            """, [player_username, coach_username])
            player_count = cursor.fetchone()[0]

            if player_count == 0:
                return HttpResponse("Player is not in your team.")

            try:
                with transaction.atomic():
                    cursor.execute("""
                        INSERT INTO SessionSquads (session_ID, played_player_username, position_ID)
                        VALUES (%s, %s, %s)
                    """, [session_id, player_username, position_id])
                    mydb.commit()
            except IntegrityError:
                return HttpResponse("Failed to add player to squad.")

            return HttpResponse("Player added to squad successfully.")
        if action == 'delete_session':
            session_id = request.POST.get('session_id')

            # Delete from SessionSquads first to maintain referential integrity
            cursor.execute("DELETE FROM SessionSquads WHERE session_ID = %s", [session_id])
            mydb.commit()
            # Then delete the MatchSession
            cursor.execute("DELETE FROM MatchSession WHERE session_ID = %s", [session_id])
            mydb.commit()
            return HttpResponse("Match session and associated squad data deleted successfully.")
        if action == 'add_session':
            stadium_name = request.POST.get('stadium_name')
            date = request.POST.get('date')
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            date = formatted_date
            time_slot = request.POST.get('time_slot')
            jury_name = request.POST.get('jury_name')
            jury_surname = request.POST.get('jury_surname')

        
            # Find jury username by name and surname
            cursor.execute("SELECT username FROM Jury WHERE name = %s AND surname = %s", [jury_name, jury_surname])
            jury_result = cursor.fetchone()
            if not jury_result:
                return HttpResponse("No such jury found.")
            jury_username = jury_result[0]

            # Find stadium ID by stadium name
            cursor.execute("SELECT stadium_ID FROM Stadium WHERE stadium_name = %s", [stadium_name])
            stadium_result = cursor.fetchone()
            if not stadium_result:
                return HttpResponse("No such stadium found.")
            stadium_ID = stadium_result[0]

            # Get the coach's username from the session or another source
            coach_username = request.session.get('username')

            # Retrieve the current team ID for the coach
            cursor.execute("SELECT team_ID FROM CoachTeam WHERE coach_username = %s", [coach_username])
            team_result = cursor.fetchone()
            if team_result:
                team_ID = team_result[0]
            else:
                return HttpResponse("No team found for the coach.")
            
            

            # Retrieve the last session ID from MatchSession
            cursor.execute("SELECT MAX(session_ID) FROM MatchSession")
            last_session_id_result = cursor.fetchone()
            new_session_id = last_session_id_result[0] + 1 if last_session_id_result[0] is not None else 1

            try:
                with transaction.atomic():
                    cursor.execute("INSERT INTO MatchSession (session_ID, team_ID, stadium_ID, time_slot, date, assigned_jury_username, rating) VALUES (%s, %s, %s, %s, %s, %s, NULL)", 
                                    [new_session_id, team_ID, stadium_ID, time_slot, date, jury_username])
                    mydb.commit()

            except IntegrityError:
                return HttpResponse("Failed to add session due to a scheduling conflict or invalid data.")

            return HttpResponse("Match session added successfully.")
    else:
        query = """
        SELECT stadium_name, stadium_country 
        FROM Stadium
        ORDER BY stadium_name;
    """
    
        cursor.execute(query)
        stadiums = cursor.fetchall()
        stadiums_list = [{'name': stadium[0], 'country': stadium[1]} for stadium in stadiums]
        return render(request, 'login/coach_dashboard.html', {'stadiums_list': stadiums_list})
    return render(request, 'login/coach_dashboard.html')
def player_dashboard_view(request):
    # Your logic here, if any
    return render(request, 'login/player_dashboard.html')
def manager_dashboard_view(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'update_stadium':
            old_name = request.POST.get('old_name')
            new_name = request.POST.get('new_name')
            cursor.execute("UPDATE stadium SET stadium_name = %s WHERE stadium_name = %s", [new_name, old_name])
            mydb.commit()
            return HttpResponse("Stadium name updated successfully.")
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')
            name = request.POST.get('name')
            surname = request.POST.get('surname')

        
            if form_type == 'player':
                date_of_birth = request.POST.get('date_of_birth')
                formatted_date = datetime.strptime(date_of_birth, "%Y-%m-%d").strftime("%d/%m/%Y")
                date_of_birth = formatted_date
                height = request.POST.get('height')
                weight = request.POST.get('weight')
                cursor.execute("INSERT INTO player (username, password, name, surname, date_of_birth, height, weight) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                [username, password, name, surname, date_of_birth, height, weight])
                mydb.commit()

            elif form_type == 'coach':
                nationality = request.POST.get('nationality')
                cursor.execute("INSERT INTO coach (username, password, name, surname, nationality) VALUES (%s, %s, %s, %s, %s)",
                                [username, password, name, surname, nationality])
                mydb.commit()

            elif form_type == 'jury':
                nationality = request.POST.get('nationality')
                cursor.execute("INSERT INTO jury (username, password, name, surname, nationality) VALUES (%s, %s, %s, %s, %s)",
                                [username, password, name, surname, nationality])
                mydb.commit()

            return HttpResponse("User added successfully.")

    # GET request: render the manager dashboard template
    return render(request, 'login/manager_dashboard.html')