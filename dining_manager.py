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

# --- Initialize session state ---
if "boarder_df" not in st.session_state:
    if os.path.exists(REPORT_PATH):
        st.session_state.boarder_df = pd.read_csv(REPORT_PATH)
    else:
        st.session_state.boarder_df = pd.DataFrame(columns=["Boarder_Number", "Eaten"])

# --- Upload new CSV ---
st.header("1️⃣ Load / Upload Boarder List")
uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        new_df = pd.read_csv(uploaded_file)
    else:
        new_df = pd.read_excel(uploaded_file)

    # Standardize columns
    new_df.columns = ["Boarder_Number"]
    new_df["Eaten"] = False

    # Save and update session state
    new_df.to_csv(REPORT_PATH, index=False)
    st.session_state.boarder_df = new_df
    st.success(f"✅ New list saved for {TODAY} with {len(new_df)} entries.")
    st.experimental_rerun()  # reload app immediately with new file

# --- Use session_state DataFrame ---
boarder_df = st.session_state.boarder_df

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
            if len(not_eaten_indices) > 0:
                idx = not_eaten_indices[0]
                boarder_df.at[idx, "Eaten"] = True
                st.session_state.boarder_df = boarder_df  # persist in session
                boarder_df.to_csv(REPORT_PATH, index=False)  # persist in file
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
csv = boarder_df.to_csv(index=False).encode("utf-8")
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
