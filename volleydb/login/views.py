from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import CustomUserLoginForm
from django.http import HttpResponse

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to the dashboard
        else:
            return HttpResponse('Invalid login credentials')
    return render(request, 'login/index.html')

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'login/dashboard.html', {'user': request.user})