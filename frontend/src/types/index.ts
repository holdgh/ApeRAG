export type Merge<M, N> = Omit<M, Extract<keyof M, keyof N>> & N;

export * from './bot';
export * from './collection';
export * from './document';
