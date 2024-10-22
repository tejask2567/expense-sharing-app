# Expense Sharing Application

A Flask-based web application for managing and splitting expenses among users. This application allows users to create expenses, split them among participants using different splitting methods (equal, exact, or percentage), and track balances with other users.

## Features

- User authentication with JWT tokens
- Create and manage expenses
- Multiple expense splitting options:
  - Equal split
  - Exact amount split
  - Percentage-based split
- View expense history
- Download expense reports as CSV
- Search for users
- View recent contacts
- Track balances with other users
- Secure password management

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd expense-sharing-app
```

2. Create a virtual environment:
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Configuration

The application uses SQLite as its database and automatically creates the database file when first run. The database will be created as `expense_sharing.db` in the application directory.

Environment variables:
- No additional environment variables are required as the application uses secure random keys generated at runtime

## Running the Application

1. Ensure you're in the project directory and your virtual environment is activated

2. Run the application:
```bash
python run.py
```

The application will start and be available at `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /login` - Login and receive JWT token
- `POST /logout` - Logout and invalidate token

### Expenses
- `POST /expense` - Create a new expense
- `GET /expenses/user` - Get user's expenses
- `GET /balance-sheet/download` - Download expense report as CSV

### Users
- `GET /user` - Get current user's details
- `PUT /user` - Update user details
- `PUT /user/change-password` - Change password
- `GET /users/search` - Search for users
- `GET /users/recent-contacts` - Get recent contacts
- `GET /user/balance` - Get balance with other users

## Security Features

- Password hashing using bcrypt
- JWT-based authentication
- Password strength validation
- Input validation and sanitization
- Token blacklisting for logout
- Session management

## Error Handling

The application includes comprehensive error handling for:
- Invalid input data
- Authentication failures
- Database errors
- Duplicate user registration
- Invalid expense splits

## Database Schema

The application uses SQLAlchemy ORM with the following main models:
- User
- Expense
- ExpenseParticipant

---