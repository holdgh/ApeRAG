export type Document = {
  id: number;
  name: string;
  status: 'RUNNING' | 'COMPLETE' | 'FAILED' | 'DELETED';
  size: string;
  gmt_created: string;
  gmt_deleted: string;
};

export default () => {};
