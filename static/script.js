const app = document.getElementById('app');

let currentUser = null;
let showtimes = [];
let moviesList = [];
let theaters = [];
let selectedSeats = [];
let currentPending = 0;
let staffBookings = [];

window.onload = async () => {
  await fetchCurrentUser();
  await loadShowtimes();
  render();
};

async function fetchCurrentUser() {
  try {
    const res = await fetch('/auth/me');
    const result = await res.json();
    if (res.ok && result.data) {
      currentUser = result.data;
    } else {
      currentUser = null;
    }
  } catch (err) {
    console.error('Auth fetch failed', err);
    currentUser = null;
  }
}

async function login() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  if (!email || !password) {
    alert('Please enter both email and password');
    return;
  }

  try {
    const res = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Login failed');
      return;
    }
    currentUser = result.data;
    await loadShowtimes();
    render();
  } catch (err) {
    console.error('Login error', err);
    alert('Login failed, check console');
  }
}

async function quickLogin(role) {
  const credentials = {
    customer: { email: 'aom@mail.com', password: '1234' },
    staff: { email: 'dan@mail.com', password: '1150' },
    admin: { email: 'eclair@gmail.com', password: '1437' }
  };
  const user = credentials[role];
  if (!user) {
    alert('Quick login is only available for customer, staff, or admin');
    return;
  }
  document.getElementById('email').value = user.email;
  document.getElementById('password').value = user.password;
  await login();
}

function render() {
  if (!currentUser || !currentUser.role) {
    renderLogin();
    return;
  }
  if (currentUser.role === 'customer') {
    renderCustomer();
  } else if (currentUser.role === 'staff') {
    renderStaff();
  } else if (currentUser.role === 'admin') {
    renderAdmin();
  } else {
    renderGeneric();
  }
}

function renderLogin() {
  app.innerHTML = `
    <div class="card form-card">
      <h2>Login</h2>
      <input id="email" placeholder="Email" />
      <input id="password" type="password" placeholder="Password" />
      <button onclick="login()">Login</button>
      <button class="secondary" onclick="renderRegister()">Create new account</button>
      <div class="quick-login">
        <p>Quick login</p>
        <button onclick="quickLogin('customer')">Customer</button>
        <button onclick="quickLogin('staff')">Staff</button>
        <button onclick="quickLogin('admin')">Admin</button>
      </div>
    </div>
  `;
}

function renderRegister() {
  app.innerHTML = `
    <div class="card form-card">
      <h2>Register</h2>
      <input id="register_user_id" type="number" placeholder="User ID" />
      <input id="register_name" placeholder="Name" />
      <input id="register_email" placeholder="Email" />
      <input id="register_password" type="password" placeholder="Password" />
      <select id="register_role">
        <option value="customer">Customer</option>
      </select>
      <button onclick="registerUser()">Register</button>
      <button class="secondary" onclick="renderLogin()">Back to login</button>
    </div>
  `;
}

async function registerUser() {
  const user_id = Number(document.getElementById('register_user_id').value);
  const name = document.getElementById('register_name').value;
  const email = document.getElementById('register_email').value;
  const password = document.getElementById('register_password').value;
  const role = document.getElementById('register_role').value;

  if (!user_id || !name || !email || !password) {
    alert('Please fill all registration fields');
    return;
  }

  try {
    const res = await fetch('/users/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id, name, email, password, role })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Registration failed');
      return;
    }
    alert(result.message || 'User registered successfully');
    renderLogin();
  } catch (err) {
    console.error('Registration error', err);
    alert('Registration failed, check console');
  }
}

