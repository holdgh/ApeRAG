import { ApeNode } from '@/types';
import Icon, { MergeCellsOutlined } from '@ant-design/icons';
import { applyNodeChanges, NodeChange } from '@xyflow/react';
import { Button, Form, Slider, Space, theme, Typography } from 'antd';
import { useEffect, useMemo } from 'react';
import { LuTextSearch } from 'react-icons/lu';
import { FormattedMessage, useModel } from 'umi';

type VarType = {
  top_k: number;
  similarity_threshold: number;
};

export const ApeNodeVectorSearch = ({ node }: { node: ApeNode }) => {
  const { token } = theme.useToken();
  const { nodes, setNodes } = useModel('bots.$botId.flow.model');
  const originNode = useMemo(() => nodes.find((n) => n.id === node.id), [node]);

  const [form] = Form.useForm<VarType>();

  const onValuesChange = (changedValues: VarType) => {
    if (!originNode) return;

    const vars = originNode?.data.vars;
    const varTopK = vars?.find((item) => item.name === 'top_k');
    const varSimilarityThreshold = vars?.find(
      (item) => item.name === 'similarity_threshold',
    );

    if (varTopK && changedValues.top_k !== undefined) {
      varTopK.value = changedValues.top_k;
    }

    if (
      varSimilarityThreshold &&
      changedValues.similarity_threshold !== undefined
    ) {
      varSimilarityThreshold.value = changedValues.similarity_threshold;
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
    const vars = originNode?.data.vars;
    const top_k = Number(vars?.find((item) => item.name === 'top_k')?.value);
    const similarity_threshold = Number(
      vars?.find((item) => item.name === 'similarity_threshold')?.value,
    );
    form.setFieldsValue({ top_k, similarity_threshold });
  }, [originNode]);

  return (
    <>
      <Space
        style={{
          display: 'flex',
          marginBottom: 8,
          justifyContent: 'space-between',
        }}
      >
        <Space>
          <Icon viewBox="0 0 14 14" style={{ color: token.blue }}>
            <LuTextSearch />
          </Icon>
          <Typography.Text>检索参数</Typography.Text>
        </Space>
      </Space>
      <Form
        size="small"
        form={form}
        layout="vertical"
        onValuesChange={onValuesChange}
      >
        <Form.Item
          required
          style={{ marginBottom: 0 }}
          label="top_k"
          name="top_k"
        >
          <Slider style={{ margin: 0 }} min={1} max={10} step={1} />
        </Form.Item>
        <Form.Item
          required
          style={{ marginBottom: 0 }}
          label="similarity_threshold"
          name="similarity_threshold"
        >
          <Slider style={{ margin: 0 }} min={0.1} max={1} step={0.1} />
        </Form.Item>
      </Form>
      <Space
        style={{
          display: 'flex',
          marginBlock: 8,
          justifyContent: 'space-between',
        }}
      >
        <Space>
          <MergeCellsOutlined style={{ color: token.blue }} />
          <Typography.Text>输入参数</Typography.Text>
        </Space>
        <Button type="text" size="small" style={{ fontSize: 12 }}>
          <FormattedMessage id="action.add" />
        </Button>
      </Space>
    </>
  );
};
