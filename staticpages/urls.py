from staticpages import views
from django.urls import path

urlpatterns = [
    path('about-us/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('newsevents/', views.newsevents, name='newsevents'),

    # BLOGS
    path('commite-team', views.commitie, name='commitie'),
    path('blog/gallery', views.gallery, name='gallery'),
    path('blog/vgallery', views.vgallery, name='vgallery'),
    path('privacy-policy', views.pp, name='privacy_policy'),
    path('terms-and-conditions', views.tc, name='terms_conditions'),
    
    # Individual Blog Posts
    path('blog/ispl-player-revealed/', views.b1, name='ispl_player_revealed'),
    path('blog/own-a-tspl-franchise-team/', views.b2, name='own_tspl_franchise'),
    path('blog/tennies-ball-cricket/', views.b3, name='tennies_ball_cricket'),
    path('blog/tspl-t10-action/', views.b4, name='tspl_t10_action'),
    path('blog/who-can-register/', views.b5, name='who_can_register'),

    # Extras
    path("points/table.view",views.points_table,name="points_table"),

]

# SEO
urlpatterns+=[
    path("robots.txt",views.robot),
    path("sitemap.xml",views.sitemap,name='sitemap'),
]