async function renderAdmin() {
  let revenue = [];
  let bookings = [];
  try {
    await loadMovies();
    await loadTheaters();
    revenue = await loadRevenue();
    bookings = await loadAllBookings();
  } catch (err) {
    console.error('Admin data error', err);
  }
  const userBox = renderUserInfo();
  app.innerHTML = `
    ${userBox}
    <div class="card form-card">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
        <h2>Admin Dashboard</h2>
        <button class="secondary" onclick="logout()">Logout</button>
      </div>
    </div>
    <section>
      <h3>📌 Create Movie</h3>
      <div class="card form-card">
        <input id="movie_id" type="number" placeholder="Movie ID" />
        <input id="owner_id" type="number" placeholder="Owner ID" />
        <input id="movie_title" placeholder="Title" />
        <input id="duration" type="number" placeholder="Duration (minutes)" />
        <button onclick="createMovie()">Create Movie</button>
      </div>
    </section>
    <section>
      <h3>🎭 Create Theater</h3>
      <div class="card form-card">
        <input id="theater_id" type="number" placeholder="Theater ID" />
        <input id="theater_name" placeholder="Theater Name" />
        <button onclick="createTheater()">Create Theater</button>
      </div>
    </section>
    <section>
      <h3>🎬 Create Showtime</h3>
      <div class="card form-card">
        <input id="showtime_id" type="number" placeholder="Showtime ID" />
        <select id="select_movie">
          <option value="">Select Movie</option>
          ${moviesList.map(m => `<option value="${m.movie_id}">${m.title}</option>`).join('')}
        </select>
        <select id="select_theater">
          <option value="">Select Theater</option>
          ${theaters.map(t => `<option value="${t.theater_id}">${t.theater_name}</option>`).join('')}
        </select>
        <input id="show_date" type="datetime-local" />
        <input id="show_price" type="number" step="0.01" placeholder="Price" />
        <button onclick="createShowtime()">Create Showtime</button>
      </div>
    </section>
    <section>
      <h3>🎞️ Genre Management</h3>
      <div class="card form-card">
        <select id="genre_movie" onchange="updateGenrePanel()">
          <option value="">Select Movie</option>
          ${moviesList.map(m => `<option value="${m.movie_id}">${m.title}</option>`).join('')}
        </select>
        <div id="genre-list" class="card"></div>
        <input id="genre_text" placeholder="New genre" />
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <button onclick="addGenre()">Add Genre</button>
          <button class="secondary" onclick="removeGenre()">Remove Genre</button>
        </div>
      </div>
    </section>
    <section>
      <h3>💰 Revenue</h3>
      ${revenue.length > 0 ? `<div class="card-grid">${revenue.map(r => `
        <div class="card">
          <h4>${r.title}</h4>
          <p>Revenue: ${r.total_revenue}</p>
        </div>
      `).join('')}</div>` : '<p>No revenue data</p>'}
    </section>
    <section>
      <h3>📋 All Bookings</h3>
      ${bookings.length > 0 ? `<div class="card-grid">${bookings.map(b => `
        <div class="card">
          <h4>Booking #${b.booking_id}</h4>
          <p>User: ${b.user_id}</p>
          <p>Showtime: ${b.showtime_id}</p>
          <p>Status: ${b.status}</p>
        </div>
      `).join('')}</div>` : '<p>No bookings available</p>'}
    </section>
  `;
  updateGenrePanel();
}

async function createMovie() {
  const movie_id = Number(document.getElementById('movie_id').value);
  const owner_id = Number(document.getElementById('owner_id').value);
  const title = document.getElementById('movie_title').value;
  const duration = Number(document.getElementById('duration').value);
  if (!movie_id || !owner_id || !title || !duration) {
    alert('Please fill all movie fields');
    return;
  }
  try {
    const res = await fetch('/movies/admin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ movie_id, owner_id, title, duration })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Create movie failed');
      return;
    }
    alert('Movie created successfully');
    await loadMovies();
    render();
  } catch (err) {
    console.error(err);
    alert('Create movie failed');
  }
}

