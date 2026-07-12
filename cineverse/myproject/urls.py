from django.urls import path
from . import views

urlpatterns = [
    # Client views
    path('', views.home, name='home'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('movie/<int:movie_id>/review/', views.add_review, name='add_review'),
    path('showtime/<int:showtime_id>/book/', views.book_seats, name='book_seats'),
    path('booking/<str:booking_id>/confirm/', views.ticket_confirmation, name='ticket_confirmation'),
    path('booking/<str:booking_id>/pdf/', views.download_ticket_pdf, name='download_ticket_pdf'),
    
    # Session Features (Wishlist & AJAX)
    path('wishlist/', views.wishlist_view, name='wishlist_view'),
    path('wishlist/toggle/<int:movie_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('ajax-search/', views.ajax_search, name='ajax_search'),
    
    # Auth & History
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Admin Custom Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/movies/', views.admin_movies, name='admin_movies'),
    path('admin-dashboard/showtimes/', views.admin_showtimes, name='admin_showtimes'),
    path('admin-dashboard/bookings/', views.admin_bookings, name='admin_bookings'),
    path('admin-dashboard/reviews/', views.admin_reviews, name='admin_reviews'),
]
