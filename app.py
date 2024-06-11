from flask import Flask, request
import mysql.connector
import os

app = Flask(__name__)
PORT = int(os.getenv("PORT", 3000))

# Connection to the MySQL database
db = mysql.connector.connect(
    host="bvvcotes65k17jl2qy0e-mysql.services.clever-cloud.com",
    user="uoefpdurpcydbpmq",
    password="6ecbpoolmcSW08SVZ1oO",
    database="bvvcotes65k17jl2qy0e"
)

# In-memory storage for user data
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
        response = 'CON Guild Voting Campaign\n1. English\n2. Swahili\n3. Kinyarwanda\n4. French'
    elif len(user_input) == 1 and user_input[0] != '':
        language_choice = user_input[0]
        if language_choice == '1':
            user_languages[phone_number] = 'en'
        elif language_choice == '2':
            user_languages[phone_number] = 'sw'
        elif language_choice == '3':
            user_languages[phone_number] = 'rw'
        elif language_choice == '4':
            user_languages[phone_number] = 'fr'

        if user_languages[phone_number] == 'en':
            response = 'CON Choose an option:\n1. Vote Candidate\n2. View Votes'
        elif user_languages[phone_number] == 'sw':
            response = 'CON Chagua chaguo:\n1. Piga kura\n2. Tazama kura'
        elif user_languages[phone_number] == 'rw':
            response = 'CON Hitamo umwanzuro:\n1. Tora umukandida\n2. Reba amajwi'
        elif user_languages[phone_number] == 'fr':
            response = 'CON Choisissez une option:\n1. Voter pour un candidat\n2. Voir les votes'
    elif len(user_input) == 2:
        if user_input[1] == '1':
            # Check if the phone number has already voted in the database
            cursor = db.cursor()
            query = 'SELECT COUNT(*) FROM votes WHERE phone_number = %s'
            cursor.execute(query, (phone_number,))
            vote_count = cursor.fetchone()[0]
            cursor.close()

            if vote_count > 0:
                if user_languages[phone_number] == 'en':
                    response = 'END You have already voted. Thank you!'
                elif user_languages[phone_number] == 'sw':
                    response = 'END Tayari umeshapiga kura. Asante!'
                elif user_languages[phone_number] == 'rw':
                    response = 'END Wamaze gutora. Murakoze!'
                elif user_languages[phone_number] == 'fr':
                    response = 'END Vous avez déjà voté. Merci!'
            else:
                # Fetch candidates from the database
                cursor = db.cursor()
                cursor.execute('SELECT cand_id, cand_name FROM candidates')
                candidates = cursor.fetchall()
                cursor.close()

                if user_languages[phone_number] == 'en':
                    response = 'CON Select a candidate:\n'
                elif user_languages[phone_number] == 'sw':
                    response = 'CON Chagua mgombea:\n'
                elif user_languages[phone_number] == 'rw':
                    response = 'CON Hitamo umukandida:\n'
                elif user_languages[phone_number] == 'fr':
                    response = 'CON Choisissez un candidat:\n'

                for candidate in candidates:
                    response += f'{candidate[0]}. {candidate[1]}\n'
        elif user_input[1] == '2':
            cursor = db.cursor(dictionary=True)
            cursor.execute('SELECT voted_candidate, COUNT(*) as count FROM votes GROUP BY voted_candidate')
            results = cursor.fetchall()
            cursor.close()

            if user_languages[phone_number] == 'en':
                response = 'END Votes:\n'
            elif user_languages[phone_number] == 'sw':
                response = 'END Kura:\n'
            elif user_languages[phone_number] == 'rw':
                response = 'END Amajwi:\n'
            elif user_languages[phone_number] == 'fr':
                response = 'END Votes:\n'
            for row in results:
                response += f'{row["voted_candidate"]}: {row["count"]} votes\n'

            cursor = db.cursor()
            view_vote_data = (session_id, phone_number, user_languages[phone_number], 'Viewed Votes')
            insert_query = 'INSERT INTO view_votes (session_id, phone_number, language_used, view_candidate) VALUES (%s, %s, %s, %s)'
            cursor.execute(insert_query, view_vote_data)
            db.commit()
            cursor.close()
    elif len(user_input) == 3:
        candidate_index = int(user_input[2])
        cursor = db.cursor()
        cursor.execute('SELECT cand_name FROM candidates WHERE cand_id = %s', (candidate_index,))
        candidate_name_result = cursor.fetchone()
        cursor.close()

        if candidate_name_result:
            candidate_name = candidate_name_result[0]
            # Mark this phone number as having voted and insert the record into the database
            cursor = db.cursor()
            vote_data = (session_id, phone_number, user_languages[phone_number], candidate_name)
            insert_query = 'INSERT INTO votes (session_id, phone_number, language_used, voted_candidate) VALUES (%s, %s, %s, %s)'
            cursor.execute(insert_query, vote_data)
            db.commit()
            cursor.close()

            if user_languages[phone_number] == 'en':
                response = f'END Thank you for voting for {candidate_name}!'
            elif user_languages[phone_number] == 'sw':
                response = f'END Asante kwa kumpigia kura {candidate_name}!'
            elif user_languages[phone_number] == 'rw':
                response = f'END Murakoze gutora {candidate_name}!'
            elif user_languages[phone_number] == 'fr':
                response = f'END Merci d\'avoir voté pour {candidate_name}!'
        else:
            if user_languages[phone_number] == 'en':
                response = 'END Invalid selection. Please try again.'
            elif user_languages[phone_number] == 'sw':
                response = 'END Uchaguzi batili. Tafadhali jaribu tena.'
            elif user_languages[phone_number] == 'rw':
                response = 'END Ibyo uhisemo sibyo. Ongera ugerageze.'
            elif user_languages[phone_number] == 'fr':
                response = 'END Sélection invalide. Veuillez réessayer.'

    return response

if __name__ == '__main__':
    app.run(port=PORT)