async function createTheater() {
  const theater_id = Number(document.getElementById('theater_id').value);
  const theater_name = document.getElementById('theater_name').value;
  if (!theater_id || !theater_name) {
    alert('Please fill all theater fields');
    return;
  }
  try {
    const res = await fetch('/movies/theaters', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theater_id, theater_name })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Create theater failed');
      return;
    }
    alert('Theater created successfully');
    await loadTheaters();
    render();
  } catch (err) {
    console.error(err);
    alert('Create theater failed');
  }
}

async function createShowtime() {
  const showtime_id = Number(document.getElementById('showtime_id').value);
  const movie_id = Number(document.getElementById('select_movie').value);
  const theater_id = Number(document.getElementById('select_theater').value);
  const show_date = document.getElementById('show_date').value;
  const price = Number(document.getElementById('show_price').value);
  if (!showtime_id || !movie_id || !theater_id || !show_date || !price) {
    alert('Please fill all showtime fields');
    return;
  }
  try {
    const res = await fetch('/showtimes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ showtime_id, movie_id, theater_id, show_date, price })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Create showtime failed');
      return;
    }
    alert('Showtime created successfully');
    await loadShowtimes();
    render();
  } catch (err) {
    console.error(err);
    alert('Create showtime failed');
  }
}

async function renderCustomer() {
  let topMovie = null;
  let pendingInfo = null;
  let bookingHistory = [];
  try {
    topMovie = await loadTopMovie();
  } catch (e) {
    console.error('topMovie error', e);
  }
  try {
    pendingInfo = await loadPending(currentUser.user_id);
  } catch (e) {
    console.error('pending error', e);
  }
  try {
    bookingHistory = await loadBookingHistory();
  } catch (e) {
    console.error('booking history error', e);
  }
  const userBox = renderUserInfo(pendingInfo);
  app.innerHTML = `
    ${userBox}
    <div class="card form-card">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
        <h2>Customer Dashboard</h2>
        <button class="secondary" onclick="logout()">Logout</button>
      </div>
    </div>
    <section>
      <h3>🔎 Search Movies</h3>
      <div class="card form-card">
        <input id="search_title" placeholder="Title contains..." />
        <input id="search_genre" placeholder="Genre" />
        <input id="search_producer" placeholder="Producer" />
        <button onclick="searchMovies()">Search Movies</button>
      </div>
    </section>
    <section>
      <h3>🎟️ Search Showtimes</h3>
      <div class="card form-card">
        <input id="search_showtime_title" placeholder="Movie title" />
        <input id="search_theater" placeholder="Theater name" />
        <input id="search_show_date" type="date" />
        <button onclick="searchShowtimes()">Search Showtimes</button>
      </div>
    </section>
    <section>
      <h3>🔥 Top Movie</h3>
      ${topMovie ? `<div class="card"><p><strong>${topMovie.title}</strong></p></div>` : '<p>No top movie available</p>'}
    </section>
    <section>
      <h3>My Bookings</h3>
      ${bookingHistory.length > 0 ? `<div class="card-grid">${bookingHistory.map(b => `
        <div class="card">
          <h4>${b.title}</h4>
          <p>Booking: ${b.booking_id}</p>
          <p>Theater: ${b.theater_name}</p>
          <p>Date: ${new Date(b.show_date).toLocaleDateString()}</p>
          <p>Total: ${b.total_amount}</p>
          <p>Status: ${b.status}</p>
          <p>Payment: ${b.payment_status}</p>
          <button onclick="viewBookingDetail(${b.booking_id})">View details</button>
          ${b.payment_status !== 'Confirmed' && b.status !== 'Cancelled' ? `<button onclick="payBooking(${b.booking_id})">Pay now</button>` : ''}
        </div>
      `).join('')}</div>` : '<p>No booking history yet.</p>'}
    </section>
    <section>
      <h3>Available Showtimes</h3>
      ${showtimes.length > 0 ? `<div class="card-grid">${showtimes.map(s => {
    const hasSeats = s.seats && s.seats.trim() !== '';
    return `
          <div class="card">
            <h4>${s.title}</h4>
            <p>Theater: ${s.theater_name}</p>
            <p>Date: ${new Date(s.show_date).toLocaleDateString()}</p>
            <p>Price: ${s.price}</p>
            <p>Seats: ${hasSeats ? s.seats : 'FULL'}</p>
            ${hasSeats ? `<button onclick="book(${s.showtime_id})">Book</button>` : '<span class="badge">Sold out</span>'}
          </div>
        `;
  }).join('')}</div>` : '<p>No showtimes available.</p>'}
    </section>
  `;
}

