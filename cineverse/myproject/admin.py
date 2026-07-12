from django.contrib import admin
from .models import Genre, Movie, Showtime, Booking, Review

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'runtime', 'release_date', 'is_currently_playing', 'is_coming_soon')
    list_filter = ('is_currently_playing', 'is_coming_soon', 'is_trending', 'is_top_rated', 'language')
    search_fields = ('title', 'director', 'cast')

@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ('movie', 'date', 'time', 'screen', 'price')
    list_filter = ('date', 'screen', 'movie')
    ordering = ('date', 'time')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer_name', 'customer_email', 'showtime', 'seats', 'total_price', 'created_at')
    search_fields = ('booking_id', 'customer_name', 'customer_email', 'customer_phone', 'seats')
    list_filter = ('showtime__date', 'showtime__movie')
    readonly_fields = ('booking_id', 'created_at')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('movie', 'customer_name', 'rating', 'created_at')
    list_filter = ('rating', 'movie')
    search_fields = ('customer_name', 'comment')
