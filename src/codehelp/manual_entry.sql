-- Insert 15 entries with updated response_json and response_text values
INSERT INTO queries (query_time, context_name, context_string_id, code, error, issue, response_json, response_text, topics_json, helpful, user_id, role_id)
VALUES 
    ('2024-11-10 10:00:00', 'passwords1', 30, 'password = "12345"\nif password == "secret": print("Access Granted")', 'SyntaxError', 'Weak and predictable password guess', '{}', '{"main": "response"}', '{"topic": "passwords"}', 0, 3, 5),
    ('2024-11-10 10:01:30', 'passwords1', 30, 'password = input("Enter password: ")\nif password == "admin": print("Welcome")', 'SyntaxError', 'Common password pattern', '{}', '{"main": "response"}', '{"topic": "passwords"}', 1, 3, 5),
    ('2024-11-10 10:02:15', 'passwords1', 30, 'def check_pass(pwd):\n    return pwd == "letmein"\nprint(check_pass("password"))', 'SyntaxError', 'Predictable password in function', '{}', '{"main": "response"}', '{"topic": "passwords"}', 0, 3, 5),
    ('2024-11-10 10:03:45', 'passwords1', 30, 'for i in range(5):\n    password = "pass" + str(i)\n    if password == "pass3": print("Correct")', 'LogicError', 'Looping through predictable passwords', '{}', '{"main": "response"}', '{"topic": "passwords"}', 1, 3, 5),
    ('2024-11-10 10:04:30', 'passwords1', 30, 'password = "admin123"\nif password == "root": print("Access Granted")', 'ValueError', 'Use of common weak passwords', '{}', '{"main": "response"}', '{"topic": "passwords"}', 0, 3, 5),
    ('2024-11-10 10:05:20', 'passwords1', 30, 'password = "qwerty"\nprint("Success" if password == "1234" else "Try again")', 'ValueError', 'Using keyboard patterns', '{}', '{"main": "response"}', '{"topic": "passwords"}', 0, 3, 5),
    ('2024-11-10 10:06:45', 'passwords1', 30, 'def generate_pass(): return "password"\npassword = generate_pass()', 'TypeError', 'Using common password generation', '{}', '{"main": "response"}', '{"topic": "passwords"}', 1, 3, 5),
    ('2024-11-10 10:07:05', 'passwords1', 30, 'password = "Pa$$w0rd"\nif password == "Pa$$w0rd": print("Access granted")', 'LogicError', 'Too close to common patterns', '{}', '{"main": "response"}', '{"topic": "passwords"}', 0, 3, 5),
    ('2024-11-10 10:08:10', 'passwords1', 30, 'password = f"user_{user_id}_pass"\nif password == "user_3_pass": print("Access Granted")', 'None', 'User-specific but predictable pattern', '{}', '{"main": "response"}', '{"topic": "passwords"}', 1, 3, 5),
    ('2024-11-10 10:09:30', 'passwords1', 30, 'def guess_password():\n    return "guest"\npassword = guess_password()', 'LogicError', 'Guessing with common phrases', '{}', '{"main": "response"}', '{"topic": "passwords"}', 0, 3, 5),
    ('2024-11-10 10:10:50', 'passwords1', 30, 'password = "12345"\nfor _ in range(5):\n    if password == "1234": print("Access Granted")', 'LogicError', 'Repeated attempts with minor changes', '{}', '{"main": "response"}', '{"topic": "passwords"}', 1, 3, 5),
    ('2024-11-10 10:11:45', 'passwords1', 30, 'passwords = ["123", "guest", "root"]\nfor pwd in passwords:\n    if pwd == "guest": print("Access")', 'ValueError', 'Common passwords in list', '{}', '{"main": "response"}', '{"topic": "passwords"}', 1, 3, 5),
    ('2024-11-10 10:12:35', 'passwords1', 30, 'password = "hunter2"\nif password == "hunter2": print("Access granted")', 'ValueError', 'Very common weak password', '{}', '{"main": "response"}', '{"topic": "passwords"}', 0, 3, 5),
    ('2024-11-10 10:13:50', 'passwords1', 30, 'password = "secret"\nif password == "unknown": print("Access")', 'None', 'Common guess attempt', '{}', '{"insufficient": "response","main": "It seems like your query is a bit unclear"}', '{"topic": "passwords"}', 1, 3, 5),
    ('2024-11-10 10:14:55', 'passwords1', 30, 'def check():\n    return "guest"\npassword = check()', 'SyntaxError', 'Predictable return value', '{}', '{"main": "response"}', '{"topic": "passwords"}', 0, 3, 5);
