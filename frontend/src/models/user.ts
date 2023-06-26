import type { User } from '@auth0/auth0-spa-js';

let user: User | undefined = undefined;

export const getUser = () => user;

export const setUser = async (u: User | undefined) => {
  user = u;
};
