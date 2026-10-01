"""
My Finance App
This app allows users to upload their finance data files
(CSV, JSON, Excel, PDF) and visualize their financial transactions.
"""
import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="My Finance App",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

CATEGORY_FILE = "categories.json"

if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": []
    }

if os.path.exists(CATEGORY_FILE):
    with open(CATEGORY_FILE, "r", encoding="utf-8") as category_reader:
        st.session_state.categories = json.load(category_reader)


def save_categories():
    """ Save the current categories to the JSON file """
    with open(CATEGORY_FILE, "w", encoding="utf-8") as category_writer:
        json.dump(st.session_state.categories, category_writer)


def categorize_transactions(df):
    """ Categorize transactions based on keywords in each category """
    df["Category"] = "Uncategorized"

    # Iterate over each category and its associated keywords to categorize transactions
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue
        lower_keywords = [keyword.lower().strip() for keyword in keywords]

        # Iterate over each row in the DataFrame to categorize transactions based on keywords
        for idx, row in df.iterrows():
            details = row["Details"].lower().strip()
            if details in lower_keywords:
                df.at[idx, "Category"] = category
    return df


def load_transactions_data(file):
    """ Load transaction data from a file and categorize it """
    try:
        df = pd.read_csv(file)
        # Strip any leading/trailing whitespace from column names
        df.columns = [col.strip() for col in df.columns]
        # Convert the "Amount" column to numeric after removing commas
        df["Amount"] = df["Amount"].str.replace(",", "").astype(float)
        # Convert the "Date" column to datetime format
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y")

        return categorize_transactions(df)
    except (ValueError, KeyError, pd.errors.ParserError, UnicodeError, OSError) as e:
        st.error(f"Error loading file: {str(e)}")
        return None


def add_keyword_to_category(category, keyword):
    """Add a keyword to a specific category in the session state and save the categories."""
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False


def main():
    """ Main function to run the Streamlit app """

    st.title("My Finance Dashboard", icon="💰", text_alignment="center")

    uploaded_file = st.file_uploader("Upload your finance data file", type=[
        "csv", "json", "xlsx", "xls", "pdf"])
    if uploaded_file is not None:
        df = load_transactions_data(uploaded_file)

        if df is not None:
            debits_df = df[df["Debit/Credit"] == "Debit"].copy()
            credits_df = df[df["Debit/Credit"] == "Credit"].copy()
            st.session_state.debits_df = debits_df.copy()
            st.session_state.credits_df = credits_df.copy()

            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])
            with tab1:
                st.subheader("Expenses (Debits)")

                new_category = st.text_input(
                    "Add a new category name for Expenses (Debits)")
                add_button = st.button("Add Category for Expenses (Debits)")
                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.session_state.success_message = (
                            f"Category '{new_category}' added successfully."
                        )
                        st.rerun()
                    else:
                        st.warning(
                            f"Category '{new_category}' already exists.")

                if "success_message" in st.session_state:
                    st.success(st.session_state.success_message)
                    del st.session_state.success_message
                st.subheader("Expenses Data")
                edited_debits_df = st.data_editor(
                    st.session_state.debits_df[[
                        "Date", "Details", "Amount", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD-MM-YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format="%0.2f"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="debits_category_editor"
                )
                save_button_debits = st.button(
                    "Save Changes",
                    key="save_debits",
                    type="primary"
                )
                if save_button_debits:
                    for idx, row in edited_debits_df.iterrows():
                        new_category = row["Category"]
                        if new_category == st.session_state.debits_df.at[idx, "Category"]:
                            continue

                        details = row["Details"]
                        st.session_state.debits_df.at[
                            idx, "Category"
                        ] = new_category
                        add_keyword_to_category(new_category, details)

                    st.session_state.debits_df.update(edited_debits_df)
                    st.success(
                        "Changes saved successfully.",
                        icon="✅"
                    )

                st.subheader("Expenses Summary")
                category_totals = st.session_state.debits_df.groupby(
                    "Category")["Amount"].sum().reset_index()
                category_totals = category_totals.sort_values(
                    by="Amount", ascending=False)
                st.dataframe(category_totals,
                             column_config={
                                 "Amount": st.column_config.NumberColumn("Amount", format="%0.2f"),
                             },
                             use_container_width=True,
                             hide_index=True
                             )
                fig = px.pie(category_totals, names="Category",
                             values="Amount", title="Expenses by Category")
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.subheader("Payments (Credits)")
                new_category = st.text_input(
                    "Add a new category name for Payments (Credits)")
                add_button = st.button(
                    "Add Category for Payments (Credits)"
                )
                total_credits = st.session_state.credits_df["Amount"].sum()
                st.metric(label="Total Payments:", value=f"{total_credits:,.2f}".replace(
                    ",", "X").replace(".", ",").replace("X", ".") + " €")
                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.session_state.success_message = (
                            f"Category '{new_category}' added successfully."
                        )
                        st.rerun()
                    else:
                        st.warning(
                            f"Category '{new_category}' already exists.")
                if "success_message" in st.session_state:
                    st.success(st.session_state.success_message)
                    del st.session_state.success_message
                st.subheader("Payments Data")
                edited_credits_df = st.data_editor(
                    st.session_state.credits_df[[
                        "Date", "Details", "Amount", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD-MM-YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format="%0.2f"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="credits_category_editor"
                )
                save_button_credits = st.button(
                    "Save Changes",
                    key="save_credits",
                    type="primary"
                )
                if save_button_credits:
                    st.session_state.credits_df.update(edited_credits_df)
                    st.success(
                        "Changes saved successfully.",
                        icon="✅"
                    )


main()
