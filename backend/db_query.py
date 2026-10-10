import pandas as pd
from sqlalchemy import create_engine, text, inspect
import google.generativeai as genai

def execute_nl_query(db_type: str, connection_string: str, api_key: str, nl_query: str) -> str:
    """
    Executes a natural language query against a database and returns CSV data.
    """
    try:
        # Prevent local database processing if it's sqlite
        if connection_string.strip().lower().startswith("sqlite") or db_type.lower() == "sqlite":
            raise ValueError("SQLite is a local database and cannot be processed here.")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        if db_type.lower() == "mongodb":
            import pymongo
            import json
            
            client = pymongo.MongoClient(connection_string)
            db = client.get_default_database(default=None)
            if db is None:
                raise ValueError("No database specified in the MongoDB connection string.")
                
            schema_info = []
            for coll_name in db.list_collection_names():
                sample = db[coll_name].find_one()
                if sample:
                    fields = list(sample.keys())
                    schema_info.append(f"Collection: {coll_name}, Fields: {', '.join(fields)}")
            schema_text = "\n".join(schema_info)
            
            prompt = f"""
You are an expert MongoDB MQL generator. Given the following database schema, generate a valid MongoDB aggregation pipeline to answer the user's question.
Return ONLY a strictly valid JSON object with two keys:
- "collection": the name of the collection to query
- "pipeline": the aggregation pipeline array

Do NOT wrap the response in markdown blocks like ```json. Return raw JSON.

Schema:
{schema_text}

Question:
{nl_query}
"""
            response = model.generate_content(prompt)
            resp_text = response.text.strip()
            
            if resp_text.startswith("```json"):
                resp_text = resp_text[7:]
            if resp_text.startswith("```"):
                resp_text = resp_text[3:]
            if resp_text.endswith("```"):
                resp_text = resp_text[:-3]
            resp_text = resp_text.strip()
            
            try:
                mql_json = json.loads(resp_text)
                coll_name = mql_json["collection"]
                pipeline = mql_json["pipeline"]
            except Exception as e:
                raise ValueError(f"Failed to parse MongoDB pipeline JSON: {str(e)} \n\nRaw output: {resp_text}")
                
            cursor = db[coll_name].aggregate(pipeline)
            df = pd.DataFrame(list(cursor))
            if "_id" in df.columns:
                df = df.drop(columns=["_id"])
                
        else:
            engine = create_engine(connection_string)
            
            # 1. Extract schema information
            schema_info = []
            inspector = inspect(engine)
            for table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                col_names = [col['name'] for col in columns]
                schema_info.append(f"Table: {table_name}, Columns: {', '.join(col_names)}")
            
            schema_text = "\n".join(schema_info)
            
            # 2. Configure Gemini and generate SQL
            prompt = f"""
You are an expert {db_type} generator. Given the following database schema, generate a valid {db_type} query to answer the user's question. 
Return ONLY the raw {db_type} query, without any markdown formatting, backticks, or explanations.

Schema:
{schema_text}

Question:
{nl_query}
"""
            
            response = model.generate_content(prompt)
            sql_query = response.text.strip()
            
            # Remove potential markdown if the model ignored instructions
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            sql_query = sql_query.strip()
            
            if not sql_query:
                raise ValueError("Failed to generate a valid SQL query.")
                
            # 3. Execute SQL query
            with engine.connect() as conn:
                df = pd.read_sql(text(sql_query), conn)
            
        # 4. Convert to CSV
        csv_data = df.to_csv(index=False)
        
        # 5. Convert to Excel Base64
        import io
        import base64
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_buf.seek(0)
        excel_base64 = base64.b64encode(excel_buf.read()).decode('utf-8')
        
        return {
            "csv_data": csv_data,
            "excel_base64": excel_base64
        }
        
    except Exception as e:
        raise ValueError(f"Database query failed: {str(e)}")
