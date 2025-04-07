import './index.css'
import { Outlet, history } from 'umi'
import { useState, useEffect } from 'react';
import CollapseBtn from '@/components/CollapseBtn';
import Menu from '@/components/Menu';
import User from '@/components/User';

export default (props) => {
  const [menuCollapse, setMenuCollapse] = useState(0);
  useEffect(() => {
    const key = history.location.pathname.replace(/.*\//g, '');
    if(key==='web'){
      history.replace('/bots');
    }
  }, [history.location]);
  return (
    <div className="page">
      <div className="side">
        <div className="container">
          <CollapseBtn menuCollapse={menuCollapse} setMenuCollapse={setMenuCollapse} />
          <h1 className="logo">ApeRAG</h1>
          <Menu menuCollapse={menuCollapse} setMenuCollapse={setMenuCollapse} />
          <User />
        </div>
      </div>
      <div className="main">
        <Outlet/>
      </div>
    </div>
  );
};
