import streamlit as st
import sqlite3
import io
from PIL import Image
from database import user_info_table, add_user, login_user, is_user_exist, image_detail_table, insert_image_detail
import pandas as pd
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
import ssl
import torch
import torchvision
from torchvision import transforms, datasets, models
from PIL import Image
import torch.nn as nn
import torch.optim as optim
import re

if 'user' not in st.session_state:
    st.session_state.user = None

if 'email' not in st.session_state:
    st.session_state.email = None

if 'login' not in st.session_state:
    st.session_state.login = False

if 'signup' not in st.session_state:
    st.session_state.signup = False

if 'reset_password' not in st.session_state:
    st.session_state.reset_password = False

if 'upload_image' not in st.session_state:
    st.session_state.upload_image = False

def get_connection():
    return sqlite3.connect('skindiseases.db', check_same_thread=False)

def delete_data(row_id):
    conn = sqlite3.connect('skindiseases.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM image_details WHERE id=?', (row_id, ))
    conn.commit()

    st.success("Data deleted successfully")

def update_user_info(name, username, email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE user_info_table SET name=?, username=?, email=?, password=? WHERE username=?',
                   (name, username, email, password, st.session_state.user))
    conn.commit()
    st.success("Your information has been updated")

def is_valid_password(password):
    # Password should have at least 8 characters
    # It should contain at least one uppercase letter, one lowercase letter, one digit, and one special character
    # You can modify the regex pattern to fit your specific requirements
    pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    return re.match(pattern, password) is not None


def image_transform(image):
    accuracy_threshold = 0.5
    num_classes = 10

    # # DenseNet
    model_path = 'densenet169.pth'
    #Define the model architecture
    loaded_model = models.densenet169(pretrained=False)
    loaded_model.classifier = torch.nn.Linear(1664, num_classes)
    # Load the model state_dict from the file
    loaded_model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    loaded_model.eval()


    #Alexnet
    # model_path = 'alexnet_model.pth'
    # loaded_model = models.alexnet(pretrained=False)
    # loaded_model.classifier[6] = torch.nn.Linear(4096, num_classes)  # Modify the classifier for your specific number of classes
    # state_dict = torch.load(model_path, map_location=torch.device('cpu'))  # Load on CPU
    # loaded_model.load_state_dict(state_dict)
    # loaded_model.eval()

    #vgg19
    # model_path = 'vgg19.pth'
    # loaded_model = models.vgg19(pretrained=False)
    # loaded_model.classifier[6] = torch.nn.Linear(4096, num_classes)  # Modify the classifier for your specific number of classes
    # state_dict = torch.load(model_path, map_location=torch.device('cpu'))  # Load on CPU
    # loaded_model.load_state_dict(state_dict)
    # loaded_model.eval()

    #Resnet (error)
    # model_path = 'resnet50.pth'
    # #Define the model architecture
    # loaded_model = models.resnet50(pretrained=False)
    # loaded_model.classifier = torch.nn.Linear(1664, num_classes)  # Modify the classifier for your specific number of classes
    # state_dict = torch.load(model_path, map_location=torch.device('cpu'))  # Load on CPU
    # loaded_model.load_state_dict(state_dict)
    # loaded_model.eval()


    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    image = transform(image).unsqueeze(0)

    with torch.no_grad():
        output = loaded_model(image)
        _, predicted = torch.max(output.data, 1)
        probabilities = torch.softmax(output, dim=1)
    
    predicted_class = predicted.item()
    max_probability = torch.max(probabilities).item()
    classes = ['Acne', 'Dermatitis', 'Eczema', 'Impetigo', 'Melanoma', 'Psoriasis', 'Ringworm', 'Rosacea', 'Urticaria Hives', 'Vitiligo']
    
    if max_probability < accuracy_threshold:
        return "Unknown disease", max_probability
    else:
        predicted_label = classes[predicted_class]
        return predicted_label, max_probability


