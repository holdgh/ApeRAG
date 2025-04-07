import Header from '@/components/Header';
import { DOCUMENT_DEFAULT_CONFIG } from '@/constants';
import CollectionForm from '@/pages/Collections/form';
import type { TypesCollection } from '@/types';
import { useModel } from '@umijs/max';
import { Form } from 'antd';
import _ from 'lodash';

export default () => {
  const [form] = Form.useForm();
  const { createColection } = useModel('collection');

  const onFinish = async (values) => {
    const data = _.merge(
      {
        config: DOCUMENT_DEFAULT_CONFIG,
      },
      values,
    );
    createColection(data);
  };

  return (
    <div className="workspace">
      <Header goback={true} title="Add a Collection" name="collections" page="collections-new" action={form.submit} />
      <div className="bd">
        <div className="content">
          <div className="border-block">
            <CollectionForm
              form={form}
              onSubmit={(values: TypesCollection) => onFinish(values)}
              action="add"
              values={{
                type: 'document',
                config: {
                  ...DOCUMENT_DEFAULT_CONFIG,
                },
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
