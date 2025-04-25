import { Menu, MenuProps } from 'antd';
import { useMemo } from 'react';
import { FormattedMessage, history, Outlet, useIntl, useLocation } from 'umi';
import { BodyContainer } from './body';
import { Navbar, NavbarBody, NavbarHeader } from './navbar';
import Sidebar from './sidebar';

type MenuItem = Required<MenuProps>['items'][number];

export default () => {
  const location = useLocation();
  const { formatMessage } = useIntl();
  const menuItems = useMemo(
    (): MenuItem[] => [
      {
        label: <FormattedMessage id="users.management" />,
        key: `/settings/users`,
      },
      {
        label: <FormattedMessage id="model.provider" />,
        key: `/settings/model_providers`,
      },
    ],
    [],
  );

  return (
    <>
      <Sidebar />
      <Navbar>
        <NavbarHeader title={formatMessage({ id: 'system.management' })} />
        <NavbarBody>
          <Menu
            onClick={({ key }) => history.push(key)}
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            style={{
              padding: 0,
              background: 'none',
              border: 'none',
            }}
          />
        </NavbarBody>
      </Navbar>
      <BodyContainer sidebar={true} navbar={true}>
        <Outlet />
      </BodyContainer>
    </>
  );
};