def Homepage():
    image_detail_table()     
    if st.session_state.user is None:
        st.error("You must be logged in to access this page.")
        Login()
        return

    st.title("Hello Dermatologist👩‍⚕️!")
    st.subheader("Welcome to ClassiDerm🔬")
    st.write("A Skin Disease Diagnosis System")

    file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png"], key="fileUploader", help="Only JPG, JPEG and PNG file formats are supported.")

    if file is None:
        st.text("Please upload an image file 😎")
    elif file.type not in ["image/jpeg", "image/jpg", "image/png"]:
        st.error("Unsupported file format. Please upload a JPG, JPEG, or PNG file.")
    else:
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data))

        st.image(image, caption="Uploaded Image", use_column_width=True)
        predicted_class, accuracy = image_transform(image)
        st.write(f"Detected disease: **{predicted_class}**")
        st.write(f"Accuracy: **{accuracy:.2f}**")
        comment = st.text_input("Comments/Description")
        st.write("Disclaimer: The skin disease detection tool provided on this platform is intended for informational purposes only and should not be considered a substitute for professional medical advice, diagnosis, or treatment. This tool is not designed to provide a definitive diagnosis of any skin condition")

        if st.button("Save Disease Details"):
            insert_image_detail(predicted_class, comment, image)
            st.success("Successfully Updated!")

def Image_list():   
    if st.session_state.user is None:
        st.title("Welcome to ClassiDerm🔬")
        st.error("You must be logged in to access this page,")
        return
    
    conn = sqlite3.connect('skindiseases.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, disease_name, comment, image FROM image_details')
    rows = cursor.fetchall()

    st.title("Uploaded Skin Disease Image📎")
    for id, disease_name, comment, image_data in rows:
        st.write("_________________________________________________________________________")
        st.subheader(f"Uploaded Image {id}")        
        st.write(f"Detected disease: {disease_name}")
        st.write(f"Comment: {comment}")
        image = Image.open(io.BytesIO(image_data))
        st.image(image)

        delete_button = st.button(f"Delete Uploaded Image {id}")
        if delete_button:
            delete_data(id)

def Account():
    user_info_table()    
    if st.session_state.user is None:
        st.title("Welcome to ClassiDerm🔬")
        st.error("You must be logged in to access this page")
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_info_table WHERE username = ?', (st.session_state.user,))
    user_data = cursor.fetchone()

    st.title("Your Account🥼")

    if user_data:
        st.write("Your Information")
        name = st.text_input(f"Name ({user_data[0]})", user_data[0])
        username = st.text_input(f"Username({user_data[0]})", user_data[1])
        email = st.text_input(f"Email ({user_data[0]})", user_data[2])
        password = st.text_input(f"Password ({user_data[0]})", user_data[3], type="password")
        
        # Define password requirements
        password_requirements = "Password must have at least 8 characters, including one uppercase letter, one lowercase letter, one digit, and one special character."
        
        if not name or not username or not email or not password:
            st.error("Please fill in all the required fields.")
        elif not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
            st.error(password_requirements)
        else:
            if st.checkbox("Confirm Update"):
                if st.button("Update"):
                    update_user_info(name, username, email, password)
                    st.success("Information updated successfully!")
                else:
                    st.warning("Click Confirm Update to confirm your update")
    else:
        st.error("User not found")

# def generate_reset_token():
#     reset_token = random.randint(100000, 999999)    
#     return reset_token

def save_reset_token_in_database(email, reset_token):
    conn = sqlite3.connect('skindiseases.db')  # Replace 'your_database.db' with your SQLite database file path
    cursor = conn.cursor()
    # Execute an SQL query to update the reset_token field for the user's email
    cursor.execute("UPDATE user_info_table SET reset_token=? WHERE email=?", (reset_token, email))
    conn.commit()
    conn.close()

