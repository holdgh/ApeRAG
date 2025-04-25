import { Outlet } from 'umi';
import { Auth } from './auth';
import { BodyContainer } from './body';
import Sidebar from './sidebar';

export default ({
  sidebar = true,
  auth = true,
}: {
  sidebar?: boolean;
  auth?: boolean;
}) => {
  const element = (
    <>
      {sidebar && <Sidebar />}
      <BodyContainer sidebar={sidebar} navbar={false}>
        <Outlet />
      </BodyContainer>
    </>
  );
  return auth ? <Auth>{element}</Auth> : element;
};
