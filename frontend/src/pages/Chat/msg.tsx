import ChatRobot from '@/assets/chatbot.png';
import { getUser } from '@/models/user';
import type { TypesMessage, TypesSocketStatus } from '@/types';
import {
  LinkOutlined,
  LoadingOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { Avatar, Badge, Divider, Drawer, Space, Typography, theme } from 'antd';
import classNames from 'classnames';
import moment from 'moment';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus as dark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import rehypeInferTitleMeta from 'rehype-infer-title-meta';
import EllipsisAnimate from '@/components/EllipsisAnimate';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import styles from './index.less';
import _ from 'lodash';

type Props = {
  item: TypesMessage;
  loading: boolean;
  status: TypesSocketStatus;
  onExecute: (msg: TypesMessage) => void;
};

export default ({ item, loading, status, onExecute = () => {} }: Props) => {
  const [showReferences, setShowReferences] = useState<boolean>(false);
  const user = getUser();
  const { token } = theme.useToken();
  const msgBgColor =
    item.role === 'human' ? token.colorPrimary : token.colorBgContainerDisabled;

  let displayText = (item.data || '').replace(/^\n*/, '');
  

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
    let text = displayText;

    if(_.isEmpty(text) && loading) {
      return <EllipsisAnimate />
    }

    if (item.type === 'sql') {
      text = '```sql\n' + displayText + '\n```';
    }

    const Markdown = (
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
        {text}
      </ReactMarkdown>
    );
    return Markdown;
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
          className={classNames({
            [styles.messageContent]: true,
            [styles.markdown]: true,
          })}
          style={{ background: msgBgColor }}
        >
          {renderContent()}
        </div>
        <Space
          className={styles.messageInfo}
          style={{ color: token.colorTextDisabled }}
          align={item.role === 'human' ? 'start' : 'end'}
        >
          <Space split={<Divider type="vertical" />}>
            <div>{moment(item.timestamp).format('llll')}</div>
            {renderReferences()}
            {item.type === 'sql' ? (
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