def send_reset_email(to_email, reset_token):
    # Email configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 465  # Change this to your SMTP server's port
    smtp_username = 'u2005247@siswa.um.edu.my'
    smtp_password = 'u20516a978b'
    from_email = 'u2005247@siswa.um.edu.my'

    
    # Create a message
    msg = EmailMessage()
    # msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = 'Password Reset Request'

    # Email body
    body = f'This is your reset token: {reset_token}'
    # msg.attach(MIMEText(body, 'plain'))
    msg.set_content(body)
    # save_reset_token_in_database(to_email, reset_token)
    # Add SSL (layer of security)
    context = ssl.create_default_context()
    # Connect to SMTP server and send email
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as smtp:
        smtp.login(from_email, smtp_password)
        smtp.sendmail(from_email, to_email, msg.as_string())        
        print("Password reset email sent successfully.")
    
# Function to check if the reset token is valid
def is_valid_reset_token(email, token):
    conn = sqlite3.connect('skindiseases.db')  # Replace 'your_database.db' with your SQLite database file path
    cursor = conn.cursor()

    # Execute an SQL query to fetch the reset token associated with the user's email
    cursor.execute("SELECT reset_token FROM user_info_table WHERE email = ?", (email,))
    stored_token = cursor.fetchone()

    conn.close()    # Check if the provided token matches the stored token
    # return token == stored_token
    if stored_token:
        return stored_token[0]  # Return the reset token as a string
    else:
        return None


def update_password_in_database(email, new_password):
    conn = sqlite3.connect('skindiseases.db')  # Replace 'your_database.db' with your SQLite database file path
    cursor = conn.cursor()

    # Execute an SQL query to update the user's password
    cursor.execute("UPDATE user_info_table SET password=? WHERE email=?", (new_password, email))
    conn.commit()

    conn.close()
    print(f"Updating password for {email} to {new_password}")

# Function to clear the reset token in the database
def clear_reset_token_in_database(email):
    reset_token = " "    
    conn = sqlite3.connect('skindiseases.db')  # Replace 'your_database.db' with your SQLite database file path
    cursor = conn.cursor()

    # Check if the user exists in the database before updating the reset_token
    cursor.execute("SELECT * FROM user_info_table WHERE email=?", (email,))
    user_data = cursor.fetchone()

    if user_data:
        # Execute an SQL query to clear the reset_token field for the user's email
        cursor.execute("UPDATE user_info_table SET reset_token=? WHERE email=?", (reset_token, email))
        conn.commit()
        conn.close()
        print(f"Reset token cleared for {email}")
    else:
        conn.close()
        print(f"User with email {email} not found in the database")



def Login():
    if not st.session_state.login:
        st.subheader("Welcome to ClassiDerm🔬")
        st.title("Login👋")
        username = st.text_input("Username👩‍⚕️")
        password = st.text_input("Password🔑", type='password')

        if st.button("Login Now👩‍⚕️"):
            conn = get_connection()
            cursor = conn.cursor()
            # hashed_password = make_hashes(password)
            cursor.execute('SELECT username AND password FROM user_info_table WHERE username = ? AND password = ?', (username, password))
            user_data = cursor.fetchone()
            if not username or not password:
                st.error("Please fill in all the required fields.")
            else:
                if user_data:
                    # stored_password = user_data[2]  # Index 2 corresponds to the password column
                    # hashed_pass = make_hashes(password)
                    result = login_user(username, password)
                    if result:
                        st.session_state.user = username
                        st.success("Logged in as {}".format(username))

                        # return True
                    else:
                        st.warning("Incorrect email or password")
                else:
                    st.warning("User not found")

        st.write("Do not have account? Please signup")

