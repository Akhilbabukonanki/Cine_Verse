import random
import string
from django.db import models
from django.contrib.auth.models import User

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=200)
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    genres = models.ManyToManyField(Genre, related_name='movies')
    runtime = models.PositiveIntegerField(help_text="Runtime in minutes")
    language = models.CharField(max_length=50)
    release_date = models.DateField()
    synopsis = models.TextField()
    cast = models.TextField(help_text="Comma-separated cast members")
    director = models.CharField(max_length=100)
    trailer_url = models.URLField(blank=True, null=True, help_text="YouTube URL, e.g. https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    is_currently_playing = models.BooleanField(default=True)
    is_coming_soon = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_top_rated = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0.0

    @property
    def review_count(self):
        return self.reviews.count()

    def get_youtube_id(self):
        """Extract YouTube ID from various YouTube URL patterns."""
        if not self.trailer_url:
            return ""
        url = self.trailer_url
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        if "youtube.com/embed/" in url:
            return url.split("youtube.com/embed/")[1].split("?")[0]
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        return ""

class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='showtimes')
    date = models.DateField()
    time = models.TimeField()
    screen = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=12.00)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.movie.title} - {self.date} at {self.time.strftime('%I:%M %p')} (Screen {self.screen})"

class Booking(models.Model):
    booking_id = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, related_name='bookings')
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField()
    seats = models.CharField(max_length=200, help_text="Comma-separated seat codes, e.g. A3,A4")
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.booking_id} - {self.customer_name} ({self.showtime.movie.title})"

    def save(self, *args, **kwargs):
        if not self.booking_id:
            while True:
                # Generate unique booking ID (MV + 6 random digits)
                bid = 'MV' + ''.join(random.choices(string.digits, k=6))
                if not Booking.objects.filter(booking_id=bid).exists():
                    self.booking_id = bid
                    break
        super().save(*args, **kwargs)

    @property
    def seat_list(self):
        return [s.strip() for s in self.seats.split(',') if s.strip()]

class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    customer_name = models.CharField(max_length=100)
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer_name}'s review on {self.movie.title} ({self.rating} stars)"
