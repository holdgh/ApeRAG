import { Message, MessageStatus } from '@/models/chat';
import { getUser } from '@/models/user';
import { RobotOutlined } from '@ant-design/icons';
import { Avatar, Skeleton, Typography, theme } from 'antd';
import classNames from 'classnames';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import dark from 'react-syntax-highlighter/dist/esm/styles/prism/vs-dark';

import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import styles from './index.less';

export default ({
  item,
  status = 'normal',
}: {
  item: Message;
  status: MessageStatus;
}) => {
  const user = getUser();
  const { token } = theme.useToken();

  const AiAvatar = (
    <Avatar size={50}>
      <RobotOutlined />
    </Avatar>
  );
  const HummanAvatar = <Avatar size={50} src={user?.picture} />;
  const MarkdownElement = (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        code({ inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <SyntaxHighlighter style={dark} language={match[1]} PreTag="div">
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className={className} {...props}>
              {children}
            </code>
          );
        },
      }}
    >
      {item.data}
    </ReactMarkdown>
  );
  const LoadingElement = (
    <Skeleton style={{ marginTop: 16 }} active paragraph={{ rows: 3 }} />
  );
  const ErrorElement = (
    <Typography.Text type="danger">response error</Typography.Text>
  );
  const AvatarElement = item.role === 'ai' ? AiAvatar : HummanAvatar;
  return (
    <div
      className={classNames({
        [styles.messageContainer]: true,
        [styles.ai]: item.role === 'ai',
        [styles.human]: item.role === 'human',
      })}
    >
      {AvatarElement}
      <div
        className={classNames({
          [styles.message]: true,
          [styles.loading]: status === 'loading',
          [styles.error]: status === 'error',
        })}
        style={{
          background:
            item.role === 'human'
              ? token.colorPrimary
              : token.colorBgContainerDisabled,
        }}
      >
        {status === 'normal' ? MarkdownElement : null}
        {status === 'loading' ? LoadingElement : null}
        {status === 'error' ? ErrorElement : null}
      </div>
    </div>
  );
};