async function renderStaff() {
  let bookings = [];
  try {
    bookings = await loadAllBookings();
    staffBookings = bookings;
  } catch (err) {
    console.error('Staff data error', err);
  }
  const userBox = renderUserInfo();
  app.innerHTML = `
    ${userBox}
    <div class="card form-card">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
        <h2>Staff Dashboard</h2>
        <button class="secondary" onclick="logout()">Logout</button>
      </div>
    </div>
    <section>
      <h3>Search Booking</h3>
      <div class="card form-card">
        <input id="search_booking_id" type="number" placeholder="Enter booking ID" />
        <button onclick="searchBookingById()">Search</button>
      </div>
    </section>
    <section>
      <h3>Booking Status</h3>
      <div id="staff-booking-list">
        ${renderStaffBookingList(bookings)}
      </div>
    </section>
  `;
}

function renderStaffBookingList(bookings) {
  if (!bookings || bookings.length === 0) {
    return '<p>No booking data</p>';
  }
  return `<div class="card-grid">${bookings.map(b => `
          <div class="card">
            <p><strong>Booking #${b.booking_id}</strong></p>
            <p>User: ${b.user_id}</p>
            <p>Showtime: ${b.showtime_id}</p>
            <p>Status: ${b.status}</p>
            ${b.status === 'Confirmed' ? `<button onclick="staffCheckin(${b.booking_id})">Check-in</button>` : b.status === 'Pending' ? '<p class="info-text">ต้องชำระเงินก่อนเพื่อยืนยันการจอง</p>' : ''}
          </div>
        `).join('')}</div>`;
}

async function searchBookingById() {
  const bookingId = Number(document.getElementById('search_booking_id')?.value || 0);
  const listContainer = document.getElementById('staff-booking-list');
  if (!listContainer) return;
  if (!bookingId) {
    listContainer.innerHTML = renderStaffBookingList(staffBookings);
    return;
  }
  const filtered = staffBookings.filter(b => b.booking_id === bookingId);
  if (filtered.length === 0) {
    listContainer.innerHTML = `<p>No booking found for ID ${bookingId}</p>`;
    return;
  }
  listContainer.innerHTML = renderStaffBookingList(filtered);
}

function renderGeneric() {
  const userBox = renderUserInfo();
  app.innerHTML = `
    ${userBox}
    <h2>Welcome</h2>
    <button onclick="logout()">Logout</button>
  `;
}

function formatDate(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

async function searchMovies() {
  const title = document.getElementById('search_title').value;
  const genre = document.getElementById('search_genre').value;
  const producer = document.getElementById('search_producer').value;
  const query = new URLSearchParams();
  if (title) query.append('title', title);
  if (genre) query.append('genre', genre);
  if (producer) query.append('producer', producer);

  try {
    const res = await fetch(`/movies/search?${query.toString()}`);
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Search failed');
      return;
    }
    renderSearchResults('Movie search results', result.data || [], 'movies');
  } catch (err) {
    console.error('Search movies error', err);
    alert('Search failed, check console');
  }
}

async function searchShowtimes() {
  const title = document.getElementById('search_showtime_title').value;
  const theater = document.getElementById('search_theater').value;
  const show_date = document.getElementById('search_show_date').value;
  const query = new URLSearchParams();
  if (title) query.append('title', title);
  if (theater) query.append('theater', theater);
  if (show_date) query.append('show_date', show_date);

  try {
    const res = await fetch(`/showtimes?${query.toString()}`);
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Search failed');
      return;
    }
    renderSearchResults('Showtime search results', result.data || [], 'showtimes');
  } catch (err) {
    console.error('Search showtimes error', err);
    alert('Search failed, check console');
  }
}

