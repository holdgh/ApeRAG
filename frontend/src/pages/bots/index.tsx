import { PageContainer, PageHeader, RefreshButton } from '@/components';
import { MODEL_FAMILYS_ICON } from '@/constants';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import {
  Avatar,
  Button,
  Card,
  Col,
  Divider,
  Input,
  Result,
  Row,
  Select,
  Space,
  theme,
  Tooltip,
  Typography,
} from 'antd';
import _ from 'lodash';
import moment from 'moment';
import { useEffect, useMemo, useState } from 'react';
import { BsBook, BsRobot } from 'react-icons/bs';
import { UndrawEmpty } from 'react-undraw-illustrations';
import { FormattedMessage, Link, useIntl, useModel } from 'umi';

type BotSearchParams = {
  title?: string;
  model?: string;
};

export default () => {
  const [searchParams, setSearchParams] = useState<BotSearchParams>();
  const { token } = theme.useToken();
  const { models } = useModel('models');
  const { bots, botsLoading, getBots } = useModel('bot');
  const { formatMessage } = useIntl();

  const groupModels = useMemo(
    () =>
      Object.keys(_.groupBy(models, 'family_name')).map((familyName) => {
        const children = models?.filter(
          (item) => item.family_name === familyName,
        );
        return {
          label: children?.[0]?.family_label || 'unknow',
          options: children?.map((item) => item),
        };
      }),
    [models],
  );

  const _bots = useMemo(
    () =>
      bots?.filter((item) => {
        const config = item.config;
        const titleMatch = searchParams?.title
          ? item.title?.includes(searchParams.title)
          : true;
        const modelMatch = searchParams?.model
          ? config?.model === searchParams.model
          : true;
        return titleMatch && modelMatch;
      }),
    [bots, searchParams],
  );

  const header = useMemo(
    () => (
      <PageHeader
        title={formatMessage({ id: 'bot.name' })}
        description={formatMessage({ id: 'bot.description' })}
      >
        <Space>
          <Select
            style={{ width: 180 }}
            placeholder={formatMessage({ id: 'model.name' })}
            options={groupModels}
            allowClear
            onChange={(v) => {
              setSearchParams({ ...searchParams, model: v });
            }}
            value={searchParams?.model}
          />
          <Input
            placeholder={formatMessage({ id: 'action.search' })}
            prefix={
              <Typography.Text disabled>
                <SearchOutlined />
              </Typography.Text>
            }
            onChange={(e) => {
              setSearchParams({
                ...searchParams,
                title: e.currentTarget.value,
              });
            }}
            allowClear
            value={searchParams?.title}
          />

          <Tooltip title={<FormattedMessage id="bot.add" />}>
            <Link to="/bots/new">
              <Button type="primary" icon={<PlusOutlined />} />
            </Link>
          </Tooltip>
          <RefreshButton loading={botsLoading} onClick={() => getBots()} />
        </Space>
      </PageHeader>
    ),
    [groupModels, searchParams, botsLoading],
  );

  useEffect(() => {
    getBots();
  }, []);

  if (bots === undefined) return;

  return (
    <PageContainer>
      {header}
      {_.isEmpty(_bots) ? (
        <Result
          icon={
            <UndrawEmpty primaryColor={token.colorPrimary} height="200px" />
          }
          subTitle={<FormattedMessage id="text.empty" />}
        />
      ) : (
        <Row gutter={[24, 24]}>
          {_bots?.map((bot) => {
            const config = bot.config;
            const model = models?.find((item) => item.value === config?.model);
            const modelIcon = model?.family_name
              ? MODEL_FAMILYS_ICON[model.family_name]
              : undefined;
            return (
              <Col key={bot.id} xs={24} sm={12} md={8} lg={6} xl={6} xxl={6}>
                <Link to={`/bots/${bot.id}/chats`}>
                  <Card hoverable size="small">
                    <div
                      style={{ display: 'flex', gap: 8, alignItems: 'center' }}
                    >
                      <Avatar
                        style={{ flex: 'none' }}
                        size={40}
                        src={modelIcon}
                      />
                      <div style={{ flex: 'auto', maxWidth: '65%' }}>
                        <div>
                          <Typography.Text ellipsis>
                            {bot.title}
                          </Typography.Text>
                        </div>
                        <div>
                          <Typography.Text ellipsis type="secondary">
                            {model?.label}
                          </Typography.Text>
                        </div>
                      </div>
                    </div>
                    <Divider style={{ marginBlock: 8 }} />
                    <div
                      style={{
                        display: 'flex',
                        gap: 8,
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <Typography.Text
                        ellipsis
                        type="secondary"
                        style={{ fontSize: '0.9em', width: '60%' }}
                      >
                        <span
                          style={{
                            display: 'inline-block',
                            verticalAlign: 'middle',
                            marginRight: 8,
                          }}
                        >
                          {bot.type === 'common' ? <BsRobot /> : <BsBook />}
                        </span>
                        {bot.type === 'common' ? (
                          <FormattedMessage id="bot.type_common" />
                        ) : (
                          <FormattedMessage id="bot.type_knowledge" />
                        )}
                      </Typography.Text>
                      <Typography.Text
                        ellipsis
                        type="secondary"
                        style={{
                          fontSize: '0.9em',
                          width: '40%',
                          textAlign: 'right',
                        }}
                      >
                        {moment(bot.created).fromNow()}
                      </Typography.Text>
                    </div>
                  </Card>
                </Link>
              </Col>
            );
          })}
        </Row>
      )}
    </PageContainer>
  );
};
