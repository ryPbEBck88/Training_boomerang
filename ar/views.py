from django.shortcuts import render


def index(request):
    return render(request, 'ar/index.html')


def ar_bets(request):
    return render(request, 'ar/ar_bets.html')
