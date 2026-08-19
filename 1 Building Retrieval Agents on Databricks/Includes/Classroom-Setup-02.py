# Databricks notebook source
# MAGIC %run ./Classroom-Setup-Common

# COMMAND ----------

# MAGIC %md
# MAGIC **適切なコンピュート環境の確認:**

# COMMAND ----------

if not is_serverless_5():
    raise EnvironmentError("⛔️ エラー: このノートブックはDatabricks Serverless 5環境で実行する必要があります。コンピュートをServerless 5に切り替えて再試行してください。")
else:
    print("✅ 環境チェック成功: Serverless 5が検出されました。")

# COMMAND ----------

# MAGIC %md
# MAGIC **このデモ/ラボに必要な変数:**

# COMMAND ----------

print(f"✍️ サンプルドキュメントボリューム: {user_docs_volume}")

# COMMAND ----------

import json
from typing import Any, Optional

def _page_id_from_bbox(bbox: Any) -> Optional[int]:
    """
    bboxはlist[dict]、dict、またはNoneの場合があります。存在する場合はbbox.page_idを返します。
    意図的にシンプルに保たれています。
    """
    if not bbox:
        return None
    if isinstance(bbox, list) and bbox:
        first = bbox[0] or {}
        return first.get("page_id")
    if isinstance(bbox, dict):
        return bbox.get("page_id")
    return None

def extract_contents_from_json(json_str: str) -> str:
    """
    - 要素の'content'を連結します（見つからない場合は'description'にフォールバック）。
    - page_idが変更されたときに'== page =='を挿入します。
    - typeが'text'でない要素の後に改行を追加します。
    - 失敗時にエラー文字列を返します（DataFrameでのデバッグを容易にするため）。
    """
    try:
        doc = json.loads(json_str) if isinstance(json_str, str) else json_str
        if not isinstance(doc, dict):
            return ""

        # {"document":{"elements":[...]}}と{"elements":[...]}の両方をサポート
        document = doc.get("document", doc)
        elements = document.get("elements", []) if isinstance(document, dict) else []
        if not isinstance(elements, list):
            return ""

        out_lines = []
        current_page = None

        for el in elements:
            if not isinstance(el, dict):
                continue

            # 変更時のページ区切り
            pid = _page_id_from_bbox(el.get("bbox"))
            if pid is not None and current_page is not None and pid != current_page:
                out_lines.append("")
                out_lines.append("== page ==")
                out_lines.append("")
            if pid is not None:
                current_page = pid

            # コンテンツ（descriptionにフォールバック）
            c = el.get("content")
            if not (isinstance(c, str) and c.strip()):
                c = el.get("description")
            if isinstance(c, str) and c.strip():
                out_lines.append(c)

                # テキスト以外の要素の後に改行を追加
                t = (el.get("type") or "").lower()
                if t != "text":
                    out_lines.append("")  # 結合後に空行を生成

        return "\n".join(out_lines)

    except Exception as e:
        return f"Error: {str(e)}"


# 上記の関数を使用するPySpark UDFを作成する小さなファクトリー。
def extract_contents_udf():
    from pyspark.sql.types import StringType
    from pyspark.sql.functions import udf
    @udf(StringType())
    def _udf(json_str):
        try:
            return extract_contents_from_json(json_str)
        except Exception as e:
            return f"Error: {str(e)}"
    return _udf