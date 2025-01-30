import vanna as vn
from vanna.remote import VannaDefault
from sqlalchemy import create_engine, inspect
from tkinter import simpledialog
import tkinter as tk
import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
import plotly.graph_objects as go

load_dotenv()
api_key = os.getenv("VANNA_API_KEY")
vanna_model_name = os.getenv("VANNA_MODEL_NAME")
vn = VannaDefault(model=vanna_model_name, api_key=api_key)

# Function to reterieve database schema for Display purposes
def retriving_schema(db_type, host, user, password, db_name):
    try:
        if db_type == "mysql":
            connection_string = f"mysql+pymysql://{user}:{password}@{host}/{db_name}"
        elif db_type == "postgresql":
            connection_string = f"postgresql://{user}:{password}@{host}/{db_name}"
        elif db_type == "sqlite":
            connection_string = f"sqlite:///{db_name}"
        elif db_type == "oracle":
            connection_string = f"oracle://{user}:{password}@{host}/{db_name}"
        else:
            raise ValueError("Unsupported database type")
        # Create a SQLAlchemy engine and establish the connection
        engine = create_engine(connection_string)
        return engine.connect()
    except SQLAlchemyError as e:
        raise Exception(f"Database connection error: {e}")
    
# Function to handle the connection to different database types (SQLite, MySQL, PostgreSQL, Oracle)
def connect_to_database(db_type, host, user, password, db_name, port):
    if db_name:  # Only proceed if the db_name is not empty
        if db_type == "sqlite":
            vn.connect_to_sqlite(db_name)
        elif db_type == "mysql":
            vn.connect_to_mysql(host=host, dbname=db_name, user=user, password=password, port=port)
        elif db_type == "postgresql":
            vn.connect_to_postgres(host=host, dbname=db_name, user=user, password=password, port=port)
        elif db_type == "oracle":
            vn.connect_to_oracle(user=user, password=password)
    else:
        # Display message or handle case where db_name is empty or wrong
        st.warning("Please enter a valid database name.")


# Function to get the schema (tables and columns) from the connected database
def get_database_schema(connection):
    try:
        # Use SQLAlchemy inspector to fetch the database schema (tables and columns)
        inspector = inspect(connection)
        tables = inspector.get_table_names()
        schema = {table: [column["name"] for column in inspector.get_columns(table)] for table in tables}
        return schema
    except Exception as e:
        return {"error": str(e)}

# Function to query the database using natural language via the Vanna model
def query_database_with_vanna(question):
    
    response = vn.ask(question=question,allow_llm_to_see_data=True)
    if isinstance(response, tuple):
        sql_query = response[0]  # Extract only the SQL query
        report = response[1] if len(response) > 1 else None # Extract the report
        visualization = response[2] if len(response) > 2 else None # Extract the visualization
    else:
        sql_query, report, visualization = response, None, None
    return sql_query, report, visualization

def main():
    st.title("Natural Language to SQL Converter")
    
    db_type = st.text_input("Database Type (mysql/postgresql/sqlite/oracle):")
    host = st.text_input("Host:")
    user = st.text_input("Username:")
    password = st.text_input("Password:", type="password")
    db_name = st.text_input("Database Name:")
    port = st.text_input("Port:")
    
    connect_to_database(db_type, host, user, password, db_name, port)
    schema = st.session_state.get("schema", None)
    
    if st.button("Retrieve Schema"):
        try:
            connection = retriving_schema(db_type, host, user, password, db_name)
            if connection:
                schema = get_database_schema(connection)
                st.session_state["schema"] = schema  
                st.success("Database connected successfully!")
            else:
                st.error("Failed to establish a database connection.")
        except Exception as e:
            st.error(f"Failed to connect to database: {e}")
            
    # Display the schema
    if schema:
        st.subheader("Database Schema")
        st.json(schema)
    
    question = st.text_input("Ask a question in natural language:")
    
    if st.button("Generate SQL Query"):
        try:
            sql_query, report, visualization = query_database_with_vanna(question)
            st.write("Generated SQL Query:")
            st.code(sql_query)
            
            if report is not None:
                st.subheader("Report")
                st.write(report)
            
            if visualization:
                st.subheader("Visualization")
                st.plotly_chart(visualization)
        except Exception as e:
            st.error(f"Error generating SQL: {e}")

if __name__ == "__main__":
    main()
