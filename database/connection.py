"""
database/connection.py
=======================
Connexion Azure Synapse via DefaultAzureCredential.

Authentification MFA-compatible — token mis en cache par az login.
Aucune saisie de mot de passe après le premier az login.
"""

import os
import struct
import urllib

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy import event

load_dotenv()

SYNAPSE_SERVER   = "met-dev-dataplatform-synapse-ondemand.sql.azuresynapse.net"
SYNAPSE_DATABASE = os.getenv("SYNAPSE_DATABASE", "SilverLayer")
TOKEN_SCOPE      = "https://database.windows.net/.default"

# Cache du credential — créé une seule fois
_credential: DefaultAzureCredential | None = None


def _get_credential() -> DefaultAzureCredential:
    """Retourne le credential mis en cache."""
    global _credential
    if _credential is None:
        _credential = DefaultAzureCredential()
    return _credential


def _get_token_bytes() -> bytes:
    """
    Obtient un token Azure et le convertit au format attendu par pyodbc.
    Le token est renouvelé automatiquement si expiré.
    """
    token = _get_credential().get_token(TOKEN_SCOPE).token
    token_utf16 = token.encode("utf-16-le")
    return struct.pack(f"<I{len(token_utf16)}s", len(token_utf16), token_utf16)


def get_engine():
    """
    Crée un Engine SQLAlchemy pour Azure Synapse.

    Authentification :
        DefaultAzureCredential essaie dans l'ordre :
        1. Variables d'environnement  (AZURE_CLIENT_ID etc.)
        2. Managed Identity           (si déployé sur Azure)
        3. Azure CLI                  (az login) ← utilisé en local
        4. Azure PowerShell
        5. Interactive browser

    Pool :
        NullPool car les tokens expirent — chaque connexion obtient
        un token frais. Pas de connexions persistantes stale.
    """
    odbc = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{SYNAPSE_SERVER},1433;"
        f"Database={SYNAPSE_DATABASE};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=300;"
    )

    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc)}",
        poolclass=NullPool,
        echo=False,
    )

    @event.listens_for(engine, "do_connect")
    def inject_token(dialect, conn_rec, cargs, cparams):
        """Injecte le token Azure dans chaque connexion pyodbc."""
        cparams["attrs_before"] = {
            1256: _get_token_bytes()   # SQL_COPT_SS_ACCESS_TOKEN
        }

    return engine


if __name__ == "__main__":
    from sqlalchemy import text

    print("Test connexion DefaultAzureCredential...")
    print(f"  Serveur  : {SYNAPSE_SERVER}")
    print(f"  Database : {SYNAPSE_DATABASE}")

    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS test"))
            print(f"✅ Connexion réussie : {result.fetchone()}")

        # Test requête métier
        with engine.connect() as conn:
            df_test = conn.execute(
                text("SELECT TOP 3 TIMESHEETNBR, PERIODFROM "
                     "FROM timesheet_header ORDER BY PERIODFROM DESC")
            )
            rows = df_test.fetchall()
            print(f"✅ Requête métier OK : {len(rows)} lignes")
            for row in rows:
                print(f"   {row}")

    except Exception as e:
        print(f"❌ Erreur : {e}")
        print("\n💡 Solution :")
        print("   az login --use-device-code")