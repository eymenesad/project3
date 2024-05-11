from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UserForm
from django.contrib.auth.decorators import login_required, user_passes_test
import mysql.connector
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.db import IntegrityError, transaction

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
    # Your logic here, if any
    return render(request, 'login/jury_dashboard.html')
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
            except IntegrityError:
                return HttpResponse("Failed to add player to squad.")

            return HttpResponse("Player added to squad successfully.")
        if action == 'delete_session':
            session_id = request.POST.get('session_id')
        
            # Delete from SessionSquads first to maintain referential integrity
            cursor.execute("DELETE FROM SessionSquads WHERE session_ID = %s", [session_id])
            # Then delete the MatchSession
            cursor.execute("DELETE FROM MatchSession WHERE session_ID = %s", [session_id])
            return HttpResponse("Match session and associated squad data deleted successfully.")
        if action == 'add_session':
            team_id = request.POST.get('team_id')
            stadium_name = request.POST.get('stadium_name')
            stadium_country = request.POST.get('stadium_country')
            date = request.POST.get('date')
            time_slot = request.POST.get('time_slot')
            jury_name = request.POST.get('jury_name')
            jury_surname = request.POST.get('jury_surname')

        
            # Find jury username by name and surname
            cursor.execute("SELECT username FROM Jury WHERE name = %s AND surname = %s", [jury_name, jury_surname])
            jury_result = cursor.fetchone()
            if not jury_result:
                return HttpResponse("No such jury found.")
            jury_username = jury_result[0]

            try:
                with transaction.atomic():
                    cursor.execute("INSERT INTO MatchSession (team_ID, stadium_name, stadium_country, time_slot, date, assigned_jury_username, rating) VALUES (%s, %s, %s, %s, %s, %s, NULL)", 
                                    [team_id, stadium_name, stadium_country, time_slot, date, jury_username])
            except IntegrityError:
                return HttpResponse("Failed to add session due to a scheduling conflict or invalid data.")

            return HttpResponse("Match session added successfully.")
    
    return render(request, 'login/coach_dashboard.html')

    # GET request: render the coach dashboard template
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
            cursor.execute("UPDATE stadium SET name = %s WHERE name = %s", [new_name, old_name])
            return HttpResponse("Stadium name updated successfully.")
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')
            name = request.POST.get('name')
            surname = request.POST.get('surname')

        
            if form_type == 'player':
                date_of_birth = request.POST.get('date_of_birth')
                height = request.POST.get('height')
                weight = request.POST.get('weight')
                cursor.execute("INSERT INTO player (username, password, name, surname, date_of_birth, height, weight) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                [username, password, name, surname, date_of_birth, height, weight])

            elif form_type == 'coach':
                nationality = request.POST.get('nationality')
                cursor.execute("INSERT INTO coach (username, password, name, surname, nationality) VALUES (%s, %s, %s, %s, %s)",
                                [username, password, name, surname, nationality])

            elif form_type == 'jury':
                nationality = request.POST.get('nationality')
                cursor.execute("INSERT INTO jury (username, password, name, surname, nationality) VALUES (%s, %s, %s, %s, %s)",
                                [username, password, name, surname, nationality])

            return HttpResponse("User added successfully.")

    # GET request: render the manager dashboard template
    return render(request, 'login/manager_dashboard.html')