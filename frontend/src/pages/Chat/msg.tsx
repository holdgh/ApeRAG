import ChatRobot from '@/assets/chatbot.png';
import EllipsisAnimate from '@/components/EllipsisAnimate';
import { getUser } from '@/models/user';
import type { TypesMessage, TypesSocketStatus } from '@/types';
import {
  LinkOutlined,
  LoadingOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { sql } from '@codemirror/lang-sql';
import { okaidiaInit } from '@uiw/codemirror-theme-okaidia';
import CodeMirror from '@uiw/react-codemirror';
import { Avatar, Badge, Divider, Drawer, Space, Typography, theme } from 'antd';
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

const EditorTheme = okaidiaInit({
  theme: 'dark',
  settings: {
    background: 'transparent',
    caret: '#FFF',
    gutterBackground: 'transparent',
    gutterForeground: 'rgba(255, 255, 255, 0.2)',
    lineHighlight: 'transparent',
  },
});

type Props = {
  item: TypesMessage;
  loading: boolean;
  status: TypesSocketStatus;
  onExecute: (msg: TypesMessage) => void;
};

const TYPE_WRITER_SPEED = 40;

export default ({ item, loading, onExecute = () => {} }: Props) => {
  const [runtimeText, setRuntimeText] = useState<string>('');
  const [displayText, setDisplayText] = useState<string>('');
  const [showReferences, setShowReferences] = useState<boolean>(false);
  const user = getUser();
  const { token } = theme.useToken();
  const msgBgColor =
    item.role === 'human' ? token.colorPrimary : token.colorBgContainerDisabled;

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
    const customStyle = {
      padding: 0,
      fontFamily: 'inherit',
      fontSize: 'inherit',
      margin: 0,
      lineHeight: 'inherit',
    };
    if (item.type === 'sql') {
      return (
        <CodeMirror
          value={displayText.replace(/\n+$/, '')}
          minHeight="0"
          minWidth="300px"
          extensions={[sql()]}
          theme={EditorTheme}
          onChange={(v) => (item.data = v)}
        />
      );
    } else {
      return (
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw, rehypeInferTitleMeta]}
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
    }
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
    if (!loading || !item._typeWriter) {
      setDisplayText(data);
    } else {
      setRuntimeText(data);
    }
  }, [item, loading]);

  return (
    <div
      className={classNames({
        [styles.messageContainer]: true,
        [styles.ai]: item.role === 'ai',
        [styles.human]: item.role === 'human',
      })}
    >
      {item._typeWriter && loading ? (
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
          style={{ background: msgBgColor }}
        >
          {_.isEmpty(displayText) && loading ? (
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
            <div>{moment(item.timestamp).format('llll')}</div>
            {renderReferences()}
            {item.type === 'sql' && !loading ? (
              <Typography.Link
                style={{ fontSize: 12 }}
                onClick={() => onExecute(item)}
              >
                Execute
              </Typography.Link>
            ) : null}
          </Space>
        </Space>
      </div>
      <Drawer
        open={showReferences}
        title="References"
        size="large"
        onClose={() => setShowReferences(false)}
      >
        {item.references?.map((reference, key) => {
          return (
            <div key={key} className={styles.markdown}>
              <Typography.Title ellipsis level={4}>
                <LinkOutlined /> {key + 1}、 {reference.metadata?.source}
              </Typography.Title>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw, rehypeInferTitleMeta]}
                components={{
                  code({ inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={dark}
                        language={match[1]}
                        PreTag="div"
                      >
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
                {reference.text || ''}
              </ReactMarkdown>
              <Divider />
            </div>
          );
        })}
      </Drawer>
    </div>
  );
};
