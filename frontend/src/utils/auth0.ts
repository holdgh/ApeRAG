import { Auth0Client } from '@auth0/auth0-spa-js';

const auth0 = new Auth0Client({
  domain: AUTH0_DOMAIN,
  clientId: AUTH0_CLIENT_ID,
  authorizationParams: {
    redirect_uri: HOSTNAME,
  },
});

try {
  await auth0.getTokenSilently();
} catch (err: any) {}

export default auth0;
