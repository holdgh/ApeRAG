import { Message } from '@/models/chat';
import { getUser } from '@/models/user';
import { LoadingOutlined, RobotOutlined } from '@ant-design/icons';
import { Avatar, Space, theme } from 'antd';
import classNames from 'classnames';
import moment from 'moment';
import ReactMarkdown from 'react-markdown';
import { useTypewriter } from 'react-simple-typewriter';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { monokai } from 'react-syntax-highlighter/dist/cjs/styles/hljs'
import rehypeRaw from 'rehype-raw';
import rehypeInferTitleMeta from 'rehype-infer-title-meta';
import remarkGfm from 'remark-gfm';
import styles from './index.less';

export default ({ item, loading }: { item: Message; loading: boolean }) => {
  const user = getUser();
  const { token } = theme.useToken();
  const msgBgColor =
    item.role === 'human' ? token.colorPrimary : token.colorBgContainerDisabled;

  let displayText = item.data || '';
  // const [animateText] = useTypewriter({
  //   words: [displayText],
  //   typeSpeed: 10,
  //   loop: 1,
  // });
  // if(loading) {
  //   displayText = animateText;
  // }

  const renderAvatar = () => {
    const size = 50;
    const AiAvatar = (
      <Avatar
        size={size}
        style={{ minWidth: size, background: token.volcano5 }}
      >
        {loading ? <LoadingOutlined /> : <RobotOutlined />}
      </Avatar>
    );
    const HummanAvatar = (
      <Avatar style={{ minWidth: size }} size={size} src={user?.picture} />
    );
    return item.role === 'ai' ? AiAvatar : HummanAvatar;
  };

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
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw, rehypeInferTitleMeta]}
            components={{
              code({ inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter style={monokai} language={match[1]} PreTag="div">
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
            {displayText}
          </ReactMarkdown>
        </div>
        <Space
          className={styles.messageInfo}
          style={{ color: token.colorTextDisabled }}
          align={item.role === 'human' ? 'start' : 'end'}
        >
          <span>{moment(item.timestamp).format('llll')}</span>
          {/* <span>{item.references ? <Tag>{item.references}</Tag> : null}</span> */}
        </Space>
      </div>
    </div>
  );
};
