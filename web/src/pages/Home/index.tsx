import imgBanner from '@/assets/banner.png';
import PageLoading from '@/components/PageLoading';
import { DOCUMENT_SOURCE_OPTIONS } from '@/constants';
import auth0Client from '@/utils/auth0';
import { CheckSquareOutlined } from '@ant-design/icons';
import { Link, history, useSearchParams } from '@umijs/max';
import {
  Avatar,
  Button,
  Card,
  Col,
  Divider,
  Row,
  Space,
  Typography,
  theme,
} from 'antd';
import classNames from 'classnames';
import { Element as ScrollElement, Link as ScrollLink } from 'react-scroll';
import styles from './index.less';

const features = [
  {
    title: '多种大模型',
    description:
      '内置多个流行LLM大模型，可随时切换大模型，选择最佳的模型能力。',
  },
  {
    title: '私有化部署',
    description:
      '大模型和向量数据库均部署在企业内部网络，文档和信息本地存储，保障信息安全。',
  },
  {
    title: '支持主流企业文档类型',
    description:
      '支持绝大多数文档格式，包括飞书文档、Office文档、WPS文档、电子书文档、PDF文档、Markdown文档及多媒体文档。',
  },
  {
    title: '支持多数据源',
    description:
      '一个智能问答机器人支持导入多个数据源，每个数据源支持多份文档。',
  },
  {
    title: '文档自动同步',
    description:
      '定期同步在线文档库，包括S3、OSS、FTP、飞书知识库等，保持机器人问答的时效性。',
  },
  {
    title: '可集成的机器人',
    description:
      '问答机器人可集成到产品官网、控制台以及飞书聊天工具等用户常用渠道。',
  },
  {
    title: '预加载问题',
    description: '在机器人中可预先加载用户常问问题，方便用户快速开始。',
  },
  {
    title: '材料引用',
    description: '所有回答均有引用的文档原文，方便用户做进一步的分析和挖掘。',
  },
  {
    title: '问答反馈与提升',
    description:
      '用户可以对所有回答方便标记为有用和无用，运营人员利用这些反馈进行模型优化，提升回答质量。',
  },
];

const questions = [
  {
    title: 'KubeChat如何工作？',
    description:
      'KubeChat提取你上传的文档，包括本地上传，FTP，S3，OSS等方式上传的文档，并用AI大模型理解文档内容。当用户提出问题时，我们的人工智能会根据你的文档给出答案。',
  },
  {
    title: '我能导入私有数据吗？',
    description:
      '可以。你可以将企业内部文档、飞书在线知识库、邮件等内容导入到资料库中，根据这些企业文档提供智能问答。',
  },
  {
    title: '我的数据存储在哪里？',
    description:
      '数据存储在企业私有网络内部的qdrant向量数据库和PostgreSQL数据库中。',
  },
  {
    title: '我能上传哪些类型文档？',
    description:
      'Markdown, Pdf, Docx, Excel, Pptx, ePub, Csv 文档，如果您需要上传其他文档类型请联系我们。 ',
  },
  {
    title: '我能本地部署KubeChat吗？',
    description:
      '可以。KubeChat建议您部署在企业内部环境中，这样可以保障数据安全。',
  },
  {
    title: '我怎样分享机器人？',
    description:
      'KubeChat机器人可以集成到任何网站，飞书聊天群中。我们在不断增加新的集成方式，如果您有好的建议请联系我们。',
  },
];

