import os
import urllib
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

SYNAPSE_SERVER   = "met-dev-dataplatform-synapse-ondemand.sql.azuresynapse.net"
SYNAPSE_DATABASE = os.getenv("SYNAPSE_DATABASE", "SilverLayer")
AZURE_USERNAME   = os.environ["AZURE_USERNAME"]
AZURE_PASSWORD   = os.environ["AZURE_PASSWORD"]


def get_engine():
    odbc = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{SYNAPSE_SERVER},1433;"
        f"Database={SYNAPSE_DATABASE};"
        f"UID={AZURE_USERNAME};"
        f"PWD={AZURE_PASSWORD};"
        "Authentication=ActiveDirectoryPassword;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=300;"
    )
    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc)}",
        pool_pre_ping=True,
        pool_recycle=1800,
    )