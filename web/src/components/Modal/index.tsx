import { Button, Modal } from 'antd';

const CustomModal: React.FC = ({show, onCancel, onConfirm, id, msg}: any) => {
  return (
    <>
      <Modal title={null} open={show} footer={null} onCancel={()=> onCancel()}>
        <div className="ant-modal-header">
          <i className="warning-icon"></i>
          <span className="title">{msg?msg[0]:'确认删除此文档？'}</span>
        </div>
        <div className="ant-modal-main">
          <span className="text">{msg?msg[1]:'删除后将无法恢复，请谨慎操作！'}</span>
        </div>
        <div className="ant-modal-footer">
          <Button type="default" onClick={()=> onCancel()}>{msg?msg[2]:'取消'}</Button>
          <Button danger onClick={()=> onConfirm(id)}>{msg?msg[3]:'确认'}</Button>
        </div>
      </Modal>
    </>
  );
};

export default CustomModal;
