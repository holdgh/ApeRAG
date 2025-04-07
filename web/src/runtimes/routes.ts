import { initializeSystem } from '@/models/system';

export const render = async (oldRender: any) => {
  await initializeSystem();
  oldRender();
};
