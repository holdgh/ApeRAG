import { SchemaProperty } from "@/api";
import { ApeNode } from "@/types";
import { Table, TableProps, Tag, theme } from "antd";
import _ from "lodash";
import { useMemo } from "react";
import { useIntl } from 'umi';

type OutPut = SchemaProperty & { name: string };

export const OutputParams = ({ node }: { node: ApeNode }) => {
   const { token } = theme.useToken();
    const { formatMessage } = useIntl();

  
    const outputs = useMemo(() => {
    const schema = node.data.output?.schema;
    if (schema?.type === 'object' && schema?.properties) {
      return Object.keys(schema?.properties).map((key) => {
        const result: OutPut = {
          ..._.get(schema.properties, key),
          name: key,
        };
        return result;
      });
    }
    return [];
  }, [node]);

  const columns: TableProps<OutPut>['columns'] = useMemo(
    () => [
      {
        title: formatMessage({ id: 'flow.variable.title' }),
        dataIndex: 'name',
      },
      {
        title: formatMessage({ id: 'flow.variable.type' }),
        dataIndex: 'type',
        render: (value) => <Tag color={token.colorPrimary}>{value}</Tag>,
      },
    ],
    [],
  );
  
  return <Table
        rowKey="name"
        pagination={false}
        size="small"
        bordered
        columns={columns}
        dataSource={outputs}
      />
}