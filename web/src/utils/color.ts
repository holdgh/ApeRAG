import uniqColor from 'uniqolor';

export const getUniqColor = (d: string | number) => {
  return uniqColor(d, {
    lightness: [40, 50],
  }).color;
};
