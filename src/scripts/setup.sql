-- Create Application Role and Schema
create application role if not exists app_instance_role;
create or alter versioned schema app_instance_schema;

-- Share Data
create or replace view app_instance_schema.REGIONAL_SALES as select *
from shared_content_schema.REGIONAL_SALES;

-- Create Streamlit app
create or replace streamlit app_instance_schema.streamlit from '/libraries' main_file='streamlit.py'

-- Create UDFs
-- Add new UDF for percentage difference
create or replace function app_instance_schema.percentage_difference
(customer_sales float, regional_sales float)
returns float
language python
runtime_version = '3.8'
packages=('snowflake-snowpark-python')
imports = ('/libraries/udf.py')
handler = 'udf.percentage_difference'

-- Create Procedures
