# CourtGo

A sports court booking application built with Python, FastAPI, MySQL, SQLAlchemy, and Streamlit.

## Features

### User Registration

- Registration collects first name, last name, email, and password.
- The backend validates email format and password length.
- Each email address can belong to only one account.
- Passwords are hashed using Argon2 before being stored.
- New accounts automatically receive the `customer` role.

### Login and Authentication

- Access tokens expire after 30 minutes.
- Protected requests send the token in the Authorization header.
- Invalid or expired tokens require the user to log in again.

### Customer and Admin Permissions

The application supports two roles.

Customers can:

- Browse courts and view court details.
- View generated court slots.
- Book available future slots.
- View their own booking history.
- Cancel their own future bookings.
- Reschedule their own future bookings.

Admins can:

- Perform the same booking actions as customers.
- Create, edit, and delete eligible courts.
- Generate court slots.
- Block and unblock slots for maintenance.
- View all customer bookings.
- Cancel and reschedule future bookings for any customer.

Permissions are checked in FastAPI for every protected request.
The UI also hides administrative controls from customers and visitors.

### Court Management

- Admins can create courts with a name, sport type, hourly price, and optional description.
- Supported sports are badminton, tennis, and football.
- Visitors and registered users can browse courts.
- Admins can update selected court fields using PATCH requests.
- Fields omitted from an update retain their existing values.
- Courts without dependent records can be deleted.
- Deleting a court with generated slots returns a clear conflict response.

### Court Slot Generation

- Admins can generate slots for a selected court and date.
- Each slot lasts one hour.
- The current opening hours are fixed at 08:00–22:00.
- A complete future day contains 14 slots.
- Slots can be generated from today through 30 days ahead.
- Slots that have already started are skipped.
- Repeating generation skips existing slots.
- A database constraint prevents duplicate starting times for the same court.

### Slot Browsing and Status

- Users select a court and date to view its slots.
- Slots appear in chronological order.
- The table displays the slot ID, start time, end time, and status.
- Status labels include Available, Booked, Maintenance, and Past.
- The booking selector includes future slots that are unblocked and have no active reservation.
- Changing the court or date reloads the slot list.
- The backend rechecks availability when a booking is submitted.

### Timezone Handling

- The sports centre uses the Europe/Berlin timezone.
- Slot generation interprets opening hours in the centre's local timezone.
- Slot timestamps are converted to UTC before database storage.
- Stored timezone-free timestamps are consistently treated as UTC.
- API responses identify slot timestamps as UTC.
- Streamlit converts timestamps to Europe/Berlin for display.
- Date filtering converts local day boundaries to UTC.

### Appointment Booking

- Logged-in users can reserve one court slot per booking.
- Bookings start with a `confirmed` status.
- Past, blocked, and out-of-window slots are rejected.
- Inactive courts cannot receive bookings.
- Successful booking refreshes the UI page and displays a confirmation message.

### Booking Conflict Prevention

- Each slot can have only one active reservation.
- Each booking can hold only one active reservation.
- A customer cannot reserve multiple courts with the same start time.
- Database uniqueness constraints enforce these rules.
- The booking endpoint locks relevant records while saving.
- Booking and reservation records are saved in one transaction.
- A reservation conflict rolls back the attempted booking.

### Booking History

- Customers can view their own confirmed and cancelled bookings.
- Admins can view bookings for all customers.
- The list displays the booking ID, court name, date, start time, end time, booked price, and status.
- Cancelled bookings remain available in history.

### Booking Cancellation

- Customers can cancel their own future bookings.
- Admins can cancel any customer's future booking.

### Booking Rescheduling

- Customers can move their own confirmed future bookings.
- Admins can reschedule confirmed future bookings for any customer.
- Users can move a booking to another court.
- The active reservation moves to the new slot and old slot becomes available again.
- The backend rejects blocked, occupied, past, or out-of-window destination slots.
- Cancelled bookings and bookings that have started cannot be moved.

### Maintenance Blocking

- Admins can block unbooked slots for maintenance.
- Admins can unblock slots when maintenance finishes.

### Validation and Error Handling

- Pydantic schemas validate API request data.
- Invalid input receives a 422 response.
- Missing or invalid authentication receives a 401 response.
- Insufficient permissions receive a 403 response.
- Missing records receive a 404 response.
- Booking and deletion conflicts receive a 409 response.
- Streamlit displays request failures and connection errors.
- Protected frontend requests clear the login session when the backend returns 401.
- Database transactions roll back failed booking operations.

## Current Scope

- One sports centre.
- Three supported sport types.
- Fixed one-hour slots.
- Fixed opening hours of 08:00–22:00.
- One court slot per booking.
- Customer and admin roles.
- A 30-day booking window.
- Payments, email notifications, recurring bookings, configurable opening hours, pagination, and reporting dashboards are future enhancements.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create the MySQL database used by the application.
4. Copy `.env.example` to `.env` and enter the database credentials.
5. Generate a JWT secret and add it to `.env`:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
## Run the backend

From `backend/app`:

```powershell
python -m uvicorn main:app --reload
```

Swagger UI is available at http://127.0.0.1:8000/docs.

The application creates missing tables during startup.

## Run the frontend

Open a second terminal, activate the same virtual environment, and run from the project root:

```powershell
python -m streamlit run frontend/app.py
```

## Create a local admin

Register an account, then update its role in MySQL:

```sql
UPDATE users
SET role = 'admin'
WHERE email = 'your_registered_email@example.com';
```
