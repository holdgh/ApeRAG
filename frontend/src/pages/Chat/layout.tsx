import { Outlet } from "@umijs/max";
import { useParams } from "@umijs/max";
import { Navigate, useModel } from "@umijs/max";

export default () => {
  const { chatId } = useParams();
  const { currentChat } = useModel("collection");


  if(!currentChat) {
    return null;
  } else {
    if(chatId && String(chatId) === String(currentChat.id)) {
      return <Outlet />
    } else {
      return <Navigate to={`/chat/${currentChat.id}`} />
    }
  }
}