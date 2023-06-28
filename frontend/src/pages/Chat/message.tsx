import { ChatHistory } from '@/models/chat';
import { getUser } from '@/models/user';
import { RobotOutlined } from '@ant-design/icons';
import { Avatar, Skeleton, theme } from 'antd';
import classNames from 'classnames';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import dark from 'react-syntax-highlighter/dist/esm/styles/prism/vs-dark';

import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import styles from './index.less';

export default ({
  item,
  loading = false,
}: {
  item: ChatHistory;
  loading: boolean;
}) => {
  const user = getUser();
  const { token } = theme.useToken();

  const markdownElement = (
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
      {item.message}
    </ReactMarkdown>
  );

  const skeletonElement = (
    <Skeleton style={{ marginTop: 16 }} active paragraph={{ rows: 3 }} />
  );

  return (
    <div
      className={classNames({
        [styles.messageContainer]: true,
        [styles.robot]: item.role === 'robot',
        [styles.human]: item.role === 'human',
      })}
    >
      {item.role === 'robot' ? (
        <Avatar size={40}>
          <RobotOutlined />
        </Avatar>
      ) : (
        <Avatar size={40} src={user?.picture} />
      )}
      <div
        className={classNames({
          [styles.message]: true,
          [styles.loading]: loading,
        })}
        style={{
          background:
            item.role === 'human'
              ? token.colorPrimary
              : token.colorBgContainerDisabled,
        }}
      >
        {loading
          ? skeletonElement
          : item.role === 'robot'
          ? markdownElement
          : item.message}
      </div>
    </div>
  );
};