export default () => {
  const { token } = theme.useToken();
  const [searchParams] = useSearchParams();
  const code = searchParams.get('code');
  const state = searchParams.get('state');

  const handleCallback = async () => {
    if (!auth0Client) return;
    const result = await auth0Client.handleRedirectCallback();

    if (result?.appState?.targetUrl) {
      history.replace(result?.appState?.targetUrl);
    } else {
      history.replace('/');
    }
  };

  if (code && state) {
    handleCallback();
    return <PageLoading mask={true} />;
  }

  return (
    <>
      <div className={classNames(styles.header)}>
        <div
          className={styles.content}
          style={{ display: 'flex', justifyContent: 'space-between' }}
        >
          <Space>
            <Link to="/" className={styles.logo}>
              KubeChat
            </Link>

            <div className={styles.nav}>
              <ScrollLink
                className={styles.navItem}
                to="banner"
                smooth={true}
                offset={-100}
                duration={400}
              >
                产品概况
              </ScrollLink>
              <ScrollLink
                className={styles.navItem}
                to="feature"
                smooth={true}
                offset={-100}
                duration={400}
              >
                产品特性
              </ScrollLink>
              <ScrollLink
                className={styles.navItem}
                to="question"
                smooth={true}
                offset={-100}
                duration={400}
              >
                常见问题
              </ScrollLink>
              <ScrollLink
                className={styles.navItem}
                to="contact"
                smooth={true}
                offset={-100}
                duration={400}
              >
                联系我们
              </ScrollLink>
            </div>
          </Space>

          <Space>
            <Link to="/bots">
              <Button type="primary">免费试用</Button>
            </Link>
          </Space>
        </div>
      </div>
      <ScrollElement name="banner" className={styles.content}>
        <div className={styles.banner}>
          <div>
            <Typography.Title level={1}>
              基于KubeBlocks的企业级智能聊天机器人
            </Typography.Title>
            <Typography.Paragraph style={{ fontSize: 20 }} type="secondary">
              KubeChat用最简单的方式将您的知识库转为24小时在线技术支持机器人
            </Typography.Paragraph>
            <br />
            <br />
            <Link to="/bots">
              <Button type="primary" size="large" style={{ width: 200 }}>
                免费试用
              </Button>
            </Link>
            <br />
            <br />
            <Typography.Paragraph type="secondary" style={{ fontSize: 16 }}>
              <CheckSquareOutlined /> 私有化部署，保护信息安全
            </Typography.Paragraph>
            <Typography.Paragraph type="secondary" style={{ fontSize: 16 }}>
              <CheckSquareOutlined /> 支持飞书企业文档库
            </Typography.Paragraph>
            <Typography.Paragraph type="secondary" style={{ fontSize: 16 }}>
              <CheckSquareOutlined /> 问答检测和运营
            </Typography.Paragraph>
          </div>
          <div>
            <img width="580" src={imgBanner} />
          </div>
        </div>
      </ScrollElement>
      <div className={styles.steps}>
        <div className={styles.content}>
          <Typography.Title
            level={5}
            style={{ textAlign: 'center', color: token.colorPrimary }}
          >
            HOW IT WORKS
          </Typography.Title>
          <Typography.Title level={2} style={{ textAlign: 'center' }}>
            三步拥有您自己的智能问答机器人
          </Typography.Title>
          <br /> <br />
          <Row gutter={[80, 80]}>
            <Col
              span={14}
              style={{ borderRight: '1px solid rgba(255, 255, 255, 10%)' }}
            >
              <div className={styles.step}>
                <div className={styles.title}>
                  <span>1</span>导入您的文档，支持多数据源。
                </div>
                <Typography.Paragraph
                  type="secondary"
                  className={styles.description}
                >
                  KubeChat支持飞书文档，本地上传，FTP，AWS
                  S3，阿里云OSS等多种数据源，支持PDF，Word，Excel，PPT，CSV，Markdown，ePub等十几种文件格式。
                </Typography.Paragraph>
              </div>
              <div className={styles.step}>
                <div className={styles.title}>
                  <span>2</span>将机器人集成到您的产品
                </div>
                <Typography.Paragraph
                  type="secondary"
                  className={styles.description}
                >
                  轻松安装聊天机器人到其他网站，应用，企业IM工具，用AI为您的客户提供价值。
                </Typography.Paragraph>
              </div>

              <div className={styles.step}>
                <div className={styles.title}>
                  <span>3</span>提供24小时自动化问答
                </div>
                <Typography.Paragraph
                  type="secondary"
                  className={styles.description}
                >
                  KubeChat跟踪所有回答记录，评估回答效果，通过人工运营和大模型Fine-tune
                  不断提升回答质量。
                </Typography.Paragraph>
              </div>
            </Col>
            <Col span={10}>
              <Row gutter={[30, 50]} style={{ marginTop: 40 }}>
                {DOCUMENT_SOURCE_OPTIONS.filter((s) => s.value !== 'local').map(
                  (s, index) => (
                    <Col key={index} span="12">
                      <Card bordered={false}>
                        <Space size="large">
                          <Avatar src={s.icon} size={50} />
                          <Typography.Text strong style={{ fontSize: 14 }}>
                            {s.label}
                          </Typography.Text>
                        </Space>
                      </Card>
                    </Col>
                  ),
                )}
              </Row>
            </Col>
          </Row>
        </div>
      </div>
      <ScrollElement
        name="feature"
        className={classNames({
          [styles.content]: true,
          [styles.feature]: true,
        })}
      >
        <Typography.Title level={2} style={{ textAlign: 'center' }}>
          产品特性
        </Typography.Title>
        <br /> <br />
        <Row gutter={[30, 30]}>
          {features.map((feature, index) => (
            <Col key={index} span={8}>
              <Card className={styles.featureCard}>
                <Typography.Title level={4}>{feature.title}</Typography.Title>
                <Typography.Text
                  type="secondary"
                  style={{
                    display: 'block',
                    height: 65,
                    overflow: 'hidden',
                    fontSize: 14,
                  }}
                >
                  {feature.description}
                </Typography.Text>
              </Card>
            </Col>
          ))}
        </Row>
      </ScrollElement>
      <br /> <br />
      <br /> <br />
      <br /> <br />
      <br /> <br />
      <ScrollElement name="question" className={styles.content}>
        <Typography.Title level={2} style={{ textAlign: 'center' }}>
          常见问题
        </Typography.Title>
        <br /> <br />
        <Row gutter={[40, 40]}>
          {questions.map((feature, index) => (
            <Col key={index} span={12}>
              <Card className={styles.questionCard}>
                <Typography.Title level={5}>{feature.title}</Typography.Title>
                <Typography.Text
                  type="secondary"
                  style={{ display: 'block', height: 40, fontSize: 14 }}
                >
                  {feature.description}
                </Typography.Text>
              </Card>
            </Col>
          ))}
        </Row>
      </ScrollElement>
      <br /> <br />
      <br /> <br />
      <br /> <br />
      <br /> <br />
      <ScrollElement name="contact" className={styles.content}>
        <Typography.Title level={2} style={{ textAlign: 'center' }}>
          联系我们
        </Typography.Title>
        <br /> <br />
        <Card bodyStyle={{ padding: 40 }} bordered={false}>
          <Row gutter={[80, 80]}>
            <Col
              span={16}
              style={{
                borderRight: `1px solid ${token.colorBorderSecondary}`,
                paddingBlock: 30,
              }}
            >
              <Typography.Paragraph type="secondary" style={{ fontSize: 16 }}>
                KubeChat 是一款企业级 LLM
                机器人管理和运营平台，将企业文档本地向量化，通过鼠标点击轻松构建具有企业领域知识的大模型问答机器人，并发布到企业网站、飞书等渠道供员工和客户使用。
              </Typography.Paragraph>
              <Typography.Text type="secondary">
                欢迎联系我们咨询 KubeChat 企业版事宜。
              </Typography.Text>
            </Col>
            <Col span={8} style={{ paddingBlock: 20 }}>
              <Typography.Title level={5}>邮箱</Typography.Title>
              <Typography.Text type="secondary">
                jason@apecloud.com
              </Typography.Text>

              <Typography.Title level={5}>地址</Typography.Title>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                杭州市余杭区五常街道赛银国际商务中心12幢8楼
              </Typography.Text>
            </Col>
          </Row>
        </Card>
      </ScrollElement>
      <br />
      <br />
      <br />
      <br />
      <Divider />
      <br />
      <br />
      <div className={styles.content} style={{ textAlign: 'center' }}>
        <Typography.Title level={4} style={{ textAlign: 'center' }}>
          99%的问题都有标准答案，找个懂的Chat问问
        </Typography.Title>
        <Link to="/bots">
          <Button type="primary">免费试用</Button>
        </Link>
        <br />
        <br />
        <Typography.Paragraph type="secondary">
          © 2023 ApeCloud PTE. Ltd.
        </Typography.Paragraph>
      </div>
    </>
  );
};
