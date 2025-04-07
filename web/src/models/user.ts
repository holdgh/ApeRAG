import type { User } from '@auth0/auth0-react';
import { useEffect, useState } from 'react';
import { request } from '@umijs/max';

export const GetUserInfo = (): Promise<{
  code: string;
  data: any;
  message?: string;
}> => {
  return request(`/api/v1/user_info`, {
    method: 'GET',
  });
};

let _user: User | undefined = undefined;

export const getUser = () => _user;

export default () => {
  const [user, setUser] = useState<User>();
  const [userInfo, setUserInfo] = useState();
  const GetUser = async () => {
    const userInfo = await GetUserInfo();
    setUserInfo(userInfo.data);
  }

  useEffect(() => {
    _user = user;
    if(user && !userInfo){
      GetUser();
    }
    if(_user && userInfo){
      _user.is_admin = userInfo?.is_admin;
    }
  }, [user, userInfo]);

  return {
    user,
    setUser,
  };
};
