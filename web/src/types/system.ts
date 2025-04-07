export type SystemConfig = {
  auth: {
    type: 'auth0' | 'authing' | 'logto' | 'none';
    auth_domain: string;
    auth_app_id: string;
  };
};
