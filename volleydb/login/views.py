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
  password="Ememno96.",
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

        # Assuming Manager has a separate table or logic
        # Add your Manager check here

        return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login/index.html')

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'login/dashboard.html', {'user': request.user})