# Databricks notebook source
import re
from typing import Optional

def _safe_uc_name(value: str) -> str:
    # UC identifiers are generally safest with letters, numbers, underscores
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_]", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "user"


def _current_user_email() -> str:
    """
    Get the user's name and email address.
    """
    return spark.sql("SELECT current_user()").first()[0]


def _get_workspace_catalogs() -> set[str]:
    """
    Returns a set of Catalogs visible to that user.
    """
    list_of_catalogs_in_workspace = {
        c.name.lower() for c in spark.catalog.listCatalogs()
    }
    return list_of_catalogs_in_workspace


def _catalog_exists(name: str, catalogs: set[str]) -> bool:
    """
    Catalog checker to see if the catalog already exists for that user.
    """
    catalog_exists = name.lower() in catalogs
    return catalog_exists


def build_user_catalog(prefix: str = "labuser", catalog_forced = None) -> str:
    """
    Returns a UC catalog name for the current user.

    Parameters
    ----------
    prefix: str
        Prefix for the catalog name. Default is 'labuser'.
    catalog_forced: str
        Uses this catalog name if specified. Otherwise uses the prefix and user's name.

    Vocareum behavior:
      - If a catalog equals the user's 'labuserxxx' name and already exists,
        assume you are in Vocareum and use it.
      - Assumes users have a catalog by default in Vocareum.

    Other workspaces:
      - Use <prefix>_<user> and create it if possible for that user.
    """

    # Obtain user's email and user name name
    user_email = _current_user_email()
    user_name = user_email.split("@")[0]

    # Make the user name safe if it's not in Vocareum
    safe_user_name = _safe_uc_name(user_name)

    # Obtain list of catalogs
    WORKSPACE_CATALOGS = _get_workspace_catalogs()

    # VOCAREUM CHECKER: Catalog is just the username (already provisioned)
    # and starts with 'labuser'
    vocareum_catalog_name = safe_user_name

    if _catalog_exists(name=vocareum_catalog_name, catalogs=WORKSPACE_CATALOGS) and user_email.lower().endswith("@vocareum.com"):
        print("✅ Vocareum Workspace check. Learner is using a Vocareum Workspace.")
        print(f"✅ Catalog check. User catalog '{vocareum_catalog_name}' already exists in Vocareum. Using this catalog.")
        return vocareum_catalog_name
    # OTHER WORKSPACE SETUP
    else:    
        print("Learner is not using a Databricks Academy provided Vocareum Workspace.")

        # Setting catalog for workspaces outside of Vocareum using the provided prefix and user name
        # If catalog_forced is set, will use that by default.
        if catalog_forced is None:
            catalog_name = f"{prefix}_{safe_user_name}"
        else:
            catalog_name = catalog_forced


        # Check if the user already has this catalog with the prefix_safeusername
        if _catalog_exists(name=catalog_name, catalogs=WORKSPACE_CATALOGS):
            print(f"✅ Catalog '{catalog_name}' already exists in your Workspace. Using this catalog.")
            return catalog_name

        # Try to create it if not available
        # Will not work if the user cannot create catalogs in the workspace
        try:
            print(f"Catalog name '{catalog_name}' does not exist in your Workspace.")
            print(f"Creating catalog '{catalog_name}'...")
            spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog_name}`")
            print(f"✅ Created catalog '{catalog_name}'.")
        except Exception as e:
            print(
                f"⚠️ Could not create catalog '{catalog_name}'. "
                "You may not have privileges to create catalogs in this workspace.\n"
                f"Error: {e}"
            )

        return catalog_name

# COMMAND ----------

def setup_complete_msg():
  '''
  Prints a note in the output that the setup was complete.
  '''
  print('\n------------------------------------------------------------------------------')
  print('✅ SETUP COMPLETE!')
  print('------------------------------------------------------------------------------')

# COMMAND ----------

def display_config_values(config_values):
    """
    Displays list of key-value pairs as rows of HTML text and textboxes
    
    param config_values: 
        list of (key, value) tuples
        
    Returns
    ----------
    HTML output displaying the config values
    Example
    --------
    display_config_values([('catalog', 'your catalog'),('schema','your schema')])
    """
    html = """<table style="width:100%">"""
    for name, value in config_values:
        html += f"""
        <tr>
            <td style="white-space:nowrap; width:1em">{name}:</td>
            <td><input type="text" value="{value}" style="width: 100%"></td></tr>"""
    html += "</table>"
    displayHTML(html)

# COMMAND ----------

## Unique to this course
def build_environment(
    schema_name: str, 
    catalog_forced: str
    ) -> tuple[str, str]:
    """
    Returns a UC schema name for the current user.
    """
    catalog_name = build_user_catalog(catalog_forced = catalog_forced)
    spark.sql(f"USE CATALOG {catalog_name}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{schema_name}")
    spark.sql(f"USE SCHEMA {schema_name}")
    print(f"✅ Created schema '{schema_name}' in catalog '{catalog_name}'.")
    print(f"Using Catalog {catalog_name} and Schema {schema_name}.")
    return catalog_name, schema_name