function renderSearchResults(title, items, type) {
  app.innerHTML = `
    <div class="card form-card">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
        <h2>${title}</h2>
        <button class="secondary" onclick="render()">Back</button>
      </div>
    </div>
    <section>
      ${items.length > 0 ? `<div class="card-grid">${items.map(item => {
    if (type === 'movies') {
      return `
            <div class="card">
              <h4>${item.title}</h4>
              <p>Producer: ${item.producer || 'N/A'}</p>
              <p>Duration: ${item.duration || 'N/A'} mins</p>
              <button onclick="viewMovieDetail(${item.movie_id})">View details</button>
            </div>
          `;
    }
    const hasSeats = item.seats && item.seats.trim() !== '';
    return `
          <div class="card">
            <h4>${item.title}</h4>
            <p>Theater: ${item.theater_name}</p>
            <p>Date: ${new Date(item.show_date).toLocaleDateString()}</p>
            <p>Price: ${item.price}</p>
            <p>Seats: ${hasSeats ? item.seats : 'FULL'}</p>
            ${hasSeats ? `<button onclick="book(${item.showtime_id})">Book</button>` : '<span class="badge">Sold out</span>'}
          </div>
        `;
  }).join('')}</div>` : '<p>No results found.</p>'}
    </section>
  `;
}

async function viewMovieDetail(movieId) {
  try {
    const res = await fetch(`/movies/${movieId}`);
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Cannot load movie');
      return;
    }
    const movie = result.data;
    app.innerHTML = `
      <div class="card form-card">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
          <h2>${movie.title}</h2>
          <button class="secondary" onclick="render()">Back</button>
        </div>
      </div>
      <section>
        <div class="card">
          <p><strong>Producer</strong>: ${movie.producer || 'N/A'}</p>
          <p><strong>Duration</strong>: ${movie.duration || 'N/A'} mins</p>
          ${movie.description ? `<p><strong>Description</strong>: ${movie.description}</p>` : ''}
          ${movie.poster_url ? `<p><strong>Poster</strong>: <a href="${movie.poster_url}" target="_blank">View image</a></p>` : ''}
          ${movie.rating ? `<p><strong>Rating</strong>: ${movie.rating}</p>` : ''}
          ${movie.genres ? `<p><strong>Genres</strong>: ${movie.genres.join(', ')}</p>` : ''}
        </div>
      </section>
    `;
  } catch (err) {
    console.error('Movie detail error', err);
    alert('Cannot load movie detail');
  }
}

async function viewBookingDetail(bookingId) {
  try {
    const [bookingRes, paymentRes] = await Promise.all([
      fetch(`/bookings/${bookingId}`),
      fetch(`/bookings/payments/${bookingId}`)
    ]);
    const bookingData = await bookingRes.json();
    const paymentData = await paymentRes.json();
    if (!bookingRes.ok) {
      alert(bookingData.message || 'Cannot load booking');
      return;
    }
    if (!paymentRes.ok) {
      alert(paymentData.message || 'Cannot load payment history');
      return;
    }
    const booking = bookingData.data;
    const payment = paymentData.data;
    app.innerHTML = `
      <div class="card form-card">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
          <h2>Booking #${booking.booking_id}</h2>
          <button class="secondary" onclick="render()">Back</button>
        </div>
      </div>
      <section>
        <div class="card">
          <p><strong>User ID</strong>: ${booking.user_id}</p>
          <p><strong>Movie</strong>: ${booking.title}</p>
          <p><strong>Theater</strong>: ${booking.theater_name}</p>
          <p><strong>Date</strong>: ${formatDate(booking.show_date)}</p>
          <p><strong>Status</strong>: ${booking.status}</p>
          <p><strong>Price</strong>: ${booking.price}</p>
        </div>
      </section>
      <section>
        <h3>Payment History</h3>
        <div class="card">
          <p><strong>Payment ID</strong>: ${payment.payment_id}</p>
          <p><strong>Amount</strong>: ${payment.amount}</p>
          <p><strong>Status</strong>: ${payment.status}</p>
          <p><strong>Date</strong>: ${formatDate(payment.payment_date)}</p>
        </div>
      </section>
    `;
  } catch (err) {
    console.error('Booking detail error', err);
    alert('Cannot load booking detail');
  }
}

