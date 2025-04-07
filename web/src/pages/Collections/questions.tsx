import { useIntl, useModel, useParams } from '@umijs/max';
import {
  App,
  Row,
  Col,
  Spin,
  Card,
  Form,
  Space,
  Input,
  Button,
  Select,
  Divider,
  Pagination,
  Typography,
} from 'antd';
import { CloseOutlined, SaveOutlined, PlusOutlined, ProfileOutlined, LoadingOutlined } from '@ant-design/icons';
import _ from 'lodash';
import { useEffect, useState } from 'react';

export default () => {
  const [ form ] = Form.useForm();
  const { modal } = App.useApp();
  const { formatMessage } = useIntl();
  const { collectionId } = useParams();
  const { questions, setQuestions, questionsLoading, totalQuestions, questionGenerating, getQuestions, GetQuestionDetails, DeleteRelatedQuestion, GenRelatedQuestions, UpdateRelatedQuestion } = useModel('collection');
  const { documents, documentLoading, totalCount, getDocuments } = useModel('document');
  const [ documentOptions, setDocumentOptions ] = useState();
  const [ pageSize, setPageSize ] = useState<number>(10);
  const [ pageNumberDoc, setPageNumberDoc ] = useState<number>(1);
  const [ pageNumberQuestion, setPageNumberQuestion ] = useState<number>(1);
  const [ questionEditing, setQuestionEditing ] = useState<number>();
  const [ questionLoading, setQuestionLoading ] = useState<number>();

  const getDocument = async (page?:any, page_size?:any) => {
    const pageId = page || pageNumberDoc;
    const page_Size = page_size || pageSize;
    getDocuments(String(collectionId), pageId, page_Size);
    setPageNumberDoc(pageId);
  };

  const getAllQuestions = async (page?:any, page_size?:any) => {
    let pageId = page || pageNumberQuestion;
    let page_Size = page_size || pageSize;
    getQuestions(String(collectionId), pageId, page_Size);
    setPageNumberQuestion(pageId);
  };

  const getRelatedDocuments = async (idx:number) => {
    const values = form.getFieldValue('related_questions');
    const question = values?.[idx];
    const questionId = question?.id;
    if(questionId){
      setQuestionLoading(idx);
      const res = await GetQuestionDetails(collectionId, questionId);
      let newQuestions = questions.filter(item=>1);
      let question = res?.data;
      if(!question.relate_documents_loaded){
        question.relate_documents_loaded = true;
      }
      newQuestions[idx] = question;
      setQuestions(newQuestions);
      setQuestionLoading(-1);
    }
  }

  const changePage = (page:any) => {
    getDocument(page);
  };

  const changePageQuestion = (page:any) => {
    getAllQuestions(page);
  };

  const onGenQuestions = async()=>{
    const data = await GenRelatedQuestions(collectionId);
    if(data?.code==='200'){
      getAllQuestions();
    }
  };

  const onSave = async (idx:number) => {
    setQuestionEditing(idx);
    const values = form.getFieldValue('related_questions');
    const question = values?.[idx];
    if(question){
      await UpdateRelatedQuestion(collectionId, question);
      setQuestionEditing(false);
      getAllQuestions();
    }
    setQuestionEditing(-1);
  };

  const onDelete = (idx:number, fnRemove:Function) => {
    const items = questions;
    if(!items || !items[idx]){
      fnRemove(idx);
      return;
    }
    modal.confirm({
      title: formatMessage({ id: 'text.delete.help' }),
      content: <>{formatMessage({ id: 'text.delete.confirm' })}</>,
      onOk: async () => {
        setQuestionEditing(idx);
        await DeleteRelatedQuestion(collectionId, items[idx]?.id);
        setQuestionEditing(-1);
        fnRemove(idx);
        let pages = Math.ceil((totalQuestions-1) / pageSize);
        if(pageNumberQuestion > pages && pages>0){
          getAllQuestions(pages);
        }else{
          getAllQuestions();
        }
      },
      okButtonProps: {
        danger: true,
      },
    });
  };

  useEffect(() => {
    getAllQuestions();
    if(!documents){
      getDocument();
    }
  },[collectionId]);

  useEffect(()=>{
    if(questions){
      form.setFieldValue('related_questions', questions);
    }
  },[questions]);
  

  useEffect(() => {
    if(documents){
      const options = documents.filter(item=>item.status==='COMPLETE').map(item=>{
        return {"label":item.name, "value":item.id}
      });
      setDocumentOptions(options);
    }
  },[documents]);

  return (
    <div className="block questions">
      <Spin 
        indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} 
        spinning={questionsLoading}
      >
      <Form form={form}>
      <Form.List name='related_questions'>
        {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name}) => (
                <Card 
                  key={key} 
                  style={{ marginBottom: 20 }}
                  title={`${formatMessage({id:'text.question'})} ${name + 1 + (pageNumberQuestion - 1) * pageSize}`}
                  loading={questionEditing===name}
                  extra={
                    <>
                      <SaveOutlined 
                        style={{margin:'0 1rem'}}
                        onClick={() => {
                          onSave(name);
                        }}
                      />
                      <CloseOutlined
                        onClick={() => {
                          onDelete(name, remove);
                        }}
                      />
                    </>
                  }
                >
                  <Row>
                    <Col span="24">
                    <Form.Item
                        name={[name, 'id']}
                        hidden
                      >
                        <Input />
                      </Form.Item>
                      <Form.Item
                        name={[name, 'question']}
                        style={{margin:'0 0 5px'}}
                        rules={[
                          { required: true, message: `${formatMessage({id:'text.question'})}${formatMessage({id:'msg.required'})}`},
                        ]}
                      >
                        <Input placeholder={formatMessage({id:'text.question'})} />
                      </Form.Item>

                      <Form.Item
                        style={{margin:'0 0 5px'}}
                        name={[name, 'answer']}
                      >
                        <Input.TextArea autoSize={{ minRows: 1, maxRows: 2 }} 
                        placeholder={formatMessage({id:'text.answer_ai'})} />
                      </Form.Item>
                    { questions[name]?.id && !questions[name]?.relate_documents_loaded  ? (
                      <Button 
                        style={{width:'100%'}}
                        loading={questionLoading===name}
                        onClick={() => {
                          getRelatedDocuments(name);
                        }}
                      >
                        {formatMessage({id:'text.related_question.documents'})}
                      </Button>
                    ) : (
                      <Form.Item
                        style={{margin:'0'}}
                        name={[name, 'relate_documents']}
                      >
                        <Select
                          mode="multiple"
                          allowClear
                          style={{ width: '100%' }}
                          maxTagCount='responsive'
                          placeholder={formatMessage({id:'text.related_question.documents'})}
                          options={documentOptions}
                          loading={documentLoading}
                          dropdownRender={(menu) => (
                            <>
                              {menu}
                              {Math.ceil(totalCount/pageNumberDoc)>1 && (
                                <>
                                <Divider style={{ margin: '8px 0' }} />
                                <Space style={{ display:'flex', justifyContent:'center' }}>
                                  <Pagination
                                    simple 
                                    hideOnSinglePage
                                    current={pageNumberDoc}
                                    pageSize={pageSize}
                                    total={totalCount}
                                    onChange={changePage}
                                  />
                                </Space>
                                </>
                              )}
                            </>
                          )}
                        />
                      </Form.Item>
                    )}
                    </Col>
                  </Row>
                </Card>
              ))}
                <Pagination
                  simple 
                  hideOnSinglePage
                  current={pageNumberQuestion}
                  pageSize={pageSize}
                  total={totalQuestions}
                  onChange={changePageQuestion}
                  style={{margin:'1rem 0'}}
                />
                <Row gutter={[8, 8]}>
                  <Col span="12">
                    <Button
                      type="dashed"
                      onClick={() => add()}
                      block
                      icon={
                        <Typography.Text type="secondary">
                          <PlusOutlined />
                        </Typography.Text>
                      }
                    >
                      {formatMessage({id:'text.related_question.new'})}
                    </Button>
                  </Col>
                  <Col span="12">
                    <Button
                      type="dashed"
                      onClick={onGenQuestions}
                      loading={questionGenerating}
                      disabled={questionGenerating}
                      block
                    >
                      {formatMessage({id:'text.related_question.gen'})}
                    </Button>
                  </Col>
                </Row>
              </>
            )}
      </Form.List>
      </Form>
      </Spin>
    </div>
  );
};
