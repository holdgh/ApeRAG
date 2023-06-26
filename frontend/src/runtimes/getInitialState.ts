import auth0 from '@/utils/auth0';
import type { User } from '@auth0/auth0-spa-js';

export type InitialStateType = {
  collapsed: boolean;
  user?: User;
};

export async function getInitialState(): Promise<InitialStateType> {
  const user = await auth0.getUser();

  // if(!user) await auth0.loginWithRedirect();

  return {
    user,
    collapsed: localStorage.getItem('sidebarCollapsed') === 'true',
  };
}
