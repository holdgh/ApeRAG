DefaultSQLPromptTemplate = (
    "I want you to act as a professional DBA.\n"
    "I will provide you with the table structure and my requirements.\n"
    "{schema}\n"
    "My question is: {query_str}\n"
    "According to my question, provide me the most optimal SQL query that can be executed.\n"
    "You should observe follow rules:\n"
    "1.The type of database you are operating on is {dialect}.\n"
    "2.Be careful to not query for columns that do not exist in above tables.\n"
    "3.If the queried field does not exist in the table, give a warn info.\n"
    "4.Pay attention to which column is in which table.\n"
)
