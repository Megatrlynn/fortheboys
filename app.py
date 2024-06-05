from flask import Flask, request
import mysql.connector
import os

app = Flask(__name__)
PORT = int(os.getenv("PORT", 3000))

# Create a connection to the MySQL database
db = mysql.connector.connect(
    host="bmwnqwmtaqw5xp1cwaty-mysql.services.clever-cloud.com",
    user="uvqpshad4m6dgq9v",
    password="LAoMxm0l0mrzxu4sJGuk",  # Replace with your MySQL password
    database="bmwnqwmtaqw5xp1cwaty"
)

# In-memory storage for user data (for simplicity)
voters = set()  # Set to track phone numbers that have already voted
user_languages = {}  # Dictionary to store the language preference of each user

@app.route('/ussd', methods=['POST'])
def ussd():
    response = ''
    session_id = request.form.get('sessionId')
    service_code = request.form.get('serviceCode')
    phone_number = request.form.get('phoneNumber')
    text = request.form.get('text')

    user_input = text.split('*')

    if len(user_input) == 1 and user_input[0] == '':
        # First level menu: Language selection
        response = 'CON Welcome to Mayor voting booth\n1. English\n2. Swahili'
    elif len(user_input) == 1 and user_input[0] != '':
        # Save user's language choice and move to the main menu
        user_languages[phone_number] = 'en' if user_input[0] == '1' else 'sw'
        response = 'CON Choose an option:\n1. Vote Candidate\n2. View Votes' if user_languages[phone_number] == 'en' else 'CON Chagua chaguo:\n1. Piga kura\n2. Tazama kura'
    elif len(user_input) == 2:
        if user_input[1] == '1':
            # Check if the phone number has already voted
            if phone_number in voters:
                response = 'END You have already voted. Thank you!' if user_languages[phone_number] == 'en' else 'END Tayari umeshapiga kura. Asante!'
            else:
                # Voting option selected
                response = 'CON Select a candidate:\n1. Raymond IGABINEZA\n2. Florence UMUTONIWASE\n3. Jean Paul KWIBUKA\n4. Gaella UWAYO\n5. Danny HABIMANA' if user_languages[phone_number] == 'en' else 'CON Chagua mgombea:\n1. Raymond IGABINEZA\n2. Florence UMUTONIWASE\n3. Jean Paul KWIBUKA\n4. Gaella UWAYO\n5. Danny HABIMANA'
        elif user_input[1] == '2':
            # View votes option selected
            cursor = db.cursor(dictionary=True)
            cursor.execute('SELECT voted_candidate, COUNT(*) as count FROM votes WHERE voted_candidate != "Viewed Votes" GROUP BY voted_candidate')
            results = cursor.fetchall()
            response = 'END Votes:\n' if user_languages[phone_number] == 'en' else 'END Kura:\n'
            for row in results:
                response += f'{row["voted_candidate"]}: {row["count"]} votes\n'
            cursor.close()

            # Insert view votes record into the database
            cursor = db.cursor()
            view_vote_data = (session_id, phone_number, user_languages[phone_number], 'Viewed Votes')
            insert_query = 'INSERT INTO votes (session_id, phone_number, language_used, voted_candidate) VALUES (%s, %s, %s, %s)'
            cursor.execute(insert_query, view_vote_data)
            db.commit()
            cursor.close()
    elif len(user_input) == 3:
        # Voting confirmation
        candidate_index = int(user_input[2]) - 1
        candidate_names = ["Raymond I. ", "Florence U. ", "Jean Paul K. ", "Gaella U. ", "Danny H. "]
        if 0 <= candidate_index < len(candidate_names):
            voters.add(phone_number)  # Mark this phone number as having voted
            response = f'END Thank you for voting for {candidate_names[candidate_index]}!' if user_languages[phone_number] == 'en' else f'END Asante kwa kumpigia kura {candidate_names[candidate_index]}!'

            # Insert voting record into the database
            cursor = db.cursor()
            vote_data = (session_id, phone_number, user_languages[phone_number], candidate_names[candidate_index])
            insert_query = 'INSERT INTO votes (session_id, phone_number, language_used, voted_candidate) VALUES (%s, %s, %s, %s)'
            cursor.execute(insert_query, vote_data)
            db.commit()
            cursor.close()
        else:
            response = 'END Invalid selection. Please try again.' if user_languages[phone_number] == 'en' else 'END Uchaguzi batili. Tafadhali jaribu tena.'

    return response

if __name__ == '__main__':
    app.run(port=PORT)
