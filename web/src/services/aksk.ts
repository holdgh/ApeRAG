import { request } from '@umijs/max';

export const getAppIdSecret = () => {
  return request(`/api/v1/apikeys`,{
      method: 'GET'
    }
  );
};

export const createAppSecret = () => {
  return request(`/api/v1/apikeys`, {
    method: 'post'
  });
};

export const deleteAppSecret = (id) => {
  return request(`/api/v1/apikeys/${id}`, {
    method: 'delete'
  });
};