def is_email_in_database(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM user_info_table WHERE email = ?", (email,))
    result = cursor.fetchone()
    return result is not None

         # Forgot Password

def get_reset_token_from_database(email_to_reset):
    conn = sqlite3.connect('skindiseases.db')
    cursor = conn.cursor()

    # Execute an SQL query to fetch the reset token for the provided email
    cursor.execute("SELECT reset_token FROM user_info_table WHERE email=?", (email_to_reset,))
    result = cursor.fetchone()

    # Close the database connection
    conn.close()

    if result:
        return result[0]  # Return the reset token
    else:
        return None
    
def reset_password():            
    st.title("Password Reset")
    email_to_reset = st.text_input("Enter your Email:")
    if st.button("Forgot Password"):
        if email_to_reset:
            # Check if the email exists in your database
            if is_email_in_database(email_to_reset):
                # Generate a unique reset token and save it in the database
                reset_token = random.randint(100000, 999999)
                save_reset_token_in_database(email_to_reset, reset_token)
                # Send an email with the reset link
                send_reset_email(email_to_reset, reset_token)
                st.success("Password reset link sent to your email. Please check your inbox.")
            else:
                st.warning("Email not found. Please check the email address.")
        else:
            st.warning("Please enter your email address.")

# Password Reset Page
# In your password reset logic
    st.subheader("Password Reset🔑")
    # if st.session_state.reset_password:            
    reset_token = st.text_input("Enter the reset token:")
    new_password = st.text_input("New Password", type='password')
    confirm_password = st.text_input("Confirm Password", type='password')

    if st.button("Reset Password"):
        # Check if the reset token is valid and associated with the user's email address
        saved_reset_token = get_reset_token_from_database(email_to_reset)
        if not reset_token or not new_password or not confirm_password:
            st.error("Please fill in all the required fields.")
        else:
            if reset_token == saved_reset_token:
                # Compare new password and confirm password                
                if new_password == confirm_password:
                    if not is_valid_password(new_password):
                        st.error("Password must have at least 8 characters, including one uppercase letter, one lowercase letter, one digit, and one special character.")
                    # Update the user's password with the new password
                    else:
                        update_password_in_database(email_to_reset, new_password)
                        clear_reset_token_in_database(email_to_reset)
                        st.success("Password reset successfully. You can now login with your new password.")
                else:
                    st.warning("Password and confirm password do not match. Please try again.")
            else:
                st.warning("Invalid reset token or password mismatch. Please try again.")
    
def Signup_account():
    st.title("Welcome to ClassiDerm🔬")
    st.subheader("Create New Account")
    new_name = st.text_input("Name")
    new_user = st.text_input("Username")
    new_email = st.text_input("Email Address")
    new_password = st.text_input("Password", type='password', key="user_password")
    reset_token = " "

    if st.button("Signup"):
        if not new_name or not new_user or not new_email or not new_password:
            st.error("Please fill in all the required fields.")
        elif not is_valid_password(new_password):
            st.error("Password must have at least 8 characters, including one uppercase letter, one lowercase letter, one digit, and one special character.")
        else:
            user_info_table()
            if is_user_exist(new_user, new_email):
                st.error("Username or Email already exists. Please choose a different Username or Email😊")
            else:
                add_user(new_name, new_user, new_email, new_password, reset_token)
                st.success("You have successfully created an Account")
                st.info("Go to the login page to log in to your account")

    st.write("If you have an account, please login")

def logout():
    st.session_state.user = None
    st.subheader("Successfully Logout🫤")
    Login()


def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to:", ["Homepage🏠", "My Account🧑‍⚕️", "Image List📃", "Login🔐", "Forgot Password?😓", "Signup🙌", "Logout🔑"])

    if page == "Homepage🏠":
        Homepage()
    elif page == "My Account🧑‍⚕️":
        Account()
    elif page == "Image List📃":
        Image_list()
    elif page == "Login🔐":
        Login()
    elif page == "Forgot Password?😓":
        reset_password()
    elif page == "Signup🙌":
        Signup_account()
    elif page == "Logout🔑":
        logout()


main()
