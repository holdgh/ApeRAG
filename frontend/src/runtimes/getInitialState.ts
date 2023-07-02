import { setUser } from '@/models/user';
import auth0 from '@/utils/auth0';

export type InitialStateType = {
  collapsed: boolean;
};

export async function getInitialState(): Promise<InitialStateType> {
  let user = await auth0.getIdTokenClaims();
  if (!user) await auth0.loginWithRedirect();



  user = {
    ...user,
    picture: 'https://img2.baidu.com/it/u=1582585185,2774298853&fm=253&fmt=auto&app=138&f=JPG?w=500&h=500',
    nickname: 'ApeCloud'
  }



  setUser(user);

  return {
    collapsed: localStorage.getItem('sidebarCollapsed') === 'true',
  };
}
