import { App, Card, Col, Form, Row, Typography, Button, Tooltip } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { useIntl, useModel } from '@umijs/max';
import { useState, useEffect } from 'react';
import Header from '../../components/Header';

export default() => {
  const { aksk, akskLoading, getAKSK, createAKSK, deleteAKSK } = useModel('aksk');
  const { modal } = App.useApp();
  const { formatMessage } = useIntl();
  const [acting, setActing] = useState(false);

  const onCreate = () => {
    modal.confirm({
      title: formatMessage({ id: 'text.newkey' }),
      content: <>{formatMessage({ id: 'text.newkey.help' })}<br/>{formatMessage({ id: 'text.confirm' })}</>,
      onOk: async () => {
        setActing(true);
        await createAKSK();
        await getAKSK();
        setActing(false);
      },
      okButtonProps: {
        danger: true,
        loading: acting,
      },
    });
  };

  const onDelete = (id) => {
    modal.confirm({
      title: formatMessage({ id: 'text.deletekey' }),
      content: <>{formatMessage({ id: 'text.deletekey.help' })}<br/>{formatMessage({ id: 'text.confirm' })}</>,
      onOk: async () => {
        setActing(true);
        await deleteAKSK(id);
        await getAKSK();
        setActing(false);
      },
      okButtonProps: {
        danger: true,
        loading: acting,
      },
    });
  };

  useEffect(()=>{
    if(!aksk){
      getAKSK();
    }
  },[aksk])

  return (
    <div className="workspace">
        <Header
          name="dev-settings"
          title={formatMessage({id:'text.dev'})}
          page="dev-settings"
          action={onCreate}
          goback={false}
        />
        <div className="bd">
        { aksk?.map((item,index)=>(
            <Card 
              key={index}
              type="inner" 
              style={{marginBottom:'16px'}}
              title={formatMessage({id:'text.authorize'})} 
              loading={akskLoading}
              extra={
                <Tooltip title={formatMessage({id:'text.deletekey'})}>
                  <Button icon={<DeleteOutlined />} onClick={()=>onDelete(item.id)} type="text" danger />
                </Tooltip>
              }
              >
                <Row gutter={[8, 0]}>
                  <Col xs={24} lg={12}>
                    <Form.Item label="App ID">
                      <Typography.Text copyable type="secondary" ellipsis={true}>
                        {item?.id}
                      </Typography.Text>
                    </Form.Item>
                    
                  </Col>
                  <Col xs={24} lg={12}>
                    <Form.Item label="App Secret">
                      <Typography.Text copyable type="secondary" ellipsis={true}>
                        {item?.key}
                      </Typography.Text>
                    </Form.Item>
                  </Col>
                </Row>
            </Card>
          ))}
        </div>
      </div>
  );
};