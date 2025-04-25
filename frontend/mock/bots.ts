const bots = [
  {
    id: 'botd9b25d1aec9f9d3b',
    title: '测试',
    type: 'knowledge',
    description: null,
    config:
      '{"model": "gpt-4", "llm": {"prompt_template": "\\n\\u5019\\u9009\\u7b54\\u6848\\u4fe1\\u606f\\u5982\\u4e0b\\n----------------\\n{context}\\n--------------------\\n\\n\\u4f60\\u662f\\u4e00\\u4e2a\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u5019\\u9009\\u7b54\\u6848\\u4fe1\\u606f\\u7ec4\\u7ec7\\u56de\\u7b54\\u7684\\u4e13\\u5bb6\\uff0c\\u4f60\\u7684\\u56de\\u7b54\\u4e25\\u683c\\u9650\\u5b9a\\u4e8e\\u7ed9\\u4f60\\u63d0\\u4f9b\\u7684\\u4fe1\\u606f\\uff0c\\u5982\\u679c\\u5019\\u9009\\u7b54\\u6848\\u5c11\\u4e8e50\\u4e2a\\u5b57\\uff0c\\u5c31\\u539f\\u6837\\u8f93\\u51fa\\u3002\\n \\n\\u4f60\\u9700\\u8981\\u8c28\\u614e\\u51c6\\u786e\\u7684\\u6839\\u636e\\u63d0\\u4f9b\\u7684markdown\\u683c\\u5f0f\\u7684\\u4fe1\\u606f\\uff0c\\u7136\\u540e\\u56de\\u7b54\\u95ee\\u9898\\uff1a{query}\\u3002\\n \\n\\u8bf7\\u4e00\\u6b65\\u4e00\\u6b65\\u601d\\u8003\\uff0c\\u8bf7\\u786e\\u4fdd\\u56de\\u7b54\\u51c6\\u786e\\u548c\\u7b80\\u6d01\\uff0c\\u5982\\u679c\\u4f60\\u4e0d\\u77e5\\u9053\\u7b54\\u6848\\uff0c\\u5c31\\u76f4\\u63a5\\u8bf4\\u4f60\\u4e0d\\u77e5\\u9053\\uff0c\\u4e0d\\u8981\\u8bd5\\u56fe\\u7f16\\u9020\\u4e00\\u4e2a\\u7b54\\u6848\\u3002\\n\\n\\u95ee\\u9898\\u53ea\\u56de\\u7b54\\u4e00\\u6b21\\u3002\\n", "context_window": 8192, "similarity_score_threshold": 0.5, "similarity_topk": 3, "temperature": 0, "endpoint": "https://api.openai.com/v1"}, "enable_keyword_recall": false, "memory": false}',
    system: false,
    collections: [
      {
        id: 'col3544125b631a1337',
        title: 'asdasdasdasd',
        description: null,
        status: 'QUESTION_PENDING',
        type: 'document',
        bot_ids: [],
        system: false,
        config:
          '{"source": "system", "crontab": {"enabled": false, "minute": "0", "hour": "0", "day_of_month": "*", "month": "*", "day_of_week": "*"}, "embedding_model": "bge"}',
        created: '2023-11-09T10:56:33.339629+00:00',
        updated: '2025-04-01T09:26:11.443915+00:00',
      },
    ],
    created: '2023-11-23T07:10:21.338020+00:00',
    updated: '2024-02-21T09:14:11.609955+00:00',
  },
  {
    id: 'bot44c9adee9c4c71fe',
    title: '翻译',
    type: 'knowledge',
    description: null,
    config:
      '{"model": "gpt-4", "llm": {"similarity_score_threshold": 0.5, "similarity_topk": 3, "temperature": 0, "context_window": 8192, "prompt_template": "\\n\\u5019\\u9009\\u7b54\\u6848\\u4fe1\\u606f\\u5982\\u4e0b\\n----------------\\n{context}\\n--------------------\\n\\n\\u4f60\\u662f\\u4e00\\u4e2a\\u6839\\u636e\\u63d0\\u4f9b\\u7684\\u5019\\u9009\\u7b54\\u6848\\u4fe1\\u606f\\u7ec4\\u7ec7\\u56de\\u7b54\\u7684\\u4e13\\u5bb6\\uff0c\\u4f60\\u7684\\u56de\\u7b54\\u4e25\\u683c\\u9650\\u5b9a\\u4e8e\\u7ed9\\u4f60\\u63d0\\u4f9b\\u7684\\u4fe1\\u606f\\uff0c\\u5982\\u679c\\u5019\\u9009\\u7b54\\u6848\\u5c11\\u4e8e50\\u4e2a\\u5b57\\uff0c\\u5c31\\u539f\\u6837\\u8f93\\u51fa\\u3002\\n \\n\\u4f60\\u9700\\u8981\\u8c28\\u614e\\u51c6\\u786e\\u7684\\u6839\\u636e\\u63d0\\u4f9b\\u7684markdown\\u683c\\u5f0f\\u7684\\u4fe1\\u606f\\uff0c\\u7136\\u540e\\u56de\\u7b54\\u95ee\\u9898\\uff1a{query}\\u3002\\n \\n\\u8bf7\\u4e00\\u6b65\\u4e00\\u6b65\\u601d\\u8003\\uff0c\\u8bf7\\u786e\\u4fdd\\u56de\\u7b54\\u51c6\\u786e\\u548c\\u7b80\\u6d01\\uff0c\\u5982\\u679c\\u4f60\\u4e0d\\u77e5\\u9053\\u7b54\\u6848\\uff0c\\u5c31\\u76f4\\u63a5\\u8bf4\\u4f60\\u4e0d\\u77e5\\u9053\\uff0c\\u4e0d\\u8981\\u8bd5\\u56fe\\u7f16\\u9020\\u4e00\\u4e2a\\u7b54\\u6848\\u3002\\n\\n\\u95ee\\u9898\\u53ea\\u56de\\u7b54\\u4e00\\u6b21\\u3002\\n", "memory_prompt_template": "\\n\\u4f60\\u662f\\u4e00\\u4e2a\\u6839\\u636e\\u5bf9\\u8bdd\\u8bb0\\u5f55\\u548c\\u5019\\u9009\\u7b54\\u6848\\u6765\\u56de\\u7b54\\u95ee\\u9898\\u7684\\u4e13\\u5bb6\\uff0c\\u4f60\\u7684\\u56de\\u7b54\\u4e25\\u683c\\u9650\\u5b9a\\u4e8e\\u521a\\u624d\\u7684\\u5bf9\\u8bdd\\u8bb0\\u5f55\\u548c\\u4e0b\\u9762\\u7ed9\\u4f60\\u63d0\\u4f9b\\u7684\\u5019\\u9009\\u7b54\\u6848\\u3002\\n\\n\\u4f60\\u9700\\u8981\\u57fa\\u4e8e\\u521a\\u624d\\u7684\\u5bf9\\u8bdd\\u8bb0\\u5f55\\uff0c\\u8c28\\u614e\\u51c6\\u786e\\u7684\\u4f9d\\u636emarkdown\\u683c\\u5f0f\\u7684\\u5019\\u9009\\u7b54\\u6848\\uff0c\\u6765\\u56de\\u7b54\\u95ee\\u9898\\uff1a{query}\\u3002\\n\\n\\u8bf7\\u4e00\\u6b65\\u4e00\\u6b65\\u601d\\u8003\\uff0c\\u8bf7\\u786e\\u4fdd\\u56de\\u7b54\\u51c6\\u786e\\u548c\\u7b80\\u6d01\\uff0c\\u5982\\u679c\\u4ece\\u5bf9\\u8bdd\\u8bb0\\u5f55\\u548c\\u5019\\u9009\\u7b54\\u6848\\u4e2d\\u627e\\u4e0d\\u51fa\\u56de\\u7b54\\uff0c\\u5c31\\u76f4\\u63a5\\u8bf4\\u4f60\\u4e0d\\u77e5\\u9053\\uff0c\\u4e0d\\u8981\\u8bd5\\u56fe\\u7f16\\u9020\\u4e00\\u4e2a\\u56de\\u7b54\\u3002\\n\\n\\u95ee\\u9898\\u53ea\\u56de\\u7b54\\u4e00\\u6b21\\u3002\\n\\n\\u5019\\u9009\\u7b54\\u6848\\u5982\\u4e0b:\\n----------------\\n{context}\\n--------------------\\n"}, "memory": false}',
    system: false,
    collections: [
      {
        id: 'col3544125b631a1337',
        title: 'asdasdasdasd',
        description: null,
        status: 'QUESTION_PENDING',
        type: 'document',
        bot_ids: [],
        system: false,
        config:
          '{"source": "system", "crontab": {"enabled": false, "minute": "0", "hour": "0", "day_of_month": "*", "month": "*", "day_of_week": "*"}, "embedding_model": "bge"}',
        created: '2023-11-09T10:56:33.339629+00:00',
        updated: '2025-04-01T09:26:11.443915+00:00',
      },
    ],
    created: '2023-12-13T05:55:26.527246+00:00',
    updated: '2023-12-13T05:55:26.541055+00:00',
  },
  {
    id: 'bot9c0da34887a3f345',
    title: '中文->英文翻译专家',
    type: 'common',
    description: null,
    config:
      '{"model": "gpt-4-1106-preview", "llm": {"similarity_score_threshold": 0.5, "similarity_topk": 10, "temperature": 0, "context_window": 128000, "prompt_template": "\\n\\u4f60\\u662f\\u4e00\\u4f4d\\u7cbe\\u901a\\u4e2d\\u6587\\u7684\\u4e13\\u4e1a\\u7ffb\\u8bd1\\uff0c\\u5c24\\u5176\\u64c5\\u957f\\u5c06\\u4e13\\u4e1a\\u5b66\\u672f\\u8bba\\u6587\\u7ffb\\u8bd1\\u6210\\u6d45\\u663e\\u6613\\u61c2\\u7684\\u79d1\\u666e\\u6587\\u7ae0\\u3002\\n\\n\\u6211\\u5e0c\\u671b\\u4f60\\u80fd\\u5e2e\\u6211\\u5c06\\u4ee5\\u4e0b\\u4e2d\\u6587\\u6280\\u672f\\u6587\\u7ae0\\u6bb5\\u843d\\u7ffb\\u8bd1\\u6210\\u82f1\\u6587\\uff0c\\u98ce\\u683c\\u4e0e\\u79d1\\u666e\\u6742\\u5fd7\\u7684\\u82f1\\u6587\\u7248\\u76f8\\u4f3c\\u3002\\n\\n\\u89c4\\u5219\\uff1a\\n- \\u7ffb\\u8bd1\\u65f6\\u8981\\u51c6\\u786e\\u4f20\\u8fbe\\u539f\\u6587\\u7684\\u4e8b\\u5b9e\\u548c\\u80cc\\u666f\\u3002\\n- \\u5373\\u4f7f\\u4e0a\\u610f\\u8bd1\\u4e5f\\u8981\\u4fdd\\u7559\\u539f\\u59cb\\u6bb5\\u843d\\u683c\\u5f0f\\uff0c\\u4ee5\\u53ca\\u4fdd\\u7559\\u672f\\u8bed\\uff0c\\u4f8b\\u5982 FLAC\\uff0cJPEG \\u7b49\\u3002\\u4fdd\\u7559\\u516c\\u53f8\\u7f29\\u5199\\uff0c\\u4f8b\\u5982 Microsoft, Amazon \\u7b49\\u3002\\n- \\u540c\\u65f6\\u8981\\u4fdd\\u7559\\u5f15\\u7528\\u7684\\u8bba\\u6587\\u548c\\u5176\\u4ed6\\u6280\\u672f\\u6587\\u7ae0\\uff0c\\u4f8b\\u5982 [20] \\u8fd9\\u6837\\u7684\\u5f15\\u7528\\u3002\\n- \\u5bf9\\u4e8e Figure \\u548c Table\\uff0c\\u7ffb\\u8bd1\\u7684\\u540c\\u65f6\\u4fdd\\u7559\\u539f\\u6709\\u683c\\u5f0f\\uff0c\\u4f8b\\u5982\\uff1a\\u201c\\u56fe 1: \\u201d\\u7ffb\\u8bd1\\u4e3a\\u201cFigure 1: \\u201d\\uff0c\\u201c\\u8868 1: \\u201d\\u7ffb\\u8bd1\\u4e3a\\uff1a\\u201cTable 1: \\u201d\\u3002\\n- \\u5168\\u89d2\\u62ec\\u53f7\\u6362\\u6210\\u534a\\u89d2\\u62ec\\u53f7\\uff0c\\u5e76\\u5728\\u5de6\\u62ec\\u53f7\\u524d\\u9762\\u52a0\\u534a\\u89d2\\u7a7a\\u683c\\uff0c\\u53f3\\u62ec\\u53f7\\u540e\\u9762\\u52a0\\u534a\\u89d2\\u7a7a\\u683c\\u3002\\n- \\u8f93\\u5165\\u683c\\u5f0f\\u4e3a Markdown \\u683c\\u5f0f\\uff0c\\u8f93\\u51fa\\u683c\\u5f0f\\u4e5f\\u5fc5\\u987b\\u4fdd\\u7559\\u539f\\u59cb Markdown \\u683c\\u5f0f\\n- \\u4ee5\\u4e0b\\u662f\\u5e38\\u89c1\\u7684 AI \\u76f8\\u5173\\u672f\\u8bed\\u8bcd\\u6c47\\u5bf9\\u5e94\\u8868\\uff1a\\n  * Transformer -> Transformer\\n  * Token -> Token\\n  * \\u5927\\u8bed\\u8a00\\u6a21\\u578b -> LLM/Large Language Model \\n  * \\u751f\\u6210\\u5f0f AI -> Generative AI\\n\\n\\u7b56\\u7565\\uff1a\\n\\u5206\\u6210\\u4e24\\u6b21\\u7ffb\\u8bd1\\uff0c\\u5e76\\u4e14\\u6253\\u5370\\u6bcf\\u4e00\\u6b21\\u7ed3\\u679c\\uff1a\\n1. \\u6839\\u636e\\u4e2d\\u6587\\u5185\\u5bb9\\u76f4\\u8bd1\\uff0c\\u4fdd\\u6301\\u539f\\u6709\\u683c\\u5f0f\\uff0c\\u4e0d\\u8981\\u9057\\u6f0f\\u4efb\\u4f55\\u4fe1\\u606f\\n2. \\u6839\\u636e\\u7b2c\\u4e00\\u6b21\\u76f4\\u8bd1\\u7684\\u7ed3\\u679c\\u91cd\\u65b0\\u610f\\u8bd1\\uff0c\\u9075\\u5b88\\u539f\\u610f\\u7684\\u524d\\u63d0\\u4e0b\\u8ba9\\u5185\\u5bb9\\u66f4\\u901a\\u4fd7\\u6613\\u61c2\\u3001\\u7b26\\u5408\\u82f1\\u6587\\u8868\\u8fbe\\u4e60\\u60ef\\uff0c\\u4f46\\u8981\\u4fdd\\u7559\\u539f\\u6709\\u683c\\u5f0f\\u4e0d\\u53d8\\n\\n\\u8fd4\\u56de\\u683c\\u5f0f\\u5982\\u4e0b\\uff0c\\u201d(xxx)\\u201d\\u8868\\u793a\\u5360\\u4f4d\\u7b26\\uff1a\\n\\n\\u76f4\\u8bd1\\n```\\n(\\u76f4\\u8bd1\\u7ed3\\u679c)\\n```\\n---\\n\\n\\u610f\\u8bd1\\n```\\n(\\u610f\\u8bd1\\u7ed3\\u679c)\\n```\\n\\n\\u73b0\\u5728\\u8bf7\\u5c06\\u4e0b\\u9762\\u7684\\u5185\\u5bb9\\u7ffb\\u8bd1\\u6210\\u82f1\\u6587\\uff1a\\n{query}\\n                ", "endpoint": "https://api.openai.com/v1"}, "memory": false, "chractor": "\\n\\u4f60\\u662f\\u4e00\\u4f4d\\u7cbe\\u901a\\u4e2d\\u6587\\u7684\\u4e13\\u4e1a\\u7ffb\\u8bd1\\uff0c\\u5c24\\u5176\\u64c5\\u957f\\u5c06\\u4e13\\u4e1a\\u5b66\\u672f\\u8bba\\u6587\\u7ffb\\u8bd1\\u6210\\u6d45\\u663e\\u6613\\u61c2\\u7684\\u79d1\\u666e\\u6587\\u7ae0\\u3002\\n\\n\\u6211\\u5e0c\\u671b\\u4f60\\u80fd\\u5e2e\\u6211\\u5c06\\u4ee5\\u4e0b\\u4e2d\\u6587\\u6280\\u672f\\u6587\\u7ae0\\u6bb5\\u843d\\u7ffb\\u8bd1\\u6210\\u82f1\\u6587\\uff0c\\u98ce\\u683c\\u4e0e\\u79d1\\u666e\\u6742\\u5fd7\\u7684\\u82f1\\u6587\\u7248\\u76f8\\u4f3c\\u3002\\n\\n\\u89c4\\u5219\\uff1a\\n- \\u7ffb\\u8bd1\\u65f6\\u8981\\u51c6\\u786e\\u4f20\\u8fbe\\u539f\\u6587\\u7684\\u4e8b\\u5b9e\\u548c\\u80cc\\u666f\\u3002\\n- \\u5373\\u4f7f\\u4e0a\\u610f\\u8bd1\\u4e5f\\u8981\\u4fdd\\u7559\\u539f\\u59cb\\u6bb5\\u843d\\u683c\\u5f0f\\uff0c\\u4ee5\\u53ca\\u4fdd\\u7559\\u672f\\u8bed\\uff0c\\u4f8b\\u5982 FLAC\\uff0cJPEG \\u7b49\\u3002\\u4fdd\\u7559\\u516c\\u53f8\\u7f29\\u5199\\uff0c\\u4f8b\\u5982 Microsoft, Amazon \\u7b49\\u3002\\n- \\u540c\\u65f6\\u8981\\u4fdd\\u7559\\u5f15\\u7528\\u7684\\u8bba\\u6587\\u548c\\u5176\\u4ed6\\u6280\\u672f\\u6587\\u7ae0\\uff0c\\u4f8b\\u5982 [20] \\u8fd9\\u6837\\u7684\\u5f15\\u7528\\u3002\\n- \\u5bf9\\u4e8e Figure \\u548c Table\\uff0c\\u7ffb\\u8bd1\\u7684\\u540c\\u65f6\\u4fdd\\u7559\\u539f\\u6709\\u683c\\u5f0f\\uff0c\\u4f8b\\u5982\\uff1a\\u201c\\u56fe 1: \\u201d\\u7ffb\\u8bd1\\u4e3a\\u201cFigure 1: \\u201d\\uff0c\\u201c\\u8868 1: \\u201d\\u7ffb\\u8bd1\\u4e3a\\uff1a\\u201cTable 1: \\u201d\\u3002\\n- \\u5168\\u89d2\\u62ec\\u53f7\\u6362\\u6210\\u534a\\u89d2\\u62ec\\u53f7\\uff0c\\u5e76\\u5728\\u5de6\\u62ec\\u53f7\\u524d\\u9762\\u52a0\\u534a\\u89d2\\u7a7a\\u683c\\uff0c\\u53f3\\u62ec\\u53f7\\u540e\\u9762\\u52a0\\u534a\\u89d2\\u7a7a\\u683c\\u3002\\n- \\u8f93\\u5165\\u683c\\u5f0f\\u4e3a Markdown \\u683c\\u5f0f\\uff0c\\u8f93\\u51fa\\u683c\\u5f0f\\u4e5f\\u5fc5\\u987b\\u4fdd\\u7559\\u539f\\u59cb Markdown \\u683c\\u5f0f\\n- \\u4ee5\\u4e0b\\u662f\\u5e38\\u89c1\\u7684 AI \\u76f8\\u5173\\u672f\\u8bed\\u8bcd\\u6c47\\u5bf9\\u5e94\\u8868\\uff1a\\n  * Transformer -> Transformer\\n  * Token -> Token\\n  * \\u5927\\u8bed\\u8a00\\u6a21\\u578b -> LLM/Large Language Model \\n  * \\u751f\\u6210\\u5f0f AI -> Generative AI\\n\\n\\u7b56\\u7565\\uff1a\\n\\u5206\\u6210\\u4e24\\u6b21\\u7ffb\\u8bd1\\uff0c\\u5e76\\u4e14\\u6253\\u5370\\u6bcf\\u4e00\\u6b21\\u7ed3\\u679c\\uff1a\\n1. \\u6839\\u636e\\u4e2d\\u6587\\u5185\\u5bb9\\u76f4\\u8bd1\\uff0c\\u4fdd\\u6301\\u539f\\u6709\\u683c\\u5f0f\\uff0c\\u4e0d\\u8981\\u9057\\u6f0f\\u4efb\\u4f55\\u4fe1\\u606f\\n2. \\u6839\\u636e\\u7b2c\\u4e00\\u6b21\\u76f4\\u8bd1\\u7684\\u7ed3\\u679c\\u91cd\\u65b0\\u610f\\u8bd1\\uff0c\\u9075\\u5b88\\u539f\\u610f\\u7684\\u524d\\u63d0\\u4e0b\\u8ba9\\u5185\\u5bb9\\u66f4\\u901a\\u4fd7\\u6613\\u61c2\\u3001\\u7b26\\u5408\\u82f1\\u6587\\u8868\\u8fbe\\u4e60\\u60ef\\uff0c\\u4f46\\u8981\\u4fdd\\u7559\\u539f\\u6709\\u683c\\u5f0f\\u4e0d\\u53d8\\n\\n\\u8fd4\\u56de\\u683c\\u5f0f\\u5982\\u4e0b\\uff0c\\u201d(xxx)\\u201d\\u8868\\u793a\\u5360\\u4f4d\\u7b26\\uff1a\\n\\n\\u76f4\\u8bd1\\n```\\n(\\u76f4\\u8bd1\\u7ed3\\u679c)\\n```\\n---\\n\\n\\u610f\\u8bd1\\n```\\n(\\u610f\\u8bd1\\u7ed3\\u679c)\\n```\\n\\n\\u73b0\\u5728\\u8bf7\\u5c06\\u4e0b\\u9762\\u7684\\u5185\\u5bb9\\u7ffb\\u8bd1\\u6210\\u82f1\\u6587\\uff1a\\n{query}\\n                "}',
    system: true,
    collections: [],
    created: '2024-01-16T15:19:29.242627+00:00',
    updated: '2024-01-16T15:19:29.246075+00:00',
  },
  {
    id: 'bot57f419b28235997d',
    title: 'CRD-Spec 注释专家',
    type: 'common',
    description: 'For generating CRD Spec annotations ',
    config:
      '{"model": "azure-openai", "llm": {"similarity_score_threshold": 0.5, "similarity_topk": 3, "temperature": 0, "context_window": 4096, "prompt_template": "As an expert Kubernetes operator, provide comprehensive comments/documentation for the Spec section of a CRD (Custom Resource Definition) you are developing. The CRD represents a custom resource used within a Kubernetes cluster.  You should refine the CRD Spec in multi round.\\n\\nFirst Round:\\nThe provided input is in the format of golang code style, and we use kubebuilder as controller framework to generate the CRD Spec annotations, you are aimed to refine the description part of the Spec to make sure it is smooth, english native, and in k8s technical style.  There are some restrictions:\\n- For the code annotation includes \'+kubebuilder\' mark or starts with \\u2018+\\u2019, do not change them, they are very important marker for kubebuilder\\n- For the code part, do not change them, but you can give some suggestions instead.\\n- For the sample part in annotation, do not change them, as they indicate the best practice from author.\\n- For the regex rules in the annotation, do not change them, do not do any escape\\n- You can elaborate the meaning of the object in the description, but do not give examples \\n- If the field does not have an annotation, try your best to generate one for it\\n- Do not need to generate annotation for \\u2018optional/required\\u2019 marker as the framework knows it\\nThen we get the Intermediate result\\n\\nSecond Round:\\nRefine the first round result again with rules, keep other parts as it was:\\n- When describe an object, such as \\u201cFiledA specifies/defines/indicates  \\u2026\\u201d, remove \\u201cFieldA\\u201d, just starts with \\u201cSpecifies/Defines/Indicates\\u201d, but keep the following contents\\n- When describe an object, such as \\u201cFiledA is/are  \\u2026\\u201d, remove \\u201cFieldA is/are\\u201d,  but keep the following contents\\n- Break long comments into paragraphs with inserting blank annotation line into the annotations, for example: annotations \\u201c// Ephemeral represents a volume that is handled by a cluster storage driver.\\n        // The volume\'s lifecycle is tied to the pod that defines it - it will be created before the pod starts,\\n        // and deleted when the pod is removed.\\n        //\\n        // Use this if:\\n        // a) the volume is only needed while the pod runs,\\n        // b) features of normal volumes like restoring from snapshot or capacity\\n        //    tracking are needed,\\n        // c) the storage driver is specified through a storage class, and\\n        // d) the storage driver supports dynamic volume provisioning through\\n        //    a PersistentVolumeClaim (see EphemeralVolumeSource for more\\n        //    information on the connection between this volume type\\n        //    and PersistentVolumeClaim).\\n        // Use PersistentVolumeClaim or one of the vendor-specific\\n        // APIs for volumes that persist for longer than the lifecycle\\n        // of an individual pod.\\n        // Use CSI for light-weight local ephemeral volumes if the CSI driver is meant to\\n        // be used that way - see the documentation of the driver for\\n        // more information.\\n        // A pod can use both types of ephemeral volumes and\\n        // persistent volumes at the same time.\\n        // +optional\\n        Ephemeral *EphemeralVolumeSource\\n\\u201d Can be separated with inserting blank annotations line \\u201c\\n        // Ephemeral represents a volume that is handled by a cluster storage driver.\\n        // The volume\'s lifecycle is tied to the pod that defines it - it will be created before the pod starts,\\n        // and deleted when the pod is removed.\\n        //\\n        // Use this if:\\n        // a) the volume is only needed while the pod runs,\\n        // b) features of normal volumes like restoring from snapshot or capacity\\n        //    tracking are needed,\\n        // c) the storage driver is specified through a storage class, and\\n        // d) the storage driver supports dynamic volume provisioning through\\n        //    a PersistentVolumeClaim (see EphemeralVolumeSource for more\\n        //    information on the connection between this volume type\\n        //    and PersistentVolumeClaim).\\n        //\\n        // Use PersistentVolumeClaim or one of the vendor-specific\\n        // APIs for volumes that persist for longer than the lifecycle\\n        // of an individual pod.\\n        //\\n        // Use CSI for light-weight local ephemeral volumes if the CSI driver is meant to\\n        // be used that way - see the documentation of the driver for\\n        // more information.\\n        //\\n        // A pod can use both types of ephemeral volumes and\\n        // persistent volumes at the same time.\\n        //\\n        // +optional\\n        Ephemeral *EphemeralVolumeSource\\n\\u201d\\n- Make sure insert a blank annotation line between normal annotations and kubebuilder markers start with \\u2018+\\u2019 , for example: \\u201c\\n        // persistent volumes at the same time.\\n        // +optional\\n        Ephemeral *EphemeralVolumeSource\\n\\u201d Can be separated with inserting blank annotation line \\u201c\\n        // persistent volumes at the same time.\\n        // \\n        // +optional\\n        Ephemeral *EphemeralVolumeSource\\n\\u201d\\n- Make sure not to insert blank annotation line before the first line of the annotation\\n- Make sure two fields and their annotation lines are separated with a blank line, for example: \\u201c\\n        // persistent volumes1 at the same time.\\n        // +optional\\n        Ephemeral1 *EphemeralVolumeSource\\n        // persistent volumes2 at the same time.\\n        // +optional\\n        Ephemeral2 *EphemeralVolumeSource\\n\\u201d Can be separated with inserting blank line \\u201c\\n        // persistent volumes1 at the same time.\\n        // +optional\\n        Ephemeral1 *EphemeralVolumeSource\\n\\n        // persistent volumes2 at the same time.\\n        // +optional\\n        Ephemeral2 *EphemeralVolumeSource\\n\\u201d\\n- Make sure other parts of the Intermediate result contents keep as it was\\nThen we get the final result.\\n\\nProvided query: {query}\\nThe return format is as follows, \\u201c[xxx]\\u201d represents a placeholder:\\nOriginal query:\\n```\\n[original query]\\n```\\nRefined final result:\\n```\\n[refined final result]\\n```", "endpoint": "", "trial": true}, "memory": false, "chractor": "{query}"}',
    system: true,
    collections: [],
    created: '2024-02-18T01:21:45.755907+00:00',
    updated: '2024-04-10T02:43:04.682406+00:00',
  },
  {
    id: 'bot723006926f6d4596',
    title: 'GPT',
    type: 'common',
    description: null,
    config:
      '{"model": "gpt-4-1106-preview", "llm": {"similarity_score_threshold": 0.5, "similarity_topk": 10, "temperature": 0, "context_window": 128000, "prompt_template": "\\u4f60\\u662f\\u4e00\\u4e2a\\u64c5\\u957f\\u7f16\\u5199\\u4ee3\\u7801\\u7684\\u4e13\\u5bb6\\uff0c\\n\\u4f60\\u9700\\u8981\\u57fa\\u4e8e\\u5bf9\\u8bdd\\u8bb0\\u5f55\\u7406\\u89e3\\u7528\\u6237\\u7684\\u95ee\\u9898\\uff0c\\u8f93\\u51fa\\u6ca1\\u6709bug\\u3001\\u7b80\\u6d01\\u3001\\u53ef\\u8bfb\\u6027\\u5f3a\\u7684\\u4ee3\\u7801\\uff0c\\u5e76\\u7ed9\\u51fa\\u76f8\\u5e94\\u6ce8\\u91ca\\uff0c\\n\\u6ce8\\u610f\\u56de\\u7b54\\u5185\\u5bb9\\u8981\\u8981\\u7cbe\\u70bc\\u3001\\u6613\\u61c2\\u3002\\n\\u7528\\u6237\\u7684\\u95ee\\u9898\\u662f: {query}", "endpoint": "https://api.openai.com/v1"}, "memory": false, "chractor": "\\u4f60\\u662f\\u4e00\\u4e2a\\u64c5\\u957f\\u7f16\\u5199\\u4ee3\\u7801\\u7684\\u4e13\\u5bb6\\uff0c\\n\\u4f60\\u9700\\u8981\\u57fa\\u4e8e\\u5bf9\\u8bdd\\u8bb0\\u5f55\\u7406\\u89e3\\u7528\\u6237\\u7684\\u95ee\\u9898\\uff0c\\u8f93\\u51fa\\u6ca1\\u6709bug\\u3001\\u7b80\\u6d01\\u3001\\u53ef\\u8bfb\\u6027\\u5f3a\\u7684\\u4ee3\\u7801\\uff0c\\u5e76\\u7ed9\\u51fa\\u76f8\\u5e94\\u6ce8\\u91ca\\uff0c\\n\\u6ce8\\u610f\\u56de\\u7b54\\u5185\\u5bb9\\u8981\\u8981\\u7cbe\\u70bc\\u3001\\u6613\\u61c2\\u3002\\n\\u7528\\u6237\\u7684\\u95ee\\u9898\\u662f: {query}"}',
    system: false,
    collections: [],
    created: '2024-02-19T02:20:18.509700+00:00',
    updated: '2024-02-19T02:20:18.511939+00:00',
  },
  {
    id: 'botb1e075a3311f7f42',
    title: '配置管理专家',
    type: 'common',
    description: null,
    config:
      '{"model": "azure-openai", "llm": {"similarity_score_threshold": 0.5, "trial": true, "similarity_topk": 3, "temperature": 0, "context_window": 128000, "prompt_template": "You are a database parameter management expert and also a cuelang language expert. You can generate corresponding cuelang constraint code based on the database parameter documentation.\\n\\nThe generated cuelang code must adhere to the following rules:\\n\\n1. Fields must have types. Deduce the field types based on the default values and descriptions in the parameter documentation. Valid field types are: int, float, string, bool.\\n2. The Default in the parameter documentation is the default value, which must be converted to the corresponding default value of the cuelang field.\\n3. The Description in the parameter documentation is the parameter description information, which MUST be converted to comments for the corresponding cuelang field. Comments must be placed above the field, maintaining the original Description content and format without any modifications.\\n4. ONLY output cuelang code, without any extra information.\\n5. If parameters value have constraints, they must be converted to cuelang constraints.\\n\\n\\nFor example, given the following parameter description documentation:\\n```plain\\nstarrocks_qe_slow_log_ms\\n\\nUnit: ms\\nDefault: 5000\\nDescription: The threshold used to determine whether a query is a slow query. If the response time of a query exceeds this threshold, it is recorded as a slow query in fe.audit.log. Value range: 1000-10000.\\n```\\n\\nThe converted cuelang constraint code would be:\\n```cuelang\\n// The threshold used to determine whether a query is a slow query. If the response time of a query exceeds this threshold, it is recorded as a slow query in fe.audit.log.\\nstarrocks_qe_slow_log_ms: int & >=1000 & <=10000 | *5000\\n```\\n\\nGiven the parameter documentation below, please convert it to cuelang constraint code:\\n{query}", "endpoint": "https://api.openai.com/v1"}, "memory": false, "chractor": "{query}"}',
    system: true,
    collections: [],
    created: '2024-02-22T10:39:57.975287+00:00',
    updated: '2024-02-23T02:35:50.596721+00:00',
  },
  {
    id: 'bot44b48e73a7b12a8a',
    title: 'ccc',
    type: 'knowledge',
    description: null,
    config:
      '{"model": "azure-openai", "llm": {"prompt_template": "\\n\\u4f60\\u662f\\u4e00\\u4e2a\\u6839\\u636e\\u5bf9\\u8bdd\\u8bb0\\u5f55\\u548c\\u5019\\u9009\\u7b54\\u6848\\u6765\\u56de\\u7b54\\u95ee\\u9898\\u7684\\u4e13\\u5bb6\\uff0c\\u4f60\\u7684\\u56de\\u7b54\\u4e25\\u683c\\u9650\\u5b9a\\u4e8e\\u521a\\u624d\\u7684\\u5bf9\\u8bdd\\u8bb0\\u5f55\\u548c\\u4e0b\\u9762\\u7ed9\\u4f60\\u63d0\\u4f9b\\u7684\\u5019\\u9009\\u7b54\\u6848\\u3002\\n\\n\\u4f60\\u9700\\u8981\\u57fa\\u4e8e\\u521a\\u624d\\u7684\\u5bf9\\u8bdd\\u8bb0\\u5f55\\uff0c\\u8c28\\u614e\\u51c6\\u786e\\u7684\\u4f9d\\u636emarkdown\\u683c\\u5f0f\\u7684\\u5019\\u9009\\u7b54\\u6848\\uff0c\\u6765\\u56de\\u7b54\\u95ee\\u9898\\uff1a{query}\\u3002\\n\\n\\u8bf7\\u4e00\\u6b65\\u4e00\\u6b65\\u601d\\u8003\\uff0c\\u8bf7\\u786e\\u4fdd\\u56de\\u7b54\\u51c6\\u786e\\u548c\\u7b80\\u6d01\\uff0c\\u5982\\u679c\\u4ece\\u5bf9\\u8bdd\\u8bb0\\u5f55\\u548c\\u5019\\u9009\\u7b54\\u6848\\u4e2d\\u627e\\u4e0d\\u51fa\\u56de\\u7b54\\uff0c\\u5c31\\u76f4\\u63a5\\u8bf4\\u4f60\\u4e0d\\u77e5\\u9053\\uff0c\\u4e0d\\u8981\\u8bd5\\u56fe\\u7f16\\u9020\\u4e00\\u4e2a\\u56de\\u7b54\\u3002\\n\\n\\u95ee\\u9898\\u53ea\\u56de\\u7b54\\u4e00\\u6b21\\u3002\\n\\n\\u5019\\u9009\\u7b54\\u6848\\u5982\\u4e0b:\\n----------------\\n{context}\\n--------------------\\n", "context_window": 4096, "similarity_score_threshold": 0.5, "similarity_topk": 3, "temperature": 0, "enable_keyword_recall": false, "deployment_id": "1", "api_version": "2", "endpoint": "3", "token": "4", "trial": false}, "use_related_question": false, "memory": false}',
    system: false,
    collections: [
      {
        id: 'col267394663b95e70b',
        title: '撒打算大',
        description: null,
        status: 'ACTIVE',
        type: 'document',
        bot_ids: [],
        system: false,
        config:
          '{"source": "system", "crontab": {"enabled": false, "minute": "0", "hour": "0", "day_of_month": "*", "month": "*", "day_of_week": "*"}, "embedding_model": "bge"}',
        created: '2023-11-08T05:48:01.867042+00:00',
        updated: '2023-11-08T05:48:02.227252+00:00',
      },
    ],
    created: '2024-04-15T03:45:32.936827+00:00',
    updated: '2024-04-15T03:48:47.872459+00:00',
  },
];