async function updateGenrePanel() {
  const movieId = Number(document.getElementById('genre_movie')?.value);
  const list = document.getElementById('genre-list');
  if (!list) return;
  if (!movieId) {
    list.innerHTML = '<p>Please select a movie to manage genres.</p>';
    return;
  }
  try {
    const res = await fetch(`/movies/${movieId}/genres`);
    const result = await res.json();
    if (!res.ok) {
      list.innerHTML = `<p>${result.message || 'Cannot load genres'}</p>`;
      return;
    }
    const genres = result.data || [];
    list.innerHTML = `<p><strong>Genres</strong>:</p>${genres.length > 0 ? genres.map(genre => `<span class="badge">${genre}</span>`).join(' ') : '<p>No genres assigned.</p>'}`;
  } catch (err) {
    console.error('Genre load error', err);
    list.innerHTML = '<p>Unable to load genres.</p>';
  }
}

async function addGenre() {
  const movieId = Number(document.getElementById('genre_movie')?.value);
  const genre = document.getElementById('genre_text')?.value?.trim();
  if (!movieId || !genre) {
    alert('Please select a movie and enter a genre');
    return;
  }
  try {
    const res = await fetch(`/movies/admin/${movieId}/genres`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ genre })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Failed to add genre');
      return;
    }
    document.getElementById('genre_text').value = '';
    updateGenrePanel();
  } catch (err) {
    console.error('Add genre error', err);
    alert('Unable to add genre');
  }
}

async function removeGenre() {
  const movieId = Number(document.getElementById('genre_movie')?.value);
  const genre = document.getElementById('genre_text')?.value?.trim();
  if (!movieId || !genre) {
    alert('Please select a movie and enter a genre to remove');
    return;
  }
  try {
    const res = await fetch(`/movies/admin/${movieId}/genres`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ genre })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Failed to remove genre');
      return;
    }
    document.getElementById('genre_text').value = '';
    updateGenrePanel();
  } catch (err) {
    console.error('Remove genre error', err);
    alert('Unable to remove genre');
  }
}

function logout() {
  fetch('/logout', { method: 'POST' })
    .then(() => {
      currentUser = null;
      renderLogin();
    })
    .catch(err => {
      console.error('Logout failed', err);
      currentUser = null;
      renderLogin();
    });
}

function book(showtimeId) {
  const s = showtimes.find(st => st.showtime_id === showtimeId);
  if (!s || !s.seats) {
    alert('No seats available');
    return;
  }
  const seats = s.seats.split(',').map(seat => seat.trim());
  selectedSeats = [];
  app.innerHTML = `
    <h2>Book: ${s.title}</h2>
    <div class="seat-grid">
      ${seats.map(seat => `
        <button id="seat-${seat}" class="seat-button" onclick="toggleSeat('${seat}')">${seat}</button>
      `).join('')}
    </div>
    <button onclick="confirmBooking(${showtimeId})">Confirm Booking</button>
    <button onclick="render()">Back</button>
  `;
}

function toggleSeat(seat) {
  if (selectedSeats.includes(seat)) {
    selectedSeats = selectedSeats.filter(s => s !== seat);
    document.getElementById(`seat-${seat}`).classList.remove('selected');
  } else {
    selectedSeats.push(seat);
    document.getElementById(`seat-${seat}`).classList.add('selected');
  }
}

