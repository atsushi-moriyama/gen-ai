# Databricks notebook source
# MAGIC %run ./_install_libraries

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors.platform import NotFound
import pyspark.sql.functions as F

class NestedNamespace:

    def __init__(self, dictionary: dict = None, prefix=None):
        prefix = prefix + '.' if prefix else ''
        self.__setattr_direct('dictionary', dictionary or dict())
        self.__setattr_direct('prefix', prefix)
        self.__setattr_direct('iterator', None)

    def __getattr__(self, name):
        name = self.prefix + name
        return self.dictionary.get(name, NestedNamespace(dictionary=self.dictionary, prefix=name))

    def __setattr__(self, name, value):
        name = self.prefix + name
        self.dictionary[name] = value

        # 辞書内のノードを上書きしたため、子/祖先を削除してブランチを剪定する
        name += '.'
        children = [k for k in filter(lambda x: x.startswith(name), self.dictionary.keys())]
        for k in children:
            del(self.dictionary[k])

    # オーバーライドされた動作をバイパスして属性を直接設定する
    def __setattr_direct(self, name, value):
        super().__setattr__(name, value)

    def __repr__(self):
        args = [f"{key}='{self[key]}'" for key in self]
        return f"{self.__class__.__name__} ({', '.join(args)})" if args else ""

    def __iter__(self):
        self.__setattr_direct(
            'iterator',
            filter(
                lambda x: x.startswith(self.prefix),
                iter(self.dictionary)
            )
        )

        return self

    def __next__(self):
        return next(self.iterator).removeprefix(self.prefix) if self.iterator else None

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __setitem__(self, name, value):
        return self.__setattr__(name, value)

class DBAcademyHelper(NestedNamespace):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.workspace = WorkspaceClient()

        try:
            default_catalog = self.workspace.settings.default_namespace.get().namespace.value
        except:
            default_catalog = 'dbacademy'

        meta = f'{default_catalog}.ops.meta'
        catalog = None
        schema = None

        from py4j.protocol import Py4JJavaError
        from pyspark.errors import PySparkException

        try:
            rows = spark.table(meta).collect()
        except Py4JJavaError:
            raise Exception(f'メタデータテーブル {meta} へのアクセス中にエラーが発生しました。サーバレスまたはDBR >= 15.1を使用していますか？')
        except PySparkException:
            raise Exception(f'メタデータテーブル {meta} が見つからないか、アクセスできません。適切に設定されたメタストアで実行していますか？')

        # メタデータテーブルをクエリし、キー/値でselfに値を設定する
        for row in rows:
            setattr(self, row['key'], row['value'])

            if row['key'] == 'catalog_name':
                catalog = row['value']
            elif row['key'] == 'schema_name':
                schema = row['value']

        # メタデータに従ってデフォルトのカタログとスキーマを設定する
        if catalog:
            spark.sql(f'USE CATALOG {catalog}')

            if schema:
                spark.sql(f'USE SCHEMA {schema}')

    # イニシャライザーを追加する。イニシャライザーはチェーンでき、DA.init()が呼ばれた時にすべて呼び出される。
    # このパターンにより、セルやノートブック間でクラスを動的に拡張しやすくなる。
    # 使用方法はいくつかあるが、関数デコレーターとして使うのが最も簡単：
    #   @DBAcademyHelper.add_init
    #   def init(self)
    #       ...
    # 別の方法：
    #   def init(self):
    #       ...
    #   DBAcademyHelper.add_init(init)
    #
    # DA.init()が呼ばれると、すべてのイニシャライザーが追加された順序で呼び出される

    @classmethod
    def add_init(cls, function_ref):
        try:
            initializers = getattr(cls, '_initializers')
        except AttributeError:
            initializers = list()

        initializers += [function_ref]
        setattr(cls, '_initializers', initializers)
        return function_ref

    # クラスメソッドを追加する（いわゆる「モンキーパッチ」）。このパターンにより、
    # セルやノートブック間でクラスを動的に拡張しやすくなる。
    # 使用方法はいくつかあるが、これが最も簡単：
    #   @DBAcademyHelper.add_method
    #   def method(self)
    #       ...
    # 別の方法：
    #   def method(self):
    #       ...
    #   DBAcademyHelper.add_method(method)
    #
    # 最終的に、新しいメソッドはノートブックコード内から呼び出すことができる：
    #   DA.method()
    
    @classmethod
    def add_method(cls, function_ref):
        setattr(cls, function_ref.__name__, function_ref)
        return function_ref

    def init(self):

        for key in self:
            value = self[key]

            if value and type(value) == str:
                try:
                    spark.conf.set(f'DA.{key}', value)
                    spark.conf.set(f'da.{key}', value)
                except:
                    # サーバレスでは失敗する
                    pass

        try:
            for i in getattr(self.__class__, '_initializers'):
                i(self)

        except AttributeError:
            pass

    def print_copyrights(self):
        datasets = self.datasets

        for i in datasets:
            catalog = datasets[i].split('.')[0]
            description = spark.sql(
                f'DESCRIBE CATALOG {catalog}'
            ).where(
                F.col('info_name') == 'Comment'
            ).select(
                'info_value'
            ).collect(
            )[0]['info_value']
            print(description)
    
    # SDKを介して一般的な検索を実行する。例えば、名前を指定して構造のIDを見つける。使用例：
    # DA.workspace_find("catalogs", "main") -> "main"という名前のカタログを表すSDK構造を返す
    # DA.workspace_find("cluster_policies", "DBAcademy DLT") -> 指定されたポリシーを表す構造を返す
    # 注意：これが機能するためには、SDKに"item_type"で指定されたAPIがあり、"list" apiを持つ必要があり、
    # "name"要素に基づいて検索することを想定している。しかし、これらの条件がすべて満たされない場合は、
    # "member"と"api"を使用して独自の検索関数を実装せずに動作を調整できる。いくつかの例：
    # DA.workspace_find("clusters", "0913-023811-rzeq07rk", "cluster_id") -> 
    # "cluster_id"の値が一致するクラスター構造を返す
    # DA. workspace_find('pipelines', pipeline_name, api='list_pipelines') -> 
    # 指定されたDLTパイプラインを表す構造を返す
    def workspace_find(
        self,
        item_type: str,
        value: str=None,
        member: str='name',
        api: str='list'
    ):
        # API（アイテムタイプ）を見つけて、"list"メソッドを取得する
        method = getattr(getattr(self.workspace, item_type), api)

        # list()が返したものを反復処理する
        for item in method():
            if getattr(item, member) == value:
                return item

    def unique_name(self, sep: str) -> str:
        return self.pseudonym.replace(' ', sep)