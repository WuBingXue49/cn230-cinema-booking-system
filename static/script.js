const app = document.getElementById("app");

let currentUser = {
  name: "Customer",
  role: "customer"
};

let showtimes = [];
let movies = [];
let selectedSeats = [];
let currentPending = 0;

window.onload = async () => {
  console.log("ONLOAD FIRED");

  await loadShowtimes();

  renderLogin();
};

function login() {
  const userId = document.getElementById("userId").value;

  fetch(`/users/${userId}`)
    .then(res => res.json())
    .then(async data => {
      currentUser = data.data;
    
      console.log("LOGIN USER =", currentUser);
    
      if (!currentUser.user_id) {
        alert("User ID missing!");
        return;
      }
    
      render();
    })
    .catch(err => console.error(err));
}

function loginAsAdmin() {
    currentUser = { name: "Admin", role: "admin" };
    render();
  }
  
  function loginAsCustomer() {
    currentUser = { name: "Customer", role: "customer" };
    render();
}

function renderLogin() {
  app.innerHTML = `
    <h2>Login</h2>

    <input id="userId" placeholder="User ID (1-5)" />
    <button onclick="login()">Login</button>

    <br><br>
    <button onclick="quickLogin('customer')">Customer</button>
    <button onclick="quickLogin('staff')">Staff</button>
    <button onclick="quickLogin('admin')">Admin</button>
    <button onclick="quickLogin('producer')">Producer</button>
  `;
}

function quickLogin(role) {
  currentUser = {
    user_id: role === "admin" ? 4 :
              role === "staff" ? 5 :
              role === "producer" ? 6 :
              1,
    name: role,
    role: role
  };

  render();
}

async function render() {
  if (currentUser.role === "customer") {
    await renderCustomer();
  } else if (currentUser.role === "staff") {
    renderStaff();
  } else if (currentUser.role === "admin") {
    await renderAdmin();
  } else if (currentUser.role === "producer") {
    renderProducer();
  }
}

async function renderAdmin() {
  let revenue = [];

  try {
    revenue = await loadRevenue();
  } catch (err) {
    console.error("Revenue error:", err);
  }

  const userBox = await renderUserInfo();

  app.innerHTML = `
    ${userBox}
    <h2>Admin Dashboard</h2>
    <button onclick="logout()">Logout</button>

    <h3>💰 Movie Revenue</h3>

    ${
      revenue && revenue.length > 0
        ? revenue.map(r => `
          <div class="card">
            🎬 ${r.title}
            <br>
            Revenue: ${r.total_revenue}
          </div>
        `).join("")
        : `<p>No revenue data</p>`
    }
  `;
}

async function renderCustomer() {
  let topMovie = null;
  let pendingInfo = null;

  try {
    topMovie = await loadTopMovie();
  } catch (e) {
    console.error("topMovie error", e);
  }

  try {
    if (currentUser.role === "customer") {
      pendingInfo = await loadPending(currentUser.user_id);
    }
  } catch (e) {
    console.error("pending error", e);
  }

  const userBox = renderUserInfo(pendingInfo);

  app.innerHTML = `
    ${userBox}

    <h2>Showtimes</h2>
    <button onclick="logout()">Logout</button>

    <h3>🔥 Top Movie</h3>
    ${topMovie ? `
      <div class="card">
        <div style="width:100px;height:150px;background:#ccc;"></div>
        <p><b>${topMovie.title}</b></p>
      </div>
    ` : ""}

    <h3>All Showtimes</h3>

    ${showtimes.map(s => {
      const hasSeats = s.seats && s.seats.trim() !== "";

      return `
        <div class="card">
          <h3>${s.title}</h3>
          <p>🏢 Theater: ${s.theater_name}</p>
          <p>💰 Price: ${s.price}</p>
          <p>📅 Date: ${new Date(s.show_date).toLocaleDateString()}</p>
          <p>💺 Seats: ${hasSeats ? s.seats : "FULL"}</p>

          ${
            hasSeats
              ? `<button onclick="book(${s.showtime_id})">Book</button>`
              : `<p style="color:red;">Fully booked</p>`
          }
        </div>
      `;
    }).join("")}
  `;
}

async function renderStaff() {
  const userBox = await renderUserInfo();

  app.innerHTML = `
    ${userBox}
    <h2>Staff Page</h2>
    <button onclick="logout()">Logout</button>

    <p>Check booking status</p>
  `;
}

async function renderProducer() {
  const userBox = await renderUserInfo();

  app.innerHTML = `
    ${userBox}
    <h2>Producer Page</h2>
    <button onclick="logout()">Logout</button>

    <p>Add new movies</p>
  `;
}

