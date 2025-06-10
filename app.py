import ast
import re
import streamlit as st
from pathlib import Path
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
from langchain_groq import ChatGroq
import pandas as pd

st.set_page_config(page_title="Langchain: Chat with Sales DB", page_icon="🦜")
st.title("🦜 Langchain: Chat with Sales DB")

db_path = Path(__file__).parent / "sales.db"
db_uri = f"sqlite:///{db_path.resolve()}"

api_key = "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"

if not api_key:
    st.info("Please enter the Groq API key")
    st.stop()

llm = ChatGroq(groq_api_key=api_key, model_name="Llama3-8b-8192", streaming=True)

@st.cache_resource(ttl="2h")
def configure_db(db_uri):
    return SQLDatabase.from_uri(db_uri)

db = configure_db(db_uri)

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    prefix="You are an AI assistant for querying a SQLite sales database. The database has two tables: CUSTOMER (CUSTOMER_ID, NAME, AGE, GENDER, ADDRESS) and INVOICE (INVOICE_ID, CUSTOMER_ID, INVOICE_DATE, TOTAL_AMOUNT, PAYMENT_STATUS). Always use SQL queries to fetch information from the database. Show the table name from where you are getting the results. Show the results you retrieve in the list of tuples format where each tuple represents a record that you are retrieving. Always get the full record from the database when retrieveing any data",
)

st.sidebar.write("Database Debug Info:")
st.sidebar.write(f"Database path: {db_path}")
st.sidebar.write(f"Database exists: {db_path.exists()}")
st.sidebar.write(f"Tables: {db.get_usable_table_names()}")

try:
    sample_customer = db.run("SELECT * FROM CUSTOMER LIMIT 3")
    st.sidebar.write("Sample data from CUSTOMER table:")
    st.sidebar.write(sample_customer)
    
    sample_invoice = db.run("SELECT * FROM INVOICE LIMIT 3")
    st.sidebar.write("Sample data from INVOICE table:")
    st.sidebar.write(sample_invoice)
except Exception as e:
    st.sidebar.write(f"Error querying database: {str(e)}")

if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you with the sales database?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input(placeholder="Ask anything about the sales database")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        streamlit_callback = StreamlitCallbackHandler(st.container())
        response = agent.run(user_query, callbacks=[streamlit_callback])
        
        # Parse the response to extract the list of tuples
        match = re.search(r'\[(.*?)\]', response, re.DOTALL)
        if match:
            try:
                # Use ast.literal_eval to safely convert the string to a Python object
                result_list = ast.literal_eval('[' + match.group(1) + ']')
                
                # Convert the list of tuples to a pandas DataFrame
                df = pd.DataFrame(result_list)
                
                # If the DataFrame is not empty, set column names and display as a table
                if not df.empty:
                    # Extract column names from the SQL query in the response
                    query_match = re.search(r'Invoice', response, re.IGNORECASE)
                    query_match1 = re.search(r'Customer', response, re.IGNORECASE)
                    if query_match:
                        columns = ['INVOICE_ID', 'CUSTOMER_ID', 'INVOICE_DATE', 'TOTAL_AMOUNT', 'PAYMENT_STATUS']
                        # If we have the correct number of columns, use them as column names
                        df.columns = columns
                        '''if len(columns) == df.shape[1]:
                            df.columns = columns
                        else:
                            # If not, use generic column names
                            df.columns = [f'Column {i+1}' for i in range(df.shape[1])]'''
                    elif query_match1:
                        columns = ['CUSTOMER_ID', 'NAME', 'AGE', 'GENDER', 'ADDRESS', 'CUSTOMER_TYPE', 'PARENT_ID', 'CUSTOMER_STATUS']
                        df.columns = columns
                    else:
                        # If we couldn't extract column names, use generic ones
                        df.columns = [f'Column {i+1}' for i in range(df.shape[1])]
                    
                    # Display the DataFrame as a table
                    st.write("Query Result:")
                    st.table(df)
                else:
                    st.write("The query returned no results.")
                
                # You can now work with the DataFrame 'df' for further processing if needed
            except (SyntaxError, ValueError) as e:
                st.write(f"Error parsing the result: {str(e)}")
                st.write("Original response:")
                st.write(response)
        else:
            st.write("Couldn't find a list in the response. Original response:")
            st.write(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        
if st.button("Test Database Connection"):
    try:
        result_customer = db.run("SELECT * FROM CUSTOMER")
        st.write("CUSTOMER table contents:")
        st.write(result_customer)
        
        result_invoice = db.run("SELECT * FROM INVOICE")
        st.write("INVOICE table contents:")
        st.write(result_invoice)
    except Exception as e:
        st.write(f"Error querying database: {str(e)}")
