import telebot
from telebot import types
import datetime
import sqlite3
import os
from threading import Thread
from time import sleep

# Initialize bot with your token
TOKEN = '7858944157:AAEIlndo9M4dwdrZFvBdRYCLUp06BcxnMzI'  # Replace with your actual bot token
bot = telebot.TeleBot(TOKEN)

# Admin ID (replace with your actual admin Telegram ID)
ADMIN_ID = '5112046216'  # Example admin ID

# Database setup
def init_db():
    conn = sqlite3.connect('matmie24_bot.db', check_same_thread=False)
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        student_id TEXT,
        group_name TEXT DEFAULT 'MATMIE24'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS deadlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        homework TEXT,
        deadline TEXT,
        notified INTEGER DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        feedback_text TEXT,
        timestamp TEXT
    )
    ''')

    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# Sample schedule data (replace with your actual schedule)
SCHEDULE = {
    'Monday': [
        '09:00-11:25 - Calculus 2 \n (Room B202)',
        '11:30-12:55 - English/French/German \n (Room B201,B202,B210)',
    ],
    'Tuesday': [
        '09:00-10:40 - Physical Education \n (Sport Hall)',
        '10:45-12:55 - Discrete math (Room B202)'
    ],
    'Wednesday': [
        '09:00-10:40 - Russian language \n (B205)',
        '10:45-12:55 - Programming language 2 \n (B213)'
    ],
    'Thursday': [
        '09:00-10:40 - English/French/German \n (Room B201,B202,B210)',
        '10:45-12:55 - Programming language 2 \n (B213)'
        '13:00-13:45 - LUNCH'
        '13:45-15:55 - Calculus 2 \n (Room B103)',
    ],
    'Friday': [
        '09:00-10:40 - Russian language \n (B205)',
        '10:45-12:55 - Discrete math \n (Room B202)'
        '13:00-14:25 - LUNCH'
        '14:30-17:25 - Computer Literacy \n (Room B210)'
    ],
    'Saturday': ['No classes'],
    'Sunday': ['No classes']
}

# Sample books data (replace with actual PDFs or links)
BOOKS = {
    'Calculus 2': 'books/calculus.pdf',
    'Discrete Mathematics': 'books/discretemath.pdf',
    'German': 'books/Netzwerk.pdf' ,
    'Russian language': 'books/Russianlg.pdf',
    'English': 'books/English.pdf' ,
    'French': 'books/French.pdf' ,
}

# Create books directory if it doesn't exist
if not os.path.exists('books'):
    os.makedirs('books')

# User states for handling different interactions
user_states = {}

# ======================
# BOT COMMAND HANDLERS
# ======================

@bot.message_handler(commands=['start'])
def start(message):
    """Handle the /start command to register new users or show menu for existing ones"""
    user_id = message.from_user.id
    
    # Check if user already exists
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user:
        show_main_menu(message)
    else:
        msg = bot.send_message(message.chat.id, "Welcome to MATMIE24 Bot!\nPlease enter your full name (Name Surname):")
        bot.register_next_step_handler(msg, process_name_step)

def process_name_step(message):
    """Process user's name input"""
    try:
        user_id = message.from_user.id
        name = message.text.strip()
        
        if len(name.split()) < 2:
            raise ValueError("Please enter both your name and surname.")
        
        user_states[user_id] = {'name': name}
        
        msg = bot.send_message(message.chat.id, "Please enter your student ID:")
        bot.register_next_step_handler(msg, process_id_step)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}\nPlease try again by sending /start")

def process_id_step(message):
    """Process user's student ID input"""
    try:
        user_id = message.from_user.id
        student_id = message.text.strip()
        
        if not student_id:
            raise ValueError("Student ID cannot be empty.")
        
        name = user_states[user_id]['name']
        cursor.execute('INSERT INTO users (user_id, name, student_id) VALUES (?, ?, ?)',
                     (user_id, name, student_id))
        conn.commit()
        
        del user_states[user_id]
        show_main_menu(message)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}\nPlease try again by sending /start")

def show_main_menu(message):
    """Display the main menu with appropriate buttons for admin/regular users"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    if str(message.from_user.id) == ADMIN_ID:
        buttons = [
            'Schedule', 'Books', 'Deadlines',
            'Add Homework', 'Profile', 'Feedback'
        ]
    else:
        buttons = [
            'Schedule', 'Books', 'Deadlines',
            'Profile', 'Feedback'
        ]
    
    markup.add(*[types.KeyboardButton(btn) for btn in buttons])
    bot.send_message(message.chat.id, "Main Menu:", reply_markup=markup)

# ======================
# SCHEDULE FUNCTIONALITY
# ======================

@bot.message_handler(func=lambda message: message.text == 'Schedule')
def show_schedule_days(message):
    """Show buttons for each day of the week"""
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    days = list(SCHEDULE.keys())
    markup.add(*[types.KeyboardButton(day) for day in days])
    markup.add(types.KeyboardButton('Back to Main Menu'))
    bot.send_message(message.chat.id, "Select a day to view schedule:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in SCHEDULE.keys())
def show_day_schedule(message):
    """Show schedule for the selected day"""
    day = message.text
    schedule_text = f"📅 Schedule for {day}:\n\n" + "\n".join(SCHEDULE[day])
    show_back_button(message, schedule_text)

# ==================
# BOOKS FUNCTIONALITY
# ==================

@bot.message_handler(func=lambda message: message.text == 'Books')
def show_subjects(message):
    """Show list of subjects for book selection"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    subjects = list(BOOKS.keys())
    markup.add(*[types.KeyboardButton(subject) for subject in subjects])
    markup.add(types.KeyboardButton('Back to Main Menu'))
    bot.send_message(message.chat.id, "Select a subject to get book:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in BOOKS.keys())
def send_book(message):
    """Send the book file for selected subject"""
    subject = message.text
    book_path = BOOKS[subject]
    
    try:
        with open(book_path, 'rb') as book_file:
            bot.send_document(message.chat.id, book_file, caption=f"📚 {subject}")
    except FileNotFoundError:
        bot.send_message(message.chat.id, f"Book for {subject} not found.")
    show_back_button(message)

# =====================
# DEADLINES FUNCTIONALITY
# =====================

@bot.message_handler(func=lambda message: message.text == 'Deadlines')
def handle_deadlines(message):
    """Route to appropriate deadlines view based on user role"""
    if str(message.from_user.id) == ADMIN_ID:
        show_admin_deadlines(message)
    else:
        show_student_deadlines(message)

def show_admin_deadlines(message):
    """Show all deadlines for admin with management options"""
    cursor.execute('SELECT * FROM deadlines ORDER BY deadline')
    deadlines = cursor.fetchall()
    
    if not deadlines:
        bot.send_message(message.chat.id, "No deadlines currently.")
    else:
        response = "📝 Current Deadlines:\n\n"
        for deadline in deadlines:
            _, subject, homework, deadline_date, _ = deadline
            response += f"📌 {subject}\n{homework}\n⏰ Due: {deadline_date}\n\n"
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Add Homework'), types.KeyboardButton('Back to Main Menu'))
        bot.send_message(message.chat.id, response, reply_mup=markup)

def show_student_deadlines(message):
    """Show deadlines to students with time remaining info"""
    cursor.execute('SELECT * FROM deadlines ORDER BY deadline')
    deadlines = cursor.fetchall()
    
    if not deadlines:
        bot.send_message(message.chat.id, "No deadlines currently.")
    else:
        response = "📝 Your Deadlines:\n\n"
        today = datetime.datetime.now().date()
        
        for deadline in deadlines:
            _, subject, homework, deadline_date, _ = deadline
            due_date = datetime.datetime.strptime(deadline_date, '%Y-%m-%d').date()
            days_left = (due_date - today).days
            
            if days_left < 0:
                status = "⌛️ Expired"
            elif days_left == 0:
                status = "⚠️ Due today!"
            elif days_left == 1:
                status = "⏳ Due tomorrow!"
            else:
                status = f"⏳ {days_left} days left"
            
            response += f"📌 {subject}\n{homework}\n⏰ Due: {deadline_date} ({status})\n\n"
        
        show_back_button(message, response)

@bot.message_handler(func=lambda message: message.text == 'Add Homework' and str(message.from_user.id) == ADMIN_ID)
def start_add_homework(message):
    """Start process of adding new homework (admin only)"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    subjects = list(BOOKS.keys())
    markup.add(*[types.KeyboardButton(subject) for subject in subjects])
    markup.add(types.KeyboardButton('Back to Main Menu'))
    msg = bot.send_message(message.chat.id, "Select subject for homework:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_hw_subject_step)

def process_hw_subject_step(message):
    """Process subject selection for new homework"""
    if message.text == 'Back to Main Menu':
        show_main_menu(message)
        return
    
    user_id = message.from_user.id
    user_states[user_id] = {'subject': message.text}
    msg = bot.send_message(message.chat.id, "Enter homework description:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_hw_description_step)

def process_hw_description_step(message):
    """Process homework description input"""
    user_id = message.from_user.id
    user_states[user_id]['homework'] = message.text
    msg = bot.send_message(message.chat.id, "Enter deadline (YYYY-MM-DD):")
    bot.register_next_step_handler(msg, process_hw_deadline_step)

def process_hw_deadline_step(message):
    """Process deadline input and save homework"""
    try:
        user_id = message.from_user.id
        deadline = message.text.strip()
        datetime.datetime.strptime(deadline, '%Y-%m-%d')  # Validate date format
        
        cursor.execute('''
            INSERT INTO deadlines (subject, homework, deadline)
            VALUES (?, ?, ?)
        ''', (user_states[user_id]['subject'], user_states[user_id]['homework'], deadline))
        conn.commit()
        
        del user_states[user_id]
        bot.send_message(message.chat.id, "✅ Homework added successfully!")
    except ValueError:
        bot.reply_to(message, "❌ Invalid date format. Please use YYYY-MM-DD.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
    finally:
        show_main_menu(message)

# ==================
# PROFILE FUNCTIONALITY
# ==================

@bot.message_handler(func=lambda message: message.text == 'Profile')
def show_profile(message):
    """Show user profile information"""
    user_id = message.from_user.id
    cursor.execute('SELECT name, student_id FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user:
        name, student_id = user
        response = f"""👤 Profile Information:
        
Name: {name}
Student ID: {student_id}
Group: MATMIE24"""
    else:
        response = "Profile not found. Please send /start to register."
    
    show_back_button(message, response)

# ===================
# FEEDBACK FUNCTIONALITY
# ===================

@bot.message_handler(func=lambda message: message.text == 'Feedback' and str(message.from_user.id) != ADMIN_ID)
def start_feedback(message):
    """Start feedback process for regular users"""
    # First check if user is registered
    cursor.execute('SELECT name FROM users WHERE user_id = ?', (message.from_user.id,))
    if not cursor.fetchone():
        bot.send_message(message.chat.id, "⚠️ Please register with /start before sending feedback.")
        return
    
    msg = bot.send_message(message.chat.id, "✍️ Please enter your feedback:", 
                         reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_feedback_step)

def process_feedback_step(message):
    """Process and save user feedback"""
    try:
        user_id = message.from_user.id
        feedback_text = message.text
        
        if not feedback_text.strip():
            raise ValueError("Feedback cannot be empty")
        
        # Get user info
        cursor.execute('SELECT name FROM users WHERE user_id = ?', (user_id,))
        user_name = cursor.fetchone()[0]
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO feedback (user_id, user_name, feedback_text, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, user_name, feedback_text, timestamp))
        conn.commit()
        
        # Notify admin about new feedback
        try:
            bot.send_message(ADMIN_ID, f"📩 New feedback from {user_name} (ID: {user_id})")
        except:
            pass  # Skip if admin notification fails
            
        bot.send_message(message.chat.id, "✅ Thank you for your feedback!", 
                        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton('Back to Main Menu')))
        
    except Exception as e:
        error_msg = "🚫 Failed to save feedback. Please try again."
        if "NoneType" in str(e):
            error_msg = "⚠️ You need to register with /start before sending feedback."
        bot.reply_to(message, error_msg)
        show_main_menu(message)

@bot.message_handler(func=lambda message: message.text == 'Feedback' and str(message.from_user.id) == ADMIN_ID)
def show_admin_feedback(message):
    """Show all feedback to admin with pagination"""
    try:
        cursor.execute('SELECT COUNT(*) FROM feedback')
        count = cursor.fetchone()[0]
        
        if count == 0:
            bot.send_message(message.chat.id, "📭 No feedback received yet.")
            return
            
        cursor.execute('''
            SELECT user_name, feedback_text, timestamp 
            FROM feedback 
            ORDER BY timestamp DESC
            LIMIT 50
        ''')
        
        feedbacks = cursor.fetchall()
        
        response = "📬 Student Feedback:\n\n"
        for i, (user_name, feedback_text, timestamp) in enumerate(feedbacks, 1):
            response += f"📌 Feedback #{i}\n👤 From: {user_name}\n⏰ {timestamp}\n✍️ {feedback_text}\n\n{'═'*30}\n\n"
            
            # Send message in chunks to avoid Telegram's limit
            if len(response) > 3000:
                bot.send_message(message.chat.id, response)
                response = ""
        
        if response.strip():
            bot.send_message(message.chat.id, response)
            
        bot.send_message(message.chat.id, 
                        f"📊 Total feedback received: {count}",
                        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton('Back to Main Menu')))
        
    except Exception as e:
        bot.send_message(message.chat.id, 
                        f"❌ Error retrieving feedback: {str(e)}",
                        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton('Back to Main Menu')))

def show_back_button(message, text=None):
    """Enhanced back button with better formatting"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Back to Main Menu'))
    
    if text:
        # Split long messages
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts[:-1]:
                bot.send_message(message.chat.id, part)
            bot.send_message(message.chat.id, parts[-1], reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "↩️ Choose an option:", reply_markup=markup)
# ===================
# DEADLINE NOTIFICATIONS
# ===================

def check_deadlines():
    """Check deadlines and send notifications for due assignments"""
    while True:
        try:
            today = datetime.datetime.now().date()
            tomorrow = today + datetime.timedelta(days=1)
            
            cursor.execute('''
                SELECT id, subject, homework 
                FROM deadlines 
                WHERE deadline = ? AND notified = 0
            ''', (tomorrow.strftime('%Y-%m-%d'),))
            
            deadlines = cursor.fetchall()
            
            for deadline in deadlines:
                id, subject, homework = deadline
                message = f"""⚠️ Deadline Reminder!
                
📌 {subject}
{homework}

⏰ Due tomorrow! Please submit on time!"""
                
                cursor.execute('SELECT user_id FROM users')
                users = [user[0] for user in cursor.fetchall()]
                
                for user_id in users:
                    try:
                        bot.send_message(user_id, message)
                    except Exception as e:
                        print(f"Failed to notify user {user_id}: {str(e)}")
                
                cursor.execute('UPDATE deadlines SET notified = 1 WHERE id = ?', (id,))
                conn.commit()
            
            sleep(3600)  # Check every hour
        except Exception as e:
            print(f"Error in deadline checker: {str(e)}")
            sleep(60)

# ===================
# BOT STARTUP
# ===================

if __name__ == '__main__':
    print("MATMIE24 Bot is running...")
    
    # Start deadline checker in background
    deadline_thread = Thread(target=check_deadlines, daemon=True)
    deadline_thread.start()
    
    # Start bot polling
    bot.polling(none_stop=True)