import PageLoading from '@/components/PageLoading';
import ReactDOM from 'react-dom/client';

const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(<PageLoading message="authorize..." />);
}
