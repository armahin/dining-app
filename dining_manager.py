import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Dining Manager", layout="centered")
st.title("🍽️ Dining Attendance Manager")

TODAY = date.today().strftime("%Y-%m-%d")
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)
REPORT_PATH = os.path.join(REPORTS_DIR, f"dining_report_{TODAY}.csv")

# --- Load existing report or initialize ---
def load_boarder_df():
    if os.path.exists(REPORT_PATH):
        return pd.read_csv(REPORT_PATH)
    else:
        return pd.DataFrame(columns=["Boarder_Number", "Eaten"])

if "boarder_df" not in st.session_state:
    st.session_state.boarder_df = load_boarder_df()

boarder_df = st.session_state.boarder_df

# --- Upload new file option ---
st.header("1️⃣ Load / Upload Boarder List")

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file

if st.session_state.uploaded_file is not None:
    uploaded_file = st.session_state.uploaded_file
    if uploaded_file.name.endswith(".csv"):
        boarder_df = pd.read_csv(uploaded_file)
    else:
        boarder_df = pd.read_excel(uploaded_file)

    boarder_df.columns = ["Boarder_Number"]
    boarder_df["Eaten"] = False
    boarder_df.to_csv(REPORT_PATH, index=False)

    st.session_state.boarder_df = boarder_df
    st.success(f"✅ New list saved for {TODAY} with {len(boarder_df)} entries.")

# --- Attendance Marking ---
st.header("2️⃣ Mark Attendance")

boarder_input = st.text_input("Enter Boarder Number:")

if st.button("Mark as Eaten"):
    if boarder_input.strip().isdigit():
        num = int(boarder_input.strip())
        matches = boarder_df[boarder_df["Boarder_Number"] == num]

        if matches.empty:
            st.error("❌ Chal Nikal Laure")
        else:
            not_eaten_indices = matches[~matches["Eaten"]].index
            if not not_eaten_indices.empty:
                first_idx = not_eaten_indices[0]
                boarder_df.at[first_idx, "Eaten"] = True
                st.session_state.boarder_df = boarder_df
                boarder_df.to_csv(REPORT_PATH, index=False)
                st.success(f"✅ Boarder {num} marked as eaten.")
            else:
                st.warning(f"⚠️ All entries for Boarder {num} are already marked as eaten.")
    else:
        st.error("Please enter a valid number.")

# --- Summary ---
st.header("3️⃣ Summary")

total = len(boarder_df)
eaten = boarder_df["Eaten"].sum()
not_eaten = total - eaten

col1, col2, col3 = st.columns(3)
col1.metric("Total Entries", total)
col2.metric("Eaten", eaten)
col3.metric("Not Eaten", not_eaten)

with st.expander("📋 View Details"):
    st.dataframe(boarder_df)

# --- Download Section ---
st.header("4️⃣ Download / View Past Reports")

csv = boarder_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Today's CSV",
    data=csv,
    file_name=f"dining_report_{TODAY}.csv",
    mime="text/csv",
)

st.write("### 🗂️ Past Reports")
files = sorted(os.listdir(REPORTS_DIR))
for f in files:
    if f.endswith(".csv"):
        st.write(f"- {f}")
