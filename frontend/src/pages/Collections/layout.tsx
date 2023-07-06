import Layout from "@/components/Layout";
import { Outlet } from "@umijs/max";

export default () => {
  return (
    <Layout
      sidebar={{
        title: 'DocChat',
        width: 220,
      }}
    >
       <Outlet />
    </Layout>
  );
}