async function confirmBooking(showtimeId) {
  if (!selectedSeats.length) {
    alert('Please select at least one seat');
    return;
  }
  try {
    const res = await fetch('/bookings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ showtime_id: showtimeId, seats: selectedSeats })
    });
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Booking failed');
      return;
    }
    alert(`Booked seats: ${selectedSeats.join(', ')}`);
    selectedSeats = [];
    await loadShowtimes();
    render();
  } catch (err) {
    console.error('BOOK ERROR:', err);
    alert('Booking failed, check console');
  }
}

async function loadShowtimes() {
  try {
    const res = await fetch('/showtimes');
    const result = await res.json();
    showtimes = result.data || [];
  } catch (err) {
    console.error('ERROR loading showtimes:', err);
    showtimes = [];
  }
}

async function loadMovies() {
  try {
    const res = await fetch('/movies');
    const result = await res.json();
    moviesList = result.data || [];
  } catch (err) {
    console.error(err);
    moviesList = [];
  }
}

async function loadTheaters() {
  try {
    const res = await fetch('/movies/theaters');
    const result = await res.json();
    theaters = result.data || [];
  } catch (err) {
    console.error(err);
    theaters = [];
  }
}

async function viewSeats(title) {
  const res = await fetch(`/movies/${title}/seats`);
  const result = await res.json();
  const showtimesByTitle = result.data || [];
  app.innerHTML = `
    <h2>Seats for ${title}</h2>
    <button onclick="render()">⬅ Back</button>
    ${showtimesByTitle.map(s => `
      <div class="card">
        <p>🏢 ${s.theater_name}</p>
        <p>💺 ${s.seats || 'FULL'}</p>
      </div>
    `).join('')}
  `;
}

async function loadTopMovie() {
  try {
    const res = await fetch('/movies/top');
    const result = await res.json();
    return result.data;
  } catch (err) {
    console.error(err);
  }
}

async function loadRevenue() {
  try {
    const res = await fetch('/movies/revenue');
    const result = await res.json();
    return result.data || [];
  } catch (err) {
    console.error(err);
    return [];
  }
}

function renderUserInfo(pendingInfo) {
  if (!currentUser) return '';
  const total = Number(pendingInfo?.total_pending || currentPending || 0);
  return `
    <div class="user-box">
      <strong>${currentUser.name}</strong><br>
      ID: ${currentUser.user_id}<br>
      Role: ${currentUser.role}<br>
      ${currentUser.role === 'customer' ? `<hr>Due: ${total}` : ''}
    </div>
  `;
}

async function loadBookingHistory() {
  try {
    const res = await fetch('/bookings/history');
    const result = await res.json();
    return result.data || [];
  } catch (err) {
    console.error('Booking history error', err);
    return [];
  }
}

async function loadAllBookings() {
  try {
    const res = await fetch('/bookings');
    const result = await res.json();
    return result.data || [];
  } catch (err) {
    console.error('All bookings error', err);
    return [];
  }
}

async function payBooking(bookingId) {
  try {
    const res = await fetch(`/bookings/${bookingId}/pay`, { method: 'POST' });
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Payment failed');
      return;
    }
    alert(result.message || 'Payment confirmed');
    render();
  } catch (err) {
    console.error('Pay error', err);
    alert('Payment failed, check console');
  }
}

async function staffCheckin(bookingId) {
  try {
    const res = await fetch(`/users/staff/bookings/${bookingId}/checkin`, { method: 'PUT' });
    const result = await res.json();
    if (!res.ok) {
      alert(result.message || 'Check-in failed');
      return;
    }
    alert(result.message || 'Booking checked in');
    render();
  } catch (err) {
    console.error('Check-in error', err);
    alert('Check-in failed, check console');
  }
}

async function loadPending(userId) {
  try {
    const res = await fetch(`/bookings/pending/${userId}`);
    const result = await res.json();
    currentPending = result.data?.total_pending || 0;
    return result.data || {};
  } catch (err) {
    console.error('Pending error', err);
    return {};
  }
}
