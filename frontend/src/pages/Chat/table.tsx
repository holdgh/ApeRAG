import { Table, Tooltip, Typography } from 'antd';
import { ColumnsType } from 'antd/es/table';
import _ from 'lodash';

type Props = {
  dataSource: { [key in string]: string | number }[];
  loading: boolean;
};

export default ({ dataSource, loading }: Props) => {
  const columns: ColumnsType<any> = _.map(
    _.first(dataSource),
    (value, key) => ({
      title: key,
      dataIndex: key,
      ellipsis: {
        showTitle: false,
      },
      sorter: (a, b) => {
        return String(a[key]).charCodeAt(0) - String(b[key]).charCodeAt(0);
      },
      render: (text) => (
        <Typography.Text
          type="secondary"
          ellipsis
          style={{ minWidth: 40, maxWidth: 100, fontSize: 12 }}
        >
          {text ? (
            <Tooltip placement="left" title={text}>
              {text}
            </Tooltip>
          ) : null}
        </Typography.Text>
      ),
    }),
  );

  dataSource.forEach((d, index) => (d['__key'] = index));

  return (
    <Table
      tableLayout="fixed"
      rowKey="__key"
      scroll={{
        x: true,
      }}
      pagination={{
        hideOnSinglePage: true,
      }}
      size="small"
      loading={loading}
      columns={columns}
      dataSource={dataSource}
    />
  );
};
