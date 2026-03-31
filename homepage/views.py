from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

def index(request):
    return render(request, 'homepage/index.html')


def register(request):
    if request.user.is_authenticated:
        return redirect("homepage_index")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("homepage_index")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})
