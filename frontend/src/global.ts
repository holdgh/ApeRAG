import PageLoading from '@/components/PageLoading';
import React from 'react';
import ReactDOM from 'react-dom/client';

const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(React.createElement(PageLoading, {}));
}
