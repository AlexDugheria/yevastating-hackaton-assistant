import pandas as pd
from typing import Dict, Any, List, Tuple
import spacy
import joblib
import logging
import warnings
from difflib import SequenceMatcher
from nltk import word_tokenize
import json

from log.logger import CustomFormatter
from conf.settings import ACTION_MAPPING, CONTEXT_MAPPING
from conf.settings import interact_actions, show_actions, trigger_actions
from utils.utils import find_deepest_granularity_hierarchy, find_shallow_granularity_hierarchy


# filter sklearn warnings
def warn(*args, **kwargs):
    pass

warnings.warn = warn



class Jarvis:

    def __init__(self) -> None:
        """Initializer for Jarvis assistant

        Returns: None
        """

        # 1. Initialie Logger
        self.logger = logging.getLogger('JARVIS')

        # 2. Import and print logo
        with open("utils/jarvis_logo.txt", "r") as f:
            self.logo = f.read()
        self.logger.info(self.logo)

        # 4. Load models
        self.logger.info('Loading models')
        self.context_model = joblib.load('models/sgd_context.joblib')
        self.action_model = joblib.load('models/sgd_action.joblib')
        self.ner_model = spacy.load('models/NER/output/model-best')

        # 5. Define context mappings
        self.context_mapping = CONTEXT_MAPPING

        # 6. Define action mappings
        self.action_mapping = ACTION_MAPPING

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

    def find_proper_granularity(self, tags:List[Tuple[str,str]]) -> List[Tuple[str,str]]:
        """Identifies platform granularity by word matching

        Args:
            tags: List[Tuple[str,str]]: list containing tags

        Returns:
            List[Tuple[str,str]]
        """

        # Loop on each tag
        for i in range(len(tags)):

            # Loop on each granularity level
            for gran in ['mediaplan','channel','platform','mediarow']:

                # Clean error for granularity in case of match
                if SequenceMatcher(None, str(tags[i][0]), gran).ratio() > 0.85:
                    if tags[i][1] != 'GRANULARITY':
                        self.logger.warning(f'Found unproper tag, fixing it to proper granularity: {tags[i]}')
                        tags[i] = (str(tags[i][0]),'GRANULARITY')

        return tags

    def remove_wrong_tags(self, tags:List[Tuple[str,str]]) -> List[Tuple[str,str]]:
        """Remove incorrect tags from output

        Args:
            tags (List[Tuple[str,str]]): list of tags

        Returns:
            List[Tuple[str,str]]
        """

        downcount = 0

        # Find all budget values which are not budgets
        for i in range(len(tags)):
            i = i-downcount
            try:
                # Check if value can be converted to float
                val = float(tags[i][0])

                if type(val) == float and tags[i][1] != 'BUDGET':
                    # If value is a float but it's not a budget, delete it
                    self.logger.warning(f'FOUND WORNG TAG: REMOVING {tags[i]}')
                    del tags[i]
                    downcount += 1

            except ValueError:
                continue

        return tags

    def find_budget_tags(self, prompt:str, tags:List[Tuple[str,str]]) -> List[Tuple[str,str]]:
        """Identifies budget tag and adds them to tag

        Args:
            prompt (str): string
            tags (List[Tuple[str,str]]): list of keywords and tags

        Returns:
            List[Tuple[str,str]]: list of tags with budget tags

        """

        # Define tokens with tokenizer
        tokens = [tok for tok in word_tokenize(prompt) if tok != ',']

        # Find budget keyword
        for i in range(len(tokens)):
            if tokens[i] == 'budget' or SequenceMatcher(None, tokens[i], 'budget').ratio() > 0.9:

                # Get all budget values into tags as BUDGET tag
                for j in range(i+1, len(tokens)):
                    try:
                        val = float(tokens[j])
                        tags.append((val,'BUDGET'))

                    except ValueError:
                        break
        return tags

    def process_tags(self,prompt:str, tags: List[Tuple[str,str]]):
        """Preprocess all the tags

        Args:
            prompt (str): command prompt
            tags (List[Tuple[str,str]]): tags identified by NER model

        Returns:
            List[Tuple[str,str]]: tags processed

        """

        # 1. Remove filter tags (model to be retrained)
        tags = [tag for tag in tags if tag[1] != 'FILTER']

        # 2. Identify budget tags
        tags = self.find_budget_tags(prompt,tags)

        # 3. Clean error in granularity identification
        tags = self.find_proper_granularity(tags)

        # 4. Remove wrong tags
        tags = self.remove_wrong_tags(tags)

        return tags

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
        tags = self.process_tags(
            prompt=prompt[0],
            tags=[(word.text,word.label_) for word in self.ner_model(prompt[0]).ents]
            )

        return {
            'context': self.context_mapping[context[0]],
            'action': self.action_mapping[action[0]],
            'tags': tags
        }

    def budget_assignment(self,
                          tags:List[Tuple[str,str]],
                          deep: str,
                          output:Dict[str,Any]) -> Dict[str,Any]:
        """Properly assigns budgets in each scenario

        Args:
            tags: List[Tuple[str,str]]: list of tags
            deep: str
            output: Dict[str,Any]: output structure

        returns:
            Dict[str,Any]: dictionary containing the output structure
        """

        # Extract granularity level and budget tags
        level_tag = [tag[0] for tag in tags if tag[1] == deep]
        budget_tag = [float(tag[0]) for tag in tags if tag[1] == 'BUDGET']

        # CASE 1: perfect match
        if len(level_tag) == len(budget_tag) and len(level_tag) > 0:

            self.logger.info(f'Found {len(level_tag)} granularities and {len(budget_tag)} budgets, proceeding with matching')

            total_budget = 0

            for i in range(len(level_tag)):

                output['level_deep']['data'].append({
                    f'{deep.lower()}_name':level_tag[i],
                    'budget':budget_tag[i]
                })

                total_budget += budget_tag[i]

            output['budget'] = total_budget

            self.logger.info(f'Total budget allocated: {total_budget}')


        # CASE 2: only 1 budget and no granularity
        elif deep == 'MEDIAPLAN' and len(budget_tag) == 1:
            self.logger.info('No granularity deeper than mediaplan found. Assigning budget at mediaplan level')
            output['budget'] = budget_tag[0]

        # CASE 3: no budgets given but we have granularities
        elif len(budget_tag) == 0 and len(level_tag) > 0:
            self.logger.info('No budgets declared. proceeding with no budget')
            for i in range(len(level_tag)):

                output['level_deep']['data'].append({
                    f'{deep.lower()}_name':level_tag[i],
                    'budget':0
                })

        # CASE 4: more budget declared than deeper granularities values
        elif len(budget_tag) > len(level_tag):

            self.logger.info('Found multiple budgets, more than granularities. Taking last declared')
            # Define total budget
            total_budget = 0

            # Cut budget array to match deepest granularity given
            budget_tag_cut = budget_tag[-(len(level_tag)):]

            for i in range(len(level_tag)):

                output['level_deep']['data'].append({
                    f'{deep.lower()}_name':level_tag[i],
                    'budget':budget_tag_cut[i]
                })

                total_budget += budget_tag_cut[i]

            self.logger.info(f'Total budget allocated {total_budget}')
            output['budget'] = total_budget


        # Any other scenario return the granularities
        else:
            for i in range(len(level_tag)):

                output['level_deep']['data'].append({
                    f'{deep.lower()}_name':level_tag[i],
                    'budget':0
                })

        return output

    def generate_output(self, model_preds:Dict[str,Any]) -> Dict[str,Any]:
        """Builds output structure

        Args:
            model_preds (Dict[str,Any]): _description_

        Returns:
            Dict[str,Any]: _description_
        """

        output_base_structure = {
            'main_action':'',
            'level_main':'',
            'budget': 0,
            'level_deep':{
                'name': '',
                'data':[]
                }
            }

        # Get tags
        tags = model_preds['tags']

        # Search for main action
        for tag in tags:
            if tag[1] == 'ACTION':

                # Extract Action token
                action = tag[0]

                # Identify proper action class
                if action in interact_actions['create']:
                    output_base_structure['main_action'] = 'create'
                elif action in interact_actions['modify']:
                    output_base_structure['main_action'] = 'modify'
                elif action in interact_actions['decision']:
                    output_base_structure['main_action'] = 'decision'
                elif action in show_actions:
                    output_base_structure['main_action'] = 'show'
                elif action in trigger_actions:
                    output_base_structure['main_action'] = 'trigger'
                else:
                    output_base_structure['main_action'] = 'unclear'

        # Search for granularity
        granularities = []

        # EXTRACT ALL GRANULARITIES
        for tag in tags:
            if tag[1] == 'GRANULARITY':
                granularities.append(tag[0])

        # FIND DEEPEST LEVEL
        deep = find_deepest_granularity_hierarchy(granularities)
        shallow = find_shallow_granularity_hierarchy(granularities)

        if not deep == shallow == 'MEDIAROW':
            shallow = 'MEDIAPLAN'

        # store deepest level
        output_base_structure['level_main'] = shallow.lower()
        output_base_structure['level_deep']['name'] = deep.lower()

        # GENERATE TAXONOMY
        output = self.budget_assignment(tags,deep,output_base_structure)

        return output

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
            for key, value in model_preds.items():
                self.logger.info(f'{key} : {value}')
            self.logger.info("")
            self.logger.info("Here's your output")
            self.logger.info(json.dumps(output_data,indent=4))
            self.logger.info("")
            self.logger.info("---------------------------------------------")


if __name__ == "__main__":

    # Define logger parameters
    handler = logging.StreamHandler()

    # Define configuration
    handler.setFormatter(CustomFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])

    # 1. Run Assistant
    Jarvis().main()
