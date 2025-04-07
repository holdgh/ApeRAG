import {
  getAppIdSecret,
  createAppSecret,
  deleteAppSecret,
} from '@/services/aksk';
import { useState } from 'react';


export default () => {
  const [aksk, setAKSK] = useState();
  const [akskLoading, setAKSKLoading] = useState(false);

  const getAKSK = async () => {
    setAKSKLoading(true);
    const { data } = await getAppIdSecret();
    setAKSK(data);
    setAKSKLoading(false);
  };

  const createAKSK = async () => {
    setAKSKLoading(true);
    const { data } = await createAppSecret();
    setAKSKLoading(false);
  };

  const deleteAKSK = async (id) => {
    setAKSKLoading(true);
    const { data } = await deleteAppSecret(id);
    setAKSKLoading(false);
  };

  return {
    aksk,
    akskLoading,
    getAKSK,
    createAKSK,
    deleteAKSK,
  };
};
