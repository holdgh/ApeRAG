import { VoteChatMessage } from '@/services/chats';
import { TypesMessage } from '@/types';
import { useParams,useIntl } from '@umijs/max';
import { Button, Drawer, Input, Segmented } from 'antd';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus as dark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import rehypeInferTitleMeta from 'rehype-infer-title-meta';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import styles from './index.less';

type Pros = {
  chatId: string;
  record: TypesMessage;
  onSuccess: () => void;
};

export default ({ chatId, record, onSuccess }: Pros) => {
  const [visible, setVisible] = useState<boolean>(false);
  const [revisedAnswer, setRevisedAnswer] = useState<string>(
    record.revised_answer || '',
  );
  const { botId } = useParams();
  const intl = useIntl();
  const actual = intl.formatMessage({id:'bots.chat.actual'});
  const revised = intl.formatMessage({id:'bots.chat.revised'})

  type TypesAnswerType = actual | revised;
  const [answerType, setAnswerType] = useState<TypesAnswerType>(revised);

  const saveExpectAnswer = async () => {
    if (!botId || !record.id) return;

    await VoteChatMessage(botId, chatId, record.id, {
      id: record.id,
      revised_answer: revisedAnswer,
    });

    onSuccess();
    setVisible(false);
  };

  const ActualAnswerNode = (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw, rehypeInferTitleMeta]}
      className={styles.markdown}
      components={{
        code({ inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <SyntaxHighlighter
              style={dark}
              customStyle={{
                padding: 0,
                fontFamily: 'inherit',
                fontSize: 'inherit',
                margin: 0,
                lineHeight: 'inherit',
              }}
              language={match[1]}
              PreTag="div"
            >
              {String(children)
                .replace(/\n$/, '')
                .replace(/^\n*/, '')
                .replace(/\n+/g, '\n')}
            </SyntaxHighlighter>
          ) : (
            <code className={className} {...props}>
              {children}
            </code>
          );
        },
      }}
    >
      {record._original_answer || ''}
    </ReactMarkdown>
  );

  const RevisedAnswerNode = (
    <Input.TextArea
      value={revisedAnswer}
      onChange={(e) => setRevisedAnswer(e.currentTarget.value)}
      autoFocus
      style={{
        position: 'absolute',
        width: '100%',
        top: 0,
        bottom: 0,
        borderWidth: 0,
        resize: 'none',
      }}
    />
  );

  return (
    <>
      <Button type="link" onClick={() => setVisible(true)}>
        {intl.formatMessage({id:'action.edit'})}
      </Button>
      <Drawer
        size="large"
        title={intl.formatMessage({id:'bots.chat.edit'})}
        open={visible}
        extra={
          <Segmented
            onChange={(v) => setAnswerType(v as TypesAnswerType)}
            value={answerType}
            options={[revised, actual]}
          />
        }
        footer={
          <Button
            onClick={() => saveExpectAnswer()}
            disabled={answerType !== revised}
            type="primary"
          >
            {intl.formatMessage({id:'action.save'})}
          </Button>
        }
        bodyStyle={{
          padding: answerType === actual ? 12 : 0,
          position: 'relative',
        }}
        onClose={() => setVisible(false)}
      >
        {answerType === actual ? ActualAnswerNode : RevisedAnswerNode}
      </Drawer>
    </>
  );
};
