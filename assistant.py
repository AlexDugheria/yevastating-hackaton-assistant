import pandas as pd
from typing import Dict, Any
import spacy
import joblib
import logging
import warnings

from log.logger import CustomFormatter
from common.athena_client import AthenaClient
from conf.settings import ATHENA


# filter sklearn warnings
def warn(*args, **kwargs):
    pass

warnings.warn = warn

class Jarvis:

    @staticmethod
    def initialize_logger() -> None:
        """Initialize logger for the process"""

        # Define logger parameters
        handler = logging.StreamHandler()

        # Define configuration
        handler.setFormatter(CustomFormatter())
        logging.basicConfig(level=logging.INFO, handlers=[handler])


    def __init__(self, client_id:int) -> None:
        """Initializer for Jarvis assistant

        Args:
            client_id (int): id of the client

        Returns: None
        """



        # 1. Initilize logger
        self.initialize_logger()
        self.logger = logging.getLogger('JARVIS')

        # 2. Import and print logo
        with open("utils/jarvis_logo.txt", "r") as f:
            self.logo = f.read()
        self.logger.info(self.logo)

        # 3. Define client_id
        self.client_id = client_id

        # 4. Load athena client
        self.athena_client = AthenaClient(ATHENA)

        # 5. Load mediaplan
        self.mediaplans = self.get_basic_data()

        # 6. Load models
        self.logger.info('Loading models')
        self.context_model = joblib.load('models/sgd_context.joblib')
        self.action_model = joblib.load('models/sgd_action.joblib')
        self.ner_model = spacy.load('models/NER/output/model-best')

        # 7. Define context mappings
        self.context_mapping = {
            0:'mycampaign-main_page',
            1:'mycampaign-mediamix',
            2:'mycampaign-planning',
            3:'mycampaign-trafficking-adserver',
            4:'mycampaign-trafficking-analytics',
            5:'mycampaign-goals-and-progres ',
            6:'notifications-recommendations'
        }

        # 8. Define action mappings
        self.action_mapping = {
            0:'show',
            1:'interact'
        }

    def get_basic_data(self) -> pd.DataFrame:
        """Extracts basic client information and stores it.

        Returns: pd.DataFrame
        """

        self.logger.info("SETUP: Extracting client information from DB")

        basic_data = self.athena_client.run_query('sql/default_data.sql',
                                         params={
                                             'client_id': self.client_id
                                                }
                                         )
        return basic_data

    def data_preprocesser(self, prompt:str) -> pd.Series:
        """Preprocess data to ML model expected format

        Args:
            prompt (str): string to optimize

        Returns:
            pd.DataFrame
        """

        # 1. Turn everything to lowercase
        prompt = prompt.lower()

        # 2. Turn single string into pandas series
        X = pd.Series(prompt)

        return X

    def model_predictions(self, prompt: pd.Series) -> Dict[str,Any]:
        """Generate models predictions

        Args:
            prompt (pd.Series): preprocessed text prompt

        Returns:
            Dict[str,Any]: Dictionary containing predictions
        """

        # 1. Identify Context
        context = self.context_model.predict(prompt)

        # 2. Identify Action
        action = self.action_model.predict(prompt)

        # 3. Parse Input to find tags
        tags = [(word.text,word.label_) for word in self.ner_model(prompt[0]).ents]

        return {
            'context': self.context_mapping[context[0]],
            'action': self.action_mapping[action[0]],
            'tags': tags
        }

    def generate_output(self, model_preds:Dict[str,Any]) -> Dict[str,Any]:
        """_summary_

        Args:
            model_preds (Dict[str,Any]): _description_

        Returns:
            Dict[str,Any]: _description_
        """
        pass

    def main(self):
        """Main trigger for Jarvis"""

        while True:

            self.logger.info("")

            # 1. Get input prompt (temporarily for demo purposes)
            prompt = input("What can i do for you today?: ")

            # 2. Generate model inputs
            input_data = self.data_preprocesser(prompt)

            # 3. Generate model predictions
            model_preds = self.model_predictions(input_data)

            # 4. Generate output structure
            output_data = self.generate_output(model_preds=model_preds)

            self.logger.info("Here's what i can do for you, currently")
            self.logger.info("")
            for key, value in model_preds.items():
                self.logger.info(f'{key} : {value}')
            self.logger.info("")
            self.logger.info("---------------------------------------------")


if __name__ == "__main__":

    # 1. Run Assistant
    Jarvis(client_id=112).main()
