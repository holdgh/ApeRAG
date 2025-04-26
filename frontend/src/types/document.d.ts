export type DocumentConfig = {
  path?: string;
  labels?: {
    [key in string]: string;
  }[];
};
