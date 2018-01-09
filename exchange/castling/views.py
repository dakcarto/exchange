

from django.shortcuts import render, render_to_response, redirect
from django.http import JsonResponse


def index(request):
    return render(request, 'castling/index.html', {
        'CASTLING_BUILD_DIR': '.',
    })


def config(request):
    config = {
        'access_token' : request.session['access_token'],
        'geoserver_url' : '/geoserver',
    }

    return JsonResponse(config);
