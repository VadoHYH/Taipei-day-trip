# Taipei Day Trip

[Live Demo](http://13.239.58.95:8000/)

Test Account
Username : 123@123.com
password : 123

An e-commerce travel website for exploring tourist attractions in Taipei and booking sightseeing trips.  
Built with Flask and vanilla JavaScript as a full-stack project for the WeHelp Bootcamp.

---

![demo](https://github.com/VadoHYH/Taipei-day-trip/blob/main/images/HomePage.png) <!-- Optional: Replace with your own screenshot -->

## 🔧 Technique Overview

### Frontend

- HTML / CSS / JavaScript (Vanilla JS)
- AJAX (Fetch API)
- Responsive Web Design (RWD)
- SVG Icons

### Backend

- Framework: Flask (Python)
- Database: MySQL
- Authentication: JWT (access token stored in HTTP-only cookie)
- Payment: TapPay SDK (TWD currency)

---

## 📌 Project Highlights

### 🔍 Search for attractions
Search by keyword or MRT station, with pagination and image carousel.

![Search](https://github.com/VadoHYH/Taipei-day-trip/blob/main/images/Search.gif)

---

### 📅 Booking system
Select date and time to reserve a tour. Bookings are available only after login.

![Booking](https://github.com/VadoHYH/Taipei-day-trip/blob/main/images/Booking.gif)

---

### 💳 Payment with TapPay
Users can fill in card info and complete the order. Order info is saved in the backend and viewable after checkout.

![Payment](https://github.com/VadoHYH/Taipei-day-trip/blob/main/images/Payment.gif)

---

### 👤 User system
Supports sign-up, login, logout, and session management with JWT. Member-specific content like bookings and orders is protected.

---

## 🧱 Project Architecture

![Architecture](https://github.com/VadoHYH/Taipei-day-trip/blob/main/images/architecture.png) <!-- Optional -->

- Frontend: Static files deployed on GitHub Pages
- Backend: Flask API deployed via Render (or EC2/Railway)
- MySQL stores attractions, bookings, members, and orders
- TapPay processes payments via client-side SDK and server-side API

---

## 🗃️ API & Database

- RESTful API design with clear separation of concerns
- Booking & order APIs require authentication
- JWT is used to keep user login persistent and secure
- MySQL schema includes tables for: `attractions`, `users`, `bookings`, `orders`

---

## 🧪 Development Tools

- VSCode
- Chrome DevTools (for layout, JS, network debugging)
- Thunder Client / Postman (for API testing)
- Git + GitHub (version control & deployment)
- GitHub Pages (frontend hosting)

---

## 📝 About This Project

This project was built during Phase 2 of the WeHelp Bootcamp to practice full-stack development, including RESTful API design, authentication, database integration, payment processing, and responsive front-end design — without using modern frameworks like React.

