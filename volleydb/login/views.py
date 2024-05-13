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
from django.db import connection

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


    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'rate_session':
            date = request.POST.get('date')
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            date = formatted_date
            input_date = '2024-05-12'
            time_slot = request.POST.get('time_slot')
            stadium_name = request.POST.get('stadium_name')
            rating = request.POST.get('rating')  # Getting the rating from the user input

            # Find stadium ID by stadium name
            cursor.execute("SELECT stadium_ID FROM Stadium WHERE stadium_name = %s", [stadium_name])
            stadium_result = cursor.fetchone()
            if not stadium_result:
                return HttpResponse("No such stadium found.")
            stadium_ID = stadium_result[0]

            query = """
                SELECT ms.session_ID, ms.team_ID, ms.date, ms.time_slot, ms.stadium_ID
                FROM MatchSession ms
                WHERE ms.assigned_jury_username = %s
                AND ms.rating IS NULL
                AND ms.date < %s
                AND ms.date = %s
                AND ms.time_slot = %s
                AND ms.stadium_ID = %s
            """

            params = [jury_username, input_date, date, time_slot, stadium_ID]


            cursor.execute(query, params)
            session = cursor.fetchone()

            # Check if a session is returned
            if session:
                session_id = session[0]  # Assuming session_ID is the first column returned

                # SQL query to update the rating
                update_query = """
                    UPDATE MatchSession
                    SET rating = %s
                    WHERE session_ID = %s
                """

                # Execute the update
                cursor.execute(update_query, [rating, session_id])
                mydb.commit()  # Make sure to commit the transaction if you're not using Django's atomic block

                return HttpResponse("Session " + str(session_id) + " successfully rated with rating " + str(rating))
            else:
                # No session matches the criteria or it cannot be rated
                return HttpResponse("No valid session found or it cannot be rated yet.")
    else:
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
        return render(request, 'login/jury_dashboard.html', {
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
    username = request.session.get('username')
    with connection.cursor() as cursor:
        # Fetch players played with in shared sessions
        cursor.execute("""
            SELECT DISTINCT p.username, p.name, p.surname
            FROM Player p
            JOIN SessionSquads ss ON p.username = ss.played_player_username
            JOIN SessionSquads ss2 ON ss.session_id = ss2.session_id
            WHERE ss2.played_player_username = %s AND p.username != %s
        """, [username, username])
        players = cursor.fetchall()

        # Fetch session IDs where the current player has participated
        cursor.execute("""
            SELECT session_id
            FROM SessionSquads
            WHERE played_player_username = %s
        """, [username])
        session_ids = [item[0] for item in cursor.fetchall()]

        # Prepare for IN clause dynamically
        placeholders = ','.join(['%s'] * len(session_ids))  # Create placeholders for the tuple

        # Fetch the most frequently played with players
        if session_ids:
            cursor.execute(f"""
                SELECT p.username, p.name, p.surname, COUNT(*) as count
                FROM SessionSquads ss
                JOIN Player p ON p.username = ss.played_player_username
                WHERE ss.session_id IN ({placeholders}) AND ss.played_player_username != %s
                GROUP BY ss.played_player_username
                ORDER BY count DESC
            """, session_ids + [username])
            most_played_with = cursor.fetchall()

            # Identify the highest frequency count to find the most played with
            highest_count = most_played_with[0][3] if most_played_with else 0
            most_frequent_users = [player[:3] for player in most_played_with if player[3] == highest_count]

            # Compute the average height of the most frequently played with players
            if most_frequent_users:
                user_placeholders = ','.join(['%s'] * len(most_frequent_users))
                cursor.execute(f"""
                    SELECT AVG(height)
                    FROM Player
                    WHERE username IN ({user_placeholders})
                """, [user[0] for user in most_frequent_users])
                most_played_with_height = cursor.fetchone()[0]
            else:
                most_played_with_height = None
        else:
            most_played_with_height = None
            most_frequent_users = []

        context = {
            'players': [{'username': player[0], 'name': player[1], 'surname': player[2]} for player in players],
            'most_played_with': [{'username': player[0], 'name': player[1], 'surname': player[2]} for player in most_frequent_users],
            'most_played_with_height': most_played_with_height
        }

    return render(request, 'login/player_dashboard.html', context)

def manager_dashboard_view(request):
    cursor.execute("SELECT stadium_name FROM Stadium")
    stadiums = cursor.fetchall()
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
    return render(request, 'login/manager_dashboard.html', {'stadiums': stadiums})