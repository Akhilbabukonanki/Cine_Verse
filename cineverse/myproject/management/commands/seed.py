import io
import urllib.request
from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from PIL import Image, ImageDraw
from myproject.models import Genre, Movie, Showtime, Booking, Review

class Command(BaseCommand):
    help = 'Seeds database with sample genres, movies, and showtimes'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing database records...')
        Booking.objects.all().delete()
        Showtime.objects.all().delete()
        Review.objects.all().delete()
        Movie.objects.all().delete()
        Genre.objects.all().delete()

        # 1. Create Superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            self.stdout.write('Creating admin user (user: admin, pass: admin)...')
            User.objects.create_superuser('admin', 'admin@cineverse.com', 'admin')

        # 2. Create standard genres
        self.stdout.write('Creating genres...')
        genres_dict = {}
        genre_names = ['Sci-Fi', 'Action', 'Animation', 'Adventure', 'Drama', 'Comedy']
        for name in genre_names:
            genre, _ = Genre.objects.get_or_create(name=name)
            genres_dict[name] = genre

        # Helper to draw a text image for posters/banners if download fails
        def generate_mock_image(text, bg_color, size=(300, 450)):
            img = Image.new("RGB", size, color=bg_color)
            draw = ImageDraw.Draw(img)
            draw.rectangle([5, 5, size[0]-5, size[1]-5], outline=(255, 255, 255), width=2)
            draw.text((size[0]//2 - 30, size[1]//3), "[ Movie ]", fill=(255, 255, 255))
            words = text.split()
            y_offset = size[1]//2 - 20
            for word in words:
                draw.text((size[0]//2 - (len(word)*3), y_offset), word, fill=(255, 255, 255))
                y_offset += 15
            
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)
            return ContentFile(buf.read(), name=f"{text.lower().replace(' ', '_')}.jpg")

        # Helper to download actual movie posters from TMDB
        def download_movie_image(url, filename):
            try:
                self.stdout.write(f"Downloading {filename} from {url}...")
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                with urllib.request.urlopen(req, timeout=8) as response:
                    return ContentFile(response.read(), name=filename)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed to download {filename}: {e}. Using placeholder instead."))
                return None

        # 3. Create movies with TMDB URL paths
        self.stdout.write('Creating movie records...')
        movies_data = [
            {
                'title': 'Interstellar',
                'genres': ['Sci-Fi', 'Adventure', 'Drama'],
                'runtime': 169,
                'language': 'English',
                'release_date': date(2014, 11, 7),
                'director': 'Christopher Nolan',
                'cast': 'Matthew McConaughey, Anne Hathaway, Jessica Chastain',
                'synopsis': 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival in the face of a global crop blight and second Dust Bowl.',
                'trailer_url': 'https://www.youtube.com/watch?v=zSWdZAIBEs4',
                'poster_url': 'https://image.tmdb.org/t/p/w500/gEU2QvIPwc30s5493R3bZ2n6llc.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/w1280/xJHok7RjGO6i9I30wUD8snCJuC6.jpg',
                'color': '#0f172a',
                'banner_color': '#1e293b',
                'is_trending': True,
                'is_top_rated': True,
                'is_currently_playing': True,
            },
            {
                'title': 'Inside Out',
                'genres': ['Animation', 'Comedy', 'Drama'],
                'runtime': 95,
                'language': 'English',
                'release_date': date(2015, 6, 19),
                'director': 'Pete Docter',
                'cast': 'Amy Poehler, Bill Hader, Lewis Black',
                'synopsis': 'After young Riley is uprooted from her Midwest life and moved to San Francisco, her emotions - Joy, Fear, Anger, Disgust and Sadness - conflict on how best to navigate a new city, house, and school.',
                'trailer_url': 'https://www.youtube.com/watch?v=yRUAzGQ3nSY',
                'poster_url': 'https://image.tmdb.org/t/p/w500/lRwqKVFlQ7v2Xg4TXrxee77eCL0.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/w1280/j29ZuefPjSTwqEm6IfbbJOK6jwu.jpg',
                'color': '#0284c7',
                'banner_color': '#0369a1',
                'is_trending': True,
                'is_top_rated': False,
                'is_currently_playing': True,
            },
            {
                'title': 'Indiana Jones',
                'genres': ['Action', 'Adventure'],
                'runtime': 115,
                'language': 'English',
                'release_date': date(1981, 6, 12),
                'director': 'Steven Spielberg',
                'cast': 'Harrison Ford, Karen Allen, Paul Freeman',
                'synopsis': 'Archaeology professor Indiana Jones ventures to seize a biblical artifact known as the Ark of the Covenant. While doing so, he must face Nazi forces who intend to employ its power for global domination.',
                'trailer_url': 'https://www.youtube.com/watch?v=XkkzKjKjSgc',
                'poster_url': 'https://image.tmdb.org/t/p/w500/ceG7Vcxr1kgkgVVk5ri38S7VzNw.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/w1280/84ly1ssm5ucx5g7PM9Vz7L59iyV.jpg',
                'color': '#b45309',
                'banner_color': '#78350f',
                'is_trending': False,
                'is_top_rated': True,
                'is_currently_playing': True,
            },
            {
                'title': 'Inception',
                'genres': ['Sci-Fi', 'Action'],
                'runtime': 148,
                'language': 'English',
                'release_date': date(2010, 7, 16),
                'director': 'Christopher Nolan',
                'cast': 'Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page',
                'synopsis': 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O., but his tragic past may doom the project.',
                'trailer_url': 'https://www.youtube.com/watch?v=YoHD9XEInc0',
                'poster_url': 'https://image.tmdb.org/t/p/w500/o01vCoZl188cR6jCg25D4iNAV69.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/w1280/ztkUQj631j9P15ascy26U51555V.jpg',
                'color': '#111827',
                'banner_color': '#1f2937',
                'is_trending': True,
                'is_top_rated': True,
                'is_currently_playing': True,
            },
            {
                'title': 'Avatar: The Way of Water',
                'genres': ['Sci-Fi', 'Action', 'Adventure'],
                'runtime': 192,
                'language': 'English',
                'release_date': date(2022, 12, 16),
                'director': 'James Cameron',
                'cast': 'Sam Worthington, Zoe Saldana, Sigourney Weaver',
                'synopsis': 'Jake Sully lives with his newfound family formed on the extrasolar moon Pandora. Once a familiar threat returns to finish what was previously started, Jake must work with Neytiri and the army of the Na\'vi race to protect their home.',
                'trailer_url': 'https://www.youtube.com/watch?v=d9MyW72ELq0',
                'poster_url': 'https://image.tmdb.org/t/p/w500/t6HI63j3iiwEbSn6w3tpJ68R402.jpg',
                'banner_url': 'https://image.tmdb.org/t/p/w1280/ovM06Pd1ReqZIB2H3gk2JUMi69v.jpg',
                'color': '#0891b2',
                'banner_color': '#0e7490',
                'is_trending': False,
                'is_top_rated': False,
                'is_coming_soon': True,
                'is_currently_playing': False,
            }
        ]

        created_movies = []
        for m_info in movies_data:
            movie = Movie.objects.create(
                title=m_info['title'],
                runtime=m_info['runtime'],
                language=m_info['language'],
                release_date=m_info['release_date'],
                director=m_info['director'],
                cast=m_info['cast'],
                synopsis=m_info['synopsis'],
                trailer_url=m_info['trailer_url'],
                is_currently_playing=m_info.get('is_currently_playing', True),
                is_coming_soon=m_info.get('is_coming_soon', False),
                is_trending=m_info.get('is_trending', False),
                is_top_rated=m_info.get('is_top_rated', False),
            )
            
            # Try loading actual images, otherwise fallback to procedural designs
            poster_file = download_movie_image(m_info['poster_url'], f"{m_info['title'].lower().replace(' ', '_')}_poster.jpg")
            if not poster_file:
                poster_file = generate_mock_image(m_info['title'], m_info['color'], (300, 450))

            banner_file = download_movie_image(m_info['banner_url'], f"{m_info['title'].lower().replace(' ', '_')}_banner.jpg")
            if not banner_file:
                banner_file = generate_mock_image(m_info['title'] + " Banner", m_info['banner_color'], (1200, 480))
            
            movie.poster.save(poster_file.name, poster_file, save=False)
            movie.banner.save(banner_file.name, banner_file, save=False)
            movie.save()

            # Set genres
            movie_genres = [genres_dict[g_name] for g_name in m_info['genres'] if g_name in genres_dict]
            movie.genres.set(movie_genres)
            created_movies.append(movie)

        # 4. Schedule Showtimes (Today & Tomorrow)
        self.stdout.write('Scheduling showtimes...')
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        times_list = [
            time(10, 30),
            time(13, 0),
            time(16, 0),
            time(16, 30),
            time(19, 30)
        ]

        for idx, movie in enumerate(created_movies):
            if movie.is_currently_playing:
                # Today showtimes
                Showtime.objects.create(
                    movie=movie,
                    date=today,
                    time=times_list[idx % len(times_list)],
                    screen=(idx % 3) + 1,
                    price=12.00
                )
                Showtime.objects.create(
                    movie=movie,
                    date=today,
                    time=times_list[(idx + 2) % len(times_list)],
                    screen=((idx + 1) % 3) + 1,
                    price=12.00
                )
                # Tomorrow showtimes
                Showtime.objects.create(
                    movie=movie,
                    date=tomorrow,
                    time=times_list[(idx + 1) % len(times_list)],
                    screen=((idx + 2) % 3) + 1,
                    price=12.00
                )
                Showtime.objects.create(
                    movie=movie,
                    date=tomorrow,
                    time=times_list[(idx + 3) % len(times_list)],
                    screen=(idx % 3) + 1,
                    price=12.00
                )

        # 5. Populate some Reviews
        self.stdout.write('Seeding customer reviews...')
        reviews_data = [
            {'movie_title': 'Interstellar', 'name': 'Akhil', 'rating': 5, 'comment': 'Amazing Visual Effects. Deep and emotional storytelling. Masterpiece!'},
            {'movie_title': 'Interstellar', 'name': 'Rahul', 'rating': 5, 'comment': 'Worth every penny. The sound design is mind blowing.'},
            {'movie_title': 'Inception', 'name': 'Sanjay', 'rating': 4, 'comment': 'Incredibly smart movie. Needs a rewatch to fully understand!'},
            {'movie_title': 'Inside Out', 'name': 'Preethi', 'rating': 5, 'comment': 'Tear jerker. Extremely creative depiction of the human mind!'}
        ]

        for rev in reviews_data:
            try:
                mov = Movie.objects.get(title=rev['movie_title'])
                Review.objects.create(
                    movie=mov,
                    customer_name=rev['name'],
                    rating=rev['rating'],
                    comment=rev['comment']
                )
            except Movie.DoesNotExist:
                pass

        self.stdout.write(self.style.SUCCESS('Successfully seeded database with mock movie theater records!'))
