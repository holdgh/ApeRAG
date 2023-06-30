import { Message } from '@/models/chat';
import { getUser } from '@/models/user';
import { LoadingOutlined, RobotOutlined } from '@ant-design/icons';
import { Avatar, Space, theme } from 'antd';
import classNames from 'classnames';
import moment from 'moment';
import ReactMarkdown from 'react-markdown';
import { useTypewriter } from 'react-simple-typewriter';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import dark from 'react-syntax-highlighter/dist/esm/styles/prism/vs-dark';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import styles from './index.less';

export default ({ item, loading }: { item: Message; loading: boolean }) => {
  const user = getUser();
  const { token } = theme.useToken();
  const [text] = useTypewriter({
    words: [item.data || ''],
    typeSpeed: 5,
    loop: false,
  });

  const msgBgColor =
    item.role === 'human' ? token.colorPrimary : token.colorBgContainerDisabled;

  const renderAvatar = () => {
    const size = 42;
    const AiAvatar = (
      <Avatar
        size={size}
        style={{ minWidth: size, background: token.colorWarning }}
      >
        {loading ? <LoadingOutlined /> : <RobotOutlined />}
      </Avatar>
    );
    const HummanAvatar = (
      <Avatar style={{ minWidth: size }} size={size} src={user?.picture} />
    );
    return item.role === 'ai' ? AiAvatar : HummanAvatar;
  };

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
      {loading ? text : item.data}
    </ReactMarkdown>
  );

  const MessageInfoElement = (
    <Space
      className={styles.messageInfo}
      style={{ color: token.colorTextDisabled }}
      align={item.role === 'human' ? 'start' : 'end'}
    >
      <span>{moment(item.timestamp).format('llll')}</span>
      {/* <span>{item.references ? <Tag>{item.references}</Tag> : null}</span> */}
    </Space>
  );

  return (
    <div
      className={classNames({
        [styles.messageContainer]: true,
        [styles.ai]: item.role === 'ai',
        [styles.human]: item.role === 'human',
      })}
    >
      {renderAvatar()}
      <div
        className={classNames({
          [styles.message]: true,
        })}
      >
        <div
          className={styles.messageContent}
          style={{ background: msgBgColor }}
        >
          {MarkdownElement}
        </div>
        {MessageInfoElement}
      </div>
    </div>
  );
};