const chats = [
  {
    id: '1',
    summary: '',
    history: [
      {
        type: 'message',
        role: 'human',
        data: 'how to start mysql cluster using kbcli',
        timestamp: 1688270030871,
        references: [],
      },
      {
        type: 'message',
        data: '### Human:\nThe original question is as follows: how to start mysql cluster using kbcli\nWe have provided an existing answer: \n\nOption 1. (Recommended) Use kbcli\n\nConfigure the name of your cluster and run the command below to start this cluster.\n\n```bash\nkbcli cluster start mysql-cluster\n```\n\n\n\n\n\nOption 2. Create an OpsRequest\n\nRun the command below to start a cluster.\n\n```bash\nkubectl apply -f - <<EOF\napiVersion: apps.kubeblocks.io/v1alpha1\nkind: OpsRequest\nmetadata:\n  name: mysql-cluster\n  generateName: start-\nspec:\n  # cluster ref\n  clusterRef: mysql-cluster\n  type: Start\nEOF \n```\n\n\n\n\n\nCreate a cluster on a node without taints\n\nThe cluster creation command is simply `kbcli cluster create`. Further, you can customize your cluster resources as demanded by using the `--set` flag.\n\n```bash\nkbcli cluster create mysql-cluster --cluster-definition=apecloud-mysql --set cpu=2000m,memory=2Gi,storage=20Gi,storageClass= --namespace \n```\n\n***Result***\n\nA cluster is created in the namespace `default` with the specified cluster resources.\n\nOr change the corresponding parameters in the YAML file.\n\n```bash\nkbcli cluster create mysql-cluster --cluster-definition=apecloud-mysql --set storageClass= --namespace  --set-file -<<EOF\n- name: mysql-cluster\n  replicas: 3\n  componentDefRef: mysql\n  volumeClaimTemplates:\n  - name: data\n    spec:\n    accessModes:\n    - ReadWriteOnce\n      resources:\n        requests:\n          cpu: 2000m\n          memory: 2Gi\n          storage: 10Gi\nEOF\n```\n\nSee the table below for detailed descriptions of customizable parameters, setting the `--termination-policy` is necessary, and you are strongly recommended to turn on the monitor and enable all logs.\n\n📎 Table 2. kbcli cluster create flags description\n\n| Option                 | Description             |\n|:-----------------------|:------------------------|\n| `--cluster-definition` | It specifies the cluster definition and you can choose the database type. Run `kbcli cd list` to show all available cluster definitions.   |\n| `--clus\nWe have the opportunity to refine the existing answer (only if needed) with some more context below.\nGiven the new context, refine and synthesize the original answer to better \nanswer the question. Make sure that the refine answer is less than 50 words. \n### Assistant :\nThe original answer is already comprehensive and covers all the necessary steps to start a MySQL cluster using kbcli. However, it is worth noting that kbcli is a command-line tool that simplifies the process of creating and managing Kubernetes-native MySQL clusters. It provides a set of commands to create, manage, and scale MySQL clusters, making it easier to deploy and manage MySQL in a Kubernetes environment.',
        timestamp: 1688270050073,
        role: 'ai',
        references: [
          {
            score: 0.6130654,
            text: '# Add-ons of KubeBlocks\n\nKubeBlocks is a control and management platform to manage a bunch of database engines and other add-ons.\n\nThis series provides basic knowledge of add-ons, so you can get a quick start and become a member of the KubeBlocks community.\n\nKubeBlocks features a rich add-on ecosystem with major databases, streaming and vector databases, including:\n\n- Relational Database: ApeCloud-MySQL (MySQL RaftGroup cluster), PostgreSQL (Replication cluster) \n- NoSQL Database: MongoDB, Redis\n- Graph Database: Nebula (from community contributors)\n- Time Series Database: TDengine, Greptime (from community contributors)\n- Vector Database: Milvus, Qdrant, Weaviate, etc.\n- Streaming: Kafka, Pulsar\n\nAdding an add-on to KubeBlocks is easy, you can just follow this guide to add the add-on to KubeBlocks as long as you know the followings: \n1. How to write a YAML file (e.g., You should know how many spaces to add when indenting with YAML).\n2. Knowledge about Helm (e.g. What is Helm and Helm chart).\n3. Have tried K8s (e.g., You should know what a pod is, or have installed an operator on K8s with Helm).\n4. Grasp basic concepts of KubeBlocks, such as ClusterDefinition, ClusterVersion and Cluster.\nIf you have any question, you can join our [slack channel](https://join.slack.com/t/kubeblocks/shared_invite/zt-22cx2f84x-BPZvnLRqBOGdZ_XSjELh4Q) to ask.',
            metadata: {
              content_ratio: 0.9844054580896686,
              path: '/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/add-ons-of-kubeblocks.md',
              name: 'add-ons-of-kubeblocks.md',
              source: 'add-ons-of-kubeblocks.md',
            },
          },
          {
            score: 0.6121108,
            text: "Title: Add an add-on to KubeBlocks\n\n## Step 3. Add an addon.yaml file\n\nThis is the last step to integrate an add-on to KubeBlocks. After creating this addon.yaml file, this add-on is in the KubeBlocks add-on family. Please refer to `tutorial-1-create-an-addon/oracle-mysql-addon.yaml`.\n\n```bash\napiVersion: extensions.kubeblocks.io/v1alpha1\nkind: Addon\nmetadata:\n  name: tutorial-mysql\nspec:\n  description: 'MySQL is a widely used, open-source....'\n  type: Helm\n  helm:                                     \n    chartsImage: registry-of-your-helm-chart\n  installable:\n    autoInstall: false\n    \n  defaultInstallValues:\n    - enabled: true\n```\n\nAnd then configure your Helm chart remote repository address with `chartsImage`.",
            metadata: {
              content_ratio: 0.9737638085218306,
              path: '/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/how-to-add-an-add-on.md',
              name: 'how-to-add-an-add-on.md',
              source: 'how-to-add-an-add-on.md',
            },
          },
          {
            score: 0.5938544,
            text: '# Add an add-on to KubeBlocks\n\nThis tutorial explains how to integrate an add-on to KubeBlocks, and takes Oracle MySQL as an example. You can also find the [PR here](https://github.com/apecloud/learn-kubeblocks-addon).\n\nThere are altogether 3 steps to integrate an add-on:\n\n1. Design cluster blueprint.\n2. Prepare cluster templates.\n3. Add an `addon.yaml` file.\n\n## Step 1. Design a blueprint for cluster\n\nBefore getting started, make sure to design your cluster blueprint. Think about what you want your cluster to look like. For example:\n\n- What components it has\n- What format each component takes\n  - stateful/stateless\n  - Standalone/Replication/RaftGroup\n\nIn this tutorial you will learn how to deploy a cluster with one Stateful component which has only one node. The design configuration of the cluster is shown in the following table.\n\nCluster Format: Deploying a MySQL 8.0 Standalone.\n\n:paperclip: Table 1. Blueprint for Oracle MySQL Cluster\n\n| Term              | Settings                                                                                                     |\n|-------------------|--------------------------------------------------------------------------------------------------------------|\n| CLusterDefinition | Startup Scripts: Default Configuration Files: Default Service Port: 3306 Number of Components: 1, i.e. MySQL |\n| ClusterVersion    | Image: docker.io/mysql:8.0.34                                                                                |\n| Cluster.yaml      | Specified by the user during creation                                                                        |',
            metadata: {
              content_ratio: 0.9737638085218306,
              path: '/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/how-to-add-an-add-on.md',
              name: 'how-to-add-an-add-on.md',
              source: 'how-to-add-an-add-on.md',
            },
          },
        ],
      },
      {
        type: 'message',
        role: 'human',
        data: 'how to start mysql cluster using kbcli',
        timestamp: 1688270054641,
        references: [],
      },
      {
        type: 'message',
        data: '### Human:\nThe original question is as follows: how to start mysql cluster using kbcli\nWe have provided an existing answer: \n\nOption 1. (Recommended) Use kbcli\n\nConfigure the name of your cluster and run the command below to start this cluster.\n\n```bash\nkbcli cluster start mysql-cluster\n```\n\n\n\n\n\nOption 2. Create an OpsRequest\n\nRun the command below to start a cluster.\n\n```bash\nkubectl apply -f - <<EOF\napiVersion: apps.kubeblocks.io/v1alpha1\nkind: OpsRequest\nmetadata:\n  name: mysql-cluster\n  generateName: start-\nspec:\n  # cluster ref\n  clusterRef: mysql-cluster\n  type: Start\nEOF \n```\n\n\n\n\n\nCreate a cluster on a node without taints\n\nThe cluster creation command is simply `kbcli cluster create`. Further, you can customize your cluster resources as demanded by using the `--set` flag.\n\n```bash\nkbcli cluster create mysql-cluster --cluster-definition=apecloud-mysql --set cpu=2000m,memory=2Gi,storage=20Gi,storageClass= --namespace \n```\n\n***Result***\n\nA cluster is created in the namespace `default` with the specified cluster resources.\n\nOr change the corresponding parameters in the YAML file.\n\n```bash\nkbcli cluster create mysql-cluster --cluster-definition=apecloud-mysql --set storageClass= --namespace  --set-file -<<EOF\n- name: mysql-cluster\n  replicas: 3\n  componentDefRef: mysql\n  volumeClaimTemplates:\n  - name: data\n    spec:\n    accessModes:\n    - ReadWriteOnce\n      resources:\n        requests:\n          cpu: 2000m\n          memory: 2Gi\n          storage: 10Gi\nEOF\n```\n\nSee the table below for detailed descriptions of customizable parameters, setting the `--termination-policy` is necessary, and you are strongly recommended to turn on the monitor and enable all logs.\n\n📎 Table 2. kbcli cluster create flags description\n\n| Option                 | Description             |\n|:-----------------------|:------------------------|\n| `--cluster-definition` | It specifies the cluster definition and you can choose the database type. Run `kbcli cd list` to show all available cluster definitions.   |\n| `--clus\nWe have the opportunity to refine the existing answer (only if needed) with some more context below.\nGiven the new context, refine and synthesize the original answer to better \nanswer the question. Make sure that the refine answer is less than 50 words. \n### Assistant :\nThe original answer is already comprehensive and covers all the necessary steps to start a MySQL cluster using kbcli. However, it is worth noting that kbcli is a command-line tool that simplifies the process of creating and managing Kubernetes-native MySQL clusters. It provides a set of commands to create, manage, and scale MySQL clusters, making it easier to deploy and manage MySQL in a Kubernetes environment.',
        timestamp: 1688270073072,
        references: [],
        role: 'ai',
      },
      {
        type: 'message',
        role: 'human',
        data: 'how to stop mysql cluster using kbcli',
        timestamp: 1688270129003,
        references: [],
      },
      {
        type: 'message',
        data: '### Human:\nThe original question is as follows: how to stop mysql cluster using kbcli\nWe have provided an existing answer: \n\nOption 1. (Recommended) Use kbcli\n\nConfigure the name of your cluster and run the command below to stop this cluster.\n\n```bash\nkbcli cluster stop mysql-cluster\n```\n\n\n\n\n\nOption 2. Create an OpsRequest\n\nRun the command below to stop a cluster.\n\n```bash\nkubectl apply -f - <<EOF\napiVersion: apps.kubeblocks.io/v1alpha1\nkind: OpsRequest\nmetadata:\n  name: mysql-cluster\n  generateName: stop-\nspec:\n  # cluster ref\n  clusterRef: mysql-cluster\n  type: Stop\nEOF\n```\n\n\n\n\n\nStep\n\nRun the command below to delete a specified cluster.\n\n```bash\nkbcli cluster delete mysql-cluster\n```\n\n\nWe have the opportunity to refine the existing answer (only if needed) with some more context below.\nGiven the new context, refine and synthesize the original answer to better \nanswer the question. Make sure that the refine answer is less than 50 words. \n### Assistant :\nRefined Answer:\n\nTo stop a MySQL cluster using kbcli, you can either use the recommended option of running the command `kbcli cluster stop mysql-cluster` or create an OpsRequest using `kubectl apply -f - <<EOF apiVersion: apps.kubeblocks.io/v1alpha1 kind: OpsRequest metadata: name: mysql-cluster generateName: stop- spec: clusterRef: mysql-cluster type: Stop EOF` or delete the cluster using `kbcli cluster delete mysql-cluster`.',
        timestamp: 1688270152681,
        references: [],
        role: 'ai',
      },
      {
        type: 'message',
        role: 'human',
        data: 'how to stop mysql cluster using kbcli',
        timestamp: 1688272185071,
        references: [],
      },
      {
        type: 'message',
        role: 'human',
        data: 'how to stop mysql cluster using kbcli',
        timestamp: 1688272270098,
        references: [],
      },
      {
        type: 'message',
        role: 'human',
        data: 'how to stop mysql cluster using kbcli',
        timestamp: 1688272339415,
        references: [],
      },
      {
        type: 'message',
        role: 'human',
        data: 'how to stop mysql cluster using kbcli',
        timestamp: 1688272449143,
        references: [],
      },
      {
        type: 'message',
        data: '\nRefined Answer:\n\nTo stop a MySQL cluster using kbcli, you can either use the recommended option of running the command `kbcli cluster stop mysql-cluster` or create an OpsRequest using `kubectl apply -f - <<EOF apiVersion: apps.kubeblocks.io/v1alpha1 kind: OpsRequest metadata: name: mysql-cluster generateName: stop- spec: clusterRef: mysql-cluster type: Stop EOF` or delete the cluster using `kbcli cluster delete mysql-cluster`.',
        timestamp: 1688272477508,
        role: 'ai',
        references: [],
      },
      {
        type: 'message',
        role: 'human',
        data: 'how to stop mysql cluster using kbcli',
        timestamp: 1688272581258,
        references: [],
      },
      {
        type: 'message',
        data: '\nRefined Answer:\n\nTo stop a MySQL cluster using kbcli, you can either use the recommended option of running the command `kbcli cluster stop mysql-cluster` or create an OpsRequest using `kubectl apply -f - <<EOF apiVersion: apps.kubeblocks.io/v1alpha1 kind: OpsRequest metadata: name: mysql-cluster generateName: stop- spec: clusterRef: mysql-cluster type: Stop EOF` or delete the cluster using `kbcli cluster delete mysql-cluster`.',
        timestamp: 1688272604972,
        role: 'ai',
        references: [],
      },
      {
        type: 'message',
        role: 'human',
        data: 'how to stop mysql cluster using kbcli',
        timestamp: 1688273394762,
        references: [],
      },
      {
        type: 'message',
        data: '\nRefined Answer:\n\nTo stop a MySQL cluster using kbcli, you can either use the recommended option of running the command `kbcli cluster stop mysql-cluster` or create an OpsRequest using `kubectl apply -f - <<EOF apiVersion: apps.kubeblocks.io/v1alpha1 kind: OpsRequest metadata: name: mysql-cluster generateName: stop- spec: clusterRef: mysql-cluster type: Stop EOF` or delete the cluster using `kbcli cluster delete mysql-cluster`.',
        timestamp: 1688273419477,
        role: 'ai',
        references: [
          {
            score: 0.88159984,
            text: '\n\nOption 1. (Recommended) Use kbcli\n\nConfigure the name of your cluster and run the command below to stop this cluster.\n\n```bash\nkbcli cluster stop mysql-cluster\n```\n\n',
            metadata: {
              source: 'stop-start-a-cluster.md',
            },
          },
          {
            score: 0.84056866,
            text: '\n\nOption 2. Create an OpsRequest\n\nRun the command below to stop a cluster.\n\n```bash\nkubectl apply -f - <<EOF\napiVersion: apps.kubeblocks.io/v1alpha1\nkind: OpsRequest\nmetadata:\n  name: mysql-cluster\n  generateName: stop-\nspec:\n  # cluster ref\n  clusterRef: mysql-cluster\n  type: Stop\nEOF\n```\n\n',
            metadata: {
              source: 'stop-start-a-cluster.md',
            },
          },
          {
            score: 0.78274,
            text: '\n\nStep\n\nRun the command below to delete a specified cluster.\n\n```bash\nkbcli cluster delete mysql-cluster\n```\n\n',
            metadata: {
              source: 'delete-mysql-cluster.md',
            },
          },
        ],
      },
    ],
    created: '2023-07-02T03:49:17.598410+00:00',
    updated: '2023-07-02T03:49:17.598425+00:00',
  },
  {
    id: 'chat126b6ae09f8f8429',
    summary: '',
    bot_id: 'bot44c9adee9c4c71fe',
    history: [
      {
        id: '1702447025254',
        type: 'message',
        timestamp: 1702447042623,
        role: 'human',
        data: 'kubeblocks add on',
      },
      {
        id: '1702447025254',
        type: 'message',
        timestamp: 1702447042626,
        role: 'ai',
        data: 'KubeBlocks是一个控制和管理平台，用于管理各种数据库引擎和其他附加组件。它具有丰富的附加组件生态系统，包括主要的数据库、流数据库和向量数据库。向KubeBlocks添加附加组件很简单，只需遵循指南，了解如何编写YAML文件，对Helm有所了解，尝试过K8s，并掌握KubeBlocks的基本概念，如ClusterDefinition，ClusterVersion和Cluster。添加附加组件的步骤包括设计集群蓝图，准备集群模板，以及添加一个`addon.yaml`文件。',
        references: [
          {
            score: 0.6130654,
            text: '# Add-ons of KubeBlocks\n\nKubeBlocks is a control and management platform to manage a bunch of database engines and other add-ons.\n\nThis series provides basic knowledge of add-ons, so you can get a quick start and become a member of the KubeBlocks community.\n\nKubeBlocks features a rich add-on ecosystem with major databases, streaming and vector databases, including:\n\n- Relational Database: ApeCloud-MySQL (MySQL RaftGroup cluster), PostgreSQL (Replication cluster) \n- NoSQL Database: MongoDB, Redis\n- Graph Database: Nebula (from community contributors)\n- Time Series Database: TDengine, Greptime (from community contributors)\n- Vector Database: Milvus, Qdrant, Weaviate, etc.\n- Streaming: Kafka, Pulsar\n\nAdding an add-on to KubeBlocks is easy, you can just follow this guide to add the add-on to KubeBlocks as long as you know the followings: \n1. How to write a YAML file (e.g., You should know how many spaces to add when indenting with YAML).\n2. Knowledge about Helm (e.g. What is Helm and Helm chart).\n3. Have tried K8s (e.g., You should know what a pod is, or have installed an operator on K8s with Helm).\n4. Grasp basic concepts of KubeBlocks, such as ClusterDefinition, ClusterVersion and Cluster.\nIf you have any question, you can join our [slack channel](https://join.slack.com/t/kubeblocks/shared_invite/zt-22cx2f84x-BPZvnLRqBOGdZ_XSjELh4Q) to ask.',
            metadata: {
              content_ratio: 0.9844054580896686,
              path: '/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/add-ons-of-kubeblocks.md',
              name: 'add-ons-of-kubeblocks.md',
              source: 'add-ons-of-kubeblocks.md',
            },
          },
          {
            score: 0.6121108,
            text: "Title: Add an add-on to KubeBlocks\n\n## Step 3. Add an addon.yaml file\n\nThis is the last step to integrate an add-on to KubeBlocks. After creating this addon.yaml file, this add-on is in the KubeBlocks add-on family. Please refer to `tutorial-1-create-an-addon/oracle-mysql-addon.yaml`.\n\n```bash\napiVersion: extensions.kubeblocks.io/v1alpha1\nkind: Addon\nmetadata:\n  name: tutorial-mysql\nspec:\n  description: 'MySQL is a widely used, open-source....'\n  type: Helm\n  helm:                                     \n    chartsImage: registry-of-your-helm-chart\n  installable:\n    autoInstall: false\n    \n  defaultInstallValues:\n    - enabled: true\n```\n\nAnd then configure your Helm chart remote repository address with `chartsImage`.",
            metadata: {
              content_ratio: 0.9737638085218306,
              path: '/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/how-to-add-an-add-on.md',
              name: 'how-to-add-an-add-on.md',
              source: 'how-to-add-an-add-on.md',
            },
          },
          {
            score: 0.5938544,
            text: '# Add an add-on to KubeBlocks\n\nThis tutorial explains how to integrate an add-on to KubeBlocks, and takes Oracle MySQL as an example. You can also find the [PR here](https://github.com/apecloud/learn-kubeblocks-addon).\n\nThere are altogether 3 steps to integrate an add-on:\n\n1. Design cluster blueprint.\n2. Prepare cluster templates.\n3. Add an `addon.yaml` file.\n\n## Step 1. Design a blueprint for cluster\n\nBefore getting started, make sure to design your cluster blueprint. Think about what you want your cluster to look like. For example:\n\n- What components it has\n- What format each component takes\n  - stateful/stateless\n  - Standalone/Replication/RaftGroup\n\nIn this tutorial you will learn how to deploy a cluster with one Stateful component which has only one node. The design configuration of the cluster is shown in the following table.\n\nCluster Format: Deploying a MySQL 8.0 Standalone.\n\n:paperclip: Table 1. Blueprint for Oracle MySQL Cluster\n\n| Term              | Settings                                                                                                     |\n|-------------------|--------------------------------------------------------------------------------------------------------------|\n| CLusterDefinition | Startup Scripts: Default Configuration Files: Default Service Port: 3306 Number of Components: 1, i.e. MySQL |\n| ClusterVersion    | Image: docker.io/mysql:8.0.34                                                                                |\n| Cluster.yaml      | Specified by the user during creation                                                                        |',
            metadata: {
              content_ratio: 0.9737638085218306,
              path: '/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/how-to-add-an-add-on.md',
              name: 'how-to-add-an-add-on.md',
              source: 'how-to-add-an-add-on.md',
            },
          },
        ],
        urls: [],
      },
      {
        id: '1702447159888',
        type: 'message',
        timestamp: 1702447173957,
        role: 'human',
        data: 'The name KubeBlocks is derived from Kubernetes and LEGO blocks, which indicates that building database and analytical workloads on Kubernetes can be both productive and enjoyable, like playing with construction toys. KubeBlocks combines the large-scale production experiences of top cloud service providers with enhanced usability and stability.',
      },
      {
        id: '1702447159888',
        type: 'message',
        timestamp: 1702447173959,
        role: 'ai',
        data: 'KubeBlocks是一个控制和管理平台，用于管理一系列数据库引擎和其他附加组件。它具有丰富的附加组件生态系统，包括主要的数据库、流数据库和向量数据库，如关系数据库、NoSQL数据库、图形数据库、时间序列数据库、向量数据库和流数据库等。添加附加组件到KubeBlocks非常简单，只需遵循指南并了解如何编写YAML文件、Helm的知识、尝试过K8s以及掌握KubeBlocks的基本概念。如果有任何问题，可以加入我们的slack频道进行提问。',
        references: [
          {
            score: 0.80768025,
            text: '# Add-ons of KubeBlocks\n\nKubeBlocks is a control and management platform to manage a bunch of database engines and other add-ons.\n\nThis series provides basic knowledge of add-ons, so you can get a quick start and become a member of the KubeBlocks community.\n\nKubeBlocks features a rich add-on ecosystem with major databases, streaming and vector databases, including:\n\n- Relational Database: ApeCloud-MySQL (MySQL RaftGroup cluster), PostgreSQL (Replication cluster) \n- NoSQL Database: MongoDB, Redis\n- Graph Database: Nebula (from community contributors)\n- Time Series Database: TDengine, Greptime (from community contributors)\n- Vector Database: Milvus, Qdrant, Weaviate, etc.\n- Streaming: Kafka, Pulsar\n\nAdding an add-on to KubeBlocks is easy, you can just follow this guide to add the add-on to KubeBlocks as long as you know the followings: \n1. How to write a YAML file (e.g., You should know how many spaces to add when indenting with YAML).\n2. Knowledge about Helm (e.g. What is Helm and Helm chart).\n3. Have tried K8s (e.g., You should know what a pod is, or have installed an operator on K8s with Helm).\n4. Grasp basic concepts of KubeBlocks, such as ClusterDefinition, ClusterVersion and Cluster.\nIf you have any question, you can join our [slack channel](https://join.slack.com/t/kubeblocks/shared_invite/zt-22cx2f84x-BPZvnLRqBOGdZ_XSjELh4Q) to ask.',
            metadata: {
              content_ratio: 0.9844054580896686,
              path: '/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/add-ons-of-kubeblocks.md',
              name: 'add-ons-of-kubeblocks.md',
              source: 'add-ons-of-kubeblocks.md',
            },
          },
          {
            score: 0.7824899,
            text: '---\ntitle: Add an add-on\ndescription: Add an add-on to KubeBlocks\nkeywords: [add-on, add an add-on]\nsidebar_position: 2\nsidebar_label: Add an add-on\n---',
            metadata: {
              content_ratio: 0.9737638085218306,
              path: '/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/how-to-add-an-add-on.md',
              name: 'how-to-add-an-add-on.md',
              source: 'how-to-add-an-add-on.md',
            },
          },
          {
            score: 0.77618957,
            text: '---\ntitle: Overview\ndescription: An overview of add an database add-on to KubeBlocks\nkeywords: [add-on, integration]\nsidebar_position: 1\nsidebar_label: Add-ons of KubeBlocks\n---',
            metadata: {
              content_ratio: 0.9844054580896686,
              path: '/data/media/documents/user-auth0-65363df666d30473af5f30eb/col3544125b631a1337/add-ons-of-kubeblocks.md',
              name: 'add-ons-of-kubeblocks.md',
              source: 'add-ons-of-kubeblocks.md',
            },
          },
        ],
        urls: [],
      },
    ],
    peer_type: 'web',
    peer_id: 'auth0|65363df666d30473af5f30eb',
    created: '2023-12-13T05:55:26.976819+00:00',
    updated: '2023-12-13T05:55:26.976834+00:00',
  },
  {
    id: 'chat88d649835cc402e5',
    summary: '',
    bot_id: 'bot723006926f6d4596',
    history: [
      {
        id: '1708309471976',
        type: 'message',
        timestamp: 1708309485719,
        role: 'human',
        data: "ReferenceError: Cannot access 'docLayoutComponent' before initialization",
      },
      {
        id: '1708309471976',
        type: 'message',
        timestamp: 1708309485721,
        role: 'ai',
        data: '用户遇到的问题是一个JavaScript中的`ReferenceError`，这个错误通常发生在尝试访问一个还没有初始化的变量时。在JavaScript中，如果你在声明一个变量之前就尝试使用它，就会遇到这个问题。这种情况通常发生在使用`let`或`const`关键字声明变量时，因为它们具有暂时性死区（Temporal Dead Zone, TDZ），即在代码执行到达声明位置之前，变量都是不可访问的。\n\n为了解决这个问题，你需要确保在引用变量`docLayoutComponent`之前，它已经被声明和初始化了。下面是一个简单的例子，展示了如何正确地声明和初始化一个变量，以避免这个错误：\n\n```javascript\n// 正确的声明和初始化顺序\nlet docLayoutComponent; // 声明变量\ndocLayoutComponent = { /* ... 初始化对象 ... */ }; // 初始化变量\n\n// 现在可以安全地引用 docLayoutComponent\nconsole.log(docLayoutComponent);\n```\n\n如果你在声明之前就尝试使用这个变量，就会遇到`ReferenceError`：\n\n```javascript\n// 错误的使用顺序会导致 ReferenceError\nconsole.log(docLayoutComponent); // 尝试访问未初始化的变量\nlet docLayoutComponent = { /* ... 初始化对象 ... */ };\n```\n\n确保你的代码中变量的使用顺序是正确的，这样就可以避免这种类型的错误。如果你能提供更多的上下文或代码片段，我可以给出更具体的建议。',
        references: [],
        urls: [],
      },
      {
        id: '1708309550835',
        type: 'message',
        timestamp: 1708309583530,
        role: 'human',
        data: "React 引用 window.customElements.define 构建时报错，ReferenceError: Cannot access 'docLayoutComponent' before initialization",
      },
      {
        id: '1708309550835',
        type: 'message',
        timestamp: 1708309583532,
        role: 'ai',
        data: "在React中，如果你在定义一个自定义元素时遇到了 `ReferenceError: Cannot access 'docLayoutComponent' before initialization` 的错误，这通常意味着你在声明自定义元素之前就尝试使用了它。这可能是因为代码中存在暂时性死区（temporal dead zone）问题，或者是因为自定义元素的定义与使用顺序不正确。\n\n为了解决这个问题，你需要确保在调用 `window.customElements.define` 之前，自定义元素类 `docLayoutComponent` 已经被完全定义并且可以访问。下面是一个简单的例子，展示了如何在React中正确地定义和注册一个自定义元素：\n\n```jsx\n// 定义自定义元素类\nclass DocLayoutComponent extends HTMLElement {\n  constructor() {\n    super();\n    // 自定义元素的初始化代码\n  }\n}\n\n// 确保在文档加载完毕后注册自定义元素\ndocument.addEventListener('DOMContentLoaded', () => {\n  // 注册自定义元素\n  if (!window.customElements.get('doc-layout')) {\n    window.customElements.define('doc-layout', DocLayoutComponent);\n  }\n});\n\n// React组件中使用自定义元素\nfunction MyComponent() {\n  return (\n    <div>\n      <doc-layout></doc-layout>\n    </div>\n  );\n}\n\nexport default MyComponent;\n```\n\n在上面的代码中，我们首先定义了一个名为 `DocLayoutComponent` 的类，它扩展了 `HTMLElement`。然后，我们监听 `DOMContentLoaded` 事件，以确保在文档加载完成后注册自定义元素。这样可以避免在自定义元素类初始化之前就尝试注册它的问题。最后，在React组件 `MyComponent` 中，我们使用了自定义元素 `<doc-layout></doc-layout>`。\n\n请注意，如果你的React应用使用了服务端渲染（SSR），你可能需要确保自定义元素的注册代码只在浏览器环境中执行，因为 `window` 和 `document` 对象在服务端环境中是不可用的。可以通过检查 `typeof window !== 'undefined'` 来实现这一点。",
        references: [],
        urls: [],
      },
      {
        id: '1708312745134',
        type: 'message',
        timestamp: 1708312765861,
        role: 'human',
        data: 'server-side rendering could not render static page',
      },
      {
        id: '1708312745134',
        type: 'message',
        timestamp: 1708312765864,
        role: 'ai',
        data: "用户的问题表明他们在服务器端渲染（Server-Side Rendering, SSR）静态页面时遇到了问题。为了提供帮助，我需要更多的上下文信息，比如他们使用的技术栈（例如Node.js, React, Angular等）、错误信息、当前的实现方式等。不过，我可以提供一个简单的Node.js服务器端渲染静态页面的示例代码。\n\n```javascript\n// 引入必要的模块\nconst express = require('express');\nconst fs = require('fs');\nconst path = require('path');\n\n// 创建一个Express应用\nconst app = express();\nconst port = 3000; // 服务器监听的端口\n\n// 定义一个路由来渲染静态页面\napp.get('/', (req, res) => {\n  // 设置静态页面的路径\n  const staticPagePath = path.join(__dirname, 'static-page.html');\n\n  // 读取静态页面的内容\n  fs.readFile(staticPagePath, 'utf8', (err, pageContent) => {\n    if (err) {\n      // 如果读取文件出错，返回500状态码和错误信息\n      res.status(500).send('Error loading the static page.');\n    } else {\n      // 如果成功读取文件，将内容发送给客户端\n      res.send(pageContent);\n    }\n  });\n});\n\n// 启动服务器\napp.listen(port, () => {\n  console.log(`Server is running at http://localhost:${port}`);\n});\n```\n\n在这个例子中，我们使用了Node.js的Express框架来创建一个简单的web服务器。我们定义了一个路由`/`，当用户访问这个路由时，服务器会读取并返回一个名为`static-page.html`的静态页面。如果在读取文件过程中出现错误，服务器会返回一个500状态码和错误信息。\n\n请注意，这个例子假设你已经有了一个名为`static-page.html`的静态页面文件位于与脚本相同的目录中。\n\n为了运行这个示例，你需要在你的项目中安装Express：\n\n```bash\nnpm install express\n```\n\n然后将上述代码保存到一个文件中，比如`server.js`，并运行它：\n\n```bash\nnode server.js\n```\n\n如果你遇到的问题与这个示例不符，请提供更多的信息，以便我能提供更具体的帮助。",
        references: [],
        urls: [],
      },
      {
        id: '1708314561717',
        type: 'message',
        timestamp: 1708314599205,
        role: 'human',
        data: 'Docusaurus server-side rendering could not render static page',
      },
      {
        id: '1708314561717',
        type: 'message',
        timestamp: 1708314599208,
        role: 'ai',
        data: 'Docusaurus 是一个用于构建、部署和维护开源项目文档网站的工具。如果你遇到了 "Docusaurus server-side rendering could not render static page" 的问题，这通常意味着在服务器端渲染（SSR）过程中出现了某些问题，导致无法生成静态页面。\n\n要解决这个问题，你可以按照以下步骤操作：\n\n1. **检查控制台错误**: 查看构建过程中的控制台输出，找出具体的错误信息。这通常会给出一个错误的堆栈跟踪，指示问题发生的位置。\n\n2. **检查代码中的SSR不兼容**: 有些代码可能只能在浏览器中运行，而不是在Node.js环境中。例如，任何直接引用 `window` 或 `document` 的代码都不会在SSR中工作。你需要修改这些代码，使其在服务器端也能正常运行。\n\n3. **更新依赖**: 确保你的Docusaurus和相关依赖项都是最新版本的，因为这可能是由于已知的bug而导致的问题，而这些bug在新版本中可能已经被修复。\n\n4. **检查自定义组件**: 如果你创建了自定义组件，确保它们正确地处理SSR。这可能意味着需要添加一些检查来避免在服务器端渲染时执行特定的客户端代码。\n\n5. **查看Docusaurus文档**: Docusaurus的文档可能有关于SSR问题的特定指导和建议。\n\n6. **搜索社区支持**: 如果上述步骤都不能解决问题，你可以在Docusaurus的GitHub仓库、社区论坛或Stack Overflow上搜索或提问，看看是否有其他人遇到了类似的问题。\n\n由于没有具体的错误信息和代码示例，我无法提供一个确切的代码修复方案。但是，如果你能提供更多的上下文和错误细节，我可以帮助你编写解决问题的代码。',
        references: [],
        urls: [],
      },
      {
        id: '1708314776009',
        type: 'message',
        timestamp: 1708314807571,
        role: 'human',
        data: '服务端渲染使用window.customElements',
      },
      {
        id: '1708314776009',
        type: 'message',
        timestamp: 1708314807573,
        role: 'ai',
        data: "服务端渲染（SSR）通常不涉及`window`对象，因为`window`是浏览器环境的全局对象，而服务端渲染是在服务器上执行的，没有浏览器环境。因此，`window.customElements` 这种通常用于定义浏览器端自定义元素的API，在服务端渲染中是不可用的。\n\n如果你想在服务端渲染中模拟或处理自定义元素，你需要使用服务器端的技术来生成相应的HTML标记，然后发送到客户端。在客户端，一旦页面加载，你可以使用`window.customElements`来定义或升级自定义元素。\n\n如果你的目标是在服务器端生成一些自定义元素的HTML，并希望在客户端能够识别并处理这些元素，你可以这样做：\n\n1. 在服务器端，生成包含自定义元素标签的HTML字符串。\n2. 将这个HTML字符串发送到客户端。\n3. 在客户端，一旦页面加载完成，使用`window.customElements.define()`来定义自定义元素。\n\n下面是一个简单的示例，展示了如何在客户端定义一个自定义元素：\n\n```javascript\n// 定义一个简单的自定义元素\nclass MyCustomElement extends HTMLElement {\n  constructor() {\n    super(); // 调用父类的constructor\n    // 在这里可以添加更多的初始化代码\n  }\n\n  connectedCallback() {\n    this.innerHTML = '<p>Hello, Custom Element!</p>'; // 当元素插入到DOM时执行\n  }\n}\n\n// 检查是否在浏览器环境中\nif (typeof window !== 'undefined') {\n  // 使用window.customElements API定义自定义元素\n  window.customElements.define('my-custom-element', MyCustomElement);\n}\n```\n\n在服务端，你可以生成包含`<my-custom-element></my-custom-element>`的HTML字符串，并将其发送到客户端。然后，上面的脚本会在客户端定义这个元素，使其在页面上正常工作。\n\n请注意，这个例子假设你已经有了服务端渲染的设置，并且你知道如何在客户端执行JavaScript代码。如果你需要具体的服务端渲染框架的帮助（如Next.js, Nuxt.js等），请提供更多的上下文信息。",
        references: [],
        urls: [],
      },
    ],
    peer_type: 'web',
    peer_id: 'auth0|65363df666d30473af5f30eb',
    created: '2024-02-19T02:20:19.190626+00:00',
    updated: '2024-02-19T02:20:19.190640+00:00',
  },
];

export default {
  'GET /api/v1/bots': {
    code: '200',
    data: bots,
    page_number: 0,
    page_size: 7,
    count: 7,
  },
  'GET /api/v1/bots/:botId': (req: any, res: any) => {
    const { params } = req;
    res.status(200).json({
      code: '200',
      data: bots.find((bot) => bot.id === params.botId),
    });
  },
  'DELETE /api/v1/bots/:botId': {
    code: '200',
  },

  'GET /api/v1/bots/:botId/chats': (req: any, res: any) => {
    res.status(200).json({
      code: '200',
      data: chats,
    });
  },
};
