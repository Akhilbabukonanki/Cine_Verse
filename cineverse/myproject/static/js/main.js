// CineVerse Interactive Client Script

document.addEventListener('DOMContentLoaded', function () {
    // -------------------------------------------------------------
    // 1. LIGHT/DARK THEME TOGGLE
    // -------------------------------------------------------------
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    
    // Check local storage for theme selection
    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function () {
            let theme = document.documentElement.getAttribute('data-theme');
            let newTheme = (theme === 'dark') ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }

    function updateThemeIcon(theme) {
        if (!themeIcon) return;
        if (theme === 'light') {
            themeIcon.className = 'bi bi-moon-fill';
        } else {
            themeIcon.className = 'bi bi-sun-fill';
        }
    }

    // -------------------------------------------------------------
    // 2. LIVE SEARCH suggestion autocomplete (AJAX)
    // -------------------------------------------------------------
    const searchInput = document.getElementById('movie-search-input');
    const searchDropdown = document.getElementById('live-search-results');

    if (searchInput && searchDropdown) {
        searchInput.addEventListener('input', function () {
            const query = searchInput.value.trim();
            if (query.length < 2) {
                searchDropdown.style.display = 'none';
                searchDropdown.innerHTML = '';
                return;
            }

            // Fetch matched movies from Django view endpoint
            fetch(`/ajax-search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.results && data.results.length > 0) {
                        searchDropdown.innerHTML = '';
                        data.results.forEach(movie => {
                            const item = document.createElement('a');
                            item.className = 'live-search-item';
                            item.href = `/movie/${movie.id}/`;
                            
                            const posterImg = movie.poster_url 
                                ? `<img src="${movie.poster_url}" alt="${movie.title}">`
                                : `<div class="bg-secondary text-white rounded d-flex align-items-center justify-content-center" style="width: 40px; height: 55px; margin-right: 12px; font-size: 8px;">No Poster</div>`;

                            item.innerHTML = `
                                ${posterImg}
                                <div>
                                    <div class="fw-bold text-light-theme-dark">${movie.title}</div>
                                    <small class="text-muted">${movie.genres} | ${movie.language}</small>
                                </div>
                            `;
                            searchDropdown.appendChild(item);
                        });
                        searchDropdown.style.display = 'block';
                    } else {
                        searchDropdown.innerHTML = '<div class="p-3 text-muted text-center"><small>No movies found</small></div>';
                        searchDropdown.style.display = 'block';
                    }
                })
                .catch(err => {
                    console.error('Error fetching search details:', err);
                });
        });

        // Close search list if user clicks away
        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.style.display = 'none';
            }
        });
    }

    // -------------------------------------------------------------
    // 3. SEAT SELECTION & LIVE PRICING CALCULATOR
    // -------------------------------------------------------------
    const seatGrid = document.querySelector('.seat-grid');
    if (seatGrid) {
        const seats = document.querySelectorAll('.seat-element:not(.booked)');
        const selectedSeatsDisplay = document.getElementById('selected-seats-display');
        const ticketCountDisplay = document.getElementById('ticket-count-display');
        const ticketPriceDisplay = document.getElementById('ticket-price-display');
        const ticketTotalDisplay = document.getElementById('ticket-total-display');
        
        // Hidden inputs to send to the backend booking post request
        const hiddenSeatsInput = document.getElementById('hidden-seats');
        const hiddenTotalInput = document.getElementById('hidden-total');
        const bookingForm = document.getElementById('seat-booking-form');

        // Read pricing parameters from showtime element
        const ticketCost = parseFloat(document.getElementById('showtime-price-holder')?.dataset.price || 12.00);

        let selectedSeats = [];

        seats.forEach(seat => {
            seat.addEventListener('click', function () {
                const seatCode = seat.dataset.seatCode;

                if (seat.classList.contains('selected')) {
                    // Remove seat
                    seat.classList.remove('selected');
                    selectedSeats = selectedSeats.filter(code => code !== seatCode);
                } else {
                    // Add seat
                    seat.classList.add('selected');
                    selectedSeats.push(seatCode);
                }

                // Update displays
                updateSeatCalculator();
            });
        });

        function updateSeatCalculator() {
            if (selectedSeats.length > 0) {
                selectedSeatsDisplay.textContent = selectedSeats.sort().join(', ');
                ticketCountDisplay.textContent = selectedSeats.length;
                ticketPriceDisplay.textContent = `${selectedSeats.length} × $${ticketCost}`;
                
                const totalPrice = (selectedSeats.length * ticketCost).toFixed(2);
                ticketTotalDisplay.textContent = `$${totalPrice}`;

                // Populate form values
                if (hiddenSeatsInput) hiddenSeatsInput.value = selectedSeats.join(',');
                if (hiddenTotalInput) hiddenTotalInput.value = totalPrice;
            } else {
                selectedSeatsDisplay.textContent = 'None';
                ticketCountDisplay.textContent = '0';
                ticketPriceDisplay.textContent = '0 × $0';
                ticketTotalDisplay.textContent = '$0';
                
                if (hiddenSeatsInput) hiddenSeatsInput.value = '';
                if (hiddenTotalInput) hiddenTotalInput.value = '';
            }
        }

        // Validate booking form selection before submit
        if (bookingForm) {
            bookingForm.addEventListener('submit', function (e) {
                if (selectedSeats.length === 0) {
                    e.preventDefault();
                    alert('Please select at least one seat before proceeding!');
                }
            });
        }
    }

    // -------------------------------------------------------------
    // 4. TRAILER MODAL INTEGRATION
    // -------------------------------------------------------------
    const trailerModal = document.getElementById('trailerModal');
    if (trailerModal) {
        const trailerIframe = document.getElementById('trailerIframe');
        
        trailerModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const embedId = button.getAttribute('data-youtube-id');
            if (embedId) {
                trailerIframe.src = `https://www.youtube.com/embed/${embedId}?autoplay=1&rel=0`;
            }
        });

        trailerModal.addEventListener('hide.bs.modal', function () {
            // Stop video playing by clearing source
            trailerIframe.src = '';
        });
    }

    // -------------------------------------------------------------
    // 5. WISHLIST AJAX TOGGLE
    // -------------------------------------------------------------
    const wishlistHeartBtns = document.querySelectorAll('.wishlist-toggle-btn');
    wishlistHeartBtns.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            const movieId = btn.dataset.movieId;
            
            fetch(`/wishlist/toggle/${movieId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'added') {
                    btn.classList.add('active');
                    if (btn.classList.contains('w-100')) {
                        btn.innerHTML = '<i class="bi bi-heart-fill me-2"></i> Remove from Wishlist';
                    } else {
                        btn.innerHTML = '<i class="bi bi-heart-fill"></i>';
                    }
                    showToast('Movie added to wishlist!', 'success');
                } else if (data.status === 'removed') {
                    btn.classList.remove('active');
                    if (btn.classList.contains('w-100')) {
                        btn.innerHTML = '<i class="bi bi-heart me-2"></i> Save to Wishlist';
                    } else {
                        btn.innerHTML = '<i class="bi bi-heart"></i>';
                    }
                    showToast('Movie removed from wishlist!', 'info');
                }
            })
            .catch(err => console.error('Error toggling wishlist:', err));
        });
    });

    // Helper: read CSRF cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Helper: Simple toast notification creator
    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '1100';
            document.body.appendChild(container);
        }
        
        const id = 'toast_' + Math.random().toString(36).substr(2, 9);
        const bgClass = type === 'success' ? 'bg-success' : (type === 'danger' ? 'bg-danger' : 'bg-primary');
        const toastHtml = `
            <div id="${id}" class="toast align-items-center text-white ${bgClass} border-0 show" role="alert" aria-live="assertive" aria-atomic="true">
              <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
              </div>
            </div>
        `;
        
        const container = document.getElementById('toast-container');
        container.insertAdjacentHTML('beforeend', toastHtml);
        
        // Auto remove toast after 3 seconds
        setTimeout(() => {
            const element = document.getElementById(id);
            if (element) {
                element.classList.remove('show');
                setTimeout(() => element.remove(), 500);
            }
        }, 3000);
    }
});
