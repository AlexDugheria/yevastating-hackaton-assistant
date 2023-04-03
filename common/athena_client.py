import logging
import boto3
import pythena
import pandas as pd

from typing import Dict, Any
from conf.settings import ATHENA

class AthenaClient:
    logger_name = "Athena Client"

    def __init__(self, config: Dict[str, Any]):
        """Initializer for the Athena client

        Args:
            config (dict): {
                db_name str,
                region: str,
                output_url: str,
                save_results: bool,
                workgroup: str
            }
        """

        self.logger = logging.getLogger(self.logger_name)
        self.config = config
        self.db = pythena.Athena(
            database=self.config["db_name"], region=self.config["region"]
        )
        self.boto3_client = boto3.client("athena")

    @staticmethod
    def read_sql(query_path: str, params: Dict[str, Any] = None) -> str:
        """Reads sql query file and formats it.

        Args:
            query_path (str): query path

        Returns:
            str: sql query
        """

        # 1. Read sql file
        with open(query_path, "r") as f:
            query = f.read()

        # 2. If params are given, format the query
        if not params:
            return query
        else:
            return query.format(**params)

    def execute_query(self, query: str) -> pd.DataFrame:
        """Runs query

        Args:
            query (str): _description_

        Returns:
            pd.DataFrame: _description_
        """

        try:
            dataframe, query_id = self.db.execute(
                query=query,
                s3_output_url=self.config["output_url"],
                save_results=self.config["save_results"],
                workgroup=self.config["workgroup"],
            )
        except Exception as e:
            self.logger.warning(query)
            raise e

        return dataframe, query_id

    def run_query(self, query_path: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """Reads data from athena

        This method takes a query string and a dictionary of parameters.
        The query gets formatted and then gets triggered.
        The output is a Pandas dataframe containing the query results

        Args:
            query_path (str): location of the query to read
            params (Dict[str,Any], optional): format parameters. Defaults to None.

        Returns:
            pd.DataFrame: results of the query
        """

        # 1. Extract and read sql query
        query = self.read_sql(query_path=query_path, params=params)

        # 2. Execute query
        dataframe, query_id = self.execute_query(query=query)

        return dataframe
