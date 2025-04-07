import { Avatar, Card, Col, Row } from 'antd';
import { useIntl } from '@umijs/max';
import classNames from 'classnames';
import { useState } from 'react';
import styles from './index.less';
import FeishuIntegration from './feishu';
import WeixinIntegration from './weixin';
import OfficialaccountIntegration from './officialaccount';
import DingtalkIntegration from './dingtalk';
import WebIntegration from './web';
import IconWeb from '@/assets/globe.svg';
import IconFeishu from '@/assets/feishu-on.svg';
import IconWeixin from '@/assets/weixin.svg';
import IconOfficialaccount from '@/assets/officialaccount-on.svg';
import IconDingtalk from '@/assets/dingtalk-on.svg';

export default () => {
  const [currentIntegration, setCurrentIntegration] = useState<
    'feishu' | 'weixin' | 'web'
  >('feishu');

  const intl = useIntl();

  return (
    <div className="border-block">
      <Row style={{ margin: '24px', justifyContent:'space-between'}} gutter={24}>
        <Col lg={24} xl={6}>
          <Card
            onClick={() => setCurrentIntegration('feishu')}
            className={classNames({
              [styles.integrationItem]: true,
              [styles.selected]: currentIntegration === 'feishu',
            })}
          >
            <Card.Meta
              avatar={
                <Avatar
                  size={55}
                  src={IconFeishu}
                />
              }
              title={intl.formatMessage({id:'bots.integration.feishu'})}
              description={intl.formatMessage({id:'bots.integration.feishu.desc'})}
            />
          </Card>
        </Col>
        <Col lg={24} xl={6}>
          <Card
            onClick={() => setCurrentIntegration('weixin')}
            className={classNames({
              [styles.integrationItem]: true,
              [styles.selected]: currentIntegration === 'weixin',
            })}
          >
            <Card.Meta
              avatar={
                <Avatar
                  size={55}
                  src={IconWeixin}
                />
              }
              title={intl.formatMessage({id:'bots.integration.weixin'})}
              description={intl.formatMessage({id:'bots.integration.weixin.desc'})}
            />
          </Card>
        </Col>
        <Col lg={24} xl={6}>
          <Card
            onClick={() => setCurrentIntegration('dingtalk')}
            className={classNames({
              [styles.integrationItem]: true,
              [styles.selected]: currentIntegration === 'dingtalk',
            })}
          >
            <Card.Meta
              avatar={
                <Avatar
                  size={55}
                  src={IconDingtalk}
                />
              }
              title={intl.formatMessage({id:'bots.integration.dingtalk'})}
              description={intl.formatMessage({id:'bots.integration.dingtalk.desc'})}
            />
          </Card>
        </Col>
        <Col lg={24} xl={6}>
          <Card
            onClick={() => setCurrentIntegration('web')}
            className={classNames({
              [styles.integrationItem]: true,
              [styles.selected]: currentIntegration === 'web',
            })}
          >
            <Card.Meta
              avatar={
                <Avatar
                  size={55}
                  src={IconWeb}
                />
              }
              title="Web"
              description={intl.formatMessage({id:'bots.integration.web.desc'})}
            />
          </Card>
        </Col>
      </Row>
      <Row style={{ margin: '24px', justifyContent:'space-between'}} gutter={24}>
        <Col lg={24} xl={6}>
          <Card
            onClick={() => setCurrentIntegration('officialaccount')}
            className={classNames({
              [styles.integrationItem]: true,
              [styles.selected]: currentIntegration === 'officialaccount',
            })}
          >
            <Card.Meta
              avatar={
                <Avatar
                  size={55}
                  src={IconOfficialaccount}
                />
              }
              title={intl.formatMessage({id:'bots.integration.officialaccount'})}
              description={intl.formatMessage({id:'bots.integration.officialaccount.desc'})}
            />
          </Card>
        </Col>
      </Row>

      {currentIntegration === 'feishu' ? <FeishuIntegration /> : null}
      {currentIntegration === 'weixin' ? <WeixinIntegration /> : null}
      {currentIntegration === 'officialaccount' ? <OfficialaccountIntegration /> : null}
      {currentIntegration === 'dingtalk' ? <DingtalkIntegration /> : null}
      {currentIntegration === 'web' ? <WebIntegration /> : null}

    </div>
  );
};
