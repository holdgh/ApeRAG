export default {
  'GET /api/v1/user': {
    code: '200',
    data: {
      username: 'sailwebs',
      email: 'sailwebs@gmail.com',
      role: 'admin',
      is_active: true,
      date_joined: '2025-04-22T11:20:30.736787+00:00',
    },
  },

  'POST /api/v1/login': (req: any, res: any) => {
    res.status(200).json({
      code: '200',
      data: {
        username: 'sailwebs',
        email: 'sailwebs@gmail.com',
        role: 'admin',
        is_active: true,
        date_joined: '2025-04-22T11:20:30.736787+00:00',
      },
    });
  },

  'POST /api/v1/register': (req: any, res: any) => {
    res.status(200).json({
      code: '200',
      data: {
        username: 'sailwebs',
        email: 'sailwebs@gmail.com',
        role: 'admin',
        is_active: true,
        date_joined: '2025-04-22T11:20:30.736787+00:00',
      },
    });
  },
  'POST /api/v1/change-password': { code: '200' },
  'POST /api/v1/logout': { code: '200', data: {} },
};
