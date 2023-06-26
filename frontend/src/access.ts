import { InitialStateType } from './runtimes/getInitialState';

export default (initialState: InitialStateType) => {
  const isLogin = initialState?.user === undefined;
  return {
    isLogin,
  };
};
