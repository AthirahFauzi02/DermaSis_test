import sqlite3
import streamlit as st
import hashlib
import os
import tempfile

def get_connection():
    return sqlite3.connect('skindiseases.db', check_same_thread=False)

get_connection()

def user_info_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_info_table (            
            name TEXT NOT NULL,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            reset_token TEXT,
            PRIMARY KEY (username)
        )
    ''')
    conn.commit()
    conn.close()

def add_user(name, username, email, password, reset_token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_info_table(name, username, email, password, reset_token) VALUES (?,?,?,?,?)', (name, username, email, password, reset_token))
    conn.commit()

def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    # hashed_password = make_hashes(password)
    cursor.execute('SELECT username AND password FROM user_info_table WHERE username = ? AND password = ?', (username, password))
    data = cursor.fetchone()
    return data   

def image_detail_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_details(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disease_name TEXT NOT NULL,
            comment TEXT,
            image BLOB
        )
    ''')
    conn.commit()

def is_user_exist(username, email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_info_table WHERE username=? OR email=?', (username, email))
    user_data = cursor.fetchone()
    conn.close()
    return user_data is not None

def insert_image_detail(disease_name, comment, image):
    conn = get_connection()
    cursor = conn.cursor()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_image_file:
        image.save(temp_image_file, format="JPEG")
    
    # Read the saved image file as binary data
    with open(temp_image_file.name, 'rb') as binary_image_file:
        image_bytes = binary_image_file.read()

    cursor.execute('''
        INSERT INTO image_details (disease_name, comment, image) VALUES (?, ?, ?)
    ''', (disease_name, comment, image_bytes))
    conn.commit()
