import { CSS_PREFIX, THEME_TOKENS } from '@/constants';
import { ReactFlowProvider } from '@xyflow/react';
import { useDebounce, useFavicon, useTitle } from 'ahooks';
import { App, ConfigProvider, theme } from 'antd';
import { useCallback, useEffect, useMemo, useRef } from 'react';
import { Slide, ToastContainer } from 'react-toastify';
import LoadingBar, { LoadingBarRef } from 'react-top-loading-bar';
import { getLocale, Outlet, useLocation, useModel } from 'umi';
import UrlPattern from 'url-pattern';
import { Auth, AuthProvider } from './auth';
import Layout from './layout';
import LayoutBot from './layout.bot';
import LayoutCollection from './layout.collection';
import LayoutSettings from './layout.settings';
import Topbar from './topbar';

import moment from 'moment';
type LayoutConfig = {
  [key in string]: React.ReactNode;
};

const { darkAlgorithm, defaultAlgorithm } = theme;

/**
 * url pattern rules
 * https://www.npmjs.com/package/url-pattern
 */
const config: LayoutConfig = {
  '/bots(/*)': (
    <>
      <Auth>
        <LayoutBot />
      </Auth>
    </>
  ),
  '/collections(/*)': (
    <>
      <Auth>
        <LayoutCollection />
      </Auth>
    </>
  ),
  '/settings(/*)': (
    <>
      <Auth>
        <LayoutSettings />
      </Auth>
    </>
  ),
  '*': <Layout auth={false} sidebar={false} />,
};

export default () => {
  const { themeName, loading } = useModel('global');
  const location = useLocation();
  const ref = useRef<LoadingBarRef>(null);
  const { token } = theme.useToken();
  const algorithm = useMemo(
    () => (themeName.includes('dark') ? darkAlgorithm : defaultAlgorithm),
    [themeName],
  );
  const debouncedLoading = useDebounce(loading, { wait: 500 });

  const getLayout = useCallback(() => {
    const path = Object.keys(config).find((p) =>
      Boolean(new UrlPattern(p).match(location.pathname)),
    );
    return path ? config[path] : <Outlet />;
  }, [location]);

  useEffect(() => {
    if (debouncedLoading) {
      ref.current?.start();
    } else {
      ref.current?.complete();
    }
  }, [debouncedLoading]);

  useTitle(APERAG_CONFIG.title || '');
  useFavicon(APERAG_CONFIG.favicon || '');

  // useEffect(() => {
  //   scroll.scrollToTop({ duration: 100 });
  // }, [location]);

  useEffect(() => {
    const locale = getLocale();
    moment.locale(locale === 'en-US' ? 'en' : 'zh');
  }, []);

  return (
    <AuthProvider>
      <ReactFlowProvider>
        <ConfigProvider
          prefixCls={CSS_PREFIX}
          theme={{
            cssVar: {
              prefix: CSS_PREFIX,
              key: themeName,
            },
            algorithm,
            token: THEME_TOKENS[themeName],
          }}
        >
          <App>
            <Topbar />
            {getLayout()}
          </App>
          <LoadingBar ref={ref} color={token.colorPrimary} />
          <ToastContainer
            theme={themeName}
            transition={Slide}
            limit={3}
            autoClose={2000}
            position="bottom-right"
            hideProgressBar
            style={{ fontSize: token.fontSize }}
          />
        </ConfigProvider>
      </ReactFlowProvider>
    </AuthProvider>
  );
};
