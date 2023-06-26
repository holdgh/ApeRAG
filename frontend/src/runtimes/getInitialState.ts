import { setUser } from '@/models/user';
import auth0 from '@/utils/auth0';

export type InitialStateType = {
  collapsed: boolean;
};

export async function getInitialState(): Promise<InitialStateType> {
  const user = await auth0.getIdTokenClaims();

  if (!user) await auth0.loginWithRedirect();

  setUser(user);

  return {
    collapsed: localStorage.getItem('sidebarCollapsed') === 'true',
  };
}
