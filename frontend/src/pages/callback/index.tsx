import { useTimeout } from 'ahooks';
import { useSearchParams } from 'umi';

export default (): any => {
  const [searchParams] = useSearchParams();
  const code = searchParams.get('code');
  const redirectUri =
    searchParams.get('redirectUri') ||
    encodeURIComponent(`${window.location.origin}${BASE_PATH}`);

  useTimeout(() => {
    if (code) window.location.href = decodeURIComponent(redirectUri);
  }, 1000);

  return null;
};
