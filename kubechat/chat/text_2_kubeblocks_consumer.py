import asyncio
import logging

from langchain import OpenAI
from langchain.llms.base import BaseLLM
from llama_index import Prompt
from llama_index.langchain_helpers.chain_wrapper import LLMPredictor

from typing import Any, List, Optional, Sequence, cast

from kubechat.chat.base_consumer import BaseConsumer
from services.kubeblocks.base import KubeBlocks
from services.kubeblocks.text2cd import Text2CD
from services.kubeblocks.text2cv import Text2CV
from services.kubeblocks.text2cluster import Text2CLUSTER
from services.kubeblocks.text2kbcli import Text2KBCLI

logger = logging.getLogger(__name__)


class PredictInfo:
    def __init__(
            self,
            generator: KubeBlocks,
            metadata: str,
    ):
        self.metadata = metadata
        self.generator = generator

    def predict(self, query: str):
        return self.generator.predict(query)


# get discrete metadata together to a long metadata
def get_funcs_prompts(predictors: List[PredictInfo]):
    texts: List[str] = []
    for ind, predictor in enumerate(predictors):
        text = " ".join(predictor.metadata.splitlines())
        text = f"({ind + 1} {text}"
        texts.append(text)
    return "\n\n".join(texts)


# Extract the first integer within parentheses from a string.
def extract_number_from_parentheses(s: str) -> int:
    num_str = ""
    for char in s:
        if char == "(":
            continue
        elif char.isdigit() and not num_str:
            num_str += char
        elif char.isdigit() and num_str:
            num_str += char
        elif char == ")" and num_str:
            break
    return int(num_str) if num_str else None


SINGLE_SELECT_PROMPT_TMPL = (
    "Some choices are given below. It is provided in a numbered list "
    "(1 to {num_choices}),"
    "where each item in the list corresponds to a summary.\n"
    "---------------------\n"
    "{context_list}"
    "\n---------------------\n"
    "Using only the choices above and not prior knowledge, return "
    "the choice that is most relevant to the question: '{query_str}'\n"
    "you must only output the order of your choice, such as '(1)'\n"
)
TEXT_TO_KUBEBLOCKS_ROUTER = Prompt(
    SINGLE_SELECT_PROMPT_TMPL,
    stop_token="\nResult:",
    prompt_type="text_to_kubeblocks_router",
)


# use llm to predict which genarator will be routed to
class RouterPredictEngine:
    def __init__(
            self,
            predict_choice: List[PredictInfo],
            llm: Optional[BaseLLM] = None,
    ):
        self.predict_choice = predict_choice
        if llm is None:
            self.llm = OpenAI(
                temperature=0,
                model_name="text-davinci-003",
                max_tokens=-1,
                streaming=True,
            )
        else:
            self.llm = llm
        self.llm_predict = LLMPredictor(llm=self.llm)
        self.choice_text = get_funcs_prompts(self.predict_choice)

    def select_predictor(self, query):
        response, _ = self.llm_predict.predict(
            prompt=TEXT_TO_KUBEBLOCKS_ROUTER,
            num_choices=len(self.predict_choice),
            context_list=self.choice_text,
            query_str=query
        )
        try:
            order = extract_number_from_parentheses(response) - 1
        except Exception as e:
            logger.error(f"select_predictor(): can not router to proper predictor:{e}")
        return order

    def predict(self, query):
        predict_ind = self.select_predictor(query)
        if predict_ind == -1 or predict_ind >= len(self.predict_choice):
            response = "None of cluster definition YAML, cluster version YAML and cluster YAML generators was chosen, " \
                       "Please Modify your requirements to include explicitly cluster definition YAML、cluster version " \
                       "YAML and cluster YAML"
            return response
        logger.info(f"select predict engine:{predict_ind + 1}")
        response = self.predict_choice[predict_ind].predict(query)
        return response


class Text2KubeblocksConsumer(BaseConsumer):
    def __init__(self):
        super().__init__()

        text2cd_info = PredictInfo(Text2CD(), "Useful for create cluster definition yaml(cd) according to input query, "
                                              "not used to create cluster version yaml(cv), cluster yaml or kbcli "
                                              "command")
        text2cv_info = PredictInfo(Text2CV(),
                                   "Useful for create cluster version yaml(cv) according to input query, not used "
                                   "to create cluster definition yaml(cd), cluster yaml or kbcli command")
        text2cluster_info = PredictInfo(Text2CLUSTER(),
                                        "Useful for create cluster yaml(cv) according to input query, not used to "
                                        "create cluster definition yaml(cd), cluster version yaml or kbcli command")
        text2kbcli_info = PredictInfo(Text2KBCLI(),
                                      "Useful for create kbcli command according to input query, not used to "
                                      "create cluster definition yaml(cd), cluster version yaml or cluster yaml(cv)")
        self.router_engine = RouterPredictEngine([text2cd_info, text2cv_info, text2cluster_info, text2kbcli_info])

    def predict(self, query):
        response = self.router_engine.predict(query)
        return response


if __name__ == '__main__':
    kb = Text2KubeblocksConsumer()
    # ans = kb.predict("what is your name?")
    ans = kb.predict("generate a kbcli command to list differences of kubeblocks version 0.4.0 and 0.5.0")
    print(ans)
