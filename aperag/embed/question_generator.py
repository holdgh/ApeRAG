# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import re
from abc import ABC

from langchain_core.prompts import PromptTemplate

from aperag.llm.prompts import QUESTION_EXTRACTION_PROMPT_TEMPLATE_V2

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class QuestionGenerator(ABC):
    def __init__(self, predictor, **kwargs):
        self.prompt_template = PromptTemplate(
            template=QUESTION_EXTRACTION_PROMPT_TEMPLATE_V2, input_variables=["context"]
        )
        self.predictor = predictor

    def gen_questions(self, text):
        prompt = self.prompt_template.format(context=text)
        response = ""
        for tokens in self.predictor.generate_stream([], prompt):
            response += tokens
        questions = re.sub(r"\n+", "\n", response).split("\n")
        for i, question in enumerate(questions):
            if question.startswith(str(i + 1) + "."):
                questions[i] = questions[i][2:].strip()
        return questions
