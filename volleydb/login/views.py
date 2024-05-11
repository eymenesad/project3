from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UserForm
from django.contrib.auth.decorators import login_required, user_passes_test
import mysql.connector
from django.http import HttpResponseRedirect
from django.shortcuts import render

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
        
        if action == 'delete_session':
            session_id = request.POST.get('session_id')
            
        
            # Begin a transaction
            cursor.execute("BEGIN;")
            try:
                # Delete related data in squad info
                cursor.execute("DELETE FROM squad_info WHERE session_id = %s", [session_id])
                
                # Delete the match session
                cursor.execute("DELETE FROM match_sessions WHERE session_id = %s", [session_id])
                
                # Commit transaction
                cursor.execute("COMMIT;")
                return HttpResponse("Match session deleted successfully.")
            
            except Exception as e:
                # Rollback in case of error
                cursor.execute("ROLLBACK;")
                return HttpResponse(f"Error deleting session: {str(e)}")

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