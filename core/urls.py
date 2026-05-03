from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    # ROOT — index_view renders home.html for guests, redirects auth users to dashboard.
    # This is the ONLY handler for '/'. Nothing else touches this path.
    path('', views.index_view, name='home'),

    # Public info pages — render for everyone
    path('about/',         views.about_view,         name='about'),
    path('plan/',          views.plan_view,           name='plan'),
    path('faq/',           views.faq_view,            name='faq'),
    path('blog/',          views.blog_view,           name='blog'),
    path('certification/', views.certification_view,  name='certification'),
    path('contact/',       views.contact_view,        name='contact'),
]
