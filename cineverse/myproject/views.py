import io
import base64
import qrcode
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse, Http404
from django.db.models import Sum, Count
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

from .models import Genre, Movie, Showtime, Booking, Review

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_staff

# Helper function to generate QR Code Base64
def get_qr_base64(data):
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Helper function to send confirmation email
def send_booking_email(booking):
    try:
        subject = f"CineVerse Booking Confirmed: {booking.booking_id}"
        html_message = render_to_string('emails/booking_confirmation.html', {'booking': booking})
        
        # Generate ticket PDF bytes dynamically
        pdf_buffer = io.BytesIO()
        p = canvas.Canvas(pdf_buffer, pagesize=(400, 600))
        
        # Draw ticket card styling
        p.setFillColor(colors.HexColor('#0b0f19'))
        p.rect(0, 0, 400, 600, fill=True, stroke=False)
        p.setStrokeColor(colors.HexColor('#1e293b'))
        p.setLineWidth(2)
        p.rect(15, 15, 370, 570, fill=False, stroke=True)
        
        p.setFillColor(colors.HexColor('#f43f5e'))
        p.rect(15, 510, 370, 75, fill=True, stroke=False)
        
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(200, 545, "CineVerse")
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(200, 525, "BOOKING CONFIRMED")
        
        p.setFillColor(colors.HexColor('#94a3b8'))
        p.setFont("Helvetica", 10)
        p.drawCentredString(200, 480, "MOVIE")
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(200, 455, booking.showtime.movie.title)
        
        p.setStrokeColor(colors.HexColor('#1e293b'))
        p.line(30, 430, 370, 430)
        
        p.setFillColor(colors.HexColor('#94a3b8'))
        p.setFont("Helvetica", 9)
        p.drawString(45, 410, "SCREEN")
        p.drawString(170, 410, "DATE")
        p.drawString(290, 410, "TIME")
        
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(45, 390, str(booking.showtime.screen))
        p.drawString(170, 390, booking.showtime.date.strftime("%d %B"))
        p.drawString(290, 390, booking.showtime.time.strftime("%I:%M %p"))
        
        p.line(30, 370, 370, 370)
        
        p.setFillColor(colors.HexColor('#94a3b8'))
        p.setFont("Helvetica", 10)
        p.drawString(45, 335, "SEATS")
        p.setFillColor(colors.HexColor('#38bdf8'))
        p.setFont("Helvetica-Bold", 14)
        p.drawString(45, 315, booking.seats.replace(',', ' '))
        
        p.setFillColor(colors.HexColor('#94a3b8'))
        p.setFont("Helvetica", 10)
        p.drawString(45, 275, "BOOKING ID")
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(45, 255, booking.booking_id)
        
        p.setFillColor(colors.HexColor('#94a3b8'))
        p.setFont("Helvetica", 10)
        p.drawString(45, 215, "AMOUNT PAID")
        p.setFillColor(colors.HexColor('#f43f5e'))
        p.setFont("Helvetica-Bold", 14)
        p.drawString(45, 195, f"${booking.total_price}")
        
        # QR Code Drawing in PDF
        qr = qrcode.QRCode(version=1, box_size=5, border=1)
        qr.add_data(booking.booking_id)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_bytes = io.BytesIO()
        qr_img.save(qr_bytes, format="PNG")
        qr_bytes.seek(0)
        p.drawImage(ImageReader(qr_bytes), 230, 185, width=120, height=120)
        
        p.setLineWidth(1)
        p.setStrokeColor(colors.HexColor('#475569'))
        p.setDash(4, 4)
        p.line(30, 140, 370, 140)
        p.setDash(1, 0)
        
        p.setFillColor(colors.HexColor('#94a3b8'))
        p.setFont("Helvetica", 9)
        p.drawCentredString(200, 100, "Show this PDF at the ticket counter.")
        p.showPage()
        p.save()
        
        # Email setup
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.customer_email]
        )
        email.content_subtype = 'html'
        email.attach(f"CineVerse_Ticket_{booking.booking_id}.pdf", pdf_buffer.getvalue(), "application/pdf")
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Error sending email: {e}")

# -------------------------------------------------------------
# CLIENT FRONTEND VIEWS
# -------------------------------------------------------------

