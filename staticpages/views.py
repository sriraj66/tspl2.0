from django.shortcuts import render,HttpResponse
from django.template.loader import get_template
from core.utils import get_general_settings

def about(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/about.html", context)


def contact(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/contactus.html",context)


def newsevents(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/newsevents.html",context)

# BLOGS

def commitie(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/blog/commitie.html",context)


def gallery(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/blog/imagegallery.html",context)

def vgallery(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/blog/videogallery.html",context)

def pp(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/blog/privacy-policy.html",context)

def tc(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/blog/tearms-and-condition.html",context)


def b1(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/blog/ispl-player-revealed.html",context)

def b2(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/blog/own-a-tspl-franchise-team.html",context)

def b3(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/blog/tennies-ball-cricket.html",context)

def b4(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/blog/tspl-t10-action.html",context)

def b5(request):
    settings = get_general_settings()
    context = {
        'settings': settings,
    }
    return render(request,"staticPages/blog/who-can-register.html",context)


def points_table(request):
    settings = get_general_settings()
    if not settings.show_points_table:
        return HttpResponse("Now Allowed", status=403)
    context = {
        'settings': settings,
    }
    return render(request,'staticPages/pointstable.html', context)

# SEO
def robot(request):
    template = get_template('robots.txt')
    robots_content = template.render()
    
    return HttpResponse(robots_content, content_type="text/plain")

def sitemap(request):
    template = get_template('sitemap.xml')
    sitemap_content = template.render()
    return HttpResponse(sitemap_content, content_type="application/xml")

