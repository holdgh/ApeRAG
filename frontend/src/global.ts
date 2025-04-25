import { Config } from '@/api';
import axios from 'axios';

const loadConfig = () =>
  new Promise((resolve) => {
    axios
      .get('/api/v1/config')
      .then((res) => {
        const conf: Config = res.data;
        Object.assign(APERAG_CONFIG, conf);
        resolve(APERAG_CONFIG);
      })
      .catch(() => {
        resolve(APERAG_CONFIG);
      });
  });

await loadConfig();