def home(request):
    active_genre = request.GET.get('genre', 'all')
    active_category = request.GET.get('category', 'all')
    active_query = request.GET.get('q', '')

    movies = Movie.objects.all()

    # Search Filter
    if active_query:
        movies = movies.filter(title__icontains=active_query)

    # Genre Filter
    if active_genre and active_genre != 'all':
        movies = movies.filter(genres__name=active_genre)

    # Category Filters
    if active_category == 'currently_playing':
        movies = movies.filter(is_currently_playing=True)
    elif active_category == 'coming_soon':
        movies = movies.filter(is_coming_soon=True)
    elif active_category == 'trending':
        movies = movies.filter(is_trending=True)
    elif active_category == 'top_rated':
        movies = movies.filter(is_top_rated=True)

    # Fetch recently viewed movies
    recently_viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed_movies = []
    if recently_viewed_ids:
        # Keep sequence using preservation list mapping
        db_movies = {m.id: m for m in Movie.objects.filter(id__in=recently_viewed_ids)}
        recently_viewed_movies = [db_movies[mid] for mid in recently_viewed_ids if mid in db_movies]

    context = {
        'movies': movies,
        'genres': Genre.objects.all(),
        'banner_movies': Movie.objects.filter(is_trending=True)[:5],
        'recently_viewed_movies': recently_viewed_movies,
        'wishlist_session': [str(x) for x in request.session.get('wishlist', [])],
        'active_genre': active_genre,
        'active_category': active_category,
        'active_query': active_query,
    }
    return render(request, 'home.html', context)

def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    # Track recently viewed
    recently_viewed = request.session.get('recently_viewed', [])
    if movie.id in recently_viewed:
        recently_viewed.remove(movie.id)
    recently_viewed.insert(0, movie.id)
    request.session['recently_viewed'] = recently_viewed[:6]
    request.session.modified = True

    # Showtime selection
    today = date.today()
    tomorrow = today + timedelta(days=1)

    context = {
        'movie': movie,
        'today_showtimes': Showtime.objects.filter(movie=movie, date=today),
        'tomorrow_showtimes': Showtime.objects.filter(movie=movie, date=tomorrow),
        'wishlist_session': [str(x) for x in request.session.get('wishlist', [])],
    }
    return render(request, 'movie_detail.html', context)

