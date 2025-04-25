import { Chat } from '@/api';
import { api } from '@/services';
import {
  DeleteOutlined,
  EditOutlined,
  MoreOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import {
  Button,
  Divider,
  Dropdown,
  Form,
  Input,
  Menu,
  MenuProps,
  Modal,
  Space,
  Tooltip,
} from 'antd';
import FormItem from 'antd/es/form/FormItem';
import _ from 'lodash';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  history,
  Outlet,
  useIntl,
  useLocation,
  useModel,
  useParams,
} from 'umi';
import { BodyContainer } from './body';
import { Navbar, NavbarBody, NavbarHeader } from './navbar';
import Sidebar from './sidebar';

type MenuItem = Required<MenuProps>['items'][number];

export default () => {
  const { botId, chatId } = useParams();
  const [renameVisible, setRenameVisible] = useState<boolean>();
  const { bot, chats, getBot, setBot, setChats, getChats } = useModel('bot');
  const location = useLocation();
  const { formatMessage } = useIntl();
  const [modal, contextHolder] = Modal.useModal();
  const isDetail = botId !== undefined;
  const [form] = Form.useForm<Chat>();

  const onDeleteBot = useCallback(async () => {
    if (!botId) return;
    const confirmed = await modal.confirm({
      title: formatMessage({ id: 'action.confirm' }),
      content: formatMessage(
        { id: 'bot.delete_confirm' },
        { name: bot?.title },
      ),
      okButtonProps: {
        danger: true,
      },
    });
    if (confirmed) {
      const res = await api.botsBotIdDelete({ botId });
      if (res.status === 200) {
        history.push('/bots');
      }
    }
  }, [botId]);

  const onCreateChat = useCallback(async () => {
    if (botId) {
      const res = await api.botsBotIdChatsPost({
        botId,
        chatCreate: {
          title: '',
        },
      });
      if (res.status === 200 && res?.data.id) {
        setChats((cs) => cs?.concat(res.data));
        history.push(`/bots/${botId}/chats/${res.data.id}`);
      }
    }
  }, [botId]);

  const onRenameChat = useCallback(async () => {
    const data = await form.validateFields();

    if (!data?.id || !botId) return;

    await api.botsBotIdChatsChatIdPut({
      botId,
      chatId: data.id,
      chatUpdate: data,
    });

    await getChats(botId);

    setRenameVisible(false);
  }, []);

  const onDeleteChat = useCallback(
    async (item: Chat) => {
      if (!botId || !item.id) return;
      const confirmed = await modal.confirm({
        title: formatMessage({ id: 'action.confirm' }),
        content: formatMessage({ id: 'chat.delete.confirm' }),
        okButtonProps: {
          danger: true,
        },
      });
      if (!confirmed) return;
      const res = await api.botsBotIdChatsChatIdDelete({
        botId,
        chatId: item.id,
      });
      if (res.status === 200) {
        const data = chats?.filter((c) => c.id !== item.id) || [];
        setChats(data);

        if (_.isEmpty(data)) {
          history.push(`/bots/${botId}/chats`);
        } else if (chatId === item.id) {
          history.push(`/bots/${botId}/chats/${data[0]?.id}`);
        }
      }
    },
    [botId, chatId, chats],
  );

  const menuItems = useMemo((): MenuItem[] => {
    return [
      {
        key: 'chat',
        label: (
          <Space
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            {formatMessage({ id: 'chat.all' })}
            <Tooltip
              title={formatMessage({ id: 'chat.new' })}
              placement="right"
            >
              <Button
                type="text"
                icon={<PlusOutlined />}
                onClick={() => onCreateChat()}
                style={{
                  transform: 'translateX(8px)',
                }}
              />
            </Tooltip>
          </Space>
        ),
        type: 'group',
        children: (chats || []).map((item) => {
          const path = `/bots/${botId}/chats/${item.id}`;
          return {
            style: { paddingRight: 40 },
            label: (
              <>
                {_.truncate(item.title || formatMessage({ id: 'chat.new' }), {
                  length: 22,
                })}
                <Dropdown
                  menu={{
                    items: [
                      {
                        key: 'rename',
                        label: formatMessage({ id: 'action.rename' }),
                        icon: <EditOutlined />,
                        onClick: ({ domEvent }) => {
                          domEvent.stopPropagation();
                          form.setFieldsValue(item);
                          setRenameVisible(true);
                        },
                      },
                      {
                        key: 'delete',
                        label: formatMessage({ id: 'chat.delete' }),
                        icon: <DeleteOutlined />,
                        danger: true,
                        onClick: ({ domEvent }) => {
                          domEvent.stopPropagation();
                          onDeleteChat(item);
                        },
                      },
                    ],
                  }}
                  overlayStyle={{
                    width: 160,
                  }}
                >
                  <Button
                    type="text"
                    style={{
                      position: 'absolute',
                      top: 4,
                      right: 4,
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                    }}
                    icon={<MoreOutlined />}
                  />
                </Dropdown>
              </>
            ),
            key: path,
          };
        }),
      },
      {
        label: formatMessage({ id: 'action.settings' }),
        key: `/bots/${botId}/settings`,
        type: 'group',
        children: [
          {
            label: formatMessage({ id: 'flow.settings' }),
            key: `/bots/${botId}/flow`,
          },
          {
            label: formatMessage({ id: 'text.integrations' }),
            key: `/bots/${botId}/integrations`,
          },
          {
            label: formatMessage({ id: 'bot.settings' }),
            key: `/bots/${botId}/settings`,
          },
        ],
      },
    ];
  }, [botId, chats, onCreateChat, onDeleteChat, onRenameChat]);

  useEffect(() => {
    if (botId) {
      getBot(botId);
      getChats(botId);
    }
    return () => {
      setBot(undefined);
      setChats(undefined);
    };
  }, [botId]);

  return (
    <>
      {contextHolder}
      <Sidebar />
      {isDetail && (
        <Navbar>
          <NavbarHeader
            title={bot?.title || formatMessage({ id: 'bot.name' })}
            backTo="/bots"
          >
            <Tooltip
              title={formatMessage({ id: 'bot.delete' })}
              placement="right"
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={() => onDeleteBot()}
              />
            </Tooltip>
          </NavbarHeader>
          <NavbarBody>
            <Menu
              onClick={({ key }) => history.push(key)}
              mode="inline"
              selectedKeys={[location.pathname]}
              items={menuItems}
              style={{
                padding: 0,
                background: 'none',
                border: 'none',
              }}
            />
          </NavbarBody>
        </Navbar>
      )}

      <BodyContainer sidebar={true} navbar={isDetail}>
        <Outlet />
      </BodyContainer>

      <Modal
        width={400}
        open={renameVisible}
        onOk={() => onRenameChat()}
        title={formatMessage({ id: 'action.rename' })}
        onCancel={() => setRenameVisible(false)}
      >
        <Divider />
        <Form layout="vertical" form={form}>
          <FormItem name="id" hidden>
            <Input />
          </FormItem>
          <FormItem
            required
            name="title"
            label={formatMessage({ id: 'chat.title' })}
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'chat.title_required' }),
              },
            ]}
          >
            <Input />
          </FormItem>
        </Form>
      </Modal>
    </>
  );
};
