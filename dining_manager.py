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

# -----------------------
# Helpers
# -----------------------
def load_df_from_file(path):
    """Load CSV/Excel file and normalize columns."""
    df = pd.read_csv(path)
    df.columns = ["Boarder_Number"]  # normalize even if column name different
    # Try to convert to int where possible to avoid string vs int mismatches
    try:
        df["Boarder_Number"] = df["Boarder_Number"].astype(int)
    except Exception:
        # keep as-is if conversion fails
        pass
    if "Eaten" not in df.columns:
        df["Eaten"] = False
    else:
        # ensure boolean dtype
        df["Eaten"] = df["Eaten"].astype(bool)
    return df

def save_df_to_report(df):
    df.to_csv(REPORT_PATH, index=False)

def ensure_session_df():
    """Ensure boarder_df exists in session_state (load from today report or stop)."""
    if "boarder_df" not in st.session_state:
        # If report exists for today, load it
        if os.path.exists(REPORT_PATH):
            st.session_state.boarder_df = load_df_from_file(REPORT_PATH)
        else:
            # nothing loaded yet; we'll wait until upload step sets it
            st.session_state.boarder_df = None

def mark_attendance():
    """Callback for Enter: mark first unmatched entry for the entered boarder number."""
    val = st.session_state.get("boarder_input", "")
    # clear input at the end regardless
    try:
        if not val:
            return
        val = val.strip()
        if not val.isdigit():
            st.session_state.last_message = ("error", "Please enter a valid numeric boarder number.")
            return

        num = int(val)

        df = st.session_state.boarder_df
        if df is None:
            st.session_state.last_message = ("error", "No boarder list loaded for today.")
            return

        # Ensure Boarder_Number dtype alignment: if stored as strings, compare as str
        if pd.api.types.is_integer_dtype(df["Boarder_Number"]):
            matches = df[df["Boarder_Number"] == num]
        else:
            matches = df[df["Boarder_Number"].astype(str) == str(num)]

        if matches.empty:
            # your original phrase kept as requested:
            st.session_state.last_message = ("error", "Chal Nikal Laure 😤")
        else:
            not_eaten_indices = matches[~matches["Eaten"]].index
            if len(not_eaten_indices) > 0:
                first_idx = not_eaten_indices[0]
                st.session_state.boarder_df.at[first_idx, "Eaten"] = True
                save_df_to_report(st.session_state.boarder_df)
                st.session_state.last_message = ("success", f"✅ Boarder {num} (Entry #{first_idx + 1}) marked as eaten.")
            else:
                st.session_state.last_message = ("warning", "⚠️ All entries for this boarder have already been marked as eaten.")
    finally:
        # clear the input so user can type next number instantly
        st.session_state["boarder_input"] = ""

# -----------------------
# Page logic
# -----------------------
ensure_session_df()

st.header("1️⃣ Load / Upload Boarder List")
new_upload = st.checkbox("Upload a new list for today (use this to replace today's list)", value=False)

uploaded_file = None
# If user wants to upload new, show uploader regardless
if new_upload or st.session_state.boarder_df is None:
    uploaded_file = st.file_uploader("Upload today's list (CSV or Excel)", type=["csv", "xlsx"], key="uploader")
    if uploaded_file:
        # Load uploaded file into a DataFrame
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Failed to read uploaded file: {e}")
            st.stop()

        # Normalize column and add Eaten column
        df.columns = ["Boarder_Number"]
        try:
            df["Boarder_Number"] = df["Boarder_Number"].astype(int)
        except Exception:
            # keep original dtype if conversion fails
            pass
        df["Eaten"] = False
        st.session_state.boarder_df = df
        save_df_to_report(st.session_state.boarder_df)
        st.success(f"✅ New list saved for {TODAY} with {len(df)} entries.")
else:
    # already loaded from file earlier (exists and not new_upload)
    st.success(f"Loaded existing report for {TODAY} ({len(st.session_state.boarder_df)} entries).")

# If still no df, stop
if st.session_state.get("boarder_df") is None:
    st.info("Upload a boarder list to start.")
    st.stop()

# -----------------------
# Attendance Marking (Enter triggers mark_attendance)
# -----------------------
st.header("2️⃣ Mark Attendance")
# create text_input with on_change callback to mark attendance on Enter (or focus loss)
st.text_input("Enter Boarder Number and press Enter:", key="boarder_input", on_change=mark_attendance, placeholder="e.g. 20023")

# Show last message from callback (success/error/warning)
last = st.session_state.get("last_message", None)
if last:
    typ, msg = last
    if typ == "success":
        st.success(msg)
    elif typ == "warning":
        st.warning(msg)
    else:
        st.error(msg)

# -----------------------
# Summary & details
# -----------------------
st.header("3️⃣ Summary")
df = st.session_state.boarder_df
total = len(df)
# make sure eaten sum returns int
eaten = int(df["Eaten"].sum())
not_eaten = total - eaten
col1, col2, col3 = st.columns(3)
col1.metric("Total Entries", total)
col2.metric("Eaten", eaten)
col3.metric("Not Eaten", not_eaten)

with st.expander("📋 View Details"):
    st.dataframe(df)

# -----------------------
# Download and past reports
# -----------------------
st.header("4️⃣ Download / View Past Reports")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(label="📥 Download Today's CSV", data=csv, file_name=f"dining_report_{TODAY}.csv", mime="text/csv")

st.write("### 🗂️ Past Reports")
for f in sorted(os.listdir(REPORTS_DIR)):
    if f.endswith(".csv"):
        st.write(f"- {f}")

# -----------------------
# Optional controls
# -----------------------
st.write("---")
cols = st.columns([1,1,1])
if cols[0].button("🔁 Reset today's Eaten (set all to False)"):
    df["Eaten"] = False
    st.session_state.boarder_df = df
    save_df_to_report(df)
    st.success("Today's eaten flags reset. You can re-mark now.")

if cols[1].button("🗑️ Delete today's report file"):
    try:
        if os.path.exists(REPORT_PATH):
            os.remove(REPORT_PATH)
        st.session_state.boarder_df = None
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Failed to delete file: {e}")

if cols[2].button("🔄 Reload from disk"):
    # reload from report if exists
    if os.path.exists(REPORT_PATH):
        st.session_state.boarder_df = load_df_from_file(REPORT_PATH)
        st.success("Reloaded today's report from disk.")
    else:
        st.error("No saved report found for today.")
