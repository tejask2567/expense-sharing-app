import requests

# First, login to get the token
login_response = requests.post('http://localhost:5000/login', json={
    'email': 'john@example.com',#add user details
    'password': 'SecurePass123!'
})
token = login_response.json()['access_token']

# Add an expense
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

expense_data = {
    "description": "Team Lunch",
    "amount": 150.00,
    "split_type": "equal",
    "participants": [
        {"user_id": 1},  
        {"user_id": 2},  
    ]
}
expense_data_exact = {
    "description": "Team Lunch",
    "amount": 150.00,
    "split_type": "equal",
    "participants": [
        {"user_id": 1},  
        {"user_id": 2}, 
    ]
}
expense_data_percentage =  {
                "description": "Party",
                "amount": 10000,
                "split_type": "percentage",
                "participants": [
                  {"user_id": 1, "share_percentage": 55},
                  {"user_id": 2, "share_percentage": 45}
                ]
              }
response = requests.post(
    'http://localhost:5000/expense',
    json=expense_data,
    headers=headers
)

print(response.json())