def add_review(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        rating = int(request.POST.get('rating', '5'))
        comment = request.POST.get('comment', '').strip()

        if not customer_name or not comment:
            messages.error(request, "Name and comment fields cannot be empty!")
            return redirect('movie_detail', movie_id=movie.id)

        review = Review(
            movie=movie,
            customer_name=customer_name,
            rating=rating,
            comment=comment
        )
        if request.user.is_authenticated:
            review.user = request.user
        
        review.save()
        messages.success(request, "Review submitted successfully!")
    return redirect('movie_detail', movie_id=movie.id)

def book_seats(request, showtime_id):
    showtime = get_object_or_404(Showtime, id=showtime_id)
    
    # Calculate booked seats
    bookings = Booking.objects.filter(showtime=showtime)
    booked_seats_set = set()
    for b in bookings:
        booked_seats_set.update(b.seat_list)

    if request.method == 'POST':
        seats_str = request.POST.get('seats', '').strip()
        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        total_price = request.POST.get('total_price', '').strip()

        selected_seats = [s.strip() for s in seats_str.split(',') if s.strip()]

        if not selected_seats:
            messages.error(request, "Please select at least one seat!")
            return redirect('book_seats', showtime_id=showtime.id)

        # Seat booking overlap checker
        if any(seat in booked_seats_set for seat in selected_seats):
            messages.error(request, "One or more selected seats were already booked. Please choose different seats!")
            return redirect('book_seats', showtime_id=showtime.id)

        booking = Booking(
            showtime=showtime,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            seats=seats_str,
            total_price=total_price
        )
        if request.user.is_authenticated:
            booking.user = request.user
        
        booking.save()
        
        # Async confirmation email
        send_booking_email(booking)

        return redirect('ticket_confirmation', booking_id=booking.booking_id)

    # Build seat rows A to E, columns 1 to 8
    rows = ['A', 'B', 'C', 'D', 'E']
    seat_rows = []
    for r in rows:
        row_seats = []
        for c in range(1, 9):
            code = f"{r}{c}"
            row_seats.append({
                'code': code,
                'number': c,
                'is_booked': code in booked_seats_set
            })
        seat_rows.append({
            'label': r,
            'seats': row_seats
        })

    context = {
        'showtime': showtime,
        'seat_rows': seat_rows,
    }
    return render(request, 'seat_booking.html', context)

def ticket_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    seats_space_separated = booking.seats.replace(',', ' ')
    
    # Generate on-the-fly QR code
    qr_base64 = get_qr_base64(booking.booking_id)

    context = {
        'booking': booking,
        'seats_space_separated': seats_space_separated,
        'qr_base64': qr_base64,
    }
    return render(request, 'ticket_confirmation.html', context)

def download_ticket_pdf(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CineVerse_Ticket_{booking_id}.pdf"'
    
    p = canvas.Canvas(response, pagesize=(400, 600))
    
    # Draw ticket design onto the canvas
    p.setFillColor(colors.HexColor('#0b0f19'))
    p.rect(0, 0, 400, 600, fill=True, stroke=False)
    
    p.setStrokeColor(colors.HexColor('#1e293b'))
    p.setLineWidth(2)
    p.rect(15, 15, 370, 570, fill=False, stroke=True)
    
    p.setFillColor(colors.HexColor('#f43f5e'))
    p.rect(15, 510, 370, 75, fill=True, stroke=False)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(200, 545, "CineVerse")
    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(200, 525, "BOOKING CONFIRMED")
    
    p.setFillColor(colors.HexColor('#94a3b8'))
    p.setFont("Helvetica", 10)
    p.drawCentredString(200, 480, "MOVIE")
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(200, 455, booking.showtime.movie.title)
    
    p.setStrokeColor(colors.HexColor('#1e293b'))
    p.line(30, 430, 370, 430)
    
    p.setFillColor(colors.HexColor('#94a3b8'))
    p.setFont("Helvetica", 9)
    p.drawString(45, 410, "SCREEN")
    p.drawString(170, 410, "DATE")
    p.drawString(290, 410, "TIME")
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(45, 390, str(booking.showtime.screen))
    p.drawString(170, 390, booking.showtime.date.strftime("%d %B"))
    p.drawString(290, 390, booking.showtime.time.strftime("%I:%M %p"))
    
    p.line(30, 370, 370, 370)
    
    p.setFillColor(colors.HexColor('#94a3b8'))
    p.setFont("Helvetica", 10)
    p.drawString(45, 335, "SEATS")
    p.setFillColor(colors.HexColor('#38bdf8'))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(45, 315, booking.seats.replace(',', ' '))
    
    p.setFillColor(colors.HexColor('#94a3b8'))
    p.setFont("Helvetica", 10)
    p.drawString(45, 275, "BOOKING ID")
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(45, 255, booking.booking_id)
    
    p.setFillColor(colors.HexColor('#94a3b8'))
    p.setFont("Helvetica", 10)
    p.drawString(45, 215, "AMOUNT PAID")
    p.setFillColor(colors.HexColor('#f43f5e'))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(45, 195, f"${booking.total_price}")
    
    # Generate QR Code image for ReportLab PDF
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(booking.booking_id)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_bytes = io.BytesIO()
    qr_img.save(qr_bytes, format="PNG")
    qr_bytes.seek(0)
    
    p.drawImage(ImageReader(qr_bytes), 230, 185, width=120, height=120)
    p.setFillColor(colors.HexColor('#94a3b8'))
    p.setFont("Helvetica", 7)
    p.drawCentredString(290, 175, "Scan at Entrance")
    
    p.setLineWidth(1)
    p.setStrokeColor(colors.HexColor('#475569'))
    p.setDash(4, 4)
    p.line(30, 140, 370, 140)
    p.setDash(1, 0)
    
    p.setFillColor(colors.HexColor('#94a3b8'))
    p.setFont("Helvetica", 9)
    p.drawCentredString(200, 100, "Show this PDF at the ticket counter.")
    p.drawCentredString(200, 85, "No cancellations or modifications allowed.")
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(200, 45, "THANK YOU FOR CHOOSING CINEVERSE!")
    
    p.showPage()
    p.save()
    return response

# -------------------------------------------------------------
# SESSION FEATURES ENDPOINTS
# -------------------------------------------------------------

@csrf_exempt
def toggle_wishlist(request, movie_id):
    if request.method == 'POST':
        wishlist = request.session.get('wishlist', [])
        if movie_id in wishlist:
            wishlist.remove(movie_id)
            status = 'removed'
        else:
            wishlist.append(movie_id)
            status = 'added'
        request.session['wishlist'] = wishlist
        request.session.modified = True
        return JsonResponse({'status': status})
    return JsonResponse({'error': 'POST required'}, status=400)

def wishlist_view(request):
    wishlist_ids = request.session.get('wishlist', [])
    wishlist_movies = Movie.objects.filter(id__in=wishlist_ids)
    context = {
        'wishlist_movies': wishlist_movies,
    }
    return render(request, 'wishlist.html', context)

def ajax_search(request):
    query = request.GET.get('q', '')
    results = []
    if len(query) >= 2:
        movies = Movie.objects.filter(title__icontains=query)[:5]
        for m in movies:
            results.append({
                'id': m.id,
                'title': m.title,
                'genres': ", ".join([g.name for g in m.genres.all()]),
                'language': m.language,
                'poster_url': m.poster.url if m.poster else ''
            })
    return JsonResponse({'results': results})

# -------------------------------------------------------------
# AUTH & HISTORY VIEWS
# -------------------------------------------------------------

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'bookings': bookings,
    }
    return render(request, 'my_bookings.html', context)

def login_view(request):
    if request.method == 'POST':
        username_str = request.POST.get('username')
        password_str = request.POST.get('password')
        user = authenticate(request, username=username_str, password=password_str)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next', 'home')
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password!")
    return render(request, 'login.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "Logged out successfully!")
    return redirect('home')

def register_view(request):
    if request.method == 'POST':
        username_str = request.POST.get('username')
        email_str = request.POST.get('email')
        password_str = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if User.objects.filter(username=username_str).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')
        if User.objects.filter(email=email_str).exists():
            messages.error(request, "Email already registered!")
            return redirect('register')

        user = User.objects.create_user(
            username=username_str,
            email=email_str,
            password=password_str,
            first_name=first_name,
            last_name=last_name
        )
        login(request, user)
        messages.success(request, f"Account created! Welcome, {user.username}!")
        return redirect('home')
    return render(request, 'register.html')

# -------------------------------------------------------------
# CUSTOM ADMIN DASHBOARD VIEWS
# -------------------------------------------------------------

@user_passes_test(is_admin)
def admin_dashboard(request):
    # Stats calculations
    movies_count = Movie.objects.count()
    bookings_count = Booking.objects.count()
    
    # Today's Revenue
    today = date.today()
    today_revenue = Booking.objects.filter(showtime__date=today).aggregate(total=Sum('total_price'))['total'] or 0.00
    
    reviews_count = Review.objects.count()
    customers_count = User.objects.filter(is_staff=False).count() or Booking.objects.values('customer_email').distinct().count()

    # Chart data calculations
    # 1. Bookings per movie
    bookings_per_movie = []
    for movie in Movie.objects.all():
        total_tickets = 0
        bookings_for_movie = Booking.objects.filter(showtime__movie=movie)
        for b in bookings_for_movie:
            total_tickets += len(b.seat_list)
        bookings_per_movie.append({'title': movie.title, 'tickets': total_tickets})
        
    # 2. Revenue per movie
    revenue_per_movie = []
    for movie in Movie.objects.all():
        rev = Booking.objects.filter(showtime__movie=movie).aggregate(total=Sum('total_price'))['total'] or 0.00
        revenue_per_movie.append({'title': movie.title, 'revenue': float(rev)})

    # 3. Popular genres
    popular_genres = []
    for genre in Genre.objects.all():
        movie_count = genre.movies.count()
        popular_genres.append({'name': genre.name, 'count': movie_count})

    context = {
        'stats': {
            'movies_count': movies_count,
            'bookings_count': bookings_count,
            'today_revenue': today_revenue,
            'reviews_count': reviews_count,
            'customers_count': customers_count,
        },
        'charts': {
            'bookings_per_movie': bookings_per_movie,
            'revenue_per_movie': revenue_per_movie,
            'popular_genres': popular_genres,
        }
    }
    return render(request, 'admin_dashboard.html', context)

@user_passes_test(is_admin)
def admin_movies(request):
    if request.method == 'POST':
        if 'add_movie' in request.POST:
            title = request.POST.get('title')
            runtime = int(request.POST.get('runtime', '120'))
            language = request.POST.get('language')
            release_date = request.POST.get('release_date')
            director = request.POST.get('director')
            cast = request.POST.get('cast')
            trailer_url = request.POST.get('trailer_url')
            synopsis = request.POST.get('synopsis')
            
            poster = request.FILES.get('poster')
            banner = request.FILES.get('banner')
            
            is_currently_playing = 'is_currently_playing' in request.POST
            is_coming_soon = 'is_coming_soon' in request.POST
            is_trending = 'is_trending' in request.POST
            is_top_rated = 'is_top_rated' in request.POST

            movie = Movie.objects.create(
                title=title,
                runtime=runtime,
                language=language,
                release_date=release_date,
                director=director,
                cast=cast,
                trailer_url=trailer_url,
                synopsis=synopsis,
                poster=poster,
                banner=banner,
                is_currently_playing=is_currently_playing,
                is_coming_soon=is_coming_soon,
                is_trending=is_trending,
                is_top_rated=is_top_rated
            )

            # Genres mapping
            genre_ids = request.POST.getlist('genres')
            if genre_ids:
                movie.genres.set(Genre.objects.filter(id__in=genre_ids))

            # Optional new genre creation
            new_genre_name = request.POST.get('new_genre', '').strip()
            if new_genre_name:
                genre, created = Genre.objects.get_or_create(name=new_genre_name)
                movie.genres.add(genre)

            messages.success(request, f"Movie '{movie.title}' added successfully!")
            return redirect('admin_movies')

        elif 'delete_movie' in request.POST:
            movie_id = request.POST.get('movie_id')
            movie = get_object_or_404(Movie, id=movie_id)
            title = movie.title
            movie.delete()
            messages.info(request, f"Movie '{title}' deleted successfully.")
            return redirect('admin_movies')

    context = {
        'movies': Movie.objects.all(),
        'genres': Genre.objects.all(),
    }
    return render(request, 'admin_movies.html', context)

@user_passes_test(is_admin)
def admin_showtimes(request):
    if request.method == 'POST':
        if 'add_showtime' in request.POST:
            movie_id = request.POST.get('movie_id')
            movie = get_object_or_404(Movie, id=movie_id)
            date_val = request.POST.get('date')
            time_val = request.POST.get('time')
            screen = int(request.POST.get('screen', '1'))
            price = request.POST.get('price', '12.00')

            Showtime.objects.create(
                movie=movie,
                date=date_val,
                time=time_val,
                screen=screen,
                price=price
            )
            messages.success(request, "Showtime scheduled successfully!")
            return redirect('admin_showtimes')

        elif 'delete_showtime' in request.POST:
            showtime_id = request.POST.get('showtime_id')
            showtime = get_object_or_404(Showtime, id=showtime_id)
            showtime.delete()
            messages.info(request, "Showtime removed successfully.")
            return redirect('admin_showtimes')

    context = {
        'showtimes': Showtime.objects.all().order_by('date', 'time'),
        'movies': Movie.objects.all(),
    }
    return render(request, 'admin_showtimes.html', context)

@user_passes_test(is_admin)
def admin_bookings(request):
    bookings = Booking.objects.all().order_by('-created_at')
    total_revenue = Booking.objects.aggregate(total=Sum('total_price'))['total'] or 0.00
    
    context = {
        'bookings': bookings,
        'total_revenue': total_revenue,
    }
    return render(request, 'admin_bookings.html', context)

@user_passes_test(is_admin)
def admin_reviews(request):
    if request.method == 'POST':
        if 'delete_review' in request.POST:
            review_id = request.POST.get('review_id')
            review = get_object_or_404(Review, id=review_id)
            review.delete()
            messages.info(request, "Review deleted successfully.")
            return redirect('admin_reviews')

    context = {
        'reviews': Review.objects.all(),
    }
    return render(request, 'admin_reviews.html', context)
