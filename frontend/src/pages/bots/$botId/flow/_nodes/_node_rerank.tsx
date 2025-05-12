import { ModelSelect } from '@/components';
import { ApeNode } from '@/types';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Form, theme } from 'antd';
import { useEffect, useMemo } from 'react';
import { useIntl, useModel } from 'umi';
import { StyledFlowNodeSection } from './_styles';

type VarType = {
  model: string;
};
export const ApeNodeRerank = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { formatMessage } = useIntl();
  const { nodes, setNodes } = useModel('bots.$botId.flow.model');
  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);
  const [form] = Form.useForm<VarType>();

  const onValuesChange = (changedValues: VarType) => {
    if (!originNode) return;

    const vars = originNode?.data.vars;
    const varModel = vars?.find((item) => item.name === 'model');

    if (varModel && changedValues.model !== undefined) {
      varModel.value = changedValues.model;
    }

    setNodes((nds) => {
      const changes: NodeChange[] = [
        {
          id: originNode.id,
          type: 'replace',
          item: {
            ...originNode,
          },
        },
      ];
      return applyNodeChanges(changes, nds);
    });
  };

  useEffect(() => {
    const model = String(
      originNode?.data.vars?.find((item) => item.name === 'model')?.value,
    );
    form.setFieldsValue({ model });
  }, []);

  return (
    <StyledFlowNodeSection token={token}>
      <Form
        form={form}
        layout="vertical"
        onValuesChange={onValuesChange}
        autoComplete="off"
      >
        <Form.Item
          name="model"
          label={formatMessage({ id: 'flow.reranker.model' })}
        >
          <ModelSelect
            style={{ width: '100%' }}
            model="rerank"
            variant="filled"
          />
        </Form.Item>
      </Form>
    </StyledFlowNodeSection>
  );
};
