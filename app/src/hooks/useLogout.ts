import { useCallback } from "react";
import { toast } from "sonner";
import { authStorage } from "@/lib/authStorage";
import { useStore } from "@/store/useStore";

export function useLogout(): () => void {
  const setCurrentUser = useStore((state) => state.setCurrentUser);
  const setCurrentHousehold = useStore((state) => state.setCurrentHousehold);

  return useCallback(() => {
    authStorage.clear();
    setCurrentUser(null);
    setCurrentHousehold(null);
    toast.success("Logged out");
  }, [setCurrentUser, setCurrentHousehold]);
}

