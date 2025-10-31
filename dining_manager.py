import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Dining Manager", layout="centered")
st.title("🍽️ Dining Attendance")

# Paths
TODAY = date.today().strftime("%Y-%m-%d")
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)
TODAY_PATH = os.path.join(REPORTS_DIR, f"dining_report_{TODAY}.csv")

# ----------------------
# Helpers
# ----------------------
def load_report(path):
    try:
        df = pd.read_csv(path)
    except Exception:
        df = pd.read_excel(path)
    # normalize
    df.columns = ["Boarder_Number"] if len(df.columns) == 1 else df.columns[:1].tolist() + (["Eaten"] if "Eaten" not in df.columns else [])
    # Ensure columns exist
    if "Boarder_Number" not in df.columns:
        df.columns = ["Boarder_Number"] + [c for c in df.columns if c != df.columns[0]]
    if "Eaten" not in df.columns:
        df["Eaten"] = False
    # try integer boarder numbers
    try:
        df["Boarder_Number"] = df["Boarder_Number"].astype(int)
    except Exception:
        df["Boarder_Number"] = df["Boarder_Number"].astype(str)
    df["Eaten"] = df["Eaten"].astype(bool)
    return df

def save_today(df):
    df.to_csv(TODAY_PATH, index=False)

def ensure_session():
    if "boarder_df" not in st.session_state:
        # load today's if exists
        if os.path.exists(TODAY_PATH):
            st.session_state.boarder_df = load_report(TODAY_PATH)
        else:
            st.session_state.boarder_df = None
    if "last_message" not in st.session_state:
        st.session_state.last_message = None

ensure_session()

# ----------------------
# Section 1: Upload / choose file
# ----------------------
st.header("1️⃣ Load / Upload Boarder List")

# Option: choose a past report to load
past_files = [f for f in sorted(os.listdir(REPORTS_DIR)) if f.endswith(".csv")]
past_choice = st.selectbox("Load a past report (or choose '-- Today --')", options=["-- Today --"] + past_files, index=0)

# Option: explicitly upload new file (checkbox)
upload_new = st.checkbox("Upload a new list for today (check to replace today's list)", value=False)

col1, col2 = st.columns([3,1])

with col1:
    if upload_new:
        uploaded = st.file_uploader("Upload today's list (CSV or Excel)", type=["csv","xlsx"], key="uploader")
        if uploaded is not None:
            # preview and confirm replace
            try:
                if uploaded.name.endswith(".csv"):
                    temp_df = pd.read_csv(uploaded)
                else:
                    temp_df = pd.read_excel(uploaded)
                st.write("Preview (first 10 rows):")
                st.dataframe(temp_df.head(10))
                if st.button("Replace today's list with uploaded file"):
                    # normalize and save
                    temp_df.columns = ["Boarder_Number"] if len(temp_df.columns)==1 else temp_df.columns[:1].tolist() + (["Eaten"] if "Eaten" not in temp_df.columns else [])
                    if "Eaten" not in temp_df.columns:
                        temp_df["Eaten"] = False
                    try:
                        temp_df["Boarder_Number"] = temp_df["Boarder_Number"].astype(int)
                    except Exception:
                        temp_df["Boarder_Number"] = temp_df["Boarder_Number"].astype(str)
                    temp_df["Eaten"] = temp_df["Eaten"].astype(bool)
                    st.session_state.boarder_df = temp_df
                    save_today(st.session_state.boarder_df)
                    st.success(f"Saved new list for {TODAY} ({len(temp_df)} entries).")
            except Exception as e:
                st.error(f"Failed to read uploaded file: {e}")

with col2:
    # Load selected past report
    if past_choice != "-- Today --":
        if st.button("Load selected past report"):
            path = os.path.join(REPORTS_DIR, past_choice)
            try:
                st.session_state.boarder_df = load_report(path)
                st.success(f"Loaded {past_choice} ({len(st.session_state.boarder_df)} entries).")
            except Exception as e:
                st.error(f"Failed to load {past_choice}: {e}")
    else:
        # Load today's saved report if exists
        if st.session_state.boarder_df is None:
            st.info("No saved report for today. Upload a new list or choose a past report.")
        else:
            st.success(f"Using today's saved list ({len(st.session_state.boarder_df)} entries).")

# If no df yet stop
if st.session_state.boarder_df is None:
    st.stop()

# ----------------------
# Section 2: Attendance (Enter or button)
# ----------------------
st.header("2️⃣ Mark Attendance")

def mark_one(val):
    """Mark first unmatched entry for boarder number val."""
    if not val:
        st.session_state.last_message = ("error", "Please enter a boarder number.")
        return
    s = val.strip()
    if not s.isdigit():
        st.session_state.last_message = ("error", "Please enter a valid numeric boarder number.")
        return
    num = int(s)
    df = st.session_state.boarder_df
    # handle dtype mismatch
    if pd.api.types.is_integer_dtype(df["Boarder_Number"]):
        matches = df[df["Boarder_Number"] == num]
    else:
        matches = df[df["Boarder_Number"].astype(str) == str(num)]

    if matches.empty:
        st.session_state.last_message = ("error", "Chal Nikal Laure")
        return

    not_eaten = matches[~matches["Eaten"]].index
    if len(not_eaten) == 0:
        st.session_state.last_message = ("warning", "All entries for this boarder are already marked eaten.")
        return

    idx = not_eaten[0]
    st.session_state.boarder_df.at[idx, "Eaten"] = True
    save_today(st.session_state.boarder_df)
    st.session_state.last_message = ("success", f"Boarder {num} (row {idx+1}) marked eaten.")
    # clear input
    st.session_state.boarder_input = ""

# Text input with Enter behavior
st.text_input("Enter boarder number and press Enter (or use Mark button):", key="boarder_input", on_change=lambda: mark_one(st.session_state.boarder_input))

b_col1, b_col2 = st.columns([2,1])
with b_col1:
    if st.button("Mark as Eaten (button)"):
        mark_one(st.session_state.get("boarder_input", ""))

with b_col2:
    if st.button("Reset today's Eaten flags"):
        st.session_state.boarder_df["Eaten"] = False
        save_today(st.session_state.boarder_df)
        st.success("Today's eaten flags reset.")

# show last message
if st.session_state.get("last_message"):
    typ, msg = st.session_state.last_message
    if typ == "success":
        st.success(msg)
    elif typ == "warning":
        st.warning(msg)
    else:
        st.error(msg)

# ----------------------
# Section 3: Summary & details
# ----------------------
st.header("3️⃣ Summary")
df = st.session_state.boarder_df
total = len(df)
eaten = int(df["Eaten"].sum())
not_eaten = total - eaten
c1, c2, c3 = st.columns(3)
c1.metric("Total Entries", total)
c2.metric("Eaten", eaten)
c3.metric("Not Eaten", not_eaten)

with st.expander("View Details"):
    st.dataframe(df)

# ----------------------
# Section 4: Download & past reports list
# ----------------------
st.header("4️⃣ Download / Past Reports")
st.download_button(label="Download today's CSV", data=df.to_csv(index=False).encode("utf-8"),
                   file_name=f"dining_report_{TODAY}.csv", mime="text/csv")

if past_files:
    st.write("Saved reports:")
    for f in past_files:
        st.write("-", f)
else:
    st.write("No saved reports yet.")
