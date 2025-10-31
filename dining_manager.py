# --- Attendance Marking ---
st.header("Mark Attendance")

boarder_input = st.text_input("Enter Boarder Number:")

if st.button("Mark as Eaten"):
    if boarder_input.strip().isdigit():
        num = int(boarder_input.strip())

        # Find all rows with that number
        matches = boarder_df[boarder_df["Boarder_Number"] == num]

        if len(matches) == 0:
            st.error("Chal Nikal Laure")
        else:
            # Find the first unmatched row
            not_eaten_indices = matches[~matches["Eaten"]].index

            if len(not_eaten_indices) > 0:
                idx = not_eaten_indices[0]
                boarder_df.loc[idx, "Eaten"] = True
                st.success(f"Boarder {num} marked as eaten ✅")
                boarder_df.to_csv(REPORT_PATH, index=False)
            else:
                st.warning(f"All entries for Boarder {num} are already marked as eaten.")
    else:
        st.error("Please enter a valid number.")
