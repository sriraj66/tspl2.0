from django.shortcuts import render,HttpResponse
from django.template.loader import get_template

def about(request):
    return render(request,"staticPages/about.html")


def contact(request):
    return render(request,"staticPages/contactus.html")


def newsevents(request):
    return render(request,"staticPages/newsevents.html")

# BLOGS

def commitie(request):
    return render(request,"staticPages/blog/commitie.html")


def gallery(request):
    return render(request,"staticPages/blog/imagegallery.html")

def vgallery(request):
    return render(request,"staticPages/blog/videogallery.html")

def pp(request):
    return render(request,"staticPages/blog/privacy-policy.html")

def tc(request):
    return render(request,"staticPages/blog/tearms-and-condition.html")


def b1(request):
    return render(request,"staticPages/blog/ispl-player-revealed.html")

def b2(request):
    return render(request,"staticPages/blog/own-a-tspl-franchise-team.html")

def b3(request):
    return render(request,"staticPages/blog/tennies-ball-cricket.html")

def b4(request):
    return render(request,"staticPages/blog/tspl-t10-action.html")

def b5(request):
    return render(request,"staticPages/blog/who-can-register.html")


def points_table(request):
    return render(request,'staticPages/pointstable.html')

# SEO
def robot(request):
    template = get_template('robots.txt')
    robots_content = template.render()
    
    return HttpResponse(robots_content, content_type="text/plain")

def sitemap(request):
    template = get_template('sitemap.xml')
    sitemap_content = template.render()
    return HttpResponse(sitemap_content, content_type="application/xml")

