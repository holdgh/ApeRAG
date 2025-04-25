import { useTheme } from 'ahooks';
import { ThemeModeType } from 'ahooks/lib/useTheme';
import { useCallback, useState } from 'react';

export default () => {
  const [loading, setLoading] = useState<boolean>(false);

  const { theme: themeName, setThemeMode } = useTheme({
    localStorageKey: 'theme',
  });

  const setThemeName = useCallback((name: ThemeModeType) => {
    document.body.classList.add('no-animate');
    setThemeMode(name);
    setTimeout(() => {
      document.body.classList.remove('no-animate');
    }, 100);
  }, []);

  return {
    loading,
    setLoading,

    themeName,
    setThemeName,
  };
};
