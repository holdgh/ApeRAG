import logging
import re
from abc import ABC, abstractmethod

from langchain import PromptTemplate

from kubechat.llm.predict import CustomLLMPredictor, Predictor
from kubechat.llm.prompts import CHINESE_QA_EXTRACTION_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class QAGenerator(ABC):
    @abstractmethod
    def gen_qa_pairs(self, text):
        pass


class AlgoletQAGenerator(QAGenerator):

    def __init__(self):
        from question_generation import pipeline
        self.qg = pipeline("question-generation", device="cpu")
        self.qa = pipeline("question-answering", device="cpu")

    def gen_qa_pairs(self, text):
        result = []
        questions = self.qg(text)
        if len(questions) == 0:
            return result

        answers = self.qa([
            {
                "question": question,
                "context": text
            }
            for question in questions
        ])
        for idx, q in enumerate(questions):
            if "answer" not in answers[idx]:
                logger.warning("no answer for question [%s]" % q)
                continue
            result.append((q, answers[idx]['answer']))
        return result


class BaiChuanQAGenerator(QAGenerator):
    def __init__(self, **kwargs):
        self.prompt_template = PromptTemplate.from_template(CHINESE_QA_EXTRACTION_PROMPT_TEMPLATE)
        self.predictor = Predictor.from_model(model="baichuan-13b", **kwargs)
        self.pattern = r"问题\d?：(.*?)答案：(.*?)(?=问题\d+：|$)"

    def gen_qa_pairs(self, text):
        prompt = self.prompt_template.format(context=text)
        response = self.predictor.generate_stream(prompt)
        matches = re.findall(self.pattern, response, re.DOTALL)
        pairs = []
        for match in matches:
            question = match[0].strip()
            answer = match[1].strip()
            pairs.append((question, answer))
        return pairs

