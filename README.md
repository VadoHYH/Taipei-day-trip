# Taipei Day Trip

An e-commerce travel website for exploring tourist attractions in Taipei and booking sightseeing trips.  
Built with FastAPI and vanilla JavaScript as a full-stack project for the WeHelp Bootcamp.

### Demo: [http://13.239.58.95:8000/](http://13.239.58.95:8000/)

Test Account:  
Username : 123@123.com  
password : 123

---

![demo](https://github.com/VadoHYH/Taipei-day-trip/blob/main/images/HomePage.png)

## Technique Overview

### Frontend

- HTML / CSS / JavaScript (Vanilla JS)
- AJAX (Fetch API)
- Responsive Web Design (RWD)
- SVG Icons

### Backend

- Framework: FastAPI (Python)
- Database: MySQL
- Authentication: JWT (access token stored in HTTP-only cookie)
- Payment: TapPay SDK (TWD currency)

---

## Project Highlights

### Search for attractions
Search by keyword or MRT station, with pagination and image carousel.

![Search](https://github.com/VadoHYH/Taipei-day-trip/blob/main/images/Search.gif)

---

### Booking system
Select date and time to reserve a tour. Bookings are available only after login.

![Booking](https://github.com/VadoHYH/Taipei-day-trip/blob/main/images/Booking.gif)

---

### Payment with TapPay
Users can fill in card info and complete the order. Order info is saved in the backend and viewable after checkout.

![Payment](https://github.com/VadoHYH/Taipei-day-trip/blob/main/images/Payment.gif)

---

### User system
Supports sign-up, login, logout, and session management with JWT. Member-specific content like bookings and orders is protected.

---

## Project Architecture

![Architecture](https://github.com/VadoHYH/Taipei-day-trip/blob/main/images/Architecture.png)

- Frontend: Static website built with HTML/CSS/JavaScript and deployed via GitHub Pages
- Backend: RESTful API built with FastAPI and deployed on AWS EC2
- Database: MySQL, used to store attractions, bookings, members, and orders
- Authentication: JWT (stored in HTTP-only cookies) for secure session management
- Payment: Integrated with TapPay, using client-side SDK to retrieve Prime and server-side API to complete the transaction

---

## API & Database

- RESTful API design with clear separation of concerns
- Booking & order APIs require authentication
- JWT is used to keep user login persistent and secure
- MySQL schema includes tables for: `attractions`, `users`, `bookings`, `orders`

---

## Development Tools

- VSCode
- Chrome DevTools (for layout, JS, network debugging)
- Git + GitHub (version control & deployment)
- GitHub Pages (frontend hosting)
- AWS EC2 (backend deployment)
- Uvicorn (ASGI server for FastAPI)

---

## About This Project

This project was built during Phase 2 of the WeHelp Bootcamp to practice full-stack development, including RESTful API design, authentication, database integration, payment processing, and responsive front-end design.

## Contact

**謝曜徽 Vado Hsieh**
* Frontend Developer (Taiwan)
* Email: [vado.hyh@gmail.com](mailto:vado.hyh@gmail.com)