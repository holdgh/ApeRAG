import type { TypesMessage } from '@/types';
import { getUser } from '@/models/user';
import {
  LoadingOutlined,
  PlayCircleFilled,
  RobotOutlined,
} from '@ant-design/icons';
import { Avatar, Button, Space, theme } from 'antd';
import classNames from 'classnames';
import moment from 'moment';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
// import { monokai } from 'react-syntax-highlighter/dist/cjs/styles/hljs';
import ChatRobot from '@/assets/chatbot.png';
import { useTypewriter } from 'react-simple-typewriter';
import dark from 'react-syntax-highlighter/dist/esm/styles/prism/vs-dark';
import rehypeInferTitleMeta from 'rehype-infer-title-meta';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import styles from './index.less';

type Props = {
  item: TypesMessage;
  loading: boolean;
  disabled: boolean;
  animate: boolean;
  onExecuteSQL: (msg?: TypesMessage) => void;
};

export default ({
  item,
  loading,
  disabled = false,
  animate = false,
  onExecuteSQL = () => {},
}: Props) => {
  const user = getUser();
  const { token } = theme.useToken();
  const msgBgColor =
    item.role === 'human' ? token.colorPrimary : token.colorBgContainerDisabled;

  let displayText = (item.data || '').replace(/^\n*/, '');
  const [animateText] = useTypewriter({
    words: [displayText],
    typeSpeed: 5,
    loop: 1,
  });

  if (animate) {
    displayText = animateText;
  }

  const renderAvatar = () => {
    const size = 50;
    const AiAvatar = (
      <Avatar
        size={size}
        src={loading ? null : ChatRobot}
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

  const renderContent = () => {
    if (item.type === 'sql') {
      displayText = '```sql\n' + displayText + '\n```';
    }

    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeInferTitleMeta]}
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
        {displayText}
      </ReactMarkdown>
    );
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
          {renderContent()}
        </div>
        <Space
          className={styles.messageInfo}
          style={{ color: token.colorTextDisabled }}
          align={item.role === 'human' ? 'start' : 'end'}
        >
          <Space>
            <span>{moment(item.timestamp).format('llll')}</span>
            {/* <span>{item.references ? <Tag>{item.references}</Tag> : null}</span> */}
          </Space>
          {item.type === 'sql' ? (
            <Button
              disabled={disabled}
              onClick={() => onExecuteSQL(item)}
              type="text"
              size="small"
              icon={<PlayCircleFilled />}
            />
          ) : null}
        </Space>
      </div>
    </div>
  );
};
