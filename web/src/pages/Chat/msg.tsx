import ChatRobot from '@/assets/chatbot.svg';
import DefaultAvatar from '@/assets/default-avatar.png';
import EllipsisAnimate from '@/components/EllipsisAnimate';
import { getUser } from '@/models/user';
import { VoteChatMessage } from '@/services/chats';
import type { TypesMessage } from '@/types';
import themeVariable from '@/variable';
import {
  DislikeFilled,
  LikeFilled,
  LoadingOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { useModel, useParams, useIntl } from '@umijs/max';
import { Avatar, Badge, Button, Divider, Space, Typography, theme } from 'antd';
import classNames from 'classnames';
import _ from 'lodash';
import moment from 'moment';
import { useEffect, useState } from 'react';
import ReactInterval from 'react-interval';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus as dark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import rehypeInferTitleMeta from 'rehype-infer-title-meta';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import styles from './index.less';

type Props = {
  item: TypesMessage;
  isTyping: boolean;
  openExtendPanel: () => void;
  onExecute: (msg: TypesMessage) => void;
};

const TYPE_WRITER_SPEED = 40;

export default ({ item, isTyping, openExtendPanel }: Props) => {
  const [runtimeText, setRuntimeText] = useState<string>('');
  const [displayText, setDisplayText] = useState<string>('');
  const [showReferences, setShowReferences] = useState<boolean>(false);
  const { getBot } = useModel('bot');
  const user = getUser();
  const { token } = theme.useToken();
  const msgBgColor =
    item.role === 'human'
      ? token.colorPrimary
      : themeVariable.sidebarBackgroundColor;

  const { botId } = useParams();
  const bot = getBot(botId);
  const { currentChat, setCurrentChatHistory } = useModel('chat');

  if (!bot) {
    return null;
  }

  const intl = useIntl();

  const messageVote = async (params: TypesMessage) => {
    if (!bot.id || !currentChat?.id || !item.id) return;
    const index = currentChat.history.findIndex(
      (h) => h.id === item.id && h.role === 'ai',
    );
    if (index !== -1) {
      const data: TypesMessage = {
        ...currentChat.history[index],
        ...params,
      };

      await VoteChatMessage(bot.id, currentChat.id, item.id, data);
      Object.assign(currentChat.history[index], data);
      setCurrentChatHistory(currentChat.history);
    }
  };

  const renderAvatar = () => {
    const size = 50;
    const AiAvatar = (
      <Avatar
        size={size}
        src={isTyping ? null : ChatRobot}
        className='avatar-ai'
        style={{ minWidth: size }}
      >
        {isTyping ? <LoadingOutlined /> : <RobotOutlined />}
      </Avatar>
    );
    const HummanAvatar = (
      <img className='avatar-human' src={user?.picture||DefaultAvatar} onError={(e) => {e.target.src = DefaultAvatar}} />
    );
    return item.role === 'ai' ? AiAvatar : HummanAvatar;
  };

  const renderContent = () => {
    const customStyle = {
      padding: 0,
      fontFamily: 'inherit',
      fontSize: 'inherit',
      margin: 0,
      lineHeight: 'inherit',
    };

    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeInferTitleMeta]}
        className={classNames({
          [styles.markdown]: true,
          [styles.error]: item.type === 'error',
        })}
        components={{
          code({ inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={dark}
                customStyle={customStyle}
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
        {displayText}
      </ReactMarkdown>
    );
  };

  const renderReferences = () => {
    if (!item.references?.length) return;
    return (
      <Typography.Link
        style={{ fontSize: 12 }}
        onClick={() => setShowReferences(true)}
      >
        References
        <Badge
          count={item.references.length}
          style={{
            background: 'rgba(255, 255, 255, 0.1)',
            color: 'rgba(255, 255, 255, 0.8)',
            transform: 'scale(0.7)',
          }}
        />
      </Typography.Link>
    );
  };

  const typingWriter = () => {
    setDisplayText((s) => {
      const distance = Math.ceil(
        (runtimeText.length - displayText.length) / 10,
      );
      const fromIndex = displayText.length;
      const toIndex = fromIndex + distance;
      const nextChar = runtimeText.substring(fromIndex, toIndex);
      return s + nextChar;
    });
  };

  useEffect(() => {
    let data = (item.data || '').replace(/^\n*/, '').replace(/\n{1}/g, '\n\n');
    if (!isTyping || !item._typeWriter) {
      setDisplayText(data);
    } else {
      setRuntimeText(data);
    }
  }, [item, isTyping]);

  return (
    <div
      className={classNames({
        [styles.messageContainer]: true,
        [styles.ai]: item.role === 'ai',
        [styles.human]: item.role === 'human',
      })}
    >
      {item._typeWriter && isTyping ? (
        <ReactInterval
          timeout={TYPE_WRITER_SPEED}
          enabled={true}
          callback={typingWriter}
        />
      ) : null}
      {renderAvatar()}
      <div
        className={classNames({
          [styles.message]: true,
        })}
      >
        <div
          className={classNames({
            [styles.messageContent]: true,
            [styles.markdown]: true,
          })}
        >
          {_.isEmpty(displayText) && isTyping ? (
            <EllipsisAnimate />
          ) : (
            renderContent()
          )}
        </div>
        <Space
          className={styles.messageInfo}
          style={{ color: token.colorTextDisabled }}
          align={item.role === 'human' ? 'start' : 'end'}
        >
          <Space split={<Divider type="vertical" />}>
            { item.role === 'ai' && <div>{moment(item.timestamp).format('lll')}</div>}
            {item.references?.length && (
              <button className={`${styles.reference} show-reference`} onClick={()=> openExtendPanel(item.references)}>
                {intl.formatMessage({id: 'text.references'})} {item.references.length}
              </button>
            )}
          </Space>
        </Space>
      </div>
      {item.role === 'ai' ? (
        <div className={styles.operate}>
          <Space className={styles.operateWrap} size="small">
            <Button
              size="middle"
              onClick={() =>
                messageVote({
                  upvote: item.upvote ? 0 : 1,
                  downvote: 0,
                })
              }
            >
              <Typography.Text type={item.upvote ? 'success' : 'secondary'}>
                <LikeFilled />
              </Typography.Text>
            </Button>
            <Button
              size="middle"
              onClick={() =>
                messageVote({
                  upvote: 0,
                  downvote: item.downvote ? 0 : 1,
                })
              }
            >
              <Typography.Text type={item.downvote ? 'danger' : 'secondary'}>
                <DislikeFilled />
              </Typography.Text>
            </Button>
          </Space>
        </div>
      ) : null}
    </div>
  );
};
