import streamlit as st
import sqlite3
import pandas as pd

# --------- SETTINGS ---------
# If you ALREADY have a SQLite DB inside Database_files/, set that path here.
# Example: DB_PATH = "Database_files/your_database.db"
DB_PATH = "database.db" # default: create/use DB in repo root

st.set_page_config(page_title="Bite Buzz", page_icon="🍴", layout="wide")

# --------- DB UTILS ---------
def get_conn():
return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
with get_conn() as conn:
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT UNIQUE
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS categories (
category_id INTEGER PRIMARY KEY AUTOINCREMENT,
category_name TEXT UNIQUE
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS food_items (
item_id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
description TEXT,
category TEXT,
added_by TEXT,
timestamp TEXT DEFAULT (DATETIME('now'))
)
""")

conn.commit()

def add_category(cat):
cat = cat.strip()
if not cat:
return
with get_conn() as conn:
conn.execute("INSERT OR IGNORE INTO categories (category_name) VALUES (?)", (cat,))
conn.commit()

def list_categories(include_all=True):
with get_conn() as conn:
rows = conn.execute("SELECT category_name FROM categories ORDER BY category_name").fetchall()
cats = [r[0] for r in rows]
return (["All"] + cats) if include_all else cats

def insert_item(name, desc, category, added_by):
with get_conn() as conn:
conn.execute(
"INSERT INTO food_items (name, description, category, added_by) VALUES (?,?,?,?)",
(name.strip(), desc.strip(), category.strip(), added_by.strip()),
)
conn.commit()

@st.cache_data(show_spinner=False)
def fetch_items(category=None, order="Latest"):
with get_conn() as conn:
c = conn.cursor()
base = "SELECT item_id, name, description, category, added_by, timestamp FROM food_items"
params = ()
if category and category != "All":
base += " WHERE category = ?"
params = (category,)
base += " ORDER BY datetime(timestamp) " + ("DESC" if order == "Latest" else "ASC")
rows = c.execute(base, params).fetchall()

df = pd.DataFrame(rows, columns=["ID", "Name", "Description", "Category", "Added By", "Timestamp"])
return df

# --------- APP STARTUP ---------
init_db()
# optional: preload a few categories the first time
for base_cat in ["Snacks", "Desserts", "Drinks", "Breakfast", "Lunch", "Dinner"]:
add_category(base_cat)

# --------- UI ---------
st.title("🍴 Bite Buzz")
with st.sidebar:
page = st.radio("Menu", ["Home", "Add Item", "Manage Categories"])

if page == "Home":
c1, c2 = st.columns([2, 1])
with c1:
chosen_cat = st.selectbox("Category", list_categories(include_all=True))
with c2:
order = st.selectbox("Sort by", ["Latest", "Oldest"])

df = fetch_items(chosen_cat, order)
if df.empty:
st.info("No items yet. Go to **Add Item** to create the first one!")
else:
st.dataframe(df, use_container_width=True)

elif page == "Add Item":
st.subheader("Add a New Food Item")
with st.form("add_form", clear_on_submit=True):
name = st.text_input("Food Name *")
desc = st.text_area("Description *", height=120)

colA, colB = st.columns([2, 1])
with colA:
existing_cats = list_categories(include_all=False)
category = st.selectbox("Choose Category *", existing_cats if existing_cats else ["(none)"])
with colB:
new_cat = st.text_input("…or add new category")

added_by = st.text_input("Added By (name or email) *")

submitted = st.form_submit_button("Submit")
if submitted:
# if user typed a new category, create it and use it
if new_cat.strip():
add_category(new_cat)
category = new_cat.strip()
# basic validation
if not all([name.strip(), desc.strip(), category.strip(), added_by.strip()]):
st.error("Please fill all required fields marked with *.")
else:
insert_item(name, desc, category, added_by)
st.success(f"✅ '{name}' added to **{category}**.")
st.cache_data.clear() # refresh the Home table

elif page == "Manage Categories":
st.subheader("Categories")
new_c = st.text_input("New category")
if st.button("Add Category"):
if new_c.strip():
add_category(new_c)
st.success(f"Added category '{new_c.strip()}'.")
st.cache_data.clear()
else:
st.warning("Please type a category name.")

cats_now = list_categories(include_all=False)
if cats_now:
st.write("**Current categories:** " + ", ".join(cats_now))
else:
st.info("No categories yet. Add one above.")
