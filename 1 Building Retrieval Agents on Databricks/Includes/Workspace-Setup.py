# Databricks notebook source
# MAGIC %run ./_common

# COMMAND ----------

DA = DBAcademyHelper()

# COMMAND ----------

import os

catalog =  DA.catalog_name

def copy_files_to_volume(source_path, volume_name, catalog, schema):
    
    shared_volume_path = f"/Volumes/{catalog}/{schema}/{volume_name}"
    full_volume_name = f"{catalog}.{schema}.{volume_name}"
    
    try:
        # ボリュームが存在するかチェック
        if spark.sql(f"SHOW VOLUMES IN {catalog}.{schema} LIKE '{volume_name}'").collect():
            print(f"✅ ボリューム {volume_name} は既に存在します。コピーをスキップします。")
            print(f"\n\n ✍️ ボリュームパス: {full_volume_name}")
            return True

        # ボリュームが存在しないため作成
        spark.sql(f"CREATE VOLUME {full_volume_name}")
        print(f"✅ ボリューム '{full_volume_name}' がスキーマ '{schema}' に作成されました。")

        # ボリュームに対してすべてのアカウントユーザーに読み取り権限を付与
        spark.sql(f"GRANT READ VOLUME ON VOLUME {full_volume_name} TO `account users`")
        print(f"✅ '{full_volume_name}' に対してすべてのアカウントユーザーにREAD VOLUME権限を付与しました。")

        # ソースからボリュームにファイルをコピー
        for name in os.listdir(source_path):
            local_path = os.path.join(source_path, name)
            if os.path.isfile(local_path):
                src_file = f"file:{local_path}"
                dst_file = f"{shared_volume_path}/{name}"
                try:
                    dbutils.fs.cp(src_file, dst_file)
                    print(f"✅ '{name}' をボリューム '{full_volume_name}' にコピーしました。")
                except Exception as file_exc:
                    print(f"⚠️ '{name}' をコピーできませんでした: {file_exc}")

        print(f"\n\n ✍️ ボリュームパス: {full_volume_name}")
        return True
    except Exception as e:
        print(f"⛔️ エラー: {e}")
        return False


def setup_orion_docs_volume(catalog, schema):
    """
    サンプルドキュメントでorion_docsボリュームをセットアップします。
    """
    source_docs_path = os.path.join(os.getcwd(), "data/orion-docs/")
    return copy_files_to_volume(source_docs_path, "orion_docs", catalog, schema)


def setup_orion_text_volume(catalog, schema):
    """
    サンプルテキストドキュメントでorion_textボリュームをセットアップします。
    """
    source_text_path = os.path.join(os.getcwd(), "data/orion-text/")
    return copy_files_to_volume(source_text_path, "orion_text", catalog, schema)


# メイン実行ロジック
shared_schema = "data"

# 'catalog'に'data'スキーマが存在しない場合は作成
try:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{shared_schema}")
    print(f"✅ スキーマ '{catalog}.{shared_schema}' が作成されたか、既に存在します。")
    
    # カタログとスキーマに対してすべてのアカウントユーザーにUSAGE権限を付与
    spark.sql(f"GRANT USAGE ON SCHEMA {catalog}.{shared_schema} TO `account users`")
    
    schema_creation_success = True
except Exception as e:
    print(f"⛔️ データセットスキーマ '{catalog}.{shared_schema}' の作成エラー: {e}")
    schema_creation_success = False

# スキーマ作成が成功した場合のみ以下のセットアップを実行
if schema_creation_success:
    setup_orion_docs_volume(catalog, shared_schema)
    setup_orion_text_volume(catalog, shared_schema)