function logout() {
  currentUser = { name: "", role: "" }; // หรือ customer ก็ได้
  renderLogin();
}

function book(showtimeId) {
  const s = showtimes.find(st => st.showtime_id === showtimeId);
  const seats = s.seats.split(",");

  selectedSeats = []; // 🔥 reset ทุกครั้ง

  app.innerHTML = `
    <h2>Book: ${s.title}</h2>

    <h3>Select Seats</h3>

    ${seats.map(seat => `
      <button id="seat-${seat.trim()}"
        onclick="toggleSeat('${seat.trim()}')">
        Seat ${seat}
      </button>
    `).join("")}

    <br><br>
    <button onclick="confirmBooking(${showtimeId})">
      ✅ Confirm Booking
    </button>

    <br><br>
    <button onclick="render()">⬅ Back</button>
  `;
}

function toggleSeat(seat) {
  if (selectedSeats.includes(seat)) {
    // ❌ เอาออก
    selectedSeats = selectedSeats.filter(s => s !== seat);
    document.getElementById(`seat-${seat}`).style.background = "";
  } else {
    // ✅ เพิ่ม
    selectedSeats.push(seat);
    document.getElementById(`seat-${seat}`).style.background = "lightgreen";
  }

  console.log("Selected:", selectedSeats);
}

function confirmBooking(showtimeId) {
  if (selectedSeats.length === 0) {
    alert("Please select at least 1 seat");
    return;
  }

  console.log("BOOKING SEND:", {
    user_id: currentUser.user_id,
    showtime_id: showtimeId,
    seats: selectedSeats
  });

  fetch("/book", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: currentUser.user_id,
      showtime_id: showtimeId,
      seats: selectedSeats
    })
  })
  .then(res => res.json())
  .then(async data => {
    console.log("BOOK RESPONSE:", data);

    alert(`Booked seats: ${selectedSeats.join(", ")}`);

    selectedSeats = [];

    await loadShowtimes();
    await loadPending(currentUser.user_id);

    render();
  })
  .catch(err => {
    console.error("BOOK ERROR:", err);
    alert("Booking failed (check console)");
  });
}

async function loadShowtimes() {
  try {
    console.log("FETCH START");

    const res = await fetch("/showtimes");

    console.log("FETCH DONE");

    const result = await res.json();

    showtimes = result.data;

    console.log("DATA =", showtimes);

  } catch (err) {
    console.error("ERROR:", err);
  }
}

async function loadMovies() {
  try {
    const res = await fetch("/movies");
    const result = await res.json();

    movies = result.data;

    console.log("MOVIES =", movies);
  } catch (err) {
    console.error(err);
  }
}

async function viewSeats(title) {
  const res = await fetch(`/movies/${title}/seats`);
  const result = await res.json();

  const showtimes = result.data;

  app.innerHTML = `
    <h2>Seats for ${title}</h2>
    <button onclick="render()">⬅ Back</button>

    ${showtimes.map(s => `
      <div class="card">
        <p>🏢 ${s.theater_name}</p>
        <p>💺 ${s.seats || "FULL"}</p>
      </div>
    `).join("")}
  `;
}

async function loadTopMovie() {
  try {
    const res = await fetch("/movies/top");
    const result = await res.json();

    return result.data; // movie เดียว
  } catch (err) {
    console.error(err);
  }
}

async function loadRevenue() {
  try {
    const res = await fetch("/movies/revenue");
    const result = await res.json();

    return result.data;
  } catch (err) {
    console.error(err);
  }
}

function renderUserInfo(pendingInfo) {
  if (!currentUser || !currentUser.role) return "";
  const total = Number(pendingInfo?.total_pending ?? currentPending ?? 0);

  return `
    <div style="
      position: fixed;
      top: 10px;
      right: 10px;
      background: white;
      color: ${pendingInfo?.total_pending > 0 ? "red" : "lightgreen"};
      padding: 10px;
      border-radius: 8px;
      width: 200px;
    ">
      👤 ${currentUser.name}<br>
      🆔 ID: ${currentUser.user_id}<br>
      🎭 Role: ${currentUser.role}

      ${
        currentUser.role === "customer"
          ? `<hr>💸 Total Due: ${total}`
          : ""
      }
    </div>
  `;
}

async function loadPending(userId) {
  const res = await fetch(`/users/${userId}/pending`);
  const data = await res.json();

  currentPending = data.data?.total_pending || 0;

  return data.data;
}
