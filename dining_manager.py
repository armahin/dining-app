import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Dining Manager", layout="centered")
st.title("🍽️ Dining Attendance")

TODAY = date.today().strftime("%Y-%m-%d")
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)
TODAY_PATH = os.path.join(REPORTS_DIR, f"dining_report_{TODAY}.csv")

# ----------------------
# Helpers
# ----------------------
def load_report(path):
    df = pd.read_csv(path)
    # Use only first column as boarder number
    if "Boarder_Number" not in df.columns:
        df.rename(columns={df.columns[0]: "Boarder_Number"}, inplace=True)
    if "Eaten" not in df.columns:
        df["Eaten"] = False
    return df

def save_today(df):
    df.to_csv(TODAY_PATH, index=False)

def ensure_session():
    if "boarder_df" not in st.session_state:
        if os.path.exists(TODAY_PATH):
            st.session_state.boarder_df = load_report(TODAY_PATH)
        else:
            st.session_state.boarder_df = None
    if "last_message" not in st.session_state:
        st.session_state.last_message = None

ensure_session()

# ----------------------
# Section 1: Load or Upload File
# ----------------------
st.header("1️⃣ Load / Upload Boarder List")

past_files = [f for f in sorted(os.listdir(REPORTS_DIR)) if f.endswith(".csv")]
past_choice = st.selectbox("Load a past report (or '-- Today --')", ["-- Today --"] + past_files)

upload_new = st.checkbox("Upload a new list for today (replace current)")

if upload_new:
    uploaded = st.file_uploader("Upload today's list (CSV)", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        df.rename(columns={df.columns[0]: "Boarder_Number"}, inplace=True)
        df["Eaten"] = False
        st.session_state.boarder_df = df
        save_today(df)
        st.success(f"New list uploaded with {len(df)} entries.")
elif past_choice != "-- Today --":
    path = os.path.join(REPORTS_DIR, past_choice)
    st.session_state.boarder_df = load_report(path)
    st.success(f"Loaded {past_choice}.")
else:
    if st.session_state.boarder_df is not None:
        st.success(f"Using today's saved list ({len(st.session_state.boarder_df)} entries).")
    else:
        st.info("Upload a list to begin.")
        st.stop()

# ----------------------
# Section 2: Mark Attendance
# ----------------------
st.header("2️⃣ Mark Attendance")

def mark_attendance(num):
    df = st.session_state.boarder_df
    matches = df[df["Boarder_Number"] == num]
    if matches.empty:
        st.session_state.last_message = ("error", "❌ Boarder not found.")
    else:
        idx = matches[~matches["Eaten"]].index
        if len(idx) == 0:
            st.session_state.last_message = ("warning", "⚠️ Already marked eaten.")
        else:
            df.at[idx[0], "Eaten"] = True
            save_today(df)
            st.session_state.last_message = ("success", f"✅ Boarder {num} marked eaten.")
            st.session_state.boarder_input = ""

st.text_input("Enter boarder number and press Enter:", key="boarder_input",
              on_change=lambda: mark_attendance(st.session_state.boarder_input.strip()))

if st.button("Reset Eaten Flags"):
    st.session_state.boarder_df["Eaten"] = False
    save_today(st.session_state.boarder_df)
    st.success("All entries reset to not eaten.")

if st.session_state.last_message:
    t, m = st.session_state.last_message
    if t == "success":
        st.success(m)
    elif t == "warning":
        st.warning(m)
    else:
        st.error(m)

# ----------------------
# Section 3: Summary
# ----------------------
st.header("3️⃣ Summary")
df = st.session_state.boarder_df
total = len(df)
eaten = df["Eaten"].sum()
not_eaten = total - eaten

c1, c2, c3 = st.columns(3)
c1.metric("Total", total)
c2.metric("Eaten", eaten)
c3.metric("Not Eaten", not_eaten)

with st.expander("📋 View Details"):
    st.dataframe(df)

# ----------------------
# Section 4: Download
# ----------------------
st.header("4️⃣ Download / Past Reports")

st.download_button("📥 Download Today's CSV", df.to_csv(index=False).encode("utf-8"),
                   file_name=f"dining_report_{TODAY}.csv", mime="text/csv")

if past_files:
    st.write("Past reports:")
    for f in past_files:
        st.write(f"- {f}")
else:
    st.write("No past reports yet.")
