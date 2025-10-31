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

# --- Load or Upload Boarder List ---
st.header("1️⃣ Load / Upload Boarder List")

# Give option to upload new even if one exists
new_upload = st.checkbox("Upload a new list for today", value=False)

if os.path.exists(REPORT_PATH) and not new_upload:
    boarder_df = pd.read_csv(REPORT_PATH)
    st.success(f"Loaded existing report for {TODAY} ({len(boarder_df)} entries).")
else:
    uploaded_file = st.file_uploader("Upload today's list (CSV or Excel)", type=["csv", "xlsx"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            boarder_df = pd.read_csv(uploaded_file)
        else:
            boarder_df = pd.read_excel(uploaded_file)

        boarder_df.columns = ["Boarder_Number"]
        boarder_df["Eaten"] = False
        boarder_df.to_csv(REPORT_PATH, index=False)
        st.success(f"✅ New list saved for {TODAY} with {len(boarder_df)} entries.")
    else:
        st.info("Upload a boarder list to start.")
        st.stop()

# --- Attendance Marking ---
st.header("2️⃣ Mark Attendance")

boarder_input = st.text_input("Enter Boarder Number and press Enter:")

# Trigger when user presses Enter
if boarder_input:
    if boarder_input.strip().isdigit():
        num = int(boarder_input.strip())
        matches = boarder_df[boarder_df["Boarder_Number"] == num]

        if matches.empty:
            st.error("❌ Boarder not found in today's list.")
        else:
            not_eaten_indices = matches[~matches["Eaten"]].index

            if not not_eaten_indices.empty:
                first_idx = not_eaten_indices[0]
                boarder_df.at[first_idx, "Eaten"] = True
                st.success(f"✅ Boarder {num} (Entry #{first_idx + 1}) marked as eaten.")
                boarder_df.to_csv(REPORT_PATH, index=False)
            else:
                st.warning("⚠️ All entries for this boarder have already been marked as eaten.")
    else:
        st.error("Please enter a valid numeric boarder number.")

# --- Summary ---
st.header("3️⃣ Summary")

total = len(boarder_df)
eaten = int(boarder_df["Eaten"].sum())
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

# Show all saved reports
st.write("### 🗂️ Past Reports")
for f in sorted(os.listdir(REPORTS_DIR)):
    if f.endswith(".csv"):
        st.write(f"- {f}")
